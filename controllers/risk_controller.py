from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date
from models.models import Users, HealthMetrics, RiskAssessments, RiskTrends
import json
import random
import traceback
import math

risk_bp = Blueprint('risk', __name__, url_prefix='/api/risk')

# 延迟获取db，解决循环导入问题
def get_db():
    from extensions import db
    return db

# 安全格式化月份标签，兼容datetime/字符串/None类型
def _format_month_label(month_value):
    if month_value is None:
        return '--'
    # 兼容date/datetime对象
    if isinstance(month_value, (datetime, date)):
        return f"{month_value.month}月"
    # 兼容MySQL的日期字符串（2025-12-01）
    try:
        parsed = datetime.strptime(str(month_value), '%Y-%m-%d').date()
        return f"{parsed.month}月"
    except (ValueError, TypeError):
        # 兜底：取前2位转数字
        try:
            month = int(str(month_value)[:2])
            return f"{month}月"
        except:
            return '--'

# 默认响应结构，避免500错误返回空数据
def build_default_risk_response():
    return {
        'diseaseRisks': [],
        'riskTrend': {'months': [], 'values': [], 'confidenceLow': [], 'confidenceHigh': []},
        'riskFactors': [],
        'healthSuggestion': '暂无健康评估数据，建议完善个人健康指标后重新评估',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@risk_bp.route('/assessment', methods=['GET'])
@jwt_required()
def get_risk_assessment():
    try:
        # 获取JWT中的用户ID并转换为整数
        user_id_str = get_jwt_identity()
        if not user_id_str or not str(user_id_str).isdigit():
            return jsonify(build_default_risk_response()), 400
        user_id = int(user_id_str)

        # 获取用户的风险评估（适配新表的assessment_id主键）
        assessments = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).all()
            
        # 获取风险趋势（适配新表的trend_id主键）
        trends = RiskTrends.query.filter_by(user_id=user_id).order_by(
            RiskTrends.month_start).all()
            
        # 如果没有评估，生成一个新的
        if not assessments:
            generate_risk_assessment(user_id)
            assessments = RiskAssessments.query.filter_by(user_id=user_id).order_by(
                RiskAssessments.assessment_date.desc()).all()
                
        # 如果没有趋势，生成趋势
        if not trends:
            generate_risk_trends(user_id)
            trends = RiskTrends.query.filter_by(user_id=user_id).order_by(
                RiskTrends.month_start).all()
                
        # 格式化疾病风险（适配Numeric类型转float，增强返回字段）
        disease_risks = []
        for assessment in assessments[:3]:  # 取前3个评估
            # 解析风险因素（JSON字符串转字典）
            try:
                factors = json.loads(assessment.key_factors) if isinstance(assessment.key_factors, str) else (assessment.key_factors or {})
            except:
                factors = {}
            
            # 解析建议（换行符转数组）
            recommendations = assessment.recommendations.split('\n') if assessment.recommendations else []
            
            disease_risks.append({
                'disease': assessment.disease,
                'risk': round(float(assessment.risk_score) / 100, 2),  # Numeric转float，转换为0-1的比例
                'riskLevel': assessment.risk_level or 'low',
                'desc': get_risk_description(assessment, factors),
                'factors': factors,
                'recommendations': recommendations,
                'assessmentDate': assessment.assessment_date.strftime('%Y-%m-%d')
            })
            
        # 格式化风险趋势（适配新表字段，增强置信区间）
        months = []
        values = []
        confidenceLow = []
        confidenceHigh = []
        for trend in trends:
            months.append(_format_month_label(trend.month_start))
            values.append(round(float(trend.predicted_score or 0) / 100, 2))
            confidenceLow.append(round(float(trend.confidence_low or 0) / 100, 2))
            confidenceHigh.append(round(float(trend.confidence_high or 0) / 100, 2))
            
        # 获取风险因素（合并所有评估的Top5因素）
        risk_factors = get_risk_factors(user_id)
        
        # 生成整体健康建议
        health_suggestion = get_comprehensive_suggestion(disease_risks)
            
        response = {
            'diseaseRisks': disease_risks,
            'riskTrend': {
                'months': months,
                'values': values,
                'confidenceLow': confidenceLow,
                'confidenceHigh': confidenceHigh
            },
            'riskFactors': risk_factors,
            'healthSuggestion': health_suggestion,
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"【风险评估核心错误】{traceback.format_exc()}")
        return jsonify(build_default_risk_response()), 200  # ✅ 改为200，避免前端报错

