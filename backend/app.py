from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import json
from typing import List, Dict, Optional, Any
import sys
import os

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings, ConfigManager
from database import init_db, get_db
from models import Session as DBSession, SystemStats, SystemConfig
from evaluator import MBTIEvaluator

# 加载题库
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
questions_path = os.path.join(BASE_DIR, 'mbti_93_questions.json')
with open(questions_path, 'r', encoding='utf-8') as f:
    QUESTIONS_DB = json.load(f)["questions"]

# 初始化FastAPI应用
app = FastAPI(title="MBTI Deep Test API", version="1.0.0")

# CORS配置（允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_evaluator(db: Session) -> MBTIEvaluator:
    """从数据库配置创建评估引擎"""
    # 获取动态配置
    api_enabled = ConfigManager.get_config(db, "api_enabled", settings.API_ENABLED)
    api_key = ConfigManager.get_config(db, "deepseek_api_key", settings.DEEPSEEK_API_KEY)
    base_url = ConfigManager.get_config(db, "deepseek_base_url", settings.DEEPSEEK_BASE_URL)
    model = ConfigManager.get_config(db, "deepseek_model", settings.DEEPSEEK_MODEL)
    cost_per_call = ConfigManager.get_config(db, "cost_per_call", settings.COST_PER_CALL)

    return MBTIEvaluator(
        api_enabled=api_enabled,
        api_key=api_key,
        base_url=base_url,
        model=model,
        cost_per_call=cost_per_call
    )

# 启动时初始化数据库
@app.on_event("startup")
def startup_event():
    init_db()

# ============ 辅助函数 ============

