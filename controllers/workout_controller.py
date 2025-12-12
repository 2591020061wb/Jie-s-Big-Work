from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models.models import Users, WorkoutPrescriptions, WorkoutSessions, HealthMetrics, RiskAssessments
import json
import random

workout_bp = Blueprint('workout', __name__)


def get_db():
    from extensions import db
    return db


@workout_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_workout_plan():
    try:
        user_id = get_jwt_identity()

        plan = WorkoutPrescriptions.query.filter(
            WorkoutPrescriptions.user_id == user_id,
            WorkoutPrescriptions.start_date <= datetime.now().date(),
            WorkoutPrescriptions.end_date >= datetime.now().date()
        ).first()

        if not plan:
            plan = create_workout_plan(user_id)

        sessions = WorkoutSessions.query.filter_by(plan_id=plan.plan_id).order_by(
            WorkoutSessions.scheduled_date).all()

        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.completion_status == 'completed')
        progress = int(completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

        recent_completed = [s for s in sessions if s.completion_status == 'completed'][-3:] if completed_sessions > 0 else []
        upcoming = [s for s in sessions if s.completion_status == 'pending' and s.scheduled_date >= datetime.now().date()][:3]

        display_sessions = recent_completed + upcoming
        display_sessions.sort(key=lambda s: s.scheduled_date)
        display_sessions = display_sessions[:3]

        formatted_sessions = []
        for session in display_sessions:
            day_name = session.scheduled_date.strftime('%A')
            day_map = {
                'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
                'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六',
                'Sunday': '周日'
            }
            day = day_map.get(day_name, day_name)

            status_map = {'pending': '计划', 'completed': '完成', 'skipped': '跳过'}
            status = status_map.get(session.completion_status, session.completion_status)

            metrics = ''
            if session.metrics_json:
                metrics_data = session.metrics_json
                if isinstance(metrics_data, str):
                    metrics_data = json.loads(metrics_data)

                if 'heart_rate_zone' in metrics_data:
                    metrics = f"心率区 {metrics_data['heart_rate_zone']}%"
                elif 'rpe' in metrics_data:
                    metrics = f"RPE {metrics_data['rpe']}"
                elif 'calories' in metrics_data:
                    metrics = f"{metrics_data['calories']} 千卡"
                elif session.duration_min:
                    metrics = f"{session.duration_min} 分钟"

            formatted_sessions.append({
                'name': session.activity_type,
                'date': day,
                'status': status,
                'metrics': metrics
            })

        phases = get_training_phases(plan, sessions)

        response = {
            'goal': plan.goal,
            'progress': progress,
            'phases': phases,
            'sessions': formatted_sessions
        }
        return jsonify(response)

    except Exception as e:
        print(f"获取运动计划失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500


@workout_bp.route('/complete', methods=['POST'])
@jwt_required()
def complete_workout():
    db = get_db()
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "缺少会话ID"}), 400

        session = WorkoutSessions.query.get(session_id)
        if not session:
            return jsonify({"error": "未找到指定的训练会话"}), 404

        plan = WorkoutPrescriptions.query.get(session.plan_id)
        if not plan or plan.user_id != int(user_id):
            return jsonify({"error": "无权访问此训练会话"}), 403

        session.completion_status = 'completed'
        session.actual_date = datetime.now().date()

        if 'duration_min' in data:
            session.duration_min = data['duration_min']

        metrics = {}
        if 'heart_rate_zone' in data:
            metrics['heart_rate_zone'] = data['heart_rate_zone']
        if 'rpe' in data:
            metrics['rpe'] = data['rpe']
        if 'calories' in data:
            metrics['calories'] = data['calories']

        for key, value in data.items():
            if key.startswith('metric_') and value:
                metrics[key[7:]] = value

        session.metrics_json = metrics

        adherence = calculate_workout_adherence(session, data)
        session.adherence_score = adherence
        session.feedback = generate_workout_feedback(session, adherence)

        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "训练会话已完成",
            "adherence": float(adherence) if adherence else None
        })

    except Exception as e:
        db.session.rollback()
        print(f"完成训练失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


@workout_bp.route('/skip', methods=['POST'])
@jwt_required()
def skip_workout():
    db = get_db()
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        session_id = data.get('session_id')
        reason = data.get('reason', '用户跳过')

        if not session_id:
            return jsonify({"error": "缺少会话ID"}), 400

        session = WorkoutSessions.query.get(session_id)
        if not session:
            return jsonify({"error": "未找到指定的训练会话"}), 404

        plan = WorkoutPrescriptions.query.get(session.plan_id)
        if not plan or plan.user_id != int(user_id):
            return jsonify({"error": "无权访问此训练会话"}), 403

        session.completion_status = 'skipped'
        session.feedback = f"用户跳过原因: {reason}"

        db.session.commit()
        return jsonify({"status": "success", "message": "已跳过训练会话"})

    except Exception as e:
        db.session.rollback()
        print(f"跳过训练失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


@workout_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_workout_sessions():
    try:
        user_id = get_jwt_identity()

        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status')

        plan = WorkoutPrescriptions.query.filter(
            WorkoutPrescriptions.user_id == user_id,
            WorkoutPrescriptions.start_date <= datetime.now().date(),
            WorkoutPrescriptions.end_date >= datetime.now().date()
        ).first()

        if not plan:
            return jsonify({"error": "没有有效的运动计划"}), 404

        query = WorkoutSessions.query.filter_by(plan_id=plan.plan_id)
        if status:
            query = query.filter_by(completion_status=status)

        total = query.count()
        sessions = query.order_by(WorkoutSessions.scheduled_date).offset(offset).limit(limit).all()

        result = []
        for session in sessions:
            day_name = session.scheduled_date.strftime('%A')
            day_map = {
                'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
                'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六',
                'Sunday': '周日'
            }
            day = day_map.get(day_name, day_name)

            status_map = {'pending': '计划', 'completed': '完成', 'skipped': '跳过'}
            status_display = status_map.get(session.completion_status, session.completion_status)

            metrics_data = {}
            if session.metrics_json:
                if isinstance(session.metrics_json, str):
                    metrics_data = json.loads(session.metrics_json)
                else:
                    metrics_data = session.metrics_json

            scheduled_date = session.scheduled_date.strftime('%Y-%m-%d')
            actual_date = session.actual_date.strftime('%Y-%m-%d') if session.actual_date else None

            result.append({
                'id': session.session_id,
                'activity': session.activity_type,
                'scheduledDate': scheduled_date,
                'actualDate': actual_date,
                'day': day,
                'status': status_display,
                'duration': session.duration_min,
                'intensity': session.intensity_level,
                'metrics': metrics_data,
                'adherence': float(session.adherence_score) if session.adherence_score else None,
                'feedback': session.feedback
            })

        return jsonify({'total': total, 'sessions': result})

    except Exception as e:
        print(f"获取训练会话失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500


def create_workout_plan(user_id):
    db = get_db()
    try:
        user = Users.query.get(user_id)

        metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).limit(10).all()

        risks = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).all()

        goal, phase = determine_workout_goal(user, metrics, risks)

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=28)

        plan = WorkoutPrescriptions(
            user_id=user_id,
            goal=goal,
            training_phase=phase,
            generated_by='algorithm_v1',
            start_date=start_date,
            end_date=end_date,
            plan_parameters={
                'frequency': 3,
                'duration': 30,
                'intensity': 'moderate'
            },
            review_notes="系统生成的个性化计划，基于用户健康数据和风险评估"
        )

        db.session.add(plan)
        db.session.flush()

        sessions = generate_workout_sessions(plan)
        for session in sessions:
            db.session.add(session)

        db.session.commit()
        return plan

    except Exception as e:
        db.session.rollback()
        print(f"创建运动处方失败: {e}")
        raise


