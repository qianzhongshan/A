import os
import json
import sys
from datetime import datetime
from typing import Optional, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv()

class Settings(BaseSettings):
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # 数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mbti_test.db")

    # 管理员配置
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

    # API开关控制（可以从数据库动态覆盖）
    API_ENABLED: bool = os.getenv("API_ENABLED", "true").lower() == "true"

    # 成本控制
    DAILY_API_LIMIT: int = int(os.getenv("DAILY_API_LIMIT", "10000"))
    COST_PER_CALL: float = float(os.getenv("COST_PER_CALL", "0.001"))

    # 会话配置
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    MAX_ANSWERS_PER_DAY: int = int(os.getenv("MAX_ANSWERS_PER_DAY", "1000"))

    class Config:
        env_file = ".env"


class ConfigManager:
    """动态配置管理器 - 从数据库读取配置，支持实时更新"""

    # 可动态配置的键列表
    DYNAMIC_CONFIG_KEYS = [
        "api_enabled",
        "daily_api_limit",
        "cost_per_call",
        "session_timeout_hours",
        "max_answers_per_day",
        "deepseek_api_key",
        "deepseek_base_url",
        "deepseek_model"
    ]

    @staticmethod
    def _import_models():
        """延迟导入模型，避免循环导入"""
        import models
        return models

    @staticmethod
    def get_config(db: Session, key: str, default: Any = None) -> Any:
        """从数据库获取配置值，如果不存在则返回默认值"""
        if key not in ConfigManager.DYNAMIC_CONFIG_KEYS:
            return default

        models = ConfigManager._import_models()
        SystemConfig = models.SystemConfig
        
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            try:
                # 尝试解析JSON
                return json.loads(config.value)
            except:
                return config.value
        return default

    @staticmethod
    def set_config(db: Session, key: str, value: Any, description: str = "", admin_user: str = "admin") -> bool:
        """设置配置值（存入数据库）"""
        if key not in ConfigManager.DYNAMIC_CONFIG_KEYS:
            return False

        # 序列化值
        if isinstance(value, (dict, list, bool)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        models = ConfigManager._import_models()
        SystemConfig = models.SystemConfig
        AdminLog = models.AdminLog
        
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = value_str
            config.description = description
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                key=key,
                value=value_str,
                description=description
            )
            db.add(config)

        # 记录管理员操作
        log = AdminLog(
            admin_user=admin_user,
            action="config_update",
            details={"key": key, "value": value, "description": description}
        )
        db.add(log)
        db.commit()
        return True

    @staticmethod
    def get_all_configs(db: Session) -> dict:
        """获取所有动态配置"""
        configs = {}
        for key in ConfigManager.DYNAMIC_CONFIG_KEYS:
            configs[key] = ConfigManager.get_config(db, key)
        return configs

    @staticmethod
    def init_default_configs(db: Session):
        """初始化默认配置（如果不存在）"""
        models = ConfigManager._import_models()
        SystemConfig = models.SystemConfig
        
        defaults = {
            "api_enabled": True,
            "daily_api_limit": 10000,
            "cost_per_call": 0.001,
            "session_timeout_hours": 24,
            "max_answers_per_day": 1000,
            "deepseek_api_key": "",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat"
        }

        for key, value in defaults.items():
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config = SystemConfig(
                    key=key,
                    value=json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value),
                    description=f"Default value for {key}"
                )
                db.add(config)
        db.commit()


settings = Settings()
