# psychology/medical.py
from flask import Blueprint, request, jsonify
import random

medical_bp = Blueprint('medical', __name__)

@medical_bp.route('/getHomeData', methods=['GET'])
def get_home_data():
    """获取首页数据"""
    try:
        pie_data = [
            {'name': '0-10岁', 'value': 50},
            {'name': '10-20岁', 'value': 120},
            {'name': '20-30岁', 'value': 300},
            {'name': '30-40岁', 'value': 250},
            {'name': '40-50岁', 'value': 180},
            {'name': '50-60岁', 'value': 100},
            {'name': '60岁以上', 'value': 80}
        ]

        config_one = [
            {'name': '感冒', 'value': 150},
            {'name': '高血压', 'value': 120},
            {'name': '糖尿病', 'value': 100},
            {'name': '心脏病', 'value': 80},
            {'name': '抑郁症', 'value': 60},
            {'name': '焦虑症', 'value': 50}
        ]

        circle_data = [
            {'name': '内科', 'value': 200},
            {'name': '外科', 'value': 150},
            {'name': '儿科', 'value': 120},
            {'name': '妇产科', 'value': 100},
            {'name': '心理科', 'value': 80}
        ]

        word_data = [
            {'name': '感冒', 'value': 100},
            {'name': '发烧', 'value': 80},
            {'name': '头痛', 'value': 70},
            {'name': '咳嗽', 'value': 60},
            {'name': '高血压', 'value': 50},
            {'name': '糖尿病', 'value': 45},
            {'name': '心脏病', 'value': 40},
            {'name': '抑郁症', 'value': 35},
            {'name': '焦虑症', 'value': 30}
        ]

        return jsonify({
            'pieData': pie_data,
            'configOne': config_one,
            'maxNum': 1080,
            'maxType': '感冒',
            'maxDep': '内科',
            'maxHos': '市人民医院',
            'maxAge': 85,
            'minAge': 3,
            'circleData': circle_data,
            'wordData': word_data,
            'boyList': [{'name': '男', 'value': 45}],
            'girlList': [{'name': '女', 'value': 55}],
            'ratioData': [55, 45],
            'lastData': {
                'xData': ['感冒', '高血压', '糖尿病', '心脏病', '抑郁症'],
                'y1Data': [165, 168, 170, 172, 171],
                'y2Data': [65, 70, 68, 75, 72]
            },
            'casesData': [
                [1, '感冒', '男', 25, '2024-01-10', '头痛发热', '张医生', '市人民医院', '内科', 'http://example.com',
                 175, 70, '3天', '无'],
                [2, '高血压', '女', 65, '2024-01-09', '头晕', '李医生', '中心医院', '心血管科', 'http://example.com',
                 160, 65, '2年', '无']
            ]
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@medical_bp.route('/tableData', methods=['GET'])
def get_table_data():
    """获取表格数据"""
    try:
        table_data = [
            ['感冒', '男', 25, '2024-01-10', '头痛发热', '张医生', '市人民医院', '内科', 'http://example.com/1', 175,
             70, '3天', '无'],
            ['高血压', '女', 65, '2024-01-09', '头晕', '李医生', '中心医院', '心血管科', 'http://example.com/2', 160,
             65, '2年', '青霉素'],
            ['糖尿病', '男', 58, '2024-01-08', '多饮多尿', '王医生', '人民医院', '内分泌科', 'http://example.com/3',
             170, 80, '5年', '无'],
            ['抑郁症', '女', 32, '2024-01-07', '情绪低落', '赵医生', '心理医院', '心理科', 'http://example.com/4', 165,
             55, '6个月', '无'],
            ['焦虑症', '男', 28, '2024-01-06', '紧张不安', '钱医生', '精神卫生中心', '心理科', 'http://example.com/5',
             178, 72, '3个月', '无']
        ]

        return jsonify({
            'resultData': table_data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@medical_bp.route('/submitModel', methods=['POST'])
def submit_model():
    """病情预测接口"""
    try:
        data = request.json
        content = data.get('content', '')

        predictions = {
            '头痛': '可能为感冒或偏头痛，建议休息观察',
            '发热': '可能为感染性疾病，建议测量体温',
            '咳嗽': '可能为呼吸道感染，建议多喝水',
            '头晕': '可能与血压有关，建议监测血压',
            '胸闷': '建议进行心电图检查',
            '失眠': '可能与压力有关，建议放松心情'
        }

        result = "建议观察症状变化，如有加重请及时就医"
        for key, value in predictions.items():
            if key in content:
                result = value
                break

        return jsonify({
            'resultData': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500