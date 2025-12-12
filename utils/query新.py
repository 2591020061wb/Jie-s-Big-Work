# file:utils/query.py
from pymysql import connect


def querys(sql, params, type='insert'):
    try:
        # 使用正确的密码
        conn = connect(host='localhost', user='root', password='1324561qt',
                       database='medicalinfo', port=3306, charset='utf8mb4')
        cursor = conn.cursor()

        if type == 'select':
            cursor.execute(sql, params)
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return '执行成功'
    except Exception as e:
        print(f"数据库操作错误: {e}")
        if 'conn' in locals():
            conn.close()
        return None
