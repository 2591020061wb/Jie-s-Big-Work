from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, time
from models.models import Users, ChronobiologyPlans, ChronobiologyActions, SleepSessions
import json
import random

chrono_bp = Blueprint('chronobiology', __name__)


def get_db():
    from extensions import db
    return db


@chrono_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_chrono_plan():
    try:
        user_id = get_jwt_identity()

        plan = ChronobiologyPlans.query.filter_by(user_id=user_id).first()
        if not plan:
            plan = create_chrono_plan(user_id)

        actions = ChronobiologyActions.query.filter_by(plan_id=plan.plan_id).order_by(
            ChronobiologyActions.action_date.desc()).limit(5).all()

        sleep_sessions = SleepSessions.query.filter_by(user_id=user_id).order_by(
            SleepSessions.start_time.desc()).limit(5).all()

        schedule = []
        for action in actions:
            day_name = action.action_date.strftime('%A')
            day_map = {
                'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
                'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六',
                'Sunday': '周日'
            }
            day = day_map.get(day_name, day_name)

            sleep = action.sleep_onset.strftime('%H:%M') if action.sleep_onset else '--:--'
            wake = action.wake_time.strftime('%H:%M') if action.wake_time else '--:--'
            adherence = int(float(action.adherence_score)) if action.adherence_score else 0

            schedule.append({
                'day': day,
                'sleep': sleep,
                'wake': wake,
                'adherence': adherence,
                'note': action.feedback or '无特殊记录'
            })

        sleep_scores = {'nights': [], '质量': [], '效率': []}
        for session in sleep_sessions:
            day_name = session.start_time.strftime('%a')
            day_map = {
                'Mon': '周一', 'Tue': '周二', 'Wed': '周三',
                'Thu': '周四', 'Fri': '周五', 'Sat': '周六',
                'Sun': '周日'
            }
            day = day_map.get(day_name, day_name)

            sleep_scores['nights'].append(day)
            quality = int(float(session.sleep_quality_score)) if session.sleep_quality_score else 0
            efficiency = int(float(session.sleep_efficiency)) if session.sleep_efficiency else 0
            sleep_scores['质量'].append(quality)
            sleep_scores['效率'].append(efficiency)

        target = '未设置'
        if plan.target_sleep_window:
            target_window = plan.target_sleep_window
            if isinstance(target_window, str):
                target_window = json.loads(target_window)
            start = target_window.get('start', '23:00')
            end = target_window.get('end', '07:00')
            target = f"{start} - {end}"

        tip = generate_chrono_tip(plan, actions)

        return jsonify({
            'target': target,
            'tip': tip,
            'schedule': schedule,
            'sleepScores': sleep_scores
        })

    except Exception as e:
        print(f"获取生物钟计划失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500


@chrono_bp.route('/update', methods=['POST'])
@jwt_required()
def update_chrono_action():
    db = get_db()
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        plan = ChronobiologyPlans.query.filter_by(user_id=user_id).first()
        if not plan:
            plan = create_chrono_plan(user_id)

        action_date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        action_date = datetime.strptime(action_date_str, '%Y-%m-%d').date()

        action = ChronobiologyActions.query.filter_by(
            plan_id=plan.plan_id,
            action_date=action_date
        ).first()

        sleep_time = data.get('sleep_time')
        wake_time = data.get('wake_time')

        sleep_time_obj = datetime.strptime(sleep_time, '%H:%M').time() if sleep_time else None
        wake_time_obj = datetime.strptime(wake_time, '%H:%M').time() if wake_time else None

        if action:
            if sleep_time_obj:
                action.sleep_onset = sleep_time_obj
            if wake_time_obj:
                action.wake_time = wake_time_obj

            if sleep_time_obj and wake_time_obj:
                action.adherence_score = calculate_adherence(plan, sleep_time_obj, wake_time_obj)
                action.feedback = generate_feedback(plan, sleep_time_obj, wake_time_obj)

            db.session.commit()
            return jsonify({"status": "success", "message": "已更新生物钟记录"})

        new_action = ChronobiologyActions(
            plan_id=plan.plan_id,
            action_date=action_date,
            sleep_onset=sleep_time_obj,
            wake_time=wake_time_obj
        )

        if sleep_time_obj and wake_time_obj:
            new_action.adherence_score = calculate_adherence(plan, sleep_time_obj, wake_time_obj)
            new_action.feedback = generate_feedback(plan, sleep_time_obj, wake_time_obj)

        new_action.light_exposure = data.get('light_exposure', {'morning': True, 'evening': False})
        new_action.caffeine_intake = data.get('caffeine_intake', {'time': '10:00', 'amount': 'moderate'})

        db.session.add(new_action)
        db.session.commit()
        return jsonify({"status": "success", "message": "已添加生物钟记录"})

    except Exception as e:
        db.session.rollback()
        print(f"更新生物钟记录失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


@chrono_bp.route('/record_sleep', methods=['POST'])
@jwt_required()
def record_sleep():
    db = get_db()
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M')

        duration_minutes = (end_time - start_time).total_seconds() / 60
        wake_episodes = data.get('wake_episodes', 0)

        sleep_efficiency = 100 * (duration_minutes - (wake_episodes * 5)) / duration_minutes
        sleep_efficiency = max(min(sleep_efficiency, 100), 0)

        sleep_quality = calculate_sleep_quality(start_time, end_time, wake_episodes, sleep_efficiency)

        sleep_stages = data.get('sleep_stages', {'deep': 25, 'light': 55, 'rem': 20})

        sleep_session = SleepSessions(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            sleep_stage_breakdown=sleep_stages,
            wake_episodes=wake_episodes,
            sleep_efficiency=sleep_efficiency,
            sleep_quality_score=sleep_quality,
            device_source=data.get('device', 'manual')
        )

        db.session.add(sleep_session)

        plan = ChronobiologyPlans.query.filter_by(user_id=user_id).first()
        if not plan:
            plan = create_chrono_plan(user_id)

        sleep_date = start_time.date()
        sleep_time = start_time.time()
        wake_time = end_time.time()

        action = ChronobiologyActions.query.filter_by(
            plan_id=plan.plan_id,
            action_date=sleep_date
        ).first()

        if action:
            action.sleep_onset = sleep_time
            action.wake_time = wake_time
            action.adherence_score = calculate_adherence(plan, sleep_time, wake_time)
            action.feedback = generate_feedback(plan, sleep_time, wake_time)
        else:
            new_action = ChronobiologyActions(
                plan_id=plan.plan_id,
                action_date=sleep_date,
                sleep_onset=sleep_time,
                wake_time=wake_time,
                adherence_score=calculate_adherence(plan, sleep_time, wake_time),
                feedback=generate_feedback(plan, sleep_time, wake_time)
            )
            db.session.add(new_action)

        db.session.commit()
        return jsonify({"status": "success", "message": "睡眠记录已保存"})

    except Exception as e:
        db.session.rollback()
        print(f"记录睡眠失败: {e}")
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


def create_chrono_plan(user_id):
    db = get_db()
    try:
        sleep_sessions = SleepSessions.query.filter_by(user_id=user_id).all()
        chronotype = determine_chronotype(sleep_sessions)

        target_window = {
            'lark': {'start': '22:30', 'end': '06:30'},
            'owl': {'start': '23:30', 'end': '07:30'},
            'intermediate': {'start': '23:00', 'end': '07:00'},
            'unknown': {'start': '23:00', 'end': '07:00'}
        }

        plan = ChronobiologyPlans(
            user_id=user_id,
            baseline_chronotype=chronotype,
            target_sleep_window=target_window[chronotype],
            algorithm_notes="基于用户历史睡眠模式和科学建议的目标睡眠窗口",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.session.add(plan)
        db.session.flush()

        today = datetime.now().date()
        for i in range(7):
            action_date = today + timedelta(days=i)
            is_weekend = action_date.weekday() >= 5

            if chronotype == 'lark':
                sleep_time = '22:30' if not is_weekend else '23:00'
                wake_time = '06:30' if not is_weekend else '07:00'
            elif chronotype == 'owl':
                sleep_time = '23:30' if not is_weekend else '00:00'
                wake_time = '07:30' if not is_weekend else '08:00'
            else:
                sleep_time = '23:00' if not is_weekend else '23:30'
                wake_time = '07:00' if not is_weekend else '07:30'

            action = ChronobiologyActions(
                plan_id=plan.plan_id,
                action_date=action_date,
                sleep_onset=datetime.strptime(sleep_time, '%H:%M').time(),
                wake_time=datetime.strptime(wake_time, '%H:%M').time(),
                light_exposure={'morning': True, 'evening': False},
                caffeine_intake={'time': '10:00', 'amount': 'moderate'},
                adherence_score=None,
                feedback="尚未记录实际睡眠时间"
            )
            db.session.add(action)

        db.session.commit()
        return plan

    except Exception as e:
        db.session.rollback()
        print(f"创建生物钟计划失败: {e}")
        raise


def determine_chronotype(sleep_sessions):
    if not sleep_sessions:
        return 'unknown'

    sleep_times = []
    wake_times = []

    for session in sleep_sessions:
        sleep_hour = session.start_time.hour + session.start_time.minute / 60
        wake_hour = session.end_time.hour + session.end_time.minute / 60

        if sleep_hour < 12 and session.start_time.day != session.end_time.day:
            sleep_hour += 24

        sleep_times.append(sleep_hour)
        wake_times.append(wake_hour)

    if len(sleep_times) < 3:
        return 'unknown'

    avg_sleep = sum(sleep_times) / len(sleep_times)
    avg_wake = sum(wake_times) / len(wake_times)

    if avg_sleep < 22.5 and avg_wake < 7:
        return 'lark'
    elif avg_sleep > 23.5 or avg_wake > 8:
        return 'owl'
    return 'intermediate'


def calculate_adherence(plan, sleep_time, wake_time):
    if not plan or not plan.target_sleep_window:
        return 50

    target_window = plan.target_sleep_window
    if isinstance(target_window, str):
        target_window = json.loads(target_window)

    target_sleep = datetime.strptime(target_window.get('start', '23:00'), '%H:%M').time()
    target_wake = datetime.strptime(target_window.get('end', '07:00'), '%H:%M').time()

    def time_diff(t1, t2):
        t1_mins = t1.hour * 60 + t1.minute
        t2_mins = t2.hour * 60 + t2.minute
        diff = abs(t1_mins - t2_mins)
        if diff > 12 * 60:
            diff = 24 * 60 - diff
        return diff

    sleep_diff = time_diff(sleep_time, target_sleep)
    wake_diff = time_diff(wake_time, target_wake)
    max_diff = 120

    sleep_adherence = max(0, 100 - (sleep_diff / max_diff * 100))
    wake_adherence = max(0, 100 - (wake_diff / max_diff * 100))
    total_adherence = (sleep_adherence * 0.5) + (wake_adherence * 0.5)

    return min(100, total_adherence)


def generate_feedback(plan, sleep_time, wake_time):
    adherence = calculate_adherence(plan, sleep_time, wake_time)
    if adherence >= 90:
        return "符合目标睡眠窗口，继续保持良好作息！"
    if adherence >= 70:
        return "接近目标窗口，略有调整空间"
    if adherence >= 50:
        return "与目标窗口存在差距，建议逐步调整"
    return "与目标窗口差距较大，建议循序渐进调整作息时间"


def calculate_sleep_quality(start_time, end_time, wake_episodes, efficiency):
    duration_hours = (end_time - start_time).total_seconds() / 3600

    if 7 <= duration_hours <= 8:
        duration_score = 100
    elif 6 <= duration_hours < 7 or 8 < duration_hours <= 9:
        duration_score = 80
    elif 5 <= duration_hours < 6 or 9 < duration_hours <= 10:
        duration_score = 60
    else:
        duration_score = 40

    efficiency_score = efficiency

    if wake_episodes == 0:
        interruption_score = 100
    elif wake_episodes <= 2:
        interruption_score = 85
    elif wake_episodes <= 5:
        interruption_score = 70
    else:
        interruption_score = 50

    sleep_hour = start_time.hour
    if 22 <= sleep_hour <= 23 or 0 <= sleep_hour <= 1:
        timing_score = 90
    elif 21 <= sleep_hour < 22 or 1 < sleep_hour <= 2:
        timing_score = 70
    else:
        timing_score = 50

    quality_score = (
        duration_score * 0.35 +
        efficiency_score * 0.35 +
        interruption_score * 0.15 +
        timing_score * 0.15
    )
    return quality_score


def generate_chrono_tip(plan, actions):
    if not plan:
        return "建议21:30开始减少蓝光暴露，22:30-23:00之间入睡，保持规律作息。"

    chronotype_tips = {
        'lark': "早起型生物钟，请保持规律作息，避免过晚活动导致交感神经激活。",
        'owl': "夜猫型生物钟，建议适当调整向前，晚餐避免高糖食物，控制灯光亮度。",
        'intermediate': "中间型生物钟，保持规律作息对健康至关重要。",
        'unknown': "需要更多数据确定您的生物钟类型，请持续记录睡眠数据。"
    }

    base_tip = chronotype_tips.get(plan.baseline_chronotype, chronotype_tips['unknown'])

    if actions:
        recent_action = actions[0]
        if recent_action.adherence_score is not None:
            adherence = float(recent_action.adherence_score)
            if adherence < 50:
                base_tip += " 您的睡眠时间与目标差距较大，建议每天提前/延后15分钟，循序渐进调整。"
            elif adherence < 70:
                base_tip += " 睡眠时间接近目标，但仍有优化空间。"

    general_tips = [
        "21:30后关闭强光屏幕，睡前补充镁，23:00前完成轻瑜伽拉伸。",
        "保持卧室温度在18-20°C，光线暗淡，减少噪音干扰。",
        "晚餐后至少2小时再睡觉，避免睡前饮水过多。",
        "建立睡前仪式，如冥想、深呼吸或阅读纸质书籍。"
    ]
    base_tip += f" {random.choice(general_tips)}"

    return base_tip
