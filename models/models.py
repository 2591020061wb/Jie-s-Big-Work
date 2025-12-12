from extensions import db 
from datetime import datetime
import json
# 补充SQLAlchemy类型导入（避免字段类型报错）
from sqlalchemy import BigInteger, String, Numeric, SmallInteger, Integer, Date, DateTime, Text, Boolean, Enum, JSON

class Users(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    username = db.Column(String(100), nullable=False, unique=True)
    password_hash = db.Column(String(255), nullable=False)
    email = db.Column(String(255), unique=True)
    phone = db.Column(String(32))
    gender = db.Column(Enum('male', 'female', 'other'))
    birth_date = db.Column(Date)
    height_cm = db.Column(Numeric(5, 2))
    weight_kg = db.Column(Numeric(5, 2))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'gender': self.gender,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'height_cm': float(self.height_cm) if self.height_cm else None,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None
        }

class HealthProfiles(db.Model):
    __tablename__ = 'health_profiles'
    
    profile_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    blood_type = db.Column(Enum('A', 'B', 'AB', 'O', 'unknown'), default='unknown')
    chronic_conditions = db.Column(JSON)
    allergies = db.Column(JSON)
    medications = db.Column(JSON)
    lifestyle_tags = db.Column(JSON)
    last_profile_update = db.Column(DateTime, default=datetime.utcnow)
    
    user = db.relationship('Users', backref=db.backref('health_profile', uselist=False))

class HealthMetrics(db.Model):
    __tablename__ = 'health_metrics'
    
    metric_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    recorded_at = db.Column(DateTime, nullable=False)
    source = db.Column(String(64))
    heart_rate = db.Column(SmallInteger)
    blood_pressure_systolic = db.Column(SmallInteger)
    blood_pressure_diastolic = db.Column(SmallInteger)
    blood_oxygen = db.Column(Numeric(4, 1))
    resp_rate = db.Column(SmallInteger)
    temperature = db.Column(Numeric(4, 1))
    glucose = db.Column(Numeric(6, 2))
    sleep_duration = db.Column(Numeric(4, 1))
    stress_level = db.Column(SmallInteger)
    steps = db.Column(Integer)
    weight_kg = db.Column(Numeric(5, 2))
    bmi = db.Column(Numeric(4, 1))
    notes = db.Column(Text)
    
    user = db.relationship('Users', backref=db.backref('health_metrics', lazy=True))
    
    def to_dict(self):
        return {
            'metric_id': self.metric_id,
            'user_id': self.user_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'source': self.source,
            'heart_rate': self.heart_rate,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'blood_oxygen': float(self.blood_oxygen) if self.blood_oxygen else None,
            'resp_rate': self.resp_rate,
            'temperature': float(self.temperature) if self.temperature else None,
            'glucose': float(self.glucose) if self.glucose else None,
            'sleep_duration': float(self.sleep_duration) if self.sleep_duration else None,
            'stress_level': self.stress_level,
            'steps': self.steps,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'bmi': float(self.bmi) if self.bmi else None,
            'notes': self.notes
        }

class AlertRules(db.Model):
    __tablename__ = 'alert_rules'
    
    rule_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    metric_field = db.Column(String(64), nullable=False)
    threshold_type = db.Column(Enum('above', 'below', 'range'), nullable=False)
    threshold_value = db.Column(JSON, nullable=False)
    duration_minutes = db.Column(Integer, default=0)
    severity = db.Column(Enum('info', 'warning', 'critical'), default='info')
    notification_channel = db.Column(Enum('app', 'sms', 'email'), default='app')
    active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    user = db.relationship('Users', backref=db.backref('alert_rules', lazy=True))

class Alerts(db.Model):
    __tablename__ = 'alerts'
    
    alert_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    rule_id = db.Column(BigInteger, db.ForeignKey('alert_rules.rule_id'), nullable=False)
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    triggered_at = db.Column(DateTime, nullable=False)
    status = db.Column(Enum('open', 'ack', 'resolved'), default='open')
    message = db.Column(Text)
    resolved_at = db.Column(DateTime)
    
    rule = db.relationship('AlertRules', backref=db.backref('alerts', lazy=True))
    user = db.relationship('Users', backref=db.backref('alerts', lazy=True))

class RiskAssessments(db.Model):
    __tablename__ = 'risk_assessments'
    
    assessment_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    disease = db.Column(String(128), nullable=False)
    assessment_date = db.Column(Date, nullable=False)
    risk_score = db.Column(Numeric(5, 2), nullable=False)
    risk_level = db.Column(Enum('low', 'medium', 'high'), nullable=False)
    key_factors = db.Column(JSON)
    recommendations = db.Column(Text)
    model_version = db.Column(String(32))
    
    user = db.relationship('Users', backref=db.backref('risk_assessments', lazy=True))

class RiskTrends(db.Model):
    __tablename__ = 'risk_trends'
    
    trend_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    month_start = db.Column(Date, nullable=False)
    predicted_score = db.Column(Numeric(5, 2))
    confidence_low = db.Column(Numeric(5, 2))
    confidence_high = db.Column(Numeric(5, 2))
    model_version = db.Column(String(32))
    
    user = db.relationship('Users', backref=db.backref('risk_trends', lazy=True))

class ChronobiologyPlans(db.Model):
    __tablename__ = 'chronobiology_plans'
    
    plan_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    baseline_chronotype = db.Column(Enum('lark', 'owl', 'intermediate', 'unknown'), default='unknown')
    target_sleep_window = db.Column(JSON)
    algorithm_notes = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('Users', backref=db.backref('chronobiology_plan', uselist=False))

