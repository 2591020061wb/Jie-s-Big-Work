# psychology/growth.py
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection
from datetime import datetime, timedelta

growth_bp = Blueprint('growth', __name__)


@growth_bp.route('/plan/create', methods=['POST'])
def create_growth_plan():
    """创建成长计划"""
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            # 如果没有登录，使用默认用户（演示用）
            user_id = 1
        plan_type = data.get('plan_type', '21_day_stress')

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       SELECT id
                       FROM growth_plans
                       WHERE user_id = %s
                         AND status = 'active' AND plan_type = %s
                       """, (user_id,plan_type))

        existing_plan = cursor.fetchone()
        if existing_plan:
            return jsonify({'code': 400, 'message': '已有进行中的计划'}), 400

        start_date = datetime.now().date()

        if plan_type == '21_day_stress':
            duration = 21
            plan_name = '21天压力管理'
        elif plan_type == '21_day_mindfulness':
            duration = 21
            plan_name = '21天正念练习'
        else:
            duration = 90
            plan_name = '90天全面健康'

        cursor.execute("""
                       INSERT INTO growth_plans
                           (user_id, plan_type, plan_name, duration, start_date, status)
                       VALUES (%s, %s, %s, %s, %s, 'active')
                       """, (user_id, plan_type, plan_name, duration, start_date))

        plan_id = cursor.lastrowid

        # 生成计划任务
        tasks = generate_plan_tasks(plan_type, duration)
        for task in tasks:
            cursor.execute("""
                           INSERT INTO growth_tasks
                               (plan_id, day, content, task_type, completed)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (plan_id, task['day'], task['content'], task['type'], False))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '成长计划创建成功',
            'data': {'plan_id': plan_id}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


def generate_plan_tasks(plan_type, duration):
    """生成计划任务"""
    tasks = []

    if plan_type == '21_day_stress':
        awareness_tasks = [
            '识别并记录一个压力源',
            '观察压力时的身体反应',
            '记录压力触发的情境',
            '分析压力的积极意义',
            '识别压力应对模式',
            '记录压力缓解方法',
            '总结一周压力观察'
        ]
        relaxation_tasks = [
            '进行5分钟深呼吸练习',
            '尝试渐进式肌肉放松',
            '练习冥想5分钟',
            '进行身体扫描练习',
            '尝试引导式想象',
            '练习正念呼吸',
            '总结放松技巧效果'
        ]
        coping_tasks = [
            '实践问题解决策略',
            '练习积极重新评估',
            '尝试情绪表达练习',
            '实践时间管理技巧',
            '练习设定边界',
            '寻求社会支持',
            '制定长期压力管理计划'
        ]

        for day in range(1, duration + 1):
            if day <= 7:
                content = awareness_tasks[(day - 1) % len(awareness_tasks)]
                task_type = '意识培养'
            elif day <= 14:
                content = relaxation_tasks[(day - 1) % len(relaxation_tasks)]
                task_type = '放松训练'
            else:
                content = coping_tasks[(day - 1) % len(coping_tasks)]
                task_type = '应对策略'

            tasks.append({
                'day': day,
                'content': content,
                'type': task_type
            })

    elif plan_type == '21_day_mindfulness':
        mindfulness_tasks = [
            '进行3分钟呼吸觉察练习',
            '练习身体觉察冥想',
            '进行正念饮食练习',
            '练习行走冥想',
            '进行情绪觉察练习',
            '练习接纳不评判',
            '进行慈心冥想',
            '练习当下觉察',
            '进行感官觉察练习',
            '练习放下执念',
            '进行正念沟通练习',
            '练习感恩冥想',
            '进行压力觉察练习',
            '练习自我关怀',
            '进行正念休息',
            '练习觉察思维模式',
            '进行正念运动',
            '练习宽恕冥想',
            '进行自然觉察练习',
            '练习正念睡眠',
            '总结正念练习收获'
        ]

        for day in range(1, duration + 1):
            content = mindfulness_tasks[day - 1] if day <= len(mindfulness_tasks) else '进行正念综合练习'
            tasks.append({
                'day': day,
                'content': content,
                'type': '正念练习'
            })

    else:
        for day in range(1, duration + 1):
            tasks.append({
                'day': day,
                'content': f'第{day}天健康习惯培养任务',
                'type': '健康习惯'
            })

    return tasks