def generate_risk_assessment(user_id):
    """生成用户的疾病风险评估"""
    try:
        db = get_db()
        user = Users.query.get(user_id)
        if not user:
            raise ValueError(f"用户ID {user_id} 不存在")
        
        metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).limit(10).all()
            
        # ✅ 年龄计算（增强None处理）
        age = 30  # 默认30岁
        if user.birth_date:
            try:
                today = date.today()
                age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
            except:
                age = 30
        
        # ✅ BMI计算（增强None处理）
        bmi = 22.0
        try:
            if user.height_cm and user.weight_kg and float(user.height_cm) > 0:
                height_m = float(user.height_cm) / 100
                weight_kg = float(user.weight_kg)
                bmi = round(weight_kg / math.pow(height_m, 2), 1)
        except:
            bmi = 22.0
            
        # 安全平均值计算
        def safe_avg(values):
            try:
                valid = [float(v) for v in values if v is not None]
                return round(sum(valid)/len(valid), 1) if valid else None
            except:
                return None
        
        avg_systolic = safe_avg([m.blood_pressure_systolic for m in metrics]) or 120.0
        avg_diastolic = safe_avg([m.blood_pressure_diastolic for m in metrics]) or 80.0
        avg_heart_rate = safe_avg([m.heart_rate for m in metrics]) or 75.0
        avg_sleep = safe_avg([float(m.sleep_duration) for m in metrics if m.sleep_duration]) or 7.0
        avg_blood_sugar = safe_avg([m.blood_sugar for m in metrics if hasattr(m, 'blood_sugar') and m.blood_sugar]) or 5.5
        
        # 评估各类疾病风险
        hbp_risk = assess_hypertension_risk(avg_systolic, avg_diastolic, age, bmi, user.gender or 'unknown')
        sleep_apnea_risk = assess_sleep_apnea_risk(bmi, avg_sleep, avg_heart_rate, user.gender or 'unknown', age)
        metabolic_risk = assess_metabolic_risk(bmi, avg_systolic, avg_heart_rate, avg_sleep, avg_blood_sugar, age)
        
        today = date.today()
        
        assessments = [
            RiskAssessments(
                user_id=user_id,
                disease='高血压',
                assessment_date=today,
                risk_score=hbp_risk['score'],
                risk_level=hbp_risk['level'],
                key_factors=json.dumps(hbp_risk['factors'], ensure_ascii=False),
                recommendations='\n'.join(hbp_risk['recommendations']),
                model_version='2.0'
            ),
            RiskAssessments(
                user_id=user_id,
                disease='睡眠呼吸暂停',
                assessment_date=today,
                risk_score=sleep_apnea_risk['score'],
                risk_level=sleep_apnea_risk['level'],
                key_factors=json.dumps(sleep_apnea_risk['factors'], ensure_ascii=False),
                recommendations='\n'.join(sleep_apnea_risk['recommendations']),
                model_version='2.0'
            ),
            RiskAssessments(
                user_id=user_id,
                disease='代谢综合征',
                assessment_date=today,
                risk_score=metabolic_risk['score'],
                risk_level=metabolic_risk['level'],
                key_factors=json.dumps(metabolic_risk['factors'], ensure_ascii=False),
                recommendations='\n'.join(metabolic_risk['recommendations']),
                model_version='2.0'
            )
        ]
        
        db.session.add_all(assessments)
        db.session.commit()
        
    except Exception as e:
        get_db().session.rollback()
        print(f"❌ 生成风险评估失败: {e}\n{traceback.format_exc()}")
        raise

