# app.py - 合并版（修复CORS + 集成新预测模块）
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity
)
import pymysql
from datetime import datetime, timedelta
import json
import os
import sys

# -------------------------- 添加项目根目录到搜索路径 --------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入SQLAlchemy扩展（如果存在）
try:
    from extensions import db, jwt
    SQLALCHEMY_AVAILABLE = True
    print("✅ 使用SQLAlchemy扩展")
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("⚠️  未找到SQLAlchemy扩展，使用pymysql")

# -------------------------- 基础配置 --------------------------
app = Flask(__name__)

# ✅ 统一的 CORS 配置（支持多个来源）
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:8080",  # ✅ Vue 默认端口
            "http://localhost:8081",  # ✅ 备用端口
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Range", "X-Content-Range"]
    }
})

# ✅ OPTIONS 预检请求处理（自动支持所有来源）
@app.before_request
def handle_options_request():
    """处理 OPTIONS 预检请求（动态支持请求来源）"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        origin = request.headers.get('Origin')
        
        # 动态设置允许的来源
        allowed_origins = [
            'http://localhost:8080',
            'http://localhost:8081',
            'http://127.0.0.1:8080',
            'http://127.0.0.1:8081'
        ]
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080'  # 默认
            
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

# JWT配置
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-this'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'medicalinfo',
    'charset': 'utf8mb4'
}

# 如果SQLAlchemy可用，配置并初始化
if SQLALCHEMY_AVAILABLE:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    jwt.init_app(app)
else:
    # 初始化JWT（没有SQLAlchemy）
    jwt = JWTManager(app)

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# -------------------------- 导入蓝图（如果SQLAlchemy可用） --------------------------
if SQLALCHEMY_AVAILABLE:
    try:
        from controllers.nutrition_controller import nutrition_bp
        from controllers.metrics_controller import metrics_bp
        from controllers.workout_controller import workout_bp
        from controllers.chronobiology_controller import chrono_bp
        from controllers.risk_controller import risk_bp 
        from controllers.visualization_controller import viz_bp
        from controllers.article_controller import article_bp
        from Psychology.dashboard import dashboard_bp
        from Psychology.emotion import emotion_bp
        from Psychology.assessment import assessment_bp
        from Psychology.growth import growth_bp
        
        app.register_blueprint(nutrition_bp, url_prefix='/api/nutrition')
        app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
        app.register_blueprint(workout_bp, url_prefix='/api/workout')
        app.register_blueprint(chrono_bp, url_prefix='/api/chronobiology')
        app.register_blueprint(risk_bp, url_prefix='/api/risk') 
        app.register_blueprint(viz_bp, url_prefix='/api/visualization')
        app.register_blueprint(article_bp, url_prefix='/api/article') 
        app.register_blueprint(dashboard_bp, url_prefix='/api/mental')
        app.register_blueprint(emotion_bp, url_prefix='/api/mental/emotion')
        app.register_blueprint(assessment_bp, url_prefix='/api/mental/assessment')
        app.register_blueprint(growth_bp, url_prefix='/api/mental/growth')

        print("✅ 蓝图注册成功")
    except ImportError as e:
        print(f"⚠️  蓝图导入失败: {e}")

# -------------------------- 原有工具函数导入 --------------------------
try:
    from utils.getAllData import *
    from utils.getPublicData import *
    print("✅ 工具函数导入成功")
except ImportError as e:
    print(f"⚠️  工具函数导入失败: {e}")

# ⚠️ 注释掉旧的机器学习导入（已替换为新预测模块）
# try:
#     from machine.tree import *
#     print("✅ 机器学习模块导入成功")
# except ImportError as e:
#     print(f"⚠️  机器学习模块导入失败: {e}")

# -------------------------- 认证相关路由 --------------------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        print(f"注册请求: username={username}, email={email}")
        
        if not all([username, email, password]):
            return jsonify({'message': '缺少必要字段'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查用户是否已存在
        cursor.execute(
            'SELECT user_id FROM users WHERE username = %s OR email = %s',
            (username, email)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'message': '用户名或邮箱已存在'}), 400
        
        # 直接存储明文密码
        cursor.execute(
            '''INSERT INTO users (username, email, password_hash) 
               VALUES (%s, %s, %s)''',
            (username, email, password)
        )
        user_id = cursor.lastrowid
        
        # 创建健康档案
        cursor.execute(
            'INSERT INTO health_profiles (user_id) VALUES (%s)',
            (user_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 注册成功: 用户ID={user_id}")
        
        return jsonify({
            'message': '注册成功',
            'userId': user_id
        }), 201
        
    except Exception as e:
        print(f'❌ 注册失败: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'message': '服务器错误'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"登录请求: username={username}")
        
        if not all([username, password]):
            return jsonify({'message': '请输入用户名和密码'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute(
            '''SELECT user_id, username, email, password_hash 
               FROM users WHERE username = %s OR email = %s''',
            (username, username)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            print(f"❌ 用户不存在: {username}")
            return jsonify({'message': '用户名或密码错误'}), 401
        
        # 直接比较明文密码
        if user['password_hash'] != password:
            print(f"❌ 密码错误")
            return jsonify({'message': '用户名或密码错误'}), 401
        
        print(f"✅ 密码验证成功")
        
        # 生成JWT令牌
        access_token = create_access_token(
            identity=str(user['user_id']),
            additional_claims={
                'username': user['username'],
                'email': user['email']
            }
        )
        
        # 返回用户信息
        user_info = {
            'userId': user['user_id'],
            'username': user['username'],
            'email': user['email']
        }
        
        print(f"✅ 登录成功: 用户ID={user['user_id']}")
        
        return jsonify({
            'message': '登录成功',
            'token': access_token,
            'user': user_info
        }), 200
        
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': '服务器错误'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('''
            SELECT u.user_id, u.username, u.email, u.phone, 
                   u.gender, u.birth_date, u.height_cm, u.weight_kg,
                   hp.blood_type, hp.chronic_conditions,
                   hp.allergies, hp.medications, hp.lifestyle_tags
            FROM users u
            LEFT JOIN health_profiles hp ON u.user_id = hp.user_id
            WHERE u.user_id = %s
        ''', (current_user,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'message': '用户不存在'}), 404
        
        # 转换JSON字段
        for field in ['chronic_conditions', 'allergies', 'medications', 'lifestyle_tags']:
            if user[field]:
                try:
                    user[field] = json.loads(user[field])
                except:
                    user[field] = user[field]
        
        return jsonify(user), 200
        
    except Exception as e:
        print(f'❌ 获取用户信息失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新用户信息
        update_fields = []
        update_values = []
        
        for field in ['email', 'phone', 'gender']:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data.get(field))
        
        if 'birth_date' in data:
            try:
                birth_date = _parse_date(data.get('birth_date'))
                if birth_date:
                    update_fields.append("birth_date = %s")
                    update_values.append(birth_date)
            except:
                pass
        
        if 'height_cm' in data:
            height = _to_float(data.get('height_cm'))
            if height is not None:
                update_fields.append("height_cm = %s")
                update_values.append(height)
        
        if 'weight_kg' in data:
            weight = _to_float(data.get('weight_kg'))
            if weight is not None:
                update_fields.append("weight_kg = %s")
                update_values.append(weight)
        
        if update_fields:
            update_values.append(current_user_id)
            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
            cursor.execute(sql, update_values)
        
        # 更新健康档案
        cursor.execute('SELECT profile_id FROM health_profiles WHERE user_id = %s', (current_user_id,))
        profile = cursor.fetchone()
        
        if profile:
            # 更新现有档案
            profile_fields = []
            profile_values = []
            
            if 'blood_type' in data:
                profile_fields.append("blood_type = %s")
                profile_values.append(data.get('blood_type') or 'unknown')
            
            for field in ['chronic_conditions', 'allergies', 'medications', 'lifestyle_tags']:
                if field in data:
                    profile_fields.append(f"{field} = %s")
                    profile_values.append(_sanitize_list_field(data.get(field)))
            
            if profile_fields:
                profile_values.append(current_user_id)
                sql = f"UPDATE health_profiles SET {', '.join(profile_fields)}, last_profile_update = NOW() WHERE user_id = %s"
                cursor.execute(sql, profile_values)
        else:
            # 创建新档案
            profile_data = {
                'blood_type': data.get('blood_type', 'unknown'),
                'chronic_conditions': _sanitize_list_field(data.get('chronic_conditions')),
                'allergies': _sanitize_list_field(data.get('allergies')),
                'medications': _sanitize_list_field(data.get('medications')),
                'lifestyle_tags': _sanitize_list_field(data.get('lifestyle_tags'))
            }
            
            cursor.execute('''
                INSERT INTO health_profiles (user_id, blood_type, chronic_conditions, 
                           allergies, medications, lifestyle_tags, last_profile_update)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ''', (current_user_id, 
                  profile_data['blood_type'],
                  profile_data['chronic_conditions'],
                  profile_data['allergies'],
                  profile_data['medications'],
                  profile_data['lifestyle_tags']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': '个人资料已更新', 'user_id': current_user_id}), 200
        
    except Exception as e:
        print(f'❌ 更新用户信息失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

@app.route('/api/auth/change_password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'message': '当前密码和新密码是必填项'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 验证当前密码
        cursor.execute('SELECT password_hash FROM users WHERE user_id = %s', (current_user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': '用户不存在'}), 404
        
        if user['password_hash'] != data.get('current_password'):
            cursor.close()
            conn.close()
            return jsonify({'message': '当前密码不正确'}), 401
        
        # 更新密码
        cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', 
                      (data.get('new_password'), current_user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': '密码已更改'}), 200
        
    except Exception as e:
        print(f'❌ 修改密码失败: {e}')
        return jsonify({'message': '服务器错误'}), 500

# -------------------------- 辅助函数 --------------------------
def _parse_date(value):
    if not value:
        return None
    try:
        if isinstance(value, str):
            return datetime.fromisoformat(value).date()
        return value
    except ValueError:
        return None

def _sanitize_list_field(value):
    if value is None or value == '':
        return json.dumps([])
    if isinstance(value, (list, tuple, set)):
        return json.dumps([str(item).strip() for item in value if str(item).strip()])
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps(parsed)
        except json.JSONDecodeError:
            pass
        items = [item.strip() for item in value.replace('\n', ',').split(',') if item.strip()]
        return json.dumps(items)
    return json.dumps([])

def _to_float(value):
    if value in (None, '', []):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

# -------------------------- 原有业务路由 --------------------------
@app.route('/getHomeData',methods=['GET','POST'])
def getHomeData():
    try:
        pieData = getPieData()
        configOne,wordData = getConfigOne()
        casesData = list(getAllCasesData())
        maxNum,maxType,maxDep,maxHos,maxAge,minAge = getFoundData()
        boyList,girlList,ratioData = getGenderData()
        circleData=getCircleData()
        xData,y1Data,y2Data = getBodyData()
        return jsonify({
            'message':'success',
            'code':200,
            'data':{
                'pieData':pieData,
                'configOne':configOne,
                'casesData':casesData,
                'maxNum':maxNum,
                'maxType': maxType,
                'maxDep': maxDep,
                'maxHos': maxHos,
                'maxAge': maxAge,
                'minAge': minAge,
                'boyList':boyList,
                'girlList':girlList,
                'ratioData':ratioData,
                'circleData':circleData,
                'wordData':wordData,
                'lastData':{
                    'xData':xData,
                    'y1Data':y1Data,
                    'y2Data':y2Data
                }
            }
        })
    except Exception as e:
        print(f"❌ 获取首页数据失败: {e}")
        return jsonify({'message': f'获取首页数据失败: {str(e)}', 'code':500}), 500
    


@app.route('/tableData', methods=['GET', 'POST', 'OPTIONS'])
def tableData():
    """获取表格数据（兼容废弃版前端）"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        tableDataList = getAllCasesData()
        resultData = [x[1:] for x in tableDataList]
        return jsonify({
            'message': 'success', 
            'code': 200, 
            'data': {'resultData': resultData}
        })
    except Exception as e:
        print(f"❌ 获取表格数据失败: {e}")
        return jsonify({
            'message': f'获取表格数据失败: {str(e)}', 
            'code': 500
        }), 500

