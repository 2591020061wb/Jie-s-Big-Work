# utils/database.py
import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None