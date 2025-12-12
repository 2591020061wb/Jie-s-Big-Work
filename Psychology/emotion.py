# psychology/emotion.py
from flask import Blueprint, request, jsonify
from utils.database import get_db_connection
import json
from datetime import datetime
import random
emotion_bp = Blueprint('mental/emotion', __name__)

@emotion_bp.route('/stats/global', methods=['GET'])
def get_global_emotion_stats():
    """获取全局情绪统计"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 统计全局情绪数据
        cursor.execute("""
                       SELECT emotion_type, COUNT(*) as count
                       FROM emotion_records
                       GROUP BY emotion_type
                       """)

        stats_result = cursor.fetchall()
        cursor.close()
        conn.close()

        # 初始化统计数据
        stats = {'positive': 0, 'neutral': 0, 'negative': 0}

        # 填充统计数据
        for row in stats_result:
            emotion_type = row['emotion_type']
            count = row['count']
            if emotion_type in stats:
                stats[emotion_type] = count

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@emotion_bp.route('/recent', methods=['GET'])
def get_recent_emotions():
    """获取最近的情绪记录"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 获取最近的10条情绪记录
        cursor.execute("""
                       SELECT er.description, er.date, er.created_at, u.username
                       FROM emotion_records er
                                JOIN users u ON er.user_id = u.user_id
                       ORDER BY er.created_at DESC LIMIT 10
                       """)

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        # 格式化返回数据
        formatted_records = []
        for record in records:
            # 格式化时间
            record_date = record['date']
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

            formatted_records.append({
                'description': record['description'] if record['description'] else '无描述',
                'date': date_str,
                'created_at': created_str,
                'username': record['username'] if record['username'] else '匿名用户',
                'time': time_part
            })

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': formatted_records
        })
    except Exception as e:
        print(f"获取最近情绪记录错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': []
        }), 500


@emotion_bp.route('/record', methods=['POST'])
def record_emotion():
    """记录情绪"""
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            # 如果没有登录，使用默认用户（演示用）
            user_id = 1
        description = data.get('description')
        emotion_type = data.get('emotion_type')

        if not description:
            return jsonify({'code': 400, 'message': '情绪描述不能为空'}), 400

        if not emotion_type:
            return jsonify({'code': 400, 'message': '情绪类型不能为空'}), 400

        # 根据情绪类型设置分数
        score_map = {
            'positive': random.randint(7, 10),
            'neutral': random.randint(4, 6),
            'negative': random.randint(1, 3)
        }
        score = score_map.get(emotion_type, 5)

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       INSERT INTO emotion_records (user_id, description, emotion_type, score, date)
                       VALUES (%s, %s, %s, %s, %s)
                       """, (user_id, description, emotion_type, score, datetime.now().date()))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': '情绪记录成功',
            'data': {
                'emotion_type': emotion_type,
                'score': score
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@emotion_bp.route('/trend/<int:user_id>', methods=['GET'])
def get_emotion_trend(user_id):
    """获取情绪趋势数据"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        cursor.execute("""
                       SELECT id, date, score, emotion_type, description
                       FROM emotion_records
                       WHERE user_id = %s
                       ORDER BY date DESC LIMIT 30
                       """, (user_id,))

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        dates = []
        scores = []

        for record in records:
            dates.append(str(record['date']))
            scores.append(record['score'])

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'dates': dates,
                'scores': scores,
                'records': [{
                    'id': r['id'],
                    'date': str(r['date']),
                    'score': r['score'],
                    'emotion_type': r['emotion_type'],
                    'description': r['description']
                } for r in records]
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@emotion_bp.route('/stats/<int:user_id>', methods=['GET'])
def get_emotion_stats(user_id):
    """获取情绪统计数据"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 统计各类情绪的数量
        cursor.execute("""
                       SELECT emotion_type, COUNT(*) as count
                       FROM emotion_records
                       WHERE user_id = %s
                       GROUP BY emotion_type
                       """, (user_id,))

        stats_result = cursor.fetchall()
        cursor.close()
        conn.close()

        # 初始化统计数据
        stats = {'positive': 0, 'neutral': 0, 'negative': 0}

        # 填充统计数据
        for row in stats_result:
            emotion_type = row['emotion_type']
            count = row['count']
            if emotion_type in stats:
                stats[emotion_type] = count

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
# 在psychology/emotion.py中添加

@emotion_bp.route('/trend', methods=['GET'])
def get_general_emotion_trend():
    """获取通用情绪趋势数据（不需要用户ID）"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 获取最近的30条情绪记录（不限制用户）
        cursor.execute("""
                       SELECT id, date, score, emotion_type, description
                       FROM emotion_records
                       ORDER BY date DESC LIMIT 30
                       """)

        records = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'records': [{
                    'id': r['id'],
                    'date': str(r['date']),
                    'score': r['score'],
                    'emotion_type': r['emotion_type'],
                    'description': r['description']
                } for r in records]
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@emotion_bp.route('/stats', methods=['GET'])
def get_general_emotion_stats():
    """获取通用情绪统计数据（不需要用户ID）"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 统计全局各类情绪的数量
        cursor.execute("""
                       SELECT emotion_type, COUNT(*) as count
                       FROM emotion_records
                       GROUP BY emotion_type
                       """)

        stats_result = cursor.fetchall()
        cursor.close()
        conn.close()

        # 初始化统计数据
        stats = {'positive': 0, 'neutral': 0, 'negative': 0}

        # 填充统计数据
        for row in stats_result:
            emotion_type = row['emotion_type']
            count = row['count']
            if emotion_type in stats:
                stats[emotion_type] = count

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500