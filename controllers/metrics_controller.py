from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Users, HealthMetrics, AlertRules, Alerts
from extensions import db  # ← 关键修改：避免从 app 导入导致循环
from datetime import datetime, timedelta
import json
import random
from controllers.risk_controller import generate_risk_assessment
metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_metrics():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # 创建新的健康指标记录（原有逻辑不变）
        new_metric = HealthMetrics(
            user_id=user_id,
            recorded_at=datetime.now(),
            source=data.get('source', 'manual'),
            heart_rate=data.get('heart_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            blood_oxygen=data.get('blood_oxygen'),
            resp_rate=data.get('resp_rate'),
            temperature=data.get('temperature'),
            glucose=data.get('glucose'),
            sleep_duration=data.get('sleep_duration'),
            stress_level=data.get('stress_level'),
            steps=data.get('steps'),
            weight_kg=data.get('weight_kg'),
            notes=data.get('notes')
        )

        # 计算BMI（原有逻辑不变）
        if data.get('weight_kg') and Users.query.get(user_id).height_cm:
            user = Users.query.get(user_id)
            height_m = float(user.height_cm) / 100
            weight_kg = float(data.get('weight_kg'))
            bmi = round(weight_kg / (height_m * height_m), 1)
            new_metric.bmi = bmi

        db.session.add(new_metric)
        db.session.commit()

        # 核心新增：提交数据后自动生成风险评估
        generate_risk_assessment(user_id)

        # 原有检查预警逻辑（保留）
        check_alerts(user_id, new_metric)

        return jsonify({
            "status": "success",
            "message": "健康数据提交成功",
            "metric_id": new_metric.metric_id
        })

    except Exception as e:
        db.session.rollback()
        print(f"提交健康数据失败: {e}")
        return jsonify({"status": "error", "message": f"提交失败: {str(e)}"}), 500


@metrics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()

        # 获取用户信息
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        # 获取最近的健康指标
        last_metric = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).first()

        # 获取监测指标和目标范围
        monitoring_data = get_monitoring_data(user_id)

        # 获取最近的预警
        alerts = get_recent_alerts(user_id)

        # 生成健康知识推荐
        knowledge = recommend_knowledge(user_id)

        # 构建用户健康画像
        persona = build_user_persona(user, monitoring_data)

        # 整合响应
        response = {
            "overview": persona,
            "lastMetric": last_metric.to_dict() if last_metric else {},
            "monitoring": {
                "metrics": monitoring_data,
                "alerts": alerts
            },
            "knowledge": knowledge
        }

        return jsonify(response)

    except Exception as e:
        print(f"获取仪表板数据失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500


@metrics_bp.route('/metrics/list', methods=['GET'])
@jwt_required()
def get_metrics_list():
    try:
        user_id = get_jwt_identity()

        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        source = request.args.get('source')
        limit = request.args.get('limit', 50, type=int)

        # 构建查询
        query = HealthMetrics.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(HealthMetrics.recorded_at >= start_date)

        if end_date:
            query = query.filter(HealthMetrics.recorded_at <= f"{end_date} 23:59:59")

        if source and source != 'all':
            query = query.filter(HealthMetrics.source == source)

        # 按记录时间降序排序并限制结果数
        metrics = query.order_by(HealthMetrics.recorded_at.desc()).limit(limit).all()

        # 计算统计数据
        stats = calculate_metrics_stats(user_id)

        # 格式化记录 - 使用模型的 to_dict() 方法确保一致性
        records = []
        for metric in metrics:
            # 使用模型的 to_dict() 方法获取完整数据
            metric_dict = metric.to_dict()
            
            # 确定严重程度
            severity = determine_severity(metric)

            # 生成标签
            tags = generate_tags(metric)

            records.append({
                "id": metric.metric_id,
                "date": metric.recorded_at.strftime('%Y-%m-%d %H:%M'),
                "source": metric.source or 'manual',
                "severity": severity,
                "tags": tags,
                "metrics": {
                    "heart_rate": metric.heart_rate,
                    "blood_pressure_systolic": metric.blood_pressure_systolic,
                    "blood_pressure_diastolic": metric.blood_pressure_diastolic,
                    "blood_oxygen": float(metric.blood_oxygen) if metric.blood_oxygen else None,
                    "resp_rate": metric.resp_rate,
                    "temperature": float(metric.temperature) if metric.temperature else None,
                    "glucose": float(metric.glucose) if metric.glucose else None,
                    "sleep_duration": float(metric.sleep_duration) if metric.sleep_duration else None,
                    "stress_level": metric.stress_level,
                    "steps": metric.steps,
                    "weight_kg": float(metric.weight_kg) if metric.weight_kg else None,
                    "bmi": float(metric.bmi) if metric.bmi else None
                }
            })

        response = {
            "stats": stats,
            "records": records
        }

        return jsonify(response)

    except Exception as e:
        print(f"获取监测记录失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500


# ------------------------ 辅助函数 ------------------------
def check_alerts(user_id, metric):
    """检查指标是否触发预警规则"""
    try:
        rules = AlertRules.query.filter_by(user_id=user_id, active=True).all()

        for rule in rules:
            triggered = False
            threshold_value = rule.threshold_value

            if isinstance(threshold_value, str):
                threshold_value = json.loads(threshold_value)

            metric_value = getattr(metric, rule.metric_field, None)
            if metric_value is None:
                continue

            if rule.threshold_type == 'above':
                if metric_value > threshold_value.get('value'):
                    triggered = True
            elif rule.threshold_type == 'below':
                if metric_value < threshold_value.get('value'):
                    triggered = True
            elif rule.threshold_type == 'range':
                if metric_value < threshold_value.get('min') or metric_value > threshold_value.get('max'):
                    triggered = True

            if triggered:
                field_labels = {
                    'heart_rate': '心率',
                    'blood_pressure_systolic': '收缩压',
                    'blood_pressure_diastolic': '舒张压',
                    'blood_oxygen': '血氧',
                    'sleep_duration': '睡眠时长',
                    'stress_level': '压力水平'
                }
                field_name = field_labels.get(rule.metric_field, rule.metric_field)

                if rule.threshold_type == 'above':
                    message = f"{field_name}超过阈值 {threshold_value.get('value')}，当前值为 {metric_value}"
                elif rule.threshold_type == 'below':
                    message = f"{field_name}低于阈值 {threshold_value.get('value')}，当前值为 {metric_value}"
                else:
                    message = f"{field_name}超出范围 {threshold_value.get('min')}-{threshold_value.get('max')}，当前值为 {metric_value}"

                alert = Alerts(
                    rule_id=rule.rule_id,
                    user_id=user_id,
                    triggered_at=datetime.now(),
                    status='open',
                    message=message
                )
                db.session.add(alert)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"检查预警失败: {e}")
        raise


def get_monitoring_data(user_id):
    """获取用户的监测数据和目标范围"""
    try:
        latest_metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).first()

        targets = {
            'heart_rate': {'min': 55, 'max': 95, 'label': '心率'},
            'blood_pressure_systolic': {'min': 90, 'max': 130, 'label': '收缩压'},
            'blood_pressure_diastolic': {'min': 60, 'max': 85, 'label': '舒张压'},
            'blood_oxygen': {'min': 95, 'max': 100, 'label': '血氧'},
            'resp_rate': {'min': 12, 'max': 20, 'label': '呼吸频率'},
            'temperature': {'min': 36.0, 'max': 37.5, 'label': '体温'},  # 添加体温
            'glucose': {'min': 3.9, 'max': 6.1, 'label': '血糖'},      # 添加血糖
            'sleep_duration': {'min': 7, 'max': 8, 'label': '睡眠时长'},
            'stress_level': {'min': 0, 'max': 40, 'label': '压力指数'},
            'steps': {'min': 7000, 'max': 10000, 'label': '步数'}
        }

        result = []
        if latest_metrics:
            for field, target in targets.items():
                value = getattr(latest_metrics, field)
                if value is not None and field in ['blood_oxygen', 'sleep_duration', 'temperature', 'glucose']:
                    value = float(value)

                status = '未知'
                if value is not None:
                    if field == 'stress_level':
                        status = '正常' if value <= target['max'] else '偏高'
                    else:
                        if target['min'] <= value <= target['max']:
                            status = '正常'
                        elif value < target['min']:
                            status = '偏低'
                        else:
                            status = '偏高'

                result.append({
                    'field': field,
                    'label': target['label'],
                    'value': value,
                    'target': f"{target['min']}-{target['max']}",
                    'status': status
                })
        else:
            for field, target in targets.items():
                result.append({
                    'field': field,
                    'label': target['label'],
                    'value': None,
                    'target': f"{target['min']}-{target['max']}",
                    'status': '未知'
                })

        return result

    except Exception as e:
        print(f"获取监测数据失败: {e}")
        return []


