# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# 初始化扩展（空实例，后续在app.py中初始化）
db = SQLAlchemy()
jwt = JWTManager()