def generate_risk_trends(user_id):
    """生成未来6个月的风险趋势预测"""
    try:
        db = get_db()
        assessment = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).first()
            
        if not assessment:
            default_assessment = RiskAssessments(
                user_id=user_id,
                disease='高血压',
                assessment_date=date.today(),
                risk_score=40,
                risk_level='medium',
                key_factors=json.dumps({"收缩压波动":0.28,"舒张压水平":0.22,"年龄因素":0.18,"体重指数":0.17,"性别因素":0.05}, ensure_ascii=False),
                recommendations="暂无健康数据，建议完善个人健康指标",
                model_version='2.0'
            )
            db.session.add(default_assessment)
            db.session.commit()
            assessment = default_assessment
            
        current_score = float(assessment.risk_score)
        current_level = assessment.risk_level or 'medium'
        today = date.today()
        
        trends = []
        improvement_base = {
            'high': 0.08,
            'medium': 0.05,
            'low': 0.02
        }.get(current_level, 0.05)
        
        for i in range(6):
            month_start = (datetime(today.year, today.month, 1) + timedelta(days=32*(i+1))).replace(day=1).date()
            improvement = improvement_base * (i+1) * (1 - 0.1*i)
            random_fluctuation = random.uniform(-0.02, 0.02)
            predicted_score = max(current_score * (1 - improvement + random_fluctuation), 10)
            
            confidence_ratio = 0.15 if current_level == 'high' else 0.10 if current_level == 'medium' else 0.05
            trend = RiskTrends(
                user_id=user_id,
                month_start=month_start,
                predicted_score=round(predicted_score, 1),
                confidence_low=round(predicted_score * (1 - confidence_ratio), 1),
                confidence_high=round(predicted_score * (1 + confidence_ratio), 1),
                model_version='2.0'
            )
            
            trends.append(trend)
            
        db.session.add_all(trends)
        db.session.commit()
        
    except Exception as e:
        get_db().session.rollback()
        print(f"❌ 生成风险趋势失败: {e}\n{traceback.format_exc()}")
        raise

# --------------- 核心评估算法 ---------------
def assess_hypertension_risk(systolic, diastolic, age, bmi, gender):
    """评估高血压风险"""
    # ✅ 参数验证
    systolic = float(systolic) if systolic is not None else 120.0
    diastolic = float(diastolic) if diastolic is not None else 80.0
    age = int(age) if age is not None else 30
    bmi = float(bmi) if bmi is not None else 22.0
    gender = str(gender) if gender else 'unknown'
    
    score = 0
    # 收缩压评分
    if systolic >= 180:
        score += 40
    elif systolic >= 160:
        score += 30
    elif systolic >= 140:
        score += 20
    elif systolic >= 130:
        score += 10
    
    # 舒张压评分
    if diastolic >= 110:
        score += 25
    elif diastolic >= 100:
        score += 20
    elif diastolic >= 90:
        score += 15
    elif diastolic >= 85:
        score += 5
    
    # 年龄评分
    if age >= 75:
        score += 15
    elif age >= 65:
        score += 10
    elif age >= 45:
        score += 5
    
    # BMI评分
    if bmi >= 30:
        score += 10
    elif bmi >= 25:
        score += 5
    
    # 性别评分
    if gender == 'male' and age < 65:
        score += 5
    
    score = min(max(score, 0), 100)
    level = 'high' if score >= 60 else 'medium' if score >= 30 else 'low'
    
    factors = {
        "收缩压": 0.35,  # 35%
        "舒张压": 0.25,  # 25%
        "年龄": 0.20,     # 20%
        "BMI指数": 0.15,  # 15%
        "性别": 0.05      # 5%
    }
    
    recommendations = [
        "每日钠摄入控制在5g以内，减少腌制食品、加工肉类",
        "每日钾摄入≥2000mg，多吃香蕉、菠菜、土豆等",
        "规律监测血压：早8点、晚8点各1次，记录数值变化",
        "每周至少150分钟中等强度有氧运动（快走、慢跑、游泳）"
    ]
    if level == 'high':
        recommendations.extend([
            "立即就医，评估是否需要启动降压药物治疗",
            "避免剧烈运动，防止血压骤升",
            "戒烟限酒，酒精每日摄入量≤25g（男性）/15g（女性）"
        ])
    elif level == 'medium':
        recommendations.extend([
            "3个月内复查血压，若持续升高需就医",
            "控制体重，目标BMI降至24以下",
            "保证每日7-8小时睡眠，避免熬夜"
        ])
    
    return {'score': score, 'level': level, 'factors': factors, 'recommendations': recommendations}

