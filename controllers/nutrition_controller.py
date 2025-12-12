# nutrition_controller.py 最终修改版
from flask import Blueprint, request, jsonify, current_app  # 新增 current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models.models import Users, NutritionPlans, Meals, RiskAssessments, HealthMetrics
# 注释掉原有的 from app import db（关键修改）
# from app import db
import json
import random

nutrition_bp = Blueprint('nutrition', __name__)

# 新增：全局获取db的辅助函数（替代直接导入）
def get_db():
    from extensions import db  # 从extensions导入db
    return db

# -------------------------- 原有接口逻辑完全保留，仅替换 db 为 get_db() --------------------------
@nutrition_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_nutrition_plan():
    try:
        user_id = get_jwt_identity()
        
        # 获取用户的营养计划
        plan = NutritionPlans.query.filter_by(user_id=user_id).first()
        
        # 如果没有计划，创建一个
        if not plan:
            plan = create_nutrition_plan(user_id)
            
        # 获取最近的餐食记录
        meals = Meals.query.filter_by(plan_id=plan.plan_id).order_by(
            Meals.meal_time.desc()).limit(10).all()
            
        # 解析宏量营养素分配
        macros = plan.macro_split
        if isinstance(macros, str):
            macros = json.loads(macros)
            
        # 获取推荐微量营养素
        micronutrients = get_recommended_micronutrients(user_id)
        
        # 格式化餐食
        formatted_meals = format_meals(meals)
        
        response = {
            'energy': plan.energy_target_kcal,
            'macros': macros,
            'micronutrients': micronutrients,
            'meals': formatted_meals
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"获取营养计划失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

@nutrition_bp.route('/record_meal', methods=['POST'])
@jwt_required()
def record_meal():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 获取用户的营养计划
        plan = NutritionPlans.query.filter_by(user_id=user_id).first()
        
        if not plan:
            plan = create_nutrition_plan(user_id)
            
        # 解析餐食时间
        meal_time_str = data.get('meal_time', datetime.now().strftime('%Y-%m-%d %H:%M'))
        meal_time = datetime.strptime(meal_time_str, '%Y-%m-%d %H:%M')
        
        # 获取食物列表
        foods = data.get('foods', [])
        
        # 计算总卡路里和宏量营养素
        calories = data.get('calories', sum(food.get('calories', 0) for food in foods))
        
        # 计算宏量营养素分布
        macros = data.get('macros', {})
        
        # 如果没有提供宏量营养素，则根据食物计算
        if not macros:
            protein = sum(food.get('protein', 0) for food in foods)
            carbs = sum(food.get('carbs', 0) for food in foods)
            fat = sum(food.get('fat', 0) for food in foods)
            
            # 如果食物也没有详细的宏量营养素，使用默认分布
            if protein == 0 and carbs == 0 and fat == 0:
                plan_macros = plan.macro_split
                if isinstance(plan_macros, str):
                    plan_macros = json.loads(plan_macros)
                    
                # 按照计划的宏量营养素比例计算
                protein_pct = plan_macros.get('protein', 25)
                carbs_pct = plan_macros.get('carb', 50)
                fat_pct = plan_macros.get('fat', 25)
                
                # 计算克数
                protein = round(calories * protein_pct / 400)  # 1g蛋白质 = 4kcal
                carbs = round(calories * carbs_pct / 400)      # 1g碳水 = 4kcal
                fat = round(calories * fat_pct / 900)          # 1g脂肪 = 9kcal
                
            macros = {
                'protein': protein,
                'carbs': carbs,
                'fat': fat
            }
            
        # 创建餐食记录
        meal = Meals(
            plan_id=plan.plan_id,
            meal_time=meal_time,
            foods=foods,
            calories=calories,
            macros_json=macros,
            glycemic_load=data.get('glycemic_load'),
            satiety_score=data.get('satiety_score'),
            user_feedback=data.get('feedback')
        )
        
        # 关键修改：替换 db 为 get_db()
        db = get_db()
        db.session.add(meal)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "餐食记录已添加",
            "meal_id": meal.meal_id
        })
        
    except Exception as e:
        # 关键修改：替换 db 为 get_db()
        db = get_db()
        db.session.rollback()
        print(f"记录餐食失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500

@nutrition_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    try:
        user_id = get_jwt_identity()
        
        # 获取用户的营养计划
        plan = NutritionPlans.query.filter_by(user_id=user_id).first()
        
        if not plan:
            plan = create_nutrition_plan(user_id)
            
        # 获取用户的健康风险
        risks = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).all()
            
        # 获取用户的健康指标
        metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).limit(10).all()
            
        # 生成营养建议
        recommendations = generate_nutrition_recommendations(plan, risks, metrics)
        
        return jsonify(recommendations)
        
    except Exception as e:
        print(f"获取营养建议失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

@nutrition_bp.route('/update_plan', methods=['POST'])
@jwt_required()
def update_plan():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 获取用户的营养计划
        plan = NutritionPlans.query.filter_by(user_id=user_id).first()
        
        if not plan:
            plan = create_nutrition_plan(user_id)
            
        # 更新能量目标
        if 'energy_target' in data:
            plan.energy_target_kcal = data['energy_target']
            
        # 更新宏量营养素分配
        if 'macro_split' in data:
            plan.macro_split = data['macro_split']
            
        # 更新饮食限制
        if 'dietary_restrictions' in data:
            plan.dietary_restrictions = data['dietary_restrictions']
            
        # 更新建议
        if 'recommendations' in data:
            plan.recommendations = data['recommendations']
            
        plan.updated_at = datetime.now()
        # 关键修改：替换 db 为 get_db()
        db = get_db()
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "营养计划已更新"
        })
        
    except Exception as e:
        # 关键修改：替换 db 为 get_db()
        db = get_db()
        db.session.rollback()
        print(f"更新营养计划失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500

# -------------------------- 辅助函数：仅修改 db 引用 --------------------------
def create_nutrition_plan(user_id):
    """创建用户的营养计划"""
    try:
        # 关键修改：获取db实例
        db = get_db()
        
        # 获取用户信息
        user = Users.query.get(user_id)
        
        # 计算基础代谢率
        bmr = calculate_bmr(user)
        
        # 确定活动因子
        activity_factor = determine_activity_factor(user_id)
        
        # 计算每日能量需求
        energy_target = int(bmr * activity_factor)
        
        # 确定宏量营养素分配
        macro_split = determine_macro_split(user_id)
        
        # 确定饮食限制
        dietary_restrictions = determine_dietary_restrictions(user_id)
        
        # 创建计划
        plan = NutritionPlans(
            user_id=user_id,
            energy_target_kcal=energy_target,
            macro_split=macro_split,
            dietary_restrictions=dietary_restrictions,
            recommendations="基于您的个人数据生成的初始营养计划。请记录您的餐食以获得更个性化的建议。",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(plan)
        db.session.commit()
        
        # 创建示例餐食记录
        create_sample_meals(plan.plan_id)
        
        return plan
        
    except Exception as e:
        db = get_db()
        db.session.rollback()
        print(f"创建营养计划失败: {e}")
        raise

def calculate_bmr(user):
    """计算基础代谢率（使用修正的哈里斯-本尼迪克特公式）"""
    # 需要性别、年龄、身高和体重
    if not user or not user.weight_kg or not user.height_cm or not user.birth_date:
        # 返回默认值
        if user and user.gender == 'male':
            return 1800  # 男性默认值
        else:
            return 1500  # 女性默认值
            
    # 计算年龄
    today = datetime.now().date()
    age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
    
    # 获取身高和体重
    weight = float(user.weight_kg)
    height = float(user.height_cm)
    
    # 根据性别使用不同公式
    if user.gender == 'male':
        return int((10 * weight) + (6.25 * height) - (5 * age) + 5)
    else:  # female 或 other
        return int((10 * weight) + (6.25 * height) - (5 * age) - 161)

def determine_activity_factor(user_id):
    """确定活动因子"""
    # 查看用户最近的步数记录
    metrics = HealthMetrics.query.filter(
        HealthMetrics.user_id == user_id,
        HealthMetrics.steps != None
    ).order_by(HealthMetrics.recorded_at.desc()).limit(7).all()
    
    # 如果有步数记录，根据步数确定活动水平
    if metrics:
        avg_steps = sum(m.steps for m in metrics) / len(metrics)
        
        if avg_steps < 5000:
            return 1.2  # 久坐不动
        elif avg_steps < 7500:
            return 1.375  # 轻度活动
        elif avg_steps < 10000:
            return 1.55  # 中度活动
        else:
            return 1.725  # 高度活动
    
    # 如果没有步数记录，返回默认值
    return 1.375  # 默认轻度活动

def determine_macro_split(user_id):
    """确定宏量营养素分配"""
    # 获取用户信息
    user = Users.query.get(user_id)
    
    # 获取健康风险
    risks = RiskAssessments.query.filter_by(user_id=user_id).order_by(
        RiskAssessments.assessment_date.desc()).all()
        
    # 获取用户BMI
    bmi = None
    if user and user.height_cm and user.weight_kg and float(user.height_cm) > 0:
        height_m = float(user.height_cm) / 100
        weight_kg = float(user.weight_kg)
        bmi = weight_kg / (height_m * height_m)
        
    # 基于风险调整宏量营养素
    if risks:
        # 查找高风险疾病
        high_risks = [r for r in risks if r.risk_level == 'high']
        
        # 高血压风险 - 低钠饮食，适当增加蛋白质
        if any(r.disease == '高血压' for r in high_risks):
            return {'carb': 45, 'protein': 30, 'fat': 25}
            
        # 代谢综合征风险 - 控制碳水，增加蛋白质，健康脂肪
        if any(r.disease == '代谢综合征' for r in high_risks):
            return {'carb': 40, 'protein': 30, 'fat': 30}
            
    # 基于BMI调整
    if bmi:
        if bmi >= 28:  # 肥胖
            return {'carb': 35, 'protein': 35, 'fat': 30}  # 低碳水，高蛋白
        elif bmi >= 24:  # 超重
            return {'carb': 40, 'protein': 30, 'fat': 30}  # 中等碳水，高蛋白
        elif bmi <= 18.5:  # 体重不足
            return {'carb': 55, 'protein': 25, 'fat': 20}  # 高碳水，中等蛋白
            
    # 默认宏量营养素分配
    if user and user.gender == 'male':
        return {'carb': 50, 'protein': 25, 'fat': 25}  # 男性默认
    else:
        return {'carb': 50, 'protein': 25, 'fat': 25}  # 女性默认

def determine_dietary_restrictions(user_id):
    """确定饮食限制"""
    # TODO: 从用户健康档案中获取过敏和限制信息
    # 暂时返回空列表
    return []

def create_sample_meals(plan_id):
    """创建示例餐食记录"""
    try:
        # 关键修改：获取db实例
        db = get_db()
        
        # 获取营养计划
        plan = NutritionPlans.query.get(plan_id)
        
        if not plan:
            return
            
        # 获取计划的能量目标和宏量营养素分配
        energy_target = plan.energy_target_kcal
        
        macro_split = plan.macro_split
        if isinstance(macro_split, str):
            macro_split = json.loads(macro_split)
            
        # 默认宏量营养素分配
        carb_pct = macro_split.get('carb', 50)
        protein_pct = macro_split.get('protein', 25)
        fat_pct = macro_split.get('fat', 25)
        
        # 示例餐食
        sample_meals = [
            {
                'name': '早餐',
                'time': datetime.now().replace(hour=8, minute=0),
                'desc': '全麦面包 + 鸡蛋 + 牛奶',
                'pct': 0.25  # 总能量的25%
            },
            {
                'name': '午餐',
                'time': datetime.now().replace(hour=12, minute=30),
                'desc': '糙米饭 + 鸡胸肉 + 蔬菜沙拉',
                'pct': 0.35  # 总能量的35%
            },
            {
                'name': '晚餐',
                'time': datetime.now().replace(hour=18, minute=30),
                'desc': '三文鱼 + 西兰花 + 甘薯',
                'pct': 0.30  # 总能量的30%
            },
            {
                'name': '加餐',
                'time': datetime.now().replace(hour=15, minute=0),
                'desc': '坚果 + 水果',
                'pct': 0.10  # 总能量的10%
            }
        ]
        
        # 创建餐食记录
        for meal in sample_meals:
            # 计算该餐能量
            calories = int(energy_target * meal['pct'])
            
            # 计算宏量营养素（克）
            protein_g = int(calories * protein_pct / 100 / 4)  # 1g蛋白质=4kcal
            carb_g = int(calories * carb_pct / 100 / 4)        # 1g碳水=4kcal
            fat_g = int(calories * fat_pct / 100 / 9)          # 1g脂肪=9kcal
            
            macros = {
                'protein': protein_g,
                'carbs': carb_g,
                'fat': fat_g
            }
            
            # 创建记录
            new_meal = Meals(
                plan_id=plan.plan_id,
                meal_time=meal['time'] - timedelta(days=1),  # 昨天的记录
                foods=[{'name': meal['desc'], 'amount': '1 份'}],
                calories=calories,
                macros_json=macros,
                glycemic_load=random.randint(5, 15),
                satiety_score=random.randint(70, 95)
            )
            
            db.session.add(new_meal)
            
        db.session.commit()
        
    except Exception as e:
        db = get_db()
        db.session.rollback()
        print(f"创建示例餐食失败: {e}")

def get_recommended_micronutrients(user_id):
    """获取推荐的微量营养素"""
    # 获取用户风险评估
    risks = RiskAssessments.query.filter_by(user_id=user_id).order_by(
        RiskAssessments.assessment_date.desc()).all()
        
    # 获取用户最近的健康指标
    metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
        HealthMetrics.recorded_at.desc()).first()
        
    # 基础重要微量营养素
    base_micros = ['维生素D', '维生素B族', '维生素C', '钙']
    
    # 根据风险和指标调整
    if risks:
        # 查找高风险疾病
        high_risks = [r for r in risks if r.risk_level in ['high', 'medium']]
        
        # 高血压风险
        if any(r.disease == '高血压' for r in high_risks):
            base_micros.extend(['钾', '镁'])
            
        # 代谢综合征风险
        if any(r.disease == '代谢综合征' for r in high_risks):
            base_micros.extend(['铬', '锌', '硒'])
            
        # 睡眠呼吸暂停风险
        if any(r.disease == '睡眠呼吸暂停' for r in high_risks):
            base_micros.append('ω-3脂肪酸')
            
    # 根据健康指标调整
    if metrics:
        # 血压偏高
        if metrics.blood_pressure_systolic and metrics.blood_pressure_systolic > 130:
            if '钾' not in base_micros:
                base_micros.append('钾')
                
        # 睡眠不足
        if metrics.sleep_duration and float(metrics.sleep_duration) < 7:
            base_micros.append('镁')
            
    # 去重
    unique_micros = list(set(base_micros))
    
    # 限制返回数量
    return unique_micros[:5]

def format_meals(meals):
    """格式化餐食记录"""
    if not meals:
        return []
        
    # 分类餐食类型
    categories = {
        'breakfast': [],
        'lunch': [],
        'dinner': [],
        'snack': []
    }
    
    # 对餐食进行分类
    for meal in meals:
        hour = meal.meal_time.hour
        
        if 5 <= hour < 11:
            category = 'breakfast'
        elif 11 <= hour < 15:
            category = 'lunch'
        elif 17 <= hour < 22:
            category = 'dinner'
        else:
            category = 'snack'
            
        # 提取食物描述
        foods_desc = []
        if meal.foods:
            try:
                foods = meal.foods
                if isinstance(foods, str):
                    foods = json.loads(foods)
                    
                for food in foods:
                    if isinstance(food, dict):
                        food_name = food.get('name', '')
                        if food_name:
                            foods_desc.append(food_name)
            except:
                pass
                
        # 提取宏量营养素比例
        macros_text = ""
        if meal.macros_json:
            try:
                macros = meal.macros_json
                if isinstance(macros, str):
                    macros = json.loads(macros)
                    
                p = macros.get('protein', 0)
                c = macros.get('carbs', 0)
                f = macros.get('fat', 0)
                
                if p or c or f:
                    macros_text = f"C{c}/P{p}/F{f}"
            except:
                pass
                
        # 格式化餐食
        formatted_meal = {
            'name': get_meal_name(category),
            'desc': ' + '.join(foods_desc) if foods_desc else '未记录详细内容',
            'kcal': meal.calories or 0,
            'macros': macros_text
        }
        
        categories[category].append(formatted_meal)
        
    # 从各类别中选取最新的一个
    result = []
    
    # 优先顺序：早餐、午餐、晚餐
    for category in ['breakfast', 'lunch', 'dinner']:
        if categories[category]:
            # 按时间倒序排序
            categories[category].sort(key=lambda x: -1)  # 简化版，实际应基于记录时间
            result.append(categories[category][0])
            
    # 如果结果不足3个，加入加餐或示例
    if len(result) < 3:
        if categories['snack']:
            result.append(categories['snack'][0])
            
    # 如果仍然不足3个，添加示例
    examples = [
        {'name': '早餐', 'desc': '全麦面包 + 鸡蛋 + 酸奶', 'kcal': 430, 'macros': 'C45/P25/F30'},
        {'name': '午餐', 'desc': '糙米饭 + 蒸鱼 + 蔬菜', 'kcal': 520, 'macros': 'C50/P30/F20'},
        {'name': '晚餐', 'desc': '鸡胸肉 + 西蓝花 + 薯类', 'kcal': 480, 'macros': 'C40/P35/F25'}
    ]
    
    # 检查哪些餐食类型已经有了
    existing_names = [m['name'] for m in result]
    
    # 添加缺失的餐食类型
    for example in examples:
        if example['name'] not in existing_names and len(result) < 3:
            result.append(example)
            
    # 确保最多返回3个
    return result[:3]

def get_meal_name(category):
    """根据分类返回餐食名称"""
    names = {
        'breakfast': '早餐',
        'lunch': '午餐',
        'dinner': '晚餐',
        'snack': '加餐'
    }
    return names.get(category, '餐食')

def generate_nutrition_recommendations(plan, risks, metrics):
    """生成营养建议"""
    recommendations = []
    
    # 基础建议
    recommendations.append({
        "category": "基础营养",
        "title": "均衡饮食原则",
        "desc": f"每日目标{plan.energy_target_kcal}卡路里，注重食物多样性，每餐包含蛋白质、复合碳水和健康脂肪。"
    })
    
    # 根据风险生成建议
    if risks:
        high_risks = [r for r in risks if r.risk_level in ['high', 'medium']]
        
        # 高血压风险
        if any(r.disease == '高血压' for r in high_risks):
            recommendations.append({
                "category": "血压管理",
                "title": "DASH饮食原则",
                "desc": "增加蔬果摄入，限制钠(<5g/天)，增加钾、镁、钙的摄入。少加工食品，多新鲜食材。"
            })
            
        # 代谢综合征风险
        if any(r.disease == '代谢综合征' for r in high_risks):
            recommendations.append({
                "category": "血糖管理",
                "title": "低GI饮食策略",
                "desc": "选择低GI碳水，控制精制糖，增加膳食纤维，规律进餐，避免过度饥饿。"
            })
            
        # 睡眠呼吸暂停风险
        if any(r.disease == '睡眠呼吸暂停' for r in high_risks):
            recommendations.append({
                "category": "体重管理",
                "title": "热量赤字策略",
                "desc": "每日控制在合理热量内，晚餐减量，睡前3小时避免进食，选择富含蛋白质的食物增加饱腹感。"
            })
            
    # 根据健康指标添加建议
    if metrics:
        # 血压偏高
        high_bp = [m for m in metrics if m.blood_pressure_systolic and m.blood_pressure_systolic > 130]
        if high_bp and not any(r["category"] == "血压管理" for r in recommendations):
            recommendations.append({
                "category": "血压管理",
                "title": "减盐增钾策略",
                "desc": "使用香草和香料代替盐调味，增加香蕉、菠菜等高钾食物摄入，适量补充镁元素。"
            })
            
        # 睡眠不足
        poor_sleep = [m for m in metrics if m.sleep_duration and float(m.sleep_duration) < 6.5]
        if poor_sleep and not any(r["category"] == "睡眠支持" for r in recommendations):
            recommendations.append({
                "category": "睡眠支持",
                "title": "促进睡眠的营养策略",
                "desc": "晚餐摄入富含色氨酸的食物(如鸡肉、鸡蛋)，适量补充镁，睡前可饮用温热牛奶或草本茶。"
            })
            
    # 季节性建议
    month = datetime.now().month
    if 3 <= month <= 5:  # 春季
        recommendations.append({
            "category": "季节性建议",
            "title": "春季饮食调整",
            "desc": "增加新鲜绿叶蔬菜摄入，适量食用时令野菜，补充维生素B族和维生素C。"
        })
    elif 6 <= month <= 8:  # 夏季
        recommendations.append({
            "category": "季节性建议",
            "title": "夏季饮食调整",
            "desc": "保持充分水分摄入，多食用西瓜、黄瓜等高水分食物，适量补充电解质。"
        })
    elif 9 <= month <= 11:  # 秋季
        recommendations.append({
            "category": "季节性建议",
            "title": "秋季饮食调整",
            "desc": "增加富含抗氧化物的深色水果摄入，如葡萄、石榴，适量补充优质蛋白质。"
        })
    else:  # 冬季
        recommendations.append({
            "category": "季节性建议",
            "title": "冬季饮食调整",
            "desc": "适量增加热量摄入，选择温热食物，增加根茎类蔬菜和富含维生素D的食物摄入。"
        })
        
    return {"recommendations": recommendations[:4]}  # 最多返回4条建议