# test_current_state.py
import requests
import json

print("=" * 60)
print("测试当前服务器状态")
print("=" * 60)

# 1. 测试服务器是否运行
print("\n1. 测试基础连接...")
try:
    response = requests.get('http://localhost:3000/', timeout=3)
    print(f"✅ 服务器运行正常: {response.status_code}")
except Exception as e:
    print(f"❌ 服务器连接失败: {e}")
    exit()

# 2. 查看所有注册的路由
print("\n2. 查看注册的路由...")
try:
    # 首先添加一个debug路由到app.py来查看所有路由
    print("建议在 app.py 中添加以下路由来调试：")
    print("""
@app.route('/debug/routes')
def debug_routes():
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        output.append(f"{rule.endpoint:50} {methods:20} {rule}")
    return "<pre>" + "\\n".join(sorted(output)) + "</pre>"
    """)
except Exception as e:
    print(f"查看路由失败: {e}")

# 3. 测试登录
print("\n3. 测试登录获取Token...")
login_data = {
    "username": "123456",
    "password": "123456"
}

try:
    response = requests.post(
        'http://localhost:3000/api/auth/login',
        json=login_data,
        timeout=5
    )
    
    print(f"登录状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token') or data.get('access_token')
        if token:
            print(f"✅ 登录成功，获取到Token")
            print(f"Token前30位: {token[:30]}...")
            
            # 4. 测试风险评估API
            print("\n4. 测试风险评估API...")
            headers = {"Authorization": f"Bearer {token}"}
            
            endpoints_to_test = [
                '/api/risk/assessment',
                '/risk/assessment',
                '/api/risk/test'  # 如果添加了测试端点
            ]
            
            for endpoint in endpoints_to_test:
                print(f"\n测试端点: {endpoint}")
                try:
                    response = requests.get(
                        f'http://localhost:3000{endpoint}',
                        headers=headers,
                        timeout=5
                    )
                    print(f"  状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("  ✅ 成功!")
                        data = response.json()
                        print(f"  响应前200字符: {str(data)[:200]}...")
                    elif response.status_code == 401:
                        print("  ❌ 需要认证")
                    elif response.status_code == 404:
                        print("  ❌ 端点不存在")
                    else:
                        print(f"  响应: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"  请求失败: {e}")
        else:
            print(f"❌ 响应中没有token: {data}")
    else:
        print(f"❌ 登录失败: {response.text}")
        
except Exception as e:
    print(f"❌ 登录请求失败: {e}")

# 5. 测试不需要认证的端点
print("\n5. 测试不需要认证的端点...")
no_auth_endpoints = [
    '/',
    '/api/health',
    '/api/test',
    '/getHomeData'
]

for endpoint in no_auth_endpoints:
    print(f"\n测试: {endpoint}")
    try:
        response = requests.get(
            f'http://localhost:3000{endpoint}',
            timeout=3
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ 成功")
    except Exception as e:
        print(f"  请求失败: {e}")

print("\n" + "=" * 60)
print("诊断结果")
print("=" * 60)

print("""
根据测试结果，如果 /api/risk/assessment 返回404，可能原因：

1. 蓝图注册问题：
   - risk_controller.py: risk_bp = Blueprint('risk', __name__)
   - app.py: app.register_blueprint(risk_bp, url_prefix='/api/risk')
   ⚠️ 注意：不要两边都设置url_prefix

2. 函数导入问题：
   - 确保 risk_controller.py 中有 get_risk_assessment 函数
   - 没有语法错误

3. 立即修复步骤：
   a) 在 app.py 中添加临时测试端点：
   b) 重启服务器
   c) 重新测试
""")