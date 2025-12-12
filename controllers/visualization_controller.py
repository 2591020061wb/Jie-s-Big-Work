from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from models.models import Users, HealthMetrics, Alerts, RiskAssessments, VisualizationSnapshots
from extensions import db 
import json

viz_bp = Blueprint('visualization', __name__)

@viz_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        # 获取要显示的用户数量
        user_count = request.args.get('count', 10, type=int)
        
        # 获取仪表板数据
        overview = get_dashboard_overview()
        user_stats = get_user_statistics(user_count)
        health_trends = get_health_trends()
        alerts = get_recent_alerts()
        
        response = {
            'overview': overview,
            'userStats': user_stats,
            'healthTrends': health_trends,
            'alerts': alerts
        }
        
        # 保存仪表板快照（修复JSON序列化问题）
        save_snapshot(user_id, response)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"获取仪表板失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

@viz_bp.route('/snapshot/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_snapshot(user_id):
    try:
        current_user = get_jwt_identity()
        
        # 获取指定用户的最新快照
        snapshot = VisualizationSnapshots.query.filter_by(user_id=user_id).order_by(
            VisualizationSnapshots.snapshot_date.desc()).first()
            
        if not snapshot:
            # 模拟快照数据
            return jsonify([
                { 'label': '本周运动完成度', 'value': '暂无数据' },
                { 'label': '高压异常次数', 'value': '暂无数据' },
                { 'label': '平均睡眠效率', 'value': '暂无数据' }
            ])
            
        # 解析KPI值（兼容字符串/字典）
        kpi_values = snapshot.kpi_values
        if isinstance(kpi_values, str):
            try:
                kpi_values = json.loads(kpi_values)
            except:
                kpi_values = {}
        elif not isinstance(kpi_values, dict):
            kpi_values = {}
            
        # 格式化结果
        result = []
        for key, value in kpi_values.items():
            result.append({
                'label': key,
                'value': value
            })
            
        return jsonify(result)
        
    except Exception as e:
        print(f"获取用户快照失败: {e}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

# 辅助函数
def get_dashboard_overview():
    """获取仪表板概览数据"""
    try:
        # 用户总数
        total_users = Users.query.count()
        
        # 活跃用户数（过去7天有记录的用户）
        active_users = db.session.query(HealthMetrics.user_id).distinct().filter(
            HealthMetrics.recorded_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        # 最近24小时的指标记录数
        recent_metrics = HealthMetrics.query.filter(
            HealthMetrics.recorded_at >= datetime.now() - timedelta(hours=24)
        ).count()
        
        # 未处理的警报数
        open_alerts = Alerts.query.filter_by(status='open').count()
        
        # 高风险用户数
        high_risk_users = db.session.query(RiskAssessments.user_id).distinct().filter(
            RiskAssessments.risk_level == 'high',
            RiskAssessments.assessment_date >= datetime.now() - timedelta(days=30)
        ).count()
        
        return {
            'totalUsers': total_users,
            'activeUsers': active_users,
            'recentMetrics': recent_metrics,
            'openAlerts': open_alerts,
            'highRiskUsers': high_risk_users
        }
        
    except Exception as e:
        print(f"获取仪表板概览失败: {e}")
        return {
            'totalUsers': 0,
            'activeUsers': 0,
            'recentMetrics': 0,
            'openAlerts': 0,
            'highRiskUsers': 0
        }

def get_user_statistics(limit):
    """获取用户统计信息"""
    try:
        # 查询最活跃的用户
        active_users = db.session.query(
            HealthMetrics.user_id,
            func.count(HealthMetrics.metric_id).label('metric_count')
        ).group_by(HealthMetrics.user_id).order_by(desc('metric_count')).limit(limit).all()
        
        result = []
        
        for user_id, count in active_users:
            # 获取用户信息
            user = Users.query.get(user_id)
            if not user:
                continue
                
            # 获取最新的健康指标
            latest_metric = HealthMetrics.query.filter_by(user_id=user_id).order_by(
                HealthMetrics.recorded_at.desc()).first()
                
            # 获取风险评估
            risk = RiskAssessments.query.filter_by(user_id=user_id).order_by(
                RiskAssessments.assessment_date.desc()).first()
                
            # 计算健康分数
            health_score = calculate_health_score(latest_metric, risk)
            
            # 格式化血压（避免空值报错）
            bp_text = 'N/A'
            if latest_metric and latest_metric.blood_pressure_systolic and latest_metric.blood_pressure_diastolic:
                bp_text = f"{latest_metric.blood_pressure_systolic}/{latest_metric.blood_pressure_diastolic}"
            
            # 格式化结果
            user_stat = {
                'userId': user.user_id,
                'username': user.username,
                'lastActive': latest_metric.recorded_at.strftime('%Y-%m-%d %H:%M') if latest_metric else 'Unknown',
                'metrics': {
                    'bloodPressure': bp_text,
                    'heartRate': latest_metric.heart_rate if latest_metric else None,
                    'sleep': float(latest_metric.sleep_duration) if (latest_metric and latest_metric.sleep_duration) else None
                },
                'riskLevel': risk.risk_level if risk else 'unknown',
                'healthScore': health_score
            }
            
            result.append(user_stat)
            
        return result
        
    except Exception as e:
        print(f"获取用户统计失败: {e}")
        return []

def get_health_trends():
    """获取健康趋势数据"""
    try:
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 按天分组查询各项健康指标的平均值
        result = db.session.query(
            func.date(HealthMetrics.recorded_at).label('date'),
            func.avg(HealthMetrics.blood_pressure_systolic).label('avg_systolic'),
            func.avg(HealthMetrics.blood_pressure_diastolic).label('avg_diastolic'),
            func.avg(HealthMetrics.heart_rate).label('avg_heart_rate'),
            func.avg(HealthMetrics.sleep_duration).label('avg_sleep'),
            func.avg(HealthMetrics.stress_level).label('avg_stress')
        ).filter(
            HealthMetrics.recorded_at.between(start_date, end_date)
        ).group_by(
            func.date(HealthMetrics.recorded_at)
        ).order_by(
            func.date(HealthMetrics.recorded_at)
        ).all()
        
        # 格式化结果
        dates = []
        systolic = []
        diastolic = []
        heart_rate = []
        sleep = []
        stress = []
        
        for row in result:
            dates.append(row.date.strftime('%m-%d'))
            
            # 确保值类型正确（空值转None）
            systolic.append(float(row.avg_systolic) if row.avg_systolic is not None else None)
            diastolic.append(float(row.avg_diastolic) if row.avg_diastolic is not None else None)
            heart_rate.append(float(row.avg_heart_rate) if row.avg_heart_rate is not None else None)
            sleep.append(float(row.avg_sleep) if row.avg_sleep is not None else None)
            stress.append(float(row.avg_stress) if row.avg_stress is not None else None)
            
        return {
            'dates': dates,
            'series': [
                {'name': '收缩压', 'data': systolic},
                {'name': '舒张压', 'data': diastolic},
                {'name': '心率', 'data': heart_rate},
                {'name': '睡眠', 'data': sleep},
                {'name': '压力', 'data': stress}
            ]
        }
        
    except Exception as e:
        print(f"获取健康趋势失败: {e}")
        return {'dates': [], 'series': []}

def get_recent_alerts():
    """获取最近的警报"""
    try:
        # 获取最近50个警报
        recent_alerts = Alerts.query.order_by(Alerts.triggered_at.desc()).limit(50).all()
        
        result = []
        for alert in recent_alerts:
            # 获取用户信息
            user = Users.query.get(alert.user_id)
            if not user:
                continue
                
            result.append({
                'alertId': alert.alert_id,
                'userId': alert.user_id,
                'username': user.username,
                'message': alert.message,
                'status': alert.status,
                'triggeredAt': alert.triggered_at.strftime('%Y-%m-%d %H:%M')
            })
            
        return result
        
    except Exception as e:
        print(f"获取最近警报失败: {e}")
        return []

def calculate_health_score(metric, risk):
    """计算健康分数（0-100）"""
    # 基础分数
    score = 70
    
    # 如果没有指标数据，返回默认分数
    if not metric:
        return score
        
    # 根据血压调整
    if metric.blood_pressure_systolic:
        if metric.blood_pressure_systolic >= 140:
            score -= 15
        elif metric.blood_pressure_systolic >= 130:
            score -= 10
        elif metric.blood_pressure_systolic <= 100:
            score -= 5
            
    if metric.blood_pressure_diastolic:
        if metric.blood_pressure_diastolic >= 90:
            score -= 15
        elif metric.blood_pressure_diastolic >= 85:
            score -= 10
            
    # 根据心率调整
    if metric.heart_rate:
        if metric.heart_rate >= 100:
            score -= 10
        elif metric.heart_rate >= 90:
            score -= 5
        elif metric.heart_rate <= 50:
            score -= 5
            
    # 根据睡眠调整
    if metric.sleep_duration:
        sleep_hours = float(metric.sleep_duration)
        if sleep_hours < 6:
            score -= 10
        elif sleep_hours < 7:
            score -= 5
        elif sleep_hours > 9:
            score -= 5
            
    # 根据压力水平调整
    if metric.stress_level:
        if metric.stress_level >= 70:
            score -= 15
        elif metric.stress_level >= 50:
            score -= 10
            
    # 根据风险评估调整
    if risk:
        if risk.risk_level == 'high':
            score -= 15
        elif risk.risk_level == 'medium':
            score -= 5
            
    # 确保分数在0-100范围内
    return max(min(score, 100), 0)

def save_snapshot(user_id, dashboard_data):
    """保存仪表板快照（修复JSON序列化）"""
    try:
        # 今天的日期
        today = datetime.now().date()
        
        # 提取KPI值
        kpi_values = {
            '本周运动完成度': f"{dashboard_data.get('overview', {}).get('activeUsers', 0)}%",
            '高压异常次数': f"{dashboard_data.get('overview', {}).get('openAlerts', 0)} 次",
            '平均睡眠效率': f"{dashboard_data.get('overview', {}).get('highRiskUsers', 0)}%"
        }
        
        # 序列化为JSON字符串（避免SQLAlchemy JSON字段报错）
        kpi_values_json = json.dumps(kpi_values, ensure_ascii=False)
        dashboard_config_json = json.dumps(dashboard_data, ensure_ascii=False)
        comparison_baseline_json = json.dumps({
            'lastWeek': {
                'activeUsers': dashboard_data.get('overview', {}).get('activeUsers', 0) - 5,
                'openAlerts': dashboard_data.get('overview', {}).get('openAlerts', 0) - 2,
                'highRiskUsers': dashboard_data.get('overview', {}).get('highRiskUsers', 0) - 1
            }
        }, ensure_ascii=False)
        
        # 检查是否已有今天的快照
        existing = VisualizationSnapshots.query.filter_by(
            user_id=user_id,
            snapshot_date=today
        ).first()
        
        if existing:
            # 更新现有快照
            existing.kpi_values = kpi_values_json
            existing.dashboard_config = dashboard_config_json
            existing.comparison_baseline = comparison_baseline_json
        else:
            # 创建新快照
            snapshot = VisualizationSnapshots(
                user_id=user_id,
                snapshot_date=today,
                dashboard_config=dashboard_config_json,
                kpi_values=kpi_values_json,
                comparison_baseline=comparison_baseline_json,
                generated_by='system'
            )
            
            db.session.add(snapshot)
            
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"保存仪表板快照失败: {e}")