class ChronobiologyActions(db.Model):
    __tablename__ = 'chronobiology_actions'
    
    action_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    plan_id = db.Column(BigInteger, db.ForeignKey('chronobiology_plans.plan_id'), nullable=False)
    action_date = db.Column(Date, nullable=False)
    sleep_onset = db.Column(db.Time)  # 补充db.前缀（避免未定义）
    wake_time = db.Column(db.Time)    # 补充db.前缀
    light_exposure = db.Column(JSON)
    caffeine_intake = db.Column(JSON)
    adherence_score = db.Column(Numeric(4, 1))
    feedback = db.Column(Text)
    
    plan = db.relationship('ChronobiologyPlans', backref=db.backref('actions', lazy=True))

class SleepSessions(db.Model):
    __tablename__ = 'sleep_sessions'
    
    session_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    start_time = db.Column(DateTime, nullable=False)
    end_time = db.Column(DateTime, nullable=False)
    sleep_stage_breakdown = db.Column(JSON)
    wake_episodes = db.Column(SmallInteger)
    sleep_efficiency = db.Column(Numeric(5, 2))
    sleep_quality_score = db.Column(Numeric(5, 2))
    device_source = db.Column(String(64))
    
    user = db.relationship('Users', backref=db.backref('sleep_sessions', lazy=True))

class WorkoutPrescriptions(db.Model):
    __tablename__ = 'workout_prescriptions'
    
    plan_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    goal = db.Column(String(255))
    training_phase = db.Column(String(64))
    generated_by = db.Column(String(64))
    start_date = db.Column(Date)
    end_date = db.Column(Date)
    plan_parameters = db.Column(JSON)
    review_notes = db.Column(Text)
    
    user = db.relationship('Users', backref=db.backref('workout_prescriptions', lazy=True))

class WorkoutSessions(db.Model):
    __tablename__ = 'workout_sessions'
    
    session_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    plan_id = db.Column(BigInteger, db.ForeignKey('workout_prescriptions.plan_id'), nullable=False)
    scheduled_date = db.Column(Date, nullable=False)
    actual_date = db.Column(Date)
    activity_type = db.Column(String(64))
    duration_min = db.Column(SmallInteger)
    intensity_level = db.Column(Enum('low', 'medium', 'high'))
    calories_burned = db.Column(Integer)
    metrics_json = db.Column(JSON)
    completion_status = db.Column(Enum('pending', 'completed', 'skipped'), default='pending')
    adherence_score = db.Column(Numeric(4, 1))
    feedback = db.Column(Text)
    
    plan = db.relationship('WorkoutPrescriptions', backref=db.backref('sessions', lazy=True))

class NutritionPlans(db.Model):
    __tablename__ = 'nutrition_plans'
    
    plan_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    energy_target_kcal = db.Column(Integer)
    macro_split = db.Column(JSON)
    dietary_restrictions = db.Column(JSON)
    recommendations = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('Users', backref=db.backref('nutrition_plan', uselist=False))

class Meals(db.Model):
    __tablename__ = 'meals'
    
    meal_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    plan_id = db.Column(BigInteger, db.ForeignKey('nutrition_plans.plan_id'), nullable=False)
    meal_time = db.Column(DateTime, nullable=False)
    foods = db.Column(JSON)
    calories = db.Column(Integer)
    macros_json = db.Column(JSON)
    glycemic_load = db.Column(Numeric(5, 2))
    satiety_score = db.Column(Numeric(4, 1))
    user_feedback = db.Column(Text)
    
    plan = db.relationship('NutritionPlans', backref=db.backref('meals', lazy=True))

class AIArticles(db.Model):
    __tablename__ = 'ai_articles'
    
    article_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    title = db.Column(String(255), nullable=False)
    summary = db.Column(Text)
    tags = db.Column(JSON)
    source = db.Column(String(128))
    published_at = db.Column(DateTime)
    relevance_vector = db.Column(JSON)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class UserArticleViews(db.Model):
    __tablename__ = 'user_article_views'
    
    view_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    article_id = db.Column(BigInteger, db.ForeignKey('ai_articles.article_id'), nullable=False)
    viewed_at = db.Column(DateTime, nullable=False)
    engagement_score = db.Column(Numeric(5, 2))
    
    user = db.relationship('Users', backref=db.backref('article_views', lazy=True))
    article = db.relationship('AIArticles', backref=db.backref('views', lazy=True))

class VisualizationSnapshots(db.Model):
    __tablename__ = 'visualization_snapshots'
    
    snapshot_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    snapshot_date = db.Column(Date, nullable=False)
    dashboard_config = db.Column(JSON)
    kpi_values = db.Column(JSON)
    comparison_baseline = db.Column(JSON)
    generated_by = db.Column(String(64))
    
    user = db.relationship('Users', backref=db.backref('visualization_snapshots', lazy=True))

class AuditLogs(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(BigInteger, primary_key=True, autoincrement=True)  # 补充自增
    user_id = db.Column(BigInteger, db.ForeignKey('users.user_id'))
    action = db.Column(String(128), nullable=False)
    target_id = db.Column(BigInteger)
    target_type = db.Column(String(64))
    # 核心修改：metadata → log_metadata（避免保留关键字冲突）
    log_metadata = db.Column('metadata', JSON)
    logged_at = db.Column(DateTime, default=datetime.utcnow)
    ip_address = db.Column(String(45))
    
    user = db.relationship('Users', backref=db.backref('audit_logs', lazy=True))