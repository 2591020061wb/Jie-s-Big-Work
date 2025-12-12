from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models.models import AIArticles, UserArticleViews, RiskAssessments, HealthMetrics
from extensions import db  # ✅ 修复循环导入
import json
import random
import traceback

# 创建蓝图
article_bp = Blueprint('article', __name__)

# ==================== 路由定义 ====================

@article_bp.route('/recommended', methods=['GET'])
@jwt_required()
def get_recommended_articles():
    """获取个性化推荐文章（Top3）"""
    try:
        user_id = get_jwt_identity()
        
        # 获取所有文章
        all_articles = AIArticles.query.order_by(AIArticles.published_at.desc()).all()
        print(f"✅ 数据库文章数量: {len(all_articles)}")
        
        # 如果文章太少，创建示例文章
        if len(all_articles) < 5:
            create_sample_articles()
            all_articles = AIArticles.query.order_by(AIArticles.published_at.desc()).all()
            
        # 获取用户已查看文章
        viewed_articles = UserArticleViews.query.filter_by(user_id=user_id).all()
        viewed_ids = [v.article_id for v in viewed_articles]
        
        # 获取用户健康数据
        risks = RiskAssessments.query.filter_by(user_id=user_id).order_by(
            RiskAssessments.assessment_date.desc()).all()
        metrics = HealthMetrics.query.filter_by(user_id=user_id).order_by(
            HealthMetrics.recorded_at.desc()).limit(5).all()
            
        # 个性化排名
        ranked_articles = rank_articles_for_user(all_articles, viewed_ids, risks, metrics)
        top_articles = ranked_articles[:3]
        
        # 格式化结果
        result = []
        for article in top_articles:
            time_text = format_relative_time(article.published_at)
            result.append({
                'id': article.article_id,
                'title': article.title,
                'source': article.source or 'MedGPT Lab',
                'time': time_text
            })
            
        print(f"📤 后端返回文章: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 获取推荐失败: {e}\n{traceback.format_exc()}")
        return jsonify([]), 200  # 返回空数组避免前端500