# ==================== 🎯 新版症状预测接口（已替换） ====================
# ==================== 🎯 新版症状预测接口（多候选显示） ====================
@app.route('/submitModel', methods=['POST'])
def submitModel():
    """
    症状预测疾病（新版 - 支持多条结果显示）
    
    请求: {"content": "头痛 发热 咳嗽"}
    响应: {
        "code": 200,
        "message": "success",
        "data": {
            "results": [
                {"name": "感冒", "category": "呼吸内科", "score": 0.4583, "symptoms": ["头痛", "发烧", "咽痛"]},
                {"name": "流感", "category": "呼吸内科", "score": 0.4394, "symptoms": ["发热", "咳嗽", "乏力"]}
            ],
            "query": "头痛 发热 咳嗽",
            "count": 2
        }
    }
    """
    try:
        # 动态导入
        try:
            from disease_predictor import predict_disease
        except ImportError as e:
            print(f"❌ 无法导入 disease_predictor: {e}")
            return jsonify({
                'code': 500,
                'message': '预测模块未安装',
                'data': {'results': [], 'query': '', 'count': 0}
            }), 500
        
        # 获取症状
        content = request.json.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '症状不能为空',
                'data': {'results': [], 'query': content, 'count': 0}
            }), 400
        
        print(f"\n{'='*70}")
        print(f"🔍 用户查询: {content}")
        
        # ⭐ 调用预测（返回字典列表）
        results = predict_disease(
            symptoms=content,
            topk=10,           # 召回前10个候选
            min_score=0.25,    # 降低阈值到25%
            alpha=0.6,         # 语义50% + 词面50%
            lexical='wexact',  # 加权精确匹配
            return_dict=True   # ⚠️ 必须为True
        )
        
        # 格式化返回（保留前5个结果）
        if results and len(results) > 0:
            # 打印详细日志
            print("\n📊 预测结果（Top 5）:")
            for i, r in enumerate(results[:5], 1):
                print(f"  {i}. {r['name']:20s} [{r['category']:12s}] {r['score']:.1%}")
                print(f"     语义: {r['semantic_score']:.1%} | 词面: {r['lexical_score']:.1%}")
                print(f"     症状: {'、'.join(r['symptoms'][:3])}")
            
            # 截取前5个结果
            top5 = results[:5]
            
            # 格式化症状列表（确保前端能正确显示）
            for r in top5:
                r['symptoms'] = r['symptoms'][:5]  # 最多显示5个症状
                r['score_percent'] = f"{r['score']:.1%}"  # 添加百分比字符串
            
            print(f"\n✅ 返回 {len(top5)} 条结果")
            print("="*70)
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'results': top5,
                    'query': content,
                    'count': len(top5)
                }
            })
            
        else:
            print(f"⚠️  未找到匹配结果（所有候选得分 < 25%）")
            print("="*70)
            
            return jsonify({
                'code': 200,
                'message': '未找到匹配疾病',
                'data': {
                    'results': [],
                    'query': content,
                    'count': 0
                }
            }), 200
        
    except FileNotFoundError as e:
        print(f"❌ 模型文件缺失: {e}")
        return jsonify({
            'code': 500,
            'message': '模型文件缺失',
            'data': {'results': [], 'query': '', 'count': 0}
        }), 500
    
    except Exception as e:
        print(f"❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'预测失败: {str(e)}',
            'data': {'results': [], 'query': '', 'count': 0}
        }), 500