@growth_bp.route('/plan/<int:user_id>', methods=['GET'])
def get_user_plans(user_id):
    """获取用户成长计划"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       SELECT *
                       FROM growth_plans
                       WHERE user_id = %s
                         AND status = 'active'
                       ORDER BY created_at DESC LIMIT 1
                       """, (user_id,))

        plan = cursor.fetchone()

        if not plan:
            return jsonify({'code': 404, 'message': '未找到活跃的计划'}), 404

        cursor.execute("""
                       SELECT *
                       FROM growth_tasks
                       WHERE plan_id = %s
                       ORDER BY day
                       """, (plan['id'],))

        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        plan_data = {
            'id': plan['id'],
            'plan_type': plan['plan_type'],
            'plan_name': plan['plan_name'],
            'duration': plan['duration'],
            'start_date': str(plan['start_date']),
            'tasks': [{
                'id': task['id'],
                'day': task['day'],
                'content': task['content'],
                'type': task['task_type'],
                'completed': bool(task['completed'])
            } for task in tasks]
        }

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': plan_data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@growth_bp.route('/task/update', methods=['POST'])
def update_growth_task():
    """更新成长任务状态"""
    try:
        data = request.json
        user_id = data.get('user_id')
        task_id = data.get('task_id')
        completed = data.get('completed')

        if not user_id or not task_id or completed is None:
            return jsonify({'code': 400, 'message': '参数不完整'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 验证任务是否属于该用户
        cursor.execute("""
                       SELECT gt.id
                       FROM growth_tasks gt
                       JOIN growth_plans gp ON gt.plan_id = gp.id
                       WHERE gt.id = %s AND gp.user_id = %s
                       """, (task_id, user_id))

        task = cursor.fetchone()
        if not task:
            return jsonify({'code': 404, 'message': '任务不存在或不属于当前用户'}), 404

        # 更新任务状态 - 使用正确的字段名
        if completed:
            cursor.execute("""
                           UPDATE growth_tasks
                           SET completed = 1, completed_at = NOW()
                           WHERE id = %s
                           """, (task_id,))
        else:
            cursor.execute("""
                           UPDATE growth_tasks
                           SET completed = 0, completed_at = NULL
                           WHERE id = %s
                           """, (task_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '任务状态更新成功'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@growth_bp.route('/plan/history/<int:user_id>', methods=['GET'])
def get_user_history_plans(user_id):
    """获取用户历史计划（非活跃状态）"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       SELECT id,
                              plan_type,
                              plan_name,
                              duration,
                              start_date,
                              status,
                              (SELECT COUNT(*) FROM growth_tasks WHERE plan_id = growth_plans.id)                   as total_tasks,
                              (SELECT COUNT(*)
                               FROM growth_tasks
                               WHERE plan_id = growth_plans.id
                                 AND completed = 1)                                                                 as completed_tasks
                       FROM growth_plans
                       WHERE user_id = %s
                         AND status != 'active'
                       ORDER BY created_at DESC
                       """, (user_id,))

        plans = cursor.fetchall()
        cursor.close()
        conn.close()

        plan_list = []
        for plan in plans:
            total_tasks = plan['total_tasks'] or 0
            completed_tasks = plan['completed_tasks'] or 0
            completion_rate = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

            # 计算结束日期（开始日期 + 天数）
            end_date = None
            if plan['start_date'] and plan['duration']:
                start_date = plan['start_date']
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = start_date + timedelta(days=plan['duration'] - 1)

            plan_list.append({
                'id': plan['id'],
                'plan_type': plan['plan_type'],
                'plan_name': plan['plan_name'],
                'duration': plan['duration'],
                'start_date': str(plan['start_date']),
                'end_date': str(end_date) if end_date else None,
                'status': plan['status'],
                'completion_rate': completion_rate
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': plan_list
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@growth_bp.route('/plans/active/<int:user_id>', methods=['GET'])
def get_user_active_plans(user_id):
    """获取用户所有活跃计划"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                gp.id,
                gp.plan_type,
                gp.plan_name,
                gp.duration,
                gp.start_date,
                gp.status,
                COUNT(gt.id) as total_tasks,
                SUM(CASE WHEN gt.completed = 1 THEN 1 ELSE 0 END) as completed_tasks
            FROM growth_plans gp
            LEFT JOIN growth_tasks gt ON gp.id = gt.plan_id
            WHERE gp.user_id = %s AND gp.status = 'active'
            GROUP BY gp.id
            ORDER BY gp.created_at DESC
        """, (user_id,))

        plans = cursor.fetchall()
        cursor.close()
        conn.close()

        plan_list = []
        for plan in plans:
            plan_list.append({
                'id': plan['id'],
                'plan_type': plan['plan_type'],
                'plan_name': plan['plan_name'],
                'duration': plan['duration'],
                'start_date': str(plan['start_date']),
                'status': plan['status'],
                'total_tasks': plan['total_tasks'] or 0,
                'completed_tasks': plan['completed_tasks'] or 0
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': plan_list
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@growth_bp.route('/plan/detail/<int:plan_id>', methods=['GET'])
def get_plan_detail(plan_id):
    """获取计划详情"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 获取计划基本信息
        cursor.execute("""
            SELECT *
            FROM growth_plans
            WHERE id = %s
        """, (plan_id,))

        plan = cursor.fetchone()
        if not plan:
            return jsonify({'code': 404, 'message': '计划不存在'}), 404

        # 获取计划任务
        cursor.execute("""
            SELECT *
            FROM growth_tasks
            WHERE plan_id = %s
            ORDER BY day
        """, (plan_id,))

        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        plan_data = {
            'id': plan['id'],
            'plan_type': plan['plan_type'],
            'plan_name': plan['plan_name'],
            'duration': plan['duration'],
            'start_date': str(plan['start_date']),
            'tasks': [{
                'id': task['id'],
                'day': task['day'],
                'content': task['content'],
                'type': task['task_type'],
                'completed': bool(task['completed'])
            } for task in tasks]
        }

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': plan_data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@growth_bp.route('/plan/archive/<int:plan_id>', methods=['POST'])
def archive_plan(plan_id):
    """归档计划（标记为完成）"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 更新计划状态为完成
        cursor.execute("""
            UPDATE growth_plans
            SET status = 'completed'
            WHERE id = %s
        """, (plan_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '计划已标记为完成'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500