@article_bp.route('/view', methods=['POST'])
@jwt_required()
def record_article_view():
    """记录用户文章查看行为"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({"error": "缺少文章ID"}), 400
            
        # 检查文章是否存在
        article = AIArticles.query.get(article_id)
        if not article:
            return jsonify({"error": "文章不存在"}), 404
            
        # 记录查看（避免重复）
        existing_view = UserArticleViews.query.filter_by(
            user_id=user_id, article_id=article_id
        ).first()
        
        if existing_view:
            # 更新查看时间
            existing_view.viewed_at = datetime.now()
        else:
            # 创建新记录
            view = UserArticleViews(
                user_id=user_id,
                article_id=article_id,
                viewed_at=datetime.now(),
                engagement_score=data.get('engagement_score', 1.0)
            )
            db.session.add(view)
            
        db.session.commit()
        return jsonify({"status": "success", "message": "已记录"})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 记录查看失败: {e}")
        return jsonify({"error": str(e)}), 500

@article_bp.route('/detail/<int:article_id>', methods=['GET'])
@jwt_required()
def get_article_detail(article_id):
    """获取文章详情"""
    try:
        article = AIArticles.query.get(article_id)
        if not article:
            return jsonify({"error": "文章不存在"}), 404
            
        # 解析标签（容错JSON）
        tags = safe_json_loads(article.tags, [])
        
        result = {
            'id': article.article_id,
            'title': article.title,
            'summary': article.summary,
            'content': generate_article_content(article),
            'source': article.source,
            'published_at': article.published_at.strftime('%Y-%m-%d %H:%M') if article.published_at else None,
            'tags': tags
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 获取详情失败: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== 辅助函数 ====================

def format_relative_time(published_at):
    """格式化相对时间"""
    if not published_at:
        return "未知时间"
        
    now = datetime.now()
    delta = now - published_at
    
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)}分钟前"
    elif delta < timedelta(hours=24):
        return f"{int(delta.total_seconds() // 3600)}小时前"
    elif delta < timedelta(days=7):
        return f"{delta.days}天前"
    else:
        return published_at.strftime('%Y-%m-%d')

def safe_json_loads(data, default=None):
    """安全的JSON解析"""
    if not data:
        return default or []
        
    try:
        if isinstance(data, str):
            return json.loads(data)
        elif isinstance(data, (list, dict)):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
        
    return default or []

def create_sample_articles():
    """创建示例文章（修复JSON格式）"""
    sample_articles = [
        {
            'title': 'AI辅助睡眠分期识别准确率突破95%',
            'summary': '最新研究表明，基于深度学习的睡眠分期算法可以准确识别各个睡眠阶段。',
            'tags': ['AI', '睡眠医学', '深度学习'],
            'source': 'MedGPT Lab',
            'published_at': datetime.now() - timedelta(hours=1),
            'relevance_vector': {'sleep': 0.9, 'technology': 0.8}
        },
        {
            'title': '多模态可穿戴数据预测血压新算法',
            'summary': '研究人员开发出一种结合多种生物信号的算法，可无创连续监测血压。',
            'tags': ['可穿戴设备', '血压监测', '算法'],
            'source': 'BioChrono',
            'published_at': datetime.now() - timedelta(hours=3),
            'relevance_vector': {'blood_pressure': 0.9, 'wearable': 0.8}
        },
        {
            'title': '个性化运动处方的闭环调优案例',
            'summary': '新研究展示如何利用实时生理数据调整运动处方。',
            'tags': ['运动科学', '个性化', '健康'],
            'source': 'SportsAI',
            'published_at': datetime.now() - timedelta(days=1),
            'relevance_vector': {'exercise': 0.9, 'personalization': 0.8}
        },
        {
            'title': '智能睡眠呼吸监测技术进展',
            'summary': '新型智能监测设备可在家庭环境下检测睡眠呼吸暂停。',
            'tags': ['睡眠呼吸暂停', '智能监测'],
            'source': 'SleepTech',
            'published_at': datetime.now() - timedelta(days=2),
            'relevance_vector': {'sleep_apnea': 0.9, 'monitoring': 0.8}
        },
        {
            'title': '地中海饮食对心血管健康的长期影响',
            'summary': '为期10年的研究证实，地中海饮食可显著降低心血管疾病风险。',
            'tags': ['营养', '心血管健康'],
            'source': 'Nutrition Science',
            'published_at': datetime.now() - timedelta(days=3),
            'relevance_vector': {'nutrition': 0.9, 'cardiovascular': 0.8}
        }
    ]
    
    try:
        for data in sample_articles:
            # 检查是否已存在
            if AIArticles.query.filter_by(title=data['title']).first():
                continue
                
            article = AIArticles(
                title=data['title'],
                summary=data['summary'],
                tags=json.dumps(data['tags'], ensure_ascii=False),  # ✅ 强制JSON序列化
                source=data['source'],
                published_at=data['published_at'],
                relevance_vector=json.dumps(data['relevance_vector'], ensure_ascii=False),
                created_at=datetime.now()
            )
            db.session.add(article)
            
        db.session.commit()
        print("✅ 示例文章创建成功")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建失败: {e}")

def rank_articles_for_user(articles, viewed_ids, risks, metrics):
    """为用户个性化排序文章"""
    # 提取健康关注点
    concerns = set()
    
    # 从风险评估提取
    for risk in risks:
        if risk.risk_level in ['medium', 'high']:
            if '高血压' in risk.disease:
                concerns.update(['blood_pressure', 'cardiovascular'])
            elif '睡眠' in risk.disease:
                concerns.update(['sleep', 'respiratory'])
            elif '代谢' in risk.disease:
                concerns.update(['metabolism', 'diabetes'])
                
    # 从健康指标提取
    if metrics:
        # 血压异常
        systolic_vals = [m.blood_pressure_systolic for m in metrics if m.blood_pressure_systolic]
        if systolic_vals and sum(v > 130 for v in systolic_vals) / len(systolic_vals) >= 0.5:
            concerns.add('blood_pressure')
            
        # 睡眠不足
        sleep_vals = [safe_float(m.sleep_duration) for m in metrics if m.sleep_duration]
        if sleep_vals and sum(v < 6.5 for v in sleep_vals) / len(sleep_vals) >= 0.5:
            concerns.add('sleep')
            
        # 高压力
        stress_vals = [m.stress_level for m in metrics if m.stress_level]
        if stress_vals and sum(v > 60 for v in stress_vals) / len(stress_vals) >= 0.5:
            concerns.add('stress')
            
    # 默认关注点
    if not concerns:
        concerns = {'health', 'wellness'}
        
    # 对文章评分
    scored = []
    for article in articles:
        # 已查看惩罚
        view_penalty = 0.5 if article.article_id in viewed_ids else 1.0
        
        # 相关性匹配
        relevance = safe_json_loads(article.relevance_vector, {})
        match_score = sum(relevance.get(c, 0) for c in concerns)
        
        # 标签匹配
        tags = safe_json_loads(article.tags, [])
        for tag in tags:
            for c in concerns:
                if c.lower() in tag.lower():
                    match_score += 0.3
                    
        # 时间新鲜度
        recency = 1.0
        if article.published_at:
            days_old = (datetime.now() - article.published_at).days
            recency = max(0.5, 1.0 - days_old / 14)
            
        # 总分
        total = (match_score * 0.7 + recency * 0.3) * view_penalty
        scored.append((article, total))
        
    # 排序
    return [a for a, s in sorted(scored, key=lambda x: x[1], reverse=True)]

def safe_float(value, default=0.0):
    """安全的浮点数转换"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def generate_article_content(article):
    """基于摘要生成文章内容"""
    if not article.summary:
        return "<p>文章内容未能加载。</p>"
        
    paragraphs = [
        f"<h3>{article.title}</h3>",
        f"<p><strong>摘要：</strong>{article.summary}</p>",
        "<h4>背景</h4>",
        "<p>在健康监测和医疗技术快速发展的今天，新型技术和方法不断涌现。</p>",
        "<h4>主要发现</h4>",
        f"<p>{article.summary}</p>",
        "<h4>实际应用</h4>",
        "<ul>",
        "<li>提高健康监测的准确性和便捷性</li>",
        "<li>为个性化健康管理提供数据支持</li>",
        "<li>帮助制定科学的干预方案</li>",
        "</ul>"
    ]
    
    # 添加标签
    tags = safe_json_loads(article.tags, [])
    if tags:
        tag_html = ", ".join([f"<span class='tag'>{t}</span>" for t in tags])
        paragraphs.append(f"<p><strong>标签：</strong>{tag_html}</p>")
        
    # 添加来源和日期
    source_info = []
    if article.source:
        source_info.append(f"来源: {article.source}")
    if article.published_at:
        source_info.append(f"发布于: {article.published_at.strftime('%Y-%m-%d')}")
    if source_info:
        paragraphs.append(f"<p><em>{' | '.join(source_info)}</em></p>")
        
    return "\n".join(paragraphs)