def get_recent_alerts(user_id):
    """获取用户最近的预警"""
    try:
        alerts = Alerts.query.filter_by(user_id=user_id).order_by(
            Alerts.triggered_at.desc()).limit(3).all()

        result = []
        for alert in alerts:
            if alert.rule:
                level = alert.rule.severity
            else:
                level = 'info'

            result.append({
                'id': alert.alert_id,
                'level': level,
                'time': alert.triggered_at.strftime('%Y-%m-%d %H:%M'),
                'message': alert.message
            })

        return result

    except Exception as e:
        print(f"获取最近预警失败: {e}")
        return []


def build_user_persona(user, metrics):
    """根据用户信息和健康指标构建健康画像"""
    try:
        age = None
        if user.birth_date:
            today = datetime.now().date()
            age = today.year - user.birth_date.year - (
                (today.month, today.day) < (user.birth_date.month, user.birth_date.day)
            )

        bmi = None
        if user.height_cm and user.weight_kg and float(user.height_cm) > 0:
            height_m = float(user.height_cm) / 100
            weight_kg = float(user.weight_kg)
            bmi = round(weight_kg / (height_m * height_m), 1)

        blood_pressure = '未知'
        systolic = next((m['value'] for m in metrics if m['field'] == 'blood_pressure_systolic' and m['value'] is not None), None)
        diastolic = next((m['value'] for m in metrics if m['field'] == 'blood_pressure_diastolic' and m['value'] is not None), None)
        if systolic and diastolic:
            blood_pressure = f"{systolic}/{diastolic}"

        tags = []
        sleep_data = next((m for m in metrics if m['field'] == 'sleep_duration'), None)
        if sleep_data and sleep_data['value'] is not None:
            if float(sleep_data['value']) < 6.5:
                tags.append('睡眠不足')
            elif float(sleep_data['value']) > 9:
                tags.append('睡眠过多')

        stress_data = next((m for m in metrics if m['field'] == 'stress_level'), None)
        if stress_data and stress_data['value'] is not None:
            if int(stress_data['value']) > 60:
                tags.append('高压力')
            elif int(stress_data['value']) > 40:
                tags.append('中等压力')

        bp_data = next((m for m in metrics if m['field'] == 'blood_pressure_systolic'), None)
        if bp_data and bp_data['value'] is not None and int(bp_data['value']) > 130:
            tags.append('血压偏高')

        steps_data = next((m for m in metrics if m['field'] == 'steps'), None)
        if steps_data and steps_data['value'] is not None and int(steps_data['value']) < 5000:
            tags.append('久坐')

        if not tags:
            default_tags = ['工作压力', '规律作息', '均衡饮食', '日常锻炼', '高钠饮食', '夜间工作']
            tags = random.sample(default_tags, min(2, len(default_tags)))

        summary = generate_health_summary(metrics, tags)
        gender_map = {'male': '男', 'female': '女', 'other': '其他'}
        gender = gender_map.get(user.gender, '未知')

        return {
            "username": user.username,
            "gender": gender,
            "age": age,
            "bmi": bmi,
            "bloodPressure": blood_pressure,
            "tags": tags,
            "summary": summary
        }

    except Exception as e:
        print(f"构建用户画像失败: {e}")
        return {
            "username": user.username if user else "未知用户",
            "gender": "未知",
            "age": None,
            "bmi": None,
            "bloodPressure": "未知",
            "tags": [],
            "summary": "无法生成健康摘要"
        }