def determine_workout_goal(user, metrics, risks):
    goal = "改善整体健康与体能"
    phase = "基础调整期"

    if risks:
        high_risks = [r for r in risks if r.risk_level == 'high']
        if high_risks:
            if any(r.disease == '高血压' for r in high_risks):
                goal = "强化心肺 + 降压 + 提升代谢"
                return goal, "针对性训练期"
            if any(r.disease == '代谢综合征' for r in high_risks):
                goal = "减脂增肌 + 提升代谢健康"
                return goal, "针对性训练期"
            if any(r.disease == '睡眠呼吸暂停' for r in high_risks):
                goal = "减脂 + 改善睡眠质量"
                return goal, "针对性训练期"

    if user.weight_kg and user.height_cm and float(user.height_cm) > 0:
        height_m = float(user.height_cm) / 100
        weight_kg = float(user.weight_kg)
        bmi = weight_kg / (height_m * height_m)

        if bmi >= 28:
            goal = "减脂 + 提高心肺功能"
            return goal, "减脂期"
        elif bmi <= 18.5:
            goal = "增肌 + 提高整体体能"
            return goal, "增肌期"

    if metrics:
        systolic_values = [m.blood_pressure_systolic for m in metrics if m.blood_pressure_systolic]
        diastolic_values = [m.blood_pressure_diastolic for m in metrics if m.blood_pressure_diastolic]

        if systolic_values and sum(1 for s in systolic_values if s >= 130) / len(systolic_values) >= 0.5:
            goal = "降压 + 提高心肺功能"
            return goal, "心脏健康期"

        if diastolic_values and sum(1 for d in diastolic_values if d >= 85) / len(diastolic_values) >= 0.5:
            goal = "降压 + 提高心肺功能"
            return goal, "心脏健康期"

        sleep_values = [float(m.sleep_duration) for m in metrics if m.sleep_duration]
        if sleep_values and sum(1 for s in sleep_values if s < 6.5) / len(sleep_values) >= 0.5:
            goal = "改善睡眠质量 + 提高体能"
            return goal, "睡眠优化期"

        stress_values = [m.stress_level for m in metrics if m.stress_level]
        if stress_values and sum(1 for s in stress_values if s > 60) / len(stress_values) >= 0.5:
            goal = "减压 + 提高整体健康"
            return goal, "压力管理期"

    if user.birth_date:
        today = datetime.now().date()
        age = today.year - user.birth_date.year - (
            (today.month, today.day) < (user.birth_date.month, user.birth_date.day)
        )

        if age > 60:
            goal += " + 保持活力与平衡"
            phase = "活力保持期"
        elif age < 30:
            goal += " + 提升运动表现"
            phase = "性能提升期"

    return goal, phase


