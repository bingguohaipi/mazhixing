from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mazhixing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,
    task_soft_time_limit=25,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    beat_schedule={
        "refresh-leaderboards-daily": {
            "task": "leaderboard.refresh_all",
            "schedule": crontab(hour=0, minute=0),
        },
        "purge-expired-logs-daily": {
            "task": "audit.purge_expired_logs",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

# 确保任务模块被注册
import app.tasks.judge_tasks  # noqa: E402, F401
import app.tasks.audit_tasks  # noqa: E402, F401
import app.tasks.leaderboard_tasks  # noqa: E402, F401