def recommend_knowledge(user_id):
    """根据用户健康数据推荐相关知识"""
    try:
        metric = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).first()

        knowledge_base = [
            {"id": "k1", "title": "晨峰血压管理策略", "tag": "高血压", "desc": "起床后1小时内完成拉伸+温水，减少交感兴奋。"},
            {"id": "k2", "title": "减压呼吸法", "tag": "压力应对", "desc": "4-7-8呼吸法可迅速降低交感张力，助眠。"},
            {"id": "k3", "title": "钾镁调压食谱", "tag": "营养", "desc": "多吃深绿色蔬菜、坚果，控制每日钠摄入<5g。"},
            {"id": "k4", "title": "提高血氧的深呼吸技巧", "tag": "呼吸技巧", "desc": "每天3次，每次5分钟的深呼吸练习。"},
            {"id": "k5", "title": "改善睡眠质量指南", "tag": "睡眠管理", "desc": "控制睡前蓝光暴露，规律的睡眠-觉醒时间。"}
        ]

        if not metric:
            return random.sample(knowledge_base, min(3, len(knowledge_base)))

        recommended = []
        if metric.blood_pressure_systolic and metric.blood_pressure_systolic > 130:
            recommended.extend([k for k in knowledge_base if k["tag"] == "高血压"])
        if metric.stress_level and metric.stress_level > 40:
            recommended.extend([k for k in knowledge_base if k["tag"] == "压力应对"])
        if metric.sleep_duration and float(metric.sleep_duration) < 7:
            recommended.extend([k for k in knowledge_base if k["tag"] == "睡眠管理"])
        if metric.blood_oxygen and float(metric.blood_oxygen) < 95:
            recommended.extend([k for k in knowledge_base if k["tag"] == "呼吸技巧"])

        if not recommended:
            recommended.extend([k for k in knowledge_base if k["tag"] == "营养"])

        unique_recommended = []
        seen_ids = set()
        for item in recommended:
            if item['id'] not in seen_ids:
                unique_recommended.append(item)
                seen_ids.add(item['id'])
                if len(unique_recommended) >= 3:
                    break

        remaining_needed = 3 - len(unique_recommended)
        if remaining_needed > 0:
            remaining_items = [k for k in knowledge_base if k['id'] not in seen_ids]
            if remaining_items:
                unique_recommended.extend(random.sample(remaining_items, min(remaining_needed, len(remaining_items))))

        return unique_recommended

    except Exception as e:
        print(f"推荐知识失败: {e}")
        return []