def generate_workout_sessions(plan):
    params = plan.plan_parameters
    if isinstance(params, str):
        params = json.loads(params)

    frequency = params.get('frequency', 3)
    duration = params.get('duration', 30)
    intensity = params.get('intensity', 'moderate')

    intensity_map = {'light': 'low', 'moderate': 'medium', 'vigorous': 'high'}
    intensity_level = intensity_map.get(intensity, 'medium')

    workout_types = get_workout_types(plan.goal, plan.training_phase)

    sessions = []
    start_date = plan.start_date

    for week in range(4):
        week_start = start_date + timedelta(days=week * 7)
        training_days = select_training_days(week_start, frequency)

        for i, day in enumerate(training_days):
            workout_type = workout_types[i % len(workout_types)]

            session = WorkoutSessions(
                plan_id=plan.plan_id,
                scheduled_date=day,
                activity_type=workout_type['name'],
                duration_min=workout_type['duration'],
                intensity_level=workout_type['intensity'],
                completion_status='pending'
            )
            sessions.append(session)

    return sessions


def get_workout_types(goal, phase):
    base_types = [
        {'name': '低冲击有氧', 'duration': 30, 'intensity': 'low', 'target': '心肺、全身、减压'},
        {'name': '力量循环', 'duration': 35, 'intensity': 'medium', 'target': '肌肉、代谢'},
        {'name': 'HIIT 间歇', 'duration': 25, 'intensity': 'high', 'target': '燃脂、心肺'},
        {'name': '瑜伽/拉伸', 'duration': 40, 'intensity': 'low', 'target': '柔韧、平衡、放松'},
        {'name': '步行/慢跑', 'duration': 45, 'intensity': 'medium', 'target': '心肺、耐力'}
    ]

    if '降压' in goal or '高血压' in goal:
        return [
            {'name': '低冲击有氧', 'duration': 35, 'intensity': 'low', 'target': '心肺、降压'},
            {'name': '步行/慢跑', 'duration': 40, 'intensity': 'medium', 'target': '心肺、耐力'},
            {'name': '瑜伽/拉伸', 'duration': 30, 'intensity': 'low', 'target': '放松、降压'}
        ]
    elif '减脂' in goal:
        return [
            {'name': 'HIIT 间歇', 'duration': 25, 'intensity': 'high', 'target': '燃脂、心肺'},
            {'name': '力量循环', 'duration': 35, 'intensity': 'medium', 'target': '肌肉、代谢'},
            {'name': '有氧间歇', 'duration': 40, 'intensity': 'medium', 'target': '燃脂、心肺'}
        ]
    elif '增肌' in goal:
        return [
            {'name': '力量循环', 'duration': 40, 'intensity': 'medium', 'target': '肌肉、代谢'},
            {'name': '功能性力量', 'duration': 35, 'intensity': 'high', 'target': '肌肉、协调'},
            {'name': '恢复性有氧', 'duration': 30, 'intensity': 'low', 'target': '恢复、心肺'}
        ]
    elif '睡眠' in goal:
        return [
            {'name': '有氧健走', 'duration': 35, 'intensity': 'medium', 'target': '心肺、全身'},
            {'name': '瑜伽/拉伸', 'duration': 40, 'intensity': 'low', 'target': '放松、改善睡眠'},
            {'name': '轻度力量', 'duration': 30, 'intensity': 'medium', 'target': '肌肉、代谢'}
        ]
    else:
        return [
            {'name': '混合有氧', 'duration': 30, 'intensity': 'medium', 'target': '心肺、全身'},
            {'name': '力量训练', 'duration': 35, 'intensity': 'medium', 'target': '肌肉、代谢'},
            {'name': '灵活性训练', 'duration': 30, 'intensity': 'low', 'target': '柔韧、平衡'}
        ]