def get_or_create_session(session_id: Optional[str], db: Session) -> DBSession:
    """获取或创建会话"""
    if session_id:
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if session:
            session.last_active = datetime.utcnow()
            db.commit()
            return session

    # 创建新会话
    new_session_id = str(uuid.uuid4())
    session = DBSession(
        id=new_session_id,
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
        completed=False,
        current_question_index=0,
        answers={},
        results={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def check_api_enabled(db: Session):
    """检查API是否启用"""
    api_enabled = ConfigManager.get_config(db, "api_enabled", settings.API_ENABLED)
    if not api_enabled:
        raise HTTPException(status_code=503, detail="API服务暂时关闭，请联系管理员")

def update_daily_stats(db: Session, sessions_completed: int = 0):
    """更新每日统计"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    stats = db.query(SystemStats).filter(SystemStats.date == today).first()

    if not stats:
        stats = SystemStats(date=today)
        db.add(stats)

    stats.total_sessions += 1
    stats.completed_sessions += sessions_completed

    # 计算今日API调用数
    from .models import APICallLog
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = db.query(APICallLog).filter(
        APICallLog.timestamp >= today_start
    ).count()
    stats.total_api_calls = calls_today

    db.commit()

# ============ API路由 ============

@app.get("/")
def root():
    return {"message": "MBTI Deep Test API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "api_enabled": settings.API_ENABLED}

# ---------- 用户端API ----------

@app.get("/questions")
def get_questions(offset: int = 0, limit: int = 30):
    """获取题目列表（分页）"""
    total = len(QUESTIONS_DB)
    questions = QUESTIONS_DB[offset:offset+limit]
    return {
        "questions": questions,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total
    }

@app.post("/session/start")
def start_session(db: Session = Depends(get_db)):
    """开始新会话"""
    session = get_or_create_session(None, db)
    return {
        "session_id": session.id,
        "current_question_index": session.current_question_index,
        "total_questions": len(QUESTIONS_DB)
    }

@app.get("/session/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取会话状态"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.id,
        "current_question_index": session.current_question_index,
        "answers": session.answers,
        "completed": session.completed,
        "total_questions": len(QUESTIONS_DB),
        "created_at": session.created_at.isoformat()
    }

@app.post("/session/{session_id}/answer")
def submit_answer(
    session_id: str,
    question_id: str,
    answer: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """提交单题答案"""
    check_api_enabled()

    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 验证题目ID
    question = next((q for q in QUESTIONS_DB if q["id"] == question_id), None)
    if not question:
        raise HTTPException(status_code=400, detail="Invalid question ID")

    # 保存答案
    session.answers = dict(session.answers)  # 复制dict
    session.answers[question_id] = answer

    # 更新进度
    question_ids = [q["id"] for q in QUESTIONS_DB]
    if question_id in question_ids:
        current_index = question_ids.index(question_id)
        session.current_question_index = max(session.current_question_index, current_index + 1)

    # 检查是否完成
    if len(session.answers) >= len(QUESTIONS_DB):
        session.completed = True
        # 异步触发评估（这里简化，实际需要分批评估）
        # background_tasks.add_task(trigger_evaluation, session_id)

    db.commit()

    return {
        "success": True,
        "session_id": session.id,
        "current_question_index": session.current_question_index,
        "answers_count": len(session.answers)
    }

@app.post("/session/{session_id}/evaluate")
def evaluate_session(session_id: str, db: Session = Depends(get_db)):
    """评估整个会话（分批）"""
    check_api_enabled(db)

    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.answers:
        raise HTTPException(status_code=400, detail="No answers to evaluate")

    # 获取动态配置的评估引擎
    evaluator = get_evaluator(db)

    # 分批评估
    batch_size = 30
    assessments = []

    questions_dict = {q["id"]: q for q in QUESTIONS_DB}

    for i in range(0, len(QUESTIONS_DB), batch_size):
        batch_ids = [q["id"] for q in QUESTIONS_DB[i:i+batch_size] if q["id"] in session.answers]
        for qid in batch_ids:
            question = questions_dict[qid]
            answer = session.answers[qid]
            result = evaluator.evaluate_single_question(question, answer, session_id)
            assessments.append(result)

    # 汇总维度得分
    dimension_scores = {"EI": [], "SN": [], "TF": [], "JP": []}
    for a in assessments:
        dim = a["dimension"]
        if dim in dimension_scores:
            dimension_scores[dim].append((a["score"], a["confidence"]))

    # 计算加权平均
    final_scores = {}
    for dim, scores in dimension_scores.items():
        if scores:
            weighted_sum = sum(s[0] * s[1] for s in scores)
            total_weight = sum(s[1] for s in scores)
            final_scores[dim] = weighted_sum / total_weight if total_weight > 0 else 5
        else:
            final_scores[dim] = 5

    # 生成最终报告
    report = evaluator.generate_final_report(assessments, final_scores)

    # 保存结果
    session.results = {
        "mbti_type": evaluator.scores_to_type(final_scores),
        "dimension_scores": final_scores,
        "assessments": assessments,
        "report": report,
        "evaluated_at": datetime.utcnow().isoformat()
    }
    session.completed = True
    db.commit()

    # 更新统计
    update_daily_stats(db, sessions_completed=1)

    return session.results

@app.get("/session/{session_id}/results")
def get_results(session_id: str, db: Session = Depends(get_db)):
    """获取评估结果"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.completed or not session.results:
        raise HTTPException(status_code=400, detail="Results not ready yet")

    return session.results

# ---------- 管理员API ----------

@app.post("/admin/login")
def admin_login(username: str, password: str):
    """管理员登录（简化版，实际需要bcrypt验证）"""
    if username == settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD_HASH:
        # 这里简化，实际需要bcrypt检查
        return {"access_token": "dummy-token", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """获取系统统计"""
    from .models import APICallLog
    from sqlalchemy import func

    # 今日统计
    today = datetime.utcnow().strftime("%Y-%m-%d")
    stats = db.query(SystemStats).filter(SystemStats.date == today).first()

    # 总体统计
    total_sessions = db.query(DBSession).count()
    completed_sessions = db.query(DBSession).filter(DBSession.completed == True).count()
    total_calls = db.query(APICallLog).count()
    total_cost = db.query(func.sum(APICallLog.cost)).scalar() or 0

    # 最近活动
    recent_sessions = db.query(DBSession).order_by(DBSession.last_active.desc()).limit(10).all()

    # 获取动态配置
    current_config = {
        "api_enabled": ConfigManager.get_config(db, "api_enabled", settings.API_ENABLED),
        "deepseek_api_key_set": bool(ConfigManager.get_config(db, "deepseek_api_key", "")),
        "deepseek_model": ConfigManager.get_config(db, "deepseek_model", settings.DEEPSEEK_MODEL),
        "daily_api_limit": ConfigManager.get_config(db, "daily_api_limit", settings.DAILY_API_LIMIT),
        "cost_per_call": ConfigManager.get_config(db, "cost_per_call", settings.COST_PER_CALL)
    }

    return {
        "today": {
            "sessions": stats.total_sessions if stats else 0,
            "completed": stats.completed_sessions if stats else 0,
            "api_calls": stats.total_api_calls if stats else 0
        },
        "total": {
            "sessions": total_sessions,
            "completed": completed_sessions,
            "api_calls": total_calls,
            "cost": round(total_cost, 2)
        },
        "recent_sessions": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat(),
                "last_active": s.last_active.isoformat(),
                "completed": s.completed,
                "answers_count": len(s.answers)
            }
            for s in recent_sessions
        ],
        "config": current_config
    }

# ---------- 配置管理API ----------

@app.get("/admin/config")
def get_config(db: Session = Depends(get_db)):
    """获取所有配置"""
    return ConfigManager.get_all_configs(db)

@app.post("/admin/config")
def update_config(
    key: str,
    value: Any,
    description: str = "",
    admin_user: str = "admin",
    db: Session = Depends(get_db)
):
    """更新配置"""
    if key not in ConfigManager.DYNAMIC_CONFIG_KEYS:
        raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")

    success = ConfigManager.set_config(db, key, value, description, admin_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update config")

    return {"success": True, "key": key, "value": value}

@app.post("/admin/toggle-api")
def toggle_api(enable: bool, db: Session = Depends(get_db)):
    """开关API功能（通过配置管理）"""
    ConfigManager.set_config(db, "api_enabled", enable, "API启用开关", "admin")
    return {"api_enabled": enable, "message": f"API已{'启用' if enable else '禁用'}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