def assess_sleep_apnea_risk(bmi, avg_sleep, avg_heart_rate, gender, age):
    """评估睡眠呼吸暂停风险"""
    # ✅ 参数验证
    bmi = float(bmi) if bmi is not None else 22.0
    avg_sleep = float(avg_sleep) if avg_sleep is not None else 7.0
    avg_heart_rate = float(avg_heart_rate) if avg_heart_rate is not None else 75.0
    age = int(age) if age is not None else 30
    gender = str(gender) if gender else 'unknown'
    
    score = 0
    
    # BMI评分
    if bmi >= 35:
        score += 40
    elif bmi >= 30:
        score += 30
    elif bmi >= 28:
        score += 20
    elif bmi >= 25:
        score += 10
    
    # 睡眠时长评分
    if avg_sleep < 5:
        score += 20
    elif avg_sleep < 6:
        score += 15
    elif avg_sleep > 9:
        score += 5
    
    # 心率评分
    if avg_heart_rate >= 85:
        score += 15
    elif avg_heart_rate >= 75:
        score += 10
    
    # 年龄评分
    if age >= 50:
        score += 10
    elif age >= 30:
        score += 5
    
    # 性别评分
    if gender == 'male':
        score += 15
    
    score = min(max(score, 0), 100)
    level = 'high' if score >= 50 else 'medium' if score >= 25 else 'low'
    
    factors = {
        "BMI指数": round(score * 0.5 if bmi >= 25 else 0.1, 2),
        "睡眠时长": round(score * 0.2 if avg_sleep < 6 else 0.05, 2),
        "静息心率": round(score * 0.15 if avg_heart_rate >= 75 else 0.05, 2),
        "年龄": round(score * 0.08 if age >= 30 else 0.02, 2),
        "性别": round(score * 0.07 if gender == 'male' else 0.01, 2)
    }
    
    recommendations = [
        "采用侧卧睡姿，减少舌根后坠阻塞气道",
        "睡前3小时避免进食、饮酒、服用镇静药物",
        "保持卧室安静、黑暗，温度控制在18-22℃",
        "每日记录睡眠时长，目标7-8小时/晚"
    ]
    if level == 'high':
        recommendations.extend([
            "尽快完成多导睡眠监测（PSG），明确呼吸暂停严重程度",
            "评估使用持续气道正压通气（CPAP）治疗的必要性",
            "制定减重计划，每月减重1-2kg，目标BMI降至28以下"
        ])
    elif level == 'medium':
        recommendations.extend([
            "使用睡眠监测手环，记录夜间血氧饱和度",
            "避免仰卧睡姿，可在背部放置枕头辅助侧卧",
            "每日有氧运动30分钟，改善心肺功能"
        ])
    
    return {'score': score, 'level': level, 'factors': factors, 'recommendations': recommendations}

def assess_metabolic_risk(bmi, systolic, heart_rate, sleep, blood_sugar, age):
    """评估代谢综合征风险"""
    # ✅ 参数验证
    bmi = float(bmi) if bmi is not None else 22.0
    systolic = float(systolic) if systolic is not None else 120.0
    heart_rate = float(heart_rate) if heart_rate is not None else 75.0
    sleep = float(sleep) if sleep is not None else 7.0
    blood_sugar = float(blood_sugar) if blood_sugar is not None else 5.5
    age = int(age) if age is not None else 30
    
    score = 0
    
    # BMI评分
    if bmi >= 30:
        score += 30
    elif bmi >= 25:
        score += 20
    
    # 血压评分
    if systolic >= 130:
        score += 20
    elif systolic >= 120:
        score += 10
    
    # 心率评分
    if heart_rate >= 90:
        score += 15
    elif heart_rate >= 80:
        score += 10
    
    # 睡眠评分
    if sleep < 6:
        score += 15
    elif sleep < 7:
        score += 5
    
    # 血糖评分
    if blood_sugar >= 7.0:
        score += 15
    elif blood_sugar >= 6.1:
        score += 10
    
    # 年龄评分
    if age >= 40:
        score += 10
    
    score = min(max(score, 0), 100)
    level = 'high' if score >= 55 else 'medium' if score >= 25 else 'low'
    
    factors = {
        "BMI指数": round(score * 0.35 if bmi >= 25 else 0.1, 2),
        "收缩压": round(score * 0.2 if systolic >= 120 else 0.05, 2),
        "静息心率": round(score * 0.15 if heart_rate >= 80 else 0.05, 2),
        "睡眠时长": round(score * 0.15 if sleep < 7 else 0.05, 2),
        "空腹血糖": round(score * 0.1 if blood_sugar >= 6.1 else 0.03, 2),
        "年龄": round(score * 0.05 if age >= 40 else 0.02, 2)
    }
    
    recommendations = [
        "饮食调整：碳水化合物占比45-50%，增加膳食纤维（每日≥25g）",
        "运动方案：每周3次力量训练+4次有氧运动，每次30分钟",
        "血糖监测：每周1次空腹血糖，记录变化趋势",
        "控制腰围：男性<90cm，女性<85cm，减少腹型肥胖"
    ]
    if level == 'high':
        recommendations.extend([
            "就医检查血脂、胰岛素抵抗指标",
            "每日热量摄入减少500kcal，目标每月减重1-2kg",
            "避免添加糖，饮料仅喝白开水/无糖茶"
        ])
    elif level == 'medium':
        recommendations.extend([
            "3个月后复查血糖、血压、BMI",
            "每日步数≥8000步，减少久坐（每小时起身活动5分钟）",
            "保证7-8小时睡眠，改善胰岛素敏感性"
        ])
    
    return {'score': score, 'level': level, 'factors': factors, 'recommendations': recommendations}