def select_training_days(week_start, frequency):
    default_days = [0, 2, 4]

    if frequency == 2:
        default_days = [1, 4]
    elif frequency == 4:
        default_days = [0, 1, 3, 5]
    elif frequency == 5:
        default_days = [0, 1, 2, 3, 4]
    elif frequency > 5:
        default_days = list(range(min(frequency, 7)))

    training_days = [week_start + timedelta(days=day) for day in default_days[:frequency]]
    return training_days


def calculate_workout_adherence(session, data):
    adherence = 100

    if session.actual_date and session.scheduled_date != session.actual_date:
        days_diff = abs((session.actual_date - session.scheduled_date).days)
        adherence -= min(days_diff * 5, 20)

    if session.duration_min and data.get('duration_min'):
        duration_ratio = data.get('duration_min') / session.duration_min
        if duration_ratio < 0.8:
            adherence -= 20
        elif duration_ratio < 0.9:
            adherence -= 10

    if 'heart_rate_zone' in data and session.intensity_level:
        hr_zone = int(data.get('heart_rate_zone'))
        if session.intensity_level == 'high' and hr_zone < 80:
            adherence -= 15
        elif session.intensity_level == 'medium' and (hr_zone < 65 or hr_zone > 85):
            adherence -= 10

    if 'rpe' in data and session.intensity_level:
        rpe = int(data.get('rpe'))
        if session.intensity_level == 'high' and rpe < 7:
            adherence -= 15
        elif session.intensity_level == 'medium' and (rpe < 5 or rpe > 8):
            adherence -= 10

    return max(min(adherence, 100), 0)


def generate_workout_feedback(session, adherence):
    if adherence >= 90:
        base_feedback = "出色完成训练！质量高，符合计划要求。"
    elif adherence >= 75:
        base_feedback = "良好完成训练，有少量改进空间。"
    elif adherence >= 50:
        base_feedback = "基本完成训练，但与计划有一定差距。"
    else:
        base_feedback = "训练完成度较低，建议回顾训练计划调整。"

    activity = session.activity_type.lower() if session.activity_type else ""

    if '有氧' in activity:
        specific_feedback = "保持均匀呼吸，注意心率区间控制。"
    elif '力量' in activity:
        specific_feedback = "注意动作质量和控制，逐步增加重量。"
    elif 'hiit' in activity or '间歇' in activity:
        specific_feedback = "高强度部分全力以赴，休息阶段完全恢复。"
    elif '瑜伽' in activity or '拉伸' in activity:
        specific_feedback = "感受肌肉拉伸，保持平稳呼吸，不要勉强。"
    else:
        specific_feedback = "注意训练强度和技术细节，保持良好姿势。"

    return f"{base_feedback} {specific_feedback}"