# -------------------------- 测试路由 --------------------------
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'API测试成功',
        'status': 'running',
        'auth': '使用明文密码方案',
        'prediction': '新版BERT预测已启用'
    })

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/api/health', methods=['GET'])
def health_check():
    # 检查预测模块状态
    try:
        from disease_predictor import predict_disease
        predictor_status = '✅ 已加载'
    except ImportError:
        predictor_status = '❌ 未安装'
    
    # 检查模型文件
    import os
    model_path = os.path.join('models', 'medical_biencoder', 'biencoder_index.npz')
    model_status = '✅ 已训练' if os.path.exists(model_path) else '❌ 未训练'
    
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'auth_mode': 'plaintext',
        'database': 'pymysql',
        'predictor_module': predictor_status,
        'model_file': model_status
    }), 200

# -------------------------- 启动应用 --------------------------
if __name__ == '__main__':
    print("🚀 启动医疗健康数据平台...")
    print(f"📡 端口: 3000")
    print(f"🔧 数据库: {DB_CONFIG['database']}")
    print(f"🧠 预测模块: 新版BERT语义理解")
    print(f"🔑 测试接口: POST http://localhost:3000/submitModel")
    print("=" * 50)
    
    # 检查预测模块
    try:
        from disease_predictor import predict_disease
        print("✅ 预测模块已加载")
    except ImportError as e:
        print(f"⚠️  预测模块未安装: {e}")
        print("💡 请先运行: python train_symptom2disease_biencoder.py --train --build_index")
    
    # 如果SQLAlchemy可用，创建表
    if SQLALCHEMY_AVAILABLE:
        with app.app_context():
            try:
                db.create_all()
                print("✅ SQLAlchemy表已创建/更新")
            except Exception as e:
                print(f"⚠️  SQLAlchemy表创建失败: {e}")
    
    app.run(debug=True, port=3000, host='0.0.0.0')
