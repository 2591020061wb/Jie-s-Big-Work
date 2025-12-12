# psychology/assessment.py
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection
import json
from datetime import datetime

assessment_bp = Blueprint('mental/assessment', __name__)

@assessment_bp.route('/risk-distribution', methods=['GET'])
def get_risk_distribution():
    """获取风险等级分布数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 统计各种风险等级的数量
        cursor.execute("""
                       SELECT risk_level, COUNT(*) as count
                       FROM assessment_records
                       GROUP BY risk_level
                       ORDER BY FIELD(risk_level, 'low', 'medium', 'high', 'critical')
                       """)

        stats_result = cursor.fetchall()
        cursor.close()
        conn.close()

        # 格式化返回数据
        stats = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for row in stats_result:
            risk_level = row['risk_level']
            count = row['count']
            if risk_level in stats:
                stats[risk_level] = count

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@assessment_bp.route('/recent', methods=['GET'])
def get_recent_assessments():
    """获取最近的测评记录"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 获取最近的10条测评记录
        cursor.execute("""
                       SELECT ar.questionnaire_type,
                              ar.total_score,
                              ar.record_date,
                              ar.created_at,
                              ar.risk_level,
                              u.username
                       FROM assessment_records ar
                                JOIN users u ON ar.user_id = u.user_id
                       ORDER BY ar.created_at DESC LIMIT 10
                       """)

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        # 格式化返回数据
        formatted_records = []
        for record in records:
            # 格式化时间
            record_date = record['record_date']
            if isinstance(record_date, str):
                date_str = record_date
            else:
                date_str = str(record_date)

            created_at = record['created_at']
            if isinstance(created_at, str):
                created_str = created_at
            else:
                created_str = str(created_at)

            # 提取时间部分（HH:MM）
            try:
                time_part = created_str.split(' ')[1][:5] if ' ' in created_str else '00:00'
            except:
                time_part = '00:00'

            # 根据测评类型获取中文名称
            questionnaire_name = record['questionnaire_type']
            if questionnaire_name == 'PHQ-9':
                questionnaire_cn = '抑郁症状量表'
            elif questionnaire_name == 'GAD-7':
                questionnaire_cn = '焦虑症状量表'
            else:
                questionnaire_cn = questionnaire_name

            formatted_records.append({
                'questionnaire_type': questionnaire_name,
                'questionnaire_cn': questionnaire_cn,
                'total_score': record['total_score'],
                'record_date': date_str,
                'created_at': created_str,
                'risk_level': record['risk_level'] if record['risk_level'] else 'unknown',
                'username': record['username'] if record['username'] else '匿名用户',
                'time': time_part
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': formatted_records
        })
    except Exception as e:
        print(f"获取最近测评记录错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': []
        }), 500


@assessment_bp.route('/submit', methods=['POST'])
def submit_assessment():
    """提交心理测评"""
    try:

        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            # 如果没有登录，使用默认用户（演示用）
            user_id = 1
        questionnaire_type = data.get('questionnaire_type')
        answers = data.get('answers', [])

        if not questionnaire_type or not answers:
            return jsonify({'code': 400, 'message': '参数不完整'}), 400

        total_score = sum(answers)

        if questionnaire_type == 'PHQ-9':
            if total_score <= 4:
                evaluation_result = '无抑郁症状'
                risk_level = 'low'
            elif total_score <= 9:
                evaluation_result = '轻度抑郁'
                risk_level = 'medium'
            elif total_score <= 14:
                evaluation_result = '中度抑郁'
                risk_level = 'high'
            else:
                evaluation_result = '重度抑郁'
                risk_level = 'critical'
        elif questionnaire_type == 'GAD-7':
            if total_score <= 4:
                evaluation_result = '无焦虑症状'
                risk_level = 'low'
            elif total_score <= 9:
                evaluation_result = '轻度焦虑'
                risk_level = 'medium'
            elif total_score <= 14:
                evaluation_result = '中度焦虑'
                risk_level = 'high'
            else:
                evaluation_result = '重度焦虑'
                risk_level = 'critical'
        else:
            evaluation_result = '待评估'
            risk_level = 'low'

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       INSERT INTO assessment_records
                       (user_id, questionnaire_type, answers, total_score, evaluation_result, risk_level, record_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, (user_id, questionnaire_type, json.dumps(answers), total_score,
                             evaluation_result, risk_level, datetime.now().date()))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '测评提交成功',
            'data': {
                'total_score': total_score,
                'evaluation_result': evaluation_result,
                'risk_level': risk_level
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@assessment_bp.route('/history/<int:user_id>', methods=['GET'])
def get_assessment_history(user_id):
    """获取用户测评历史记录"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       SELECT id, questionnaire_type, total_score, evaluation_result, 
                              risk_level, record_date
                       FROM assessment_records
                       WHERE user_id = %s
                       ORDER BY record_date DESC
                       """, (user_id,))

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [{
                'id': r['id'],
                'questionnaire_type': r['questionnaire_type'],
                'total_score': r['total_score'],
                'evaluation_result': r['evaluation_result'],
                'risk_level': r['risk_level'],
                'record_date': str(r['record_date'])
            } for r in records]
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