def get_training_phases(plan, sessions):
    if plan.start_date and plan.end_date:
        total_weeks = (plan.end_date - plan.start_date).days // 7
    else:
        total_weeks = 4

    if plan.training_phase == '基础调整期':
        return [
            {
                'name': f'第 1-{total_weeks//3} 周 · 适应期',
                'duration': f'{total_weeks//3} 周',
                'target': '最大心率 60-70%',
                'desc': '低冲击有氧 + 核心稳定性训练'
            },
            {
                'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 发展期',
                'duration': f'{total_weeks//3} 周',
                'target': '最大心率 65-75%',
                'desc': '逐步提高强度 + 增加力量元素'
            },
            {
                'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 巩固期',
                'duration': f'{total_weeks - 2*total_weeks//3} 周',
                'target': '最大心率 70-80%',
                'desc': '混合训练 + 技能提升'
            }
        ]
    elif plan.training_phase == '减脂期':
        return [
            {
                'name': f'第 1-{total_weeks//3} 周 · 基础期',
                'duration': f'{total_weeks//3} 周',
                'target': '脂肪燃烧区',
                'desc': '有氧训练 + 轻度力量'
            },
            {
                'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 加速期',
                'duration': f'{total_weeks//3} 周',
                'target': '最大心率 70-85%',
                'desc': 'HIIT间歇 + 力量循环'
            },
            {
                'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 强化期',
                'duration': f'{total_weeks - 2*total_weeks//3} 周',
                'target': '混合区间',
                'desc': '复合训练 + 代谢刺激'
            }
        ]
    elif '针对性' in plan.training_phase:
        if '降压' in plan.goal:
            return [
                {
                    'name': f'第 1-{total_weeks//3} 周 · 调节期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '最大心率 60-70%',
                    'desc': '低强度持续有氧 + 呼吸训练'
                },
                {
                    'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 优化期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '最大心率 65-75%',
                    'desc': '中强度间歇 + 瑜伽放松'
                },
                {
                    'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 巩固期',
                    'duration': f'{total_weeks - 2*total_weeks//3} 周',
                    'target': '最大心率 65-75%',
                    'desc': '多样化有氧 + 压力管理'
                }
            ]
        elif '代谢' in plan.goal:
            return [
                {
                    'name': f'第 1-{total_weeks//3} 周 · 激活期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '混合区间',
                    'desc': '复合动作 + 全身训练'
                },
                {
                    'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 增强期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '最大心率 70-85%',
                    'desc': '高强度循环 + 力量训练'
                },
                {
                    'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 稳定期',
                    'duration': f'{total_weeks - 2*total_weeks//3} 周',
                    'target': '混合区间',
                    'desc': '持续刺激 + 有氧力量结合'
                }
            ]
        else:
            return [
                {
                    'name': f'第 1-{total_weeks//3} 周 · 基础期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '目标区间',
                    'desc': '针对性基础训练'
                },
                {
                    'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 提升期',
                    'duration': f'{total_weeks//3} 周',
                    'target': '挑战区间',
                    'desc': '强化训练 + 技能提升'
                },
                {
                    'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 巩固期',
                    'duration': f'{total_weeks - 2*total_weeks//3} 周',
                    'target': '维持区间',
                    'desc': '混合训练 + 成果巩固'
                }
            ]
    else:
        return [
            {
                'name': f'第 1-{total_weeks//3} 周 · 第一阶段',
                'duration': f'{total_weeks//3} 周',
                'target': '基础区间',
                'desc': '基础训练 + 技能建立'
            },
            {
                'name': f'第 {total_weeks//3+1}-{2*total_weeks//3} 周 · 第二阶段',
                'duration': f'{total_weeks//3} 周',
                'target': '进阶区间',
                'desc': '强度提升 + 能力发展'
            },
            {
                'name': f'第 {2*total_weeks//3+1}-{total_weeks} 周 · 第三阶段',
                'duration': f'{total_weeks - 2*total_weeks//3} 周',
                'target': '峰值区间',
                'desc': '综合训练 + 能力整合'
            }
        ]
