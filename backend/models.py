from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class SystemConfig(Base):
    """系统配置表 - 支持动态配置"""
    __tablename__ = "system_config"

    key = Column(String, primary_key=True)  # 配置项键名
    value = Column(Text, nullable=True)     # 配置值（JSON字符串或文本）
    description = Column(String)            # 配置描述
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    """用户会话"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)  # session_id
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)

    # 进度：当前题目索引
    current_question_index = Column(Integer, default=0)

    # 答案：{question_id: answer_text}
    answers = Column(JSON, default=dict)

    # 评估结果（完成后的）
    results = Column(JSON, default=dict)

class APICallLog(Base):
    """API调用日志"""
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String)
    call_type = Column(String)  # "evaluate_single" 或 "generate_report"
    question_id = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)

class AdminLog(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    admin_user = Column(String)
    action = Column(String)
    details = Column(JSON, default=dict)

class SystemStats(Base):
    """系统统计数据"""
    __tablename__ = "system_stats"

    date = Column(String, primary_key=True)  # YYYY-MM-DD
    total_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_questions_per_session = Column(Float, default=0.0)
