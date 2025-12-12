# psychology/dashboard.py
from flask import Blueprint, jsonify
from utils.database import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    """获取心理健康概览数据"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        cursor = conn.cursor()

        # 获取总用户数
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']

        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as count FROM emotion_records")
        total_records = cursor.fetchone()['count']

        # 获取平均情绪分数
        cursor.execute("SELECT AVG(score) as avg_score FROM emotion_records")
        avg_result = cursor.fetchone()
        avg_emotion_score = round(float(avg_result['avg_score'] or 0), 1)

        # 获取高风险案例数（最近7天分数<3）
        cursor.execute("""
                       SELECT COUNT(DISTINCT user_id) as count
                       FROM emotion_records
                       WHERE score
                           < 3
                         AND date >= DATE_SUB(CURDATE()
                           , INTERVAL 7 DAY)
                       """)
        high_risk_cases = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_users': total_users,
                'total_records': total_records,
                'avg_emotion_score': avg_emotion_score,
                'high_risk_cases': high_risk_cases
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
