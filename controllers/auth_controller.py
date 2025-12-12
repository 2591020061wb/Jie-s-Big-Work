from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.models import Users, HealthProfiles
from app import db
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'message': '缺少必要字段'}), 400
        
        # 检查用户是否已存在
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()
        
        if existing_user:
            return jsonify({'message': '用户名或邮箱已存在'}), 400
        
        # 创建新用户
        new_user = Users(
            username=username,
            password_hash=password,  # 直接存储密码（非安全做法，仅作示例）
            email=email,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(new_user)
        db.session.flush()  # 获取新用户的ID
        
        # 创建健康档案
        profile = HealthProfiles(
            user_id=new_user.user_id,
            blood_type='unknown',
            chronic_conditions=json.dumps([]),
            allergies=json.dumps([]),
            medications=json.dumps([]),
            lifestyle_tags=json.dumps([]),
            last_profile_update=datetime.now()
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return jsonify({
            'message': '注册成功',
            'userId': new_user.user_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'注册失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'message': '请输入用户名和密码'}), 400
        
        # 查找用户
        user = Users.query.filter((Users.username == username) | (Users.email == username)).first()
        
        if not user:
            return jsonify({'message': '用户名或密码错误'}), 401
        
        # 检查密码（直接比较，非安全做法）
        if user.password_hash != password:
            return jsonify({'message': '用户名或密码错误'}), 401
        
        # 生成JWT令牌
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                'username': user.username,
                'email': user.email
            }
        )
        
        # 返回用户信息
        return jsonify({
            'message': '登录成功',
            'token': access_token,
            'user': {
                'userId': user.user_id,
                'username': user.username,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        print(f'登录失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        
        # 获取用户信息和健康档案
        user = Users.query.get(user_id)
        
        if not user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 获取健康档案
        profile = HealthProfiles.query.filter_by(user_id=user_id).first()
        
        # 构建响应
        user_data = user.to_dict()
        
        # 添加健康档案信息
        if profile:
            profile_data = {
                'blood_type': profile.blood_type,
                'chronic_conditions': parse_json_field(profile.chronic_conditions),
                'allergies': parse_json_field(profile.allergies),
                'medications': parse_json_field(profile.medications),
                'lifestyle_tags': parse_json_field(profile.lifestyle_tags)
            }
            user_data.update(profile_data)
        
        return jsonify(user_data), 200
        
    except Exception as e:
        print(f'获取用户信息失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 获取用户
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 更新用户信息
        if 'email' in data:
            user.email = data.get('email')
            
        if 'phone' in data:
            user.phone = data.get('phone')
            
        if 'gender' in data:
            user.gender = data.get('gender')
            
        if 'birth_date' in data:
            user.birth_date = data.get('birth_date')
            
        if 'height_cm' in data:
            user.height_cm = data.get('height_cm')
            
        if 'weight_kg' in data:
            user.weight_kg = data.get('weight_kg')
        
        # 更新健康档案
        profile = HealthProfiles.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = HealthProfiles(user_id=user_id)
            db.session.add(profile)
        
        if 'blood_type' in data:
            profile.blood_type = data.get('blood_type')
            
        if 'chronic_conditions' in data:
            profile.chronic_conditions = data.get('chronic_conditions')
            
        if 'allergies' in data:
            profile.allergies = data.get('allergies')
            
        if 'medications' in data:
            profile.medications = data.get('medications')
            
        if 'lifestyle_tags' in data:
            profile.lifestyle_tags = data.get('lifestyle_tags')
            
        profile.last_profile_update = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': '个人资料已更新',
            'user_id': user.user_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f'更新个人资料失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@auth_bp.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证请求数据
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'message': '当前密码和新密码是必填项'}), 400
        
        # 获取用户
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 验证当前密码
        if user.password_hash != data.get('current_password'):
            return jsonify({'message': '当前密码不正确'}), 401
        
        # 更新密码
        user.password_hash = data.get('new_password')
        db.session.commit()
        
        return jsonify({'message': '密码已更改'})
        
    except Exception as e:
        db.session.rollback()
        print(f'修改密码失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

# 辅助函数
def parse_json_field(field):
    """解析JSON字段"""
    if not field:
        return []
    
    try:
        if isinstance(field, str):
            return json.loads(field)
        return field
    except:
        return field