# --------------- 辅助函数 ---------------
def get_risk_factors(user_id):
    """获取用户的风险因素"""
    try:
        assessments = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).limit(3).all()
        
        all_factors = {}
        for assessment in assessments:
            if not assessment.key_factors:
                continue
            try:
                factors = json.loads(assessment.key_factors) if isinstance(assessment.key_factors, str) else (assessment.key_factors or {})
                for factor, weight in factors.items():
                    if factor in all_factors:
                        all_factors[factor] = (all_factors[factor] + weight) / 2
                    else:
                        all_factors[factor] = weight
            except:
                continue
        
        if not all_factors:
            return [
                {'factor': '收缩压波动', 'weight': 0.28},
                {'factor': '睡眠时长不足', 'weight': 0.22},
                {'factor': 'BMI指数偏高', 'weight': 0.18},
                {'factor': '静息心率异常', 'weight': 0.17},
                {'factor': '空腹血糖偏高', 'weight': 0.15}
            ]
            
        result = [{'factor': k, 'weight': round(v, 2)} for k, v in all_factors.items()]
        return sorted(result, key=lambda x: x['weight'], reverse=True)[:5]
        
    except Exception as e:
        print(f"❌ 获取风险因素失败: {e}")
        return [
            {'factor': '收缩压波动', 'weight': 0.28},
            {'factor': '睡眠时长不足', 'weight': 0.22},
            {'factor': 'BMI指数偏高', 'weight': 0.18},
            {'factor': '静息心率异常', 'weight': 0.17},
            {'factor': '空腹血糖偏高', 'weight': 0.15}
        ]

def get_risk_description(assessment, factors):
    """生成风险描述"""
    disease = assessment.disease
    risk_score = float(assessment.risk_score) / 100
    level_text = {
        'high': '高',
        'medium': '中',
        'low': '低'
    }.get(assessment.risk_level or 'low', '低')
    
    try:
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:2]
        factor_text = '、'.join([f"{k}（权重{v}）" for k, v in top_factors]) if top_factors else '暂无明确风险因素'
    except:
        factor_text = '暂无明确风险因素'
    
    descriptions = {
        '高血压': f"当前高血压风险为{level_text}风险（风险值{risk_score:.2f}），主要风险因素为{factor_text}，需重点关注血压控制。",
        '睡眠呼吸暂停': f"当前睡眠呼吸暂停风险为{level_text}风险（风险值{risk_score:.2f}），主要风险因素为{factor_text}，需改善睡眠习惯。",
        '代谢综合征': f"当前代谢综合征风险为{level_text}风险（风险值{risk_score:.2f}），主要风险因素为{factor_text}，需调整饮食和运动习惯。"
    }
    return descriptions.get(disease, f"当前{disease}风险为{level_text}风险（风险值{risk_score:.2f}），{factor_text}。")

def get_comprehensive_suggestion(disease_risks):
    """生成综合健康建议"""
    try:
        high_risk_diseases = [d['disease'] for d in disease_risks if d.get('riskLevel') == 'high']
        medium_risk_diseases = [d['disease'] for d in disease_risks if d.get('riskLevel') == 'medium']
        
        if high_risk_diseases:
            return f"你当前{','.join(high_risk_diseases)}为高风险，建议立即就医评估，并严格遵循个性化干预方案；{','.join(medium_risk_diseases) if medium_risk_diseases else '其他指标'}需持续监测并调整生活方式。"
        elif medium_risk_diseases:
            return f"你当前{','.join(medium_risk_diseases)}为中风险，建议3个月内复查相关指标，坚持健康饮食和规律运动，可有效降低风险。"
        else:
            return "你当前各项疾病风险均为低风险，建议保持现有健康生活方式，每年进行1次常规体检即可。"
    except:
        return "暂无健康评估数据，建议完善个人健康指标后重新评估。"