def calculate_metrics_stats(user_id):
    """计算用户的健康指标统计数据"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        metrics = HealthMetrics.query.filter(
            HealthMetrics.user_id == user_id,
            HealthMetrics.recorded_at.between(start_date, end_date)
        ).all()

        if not metrics:
            return {
                "avgHeartRate": '--',
                "avgBloodPressure": '--/--',
                "avgGlucose": '--',
                "avgTemperature": '--',
                "avgSleep": '--',
                "highRiskCount": 0
            }

        heart_rates = [m.heart_rate for m in metrics if m.heart_rate]
        systolics = [m.blood_pressure_systolic for m in metrics if m.blood_pressure_systolic]
        diastolics = [m.blood_pressure_diastolic for m in metrics if m.blood_pressure_diastolic]
        glucoses = [float(m.glucose) for m in metrics if m.glucose]
        temperatures = [float(m.temperature) for m in metrics if m.temperature]
        sleeps = [float(m.sleep_duration) for m in metrics if m.sleep_duration]

        high_risk_days = set()
        for m in metrics:
            if ((m.blood_pressure_systolic and m.blood_pressure_systolic > 140) or
                (m.blood_pressure_diastolic and m.blood_pressure_diastolic > 90) or
                (m.glucose and float(m.glucose) > 7.0) or
                (m.temperature and float(m.temperature) > 37.5) or
                (m.sleep_duration and float(m.sleep_duration) < 6)):
                high_risk_days.add(m.recorded_at.date())

        avg_heart_rate = int(sum(heart_rates) / len(heart_rates)) if heart_rates else '--'
        avg_systolic = int(sum(systolics) / len(systolics)) if systolics else '--'
        avg_diastolic = int(sum(diastolics) / len(diastolics)) if diastolics else '--'
        avg_blood_pressure = f"{avg_systolic}/{avg_diastolic}" if avg_systolic != '--' and avg_diastolic != '--' else '--/--'
        avg_glucose = round(sum(glucoses) / len(glucoses), 1) if glucoses else '--'
        avg_temperature = round(sum(temperatures) / len(temperatures), 1) if temperatures else '--'
        avg_sleep = round(sum(sleeps) / len(sleeps), 1) if sleeps else '--'

        return {
            "avgHeartRate": avg_heart_rate,
            "avgBloodPressure": avg_blood_pressure,
            "avgGlucose": avg_glucose,
            "avgTemperature": avg_temperature,
            "avgSleep": avg_sleep,
            "highRiskCount": len(high_risk_days)
        }

    except Exception as e:
        print(f"计算统计数据失败: {e}")
        return {
            "avgHeartRate": '--',
            "avgBloodPressure": '--/--',
            "avgGlucose": '--',
            "avgTemperature": '--',
            "avgSleep": '--',
            "highRiskCount": 0
        }


def determine_severity(metric):
    """根据指标确定严重程度"""
    severity = "info"

    if (metric.blood_pressure_systolic and metric.blood_pressure_systolic >= 140) or (metric.blood_pressure_diastolic and metric.blood_pressure_diastolic >= 90):
        severity = "danger"
    elif (metric.blood_pressure_systolic and metric.blood_pressure_systolic >= 130) or (metric.blood_pressure_diastolic and metric.blood_pressure_diastolic >= 85):
        severity = "warning"

    if metric.sleep_duration and float(metric.sleep_duration) < 6:
        severity = max(severity, "warning", key={"info": 0, "warning": 1, "danger": 2}.get)

    if metric.stress_level and metric.stress_level > 70:
        severity = "danger"
    elif metric.stress_level and metric.stress_level > 50:
        severity = max(severity, "warning", key={"info": 0, "warning": 1, "danger": 2}.get)

    return severity


def generate_tags(metric):
    """根据指标生成标签"""
    tags = []
    hour = metric.recorded_at.hour

    if hour < 6:
        tags.append('凌晨')
    elif hour < 9:
        tags.append('早晨')
    elif hour < 12:
        tags.append('上午')
    elif hour < 14:
        tags.append('中午')
    elif hour < 18:
        tags.append('下午')
    elif hour < 22:
        tags.append('晚上')
    else:
        tags.append('深夜')

    if metric.blood_pressure_systolic:
        if metric.blood_pressure_systolic >= 140:
            tags.append('高血压')
        elif metric.blood_pressure_systolic <= 100:
            tags.append('低血压')
        if hour < 10 and metric.blood_pressure_systolic >= 135:
            tags.append('晨峰血压')

    if metric.sleep_duration:
        if float(metric.sleep_duration) < 6:
            tags.append('睡眠不足')
        elif float(metric.sleep_duration) > 9:
            tags.append('睡眠过多')

    if metric.stress_level:
        if metric.stress_level > 60:
            tags.append('高压力')
        if hour > 22 and metric.stress_level > 50:
            tags.append('夜间交感激活')

    if metric.steps:
        if metric.steps < 3000:
            tags.append('活动不足')
        elif metric.steps > 10000:
            tags.append('活动充分')

    if hour > 20:
        tags.append('蓝光暴露')

    if not tags:
        if metric.source == 'manual':
            tags.append('手动记录')
        elif metric.source == 'wearable':
            tags.append('可穿戴监测')
        elif metric.source == 'hospital':
            tags.append('例行体检')
        else:
            tags.append('健康监测')

    return tags


def generate_health_summary(metrics, tags):
    """生成健康摘要"""
    summaries = [
        "保持良好生活习惯，定期监测健康指标",
        "近期项目冲刺导致睡眠不足，存在久坐与高盐饮食习惯",
        "血压波动较大，建议注意饮食作息规律性",
        "工作压力较大，需要更多休息与放松",
        "健康状况整体良好，建议保持运动习惯"
    ]

    if '睡眠不足' in tags:
        return "近期睡眠不足，注意工作与休息平衡"
    if '高压力' in tags or '中等压力' in tags:
        return "工作压力较大，建议适当减压放松"
    if '血压偏高' in tags:
        return "血压偏高，需关注饮食习惯和生活方式"
    if '久坐' in tags:
        return "久坐生活方式，建议增加日常活动量"

    return random.choice(summaries)
