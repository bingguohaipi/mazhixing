"""启动期数据初始化（幂等）。

gunicorn 多 worker 会各自跑一遍 lifespan，若每个 worker 都做「查不到就插入」，
并发下必然撞唯一键（1062 Duplicate entry）导致 worker 启动失败。
因此在 scripts/start_gunicorn.sh 里 fork 之前单进程跑一次，worker 里只做兜底。
"""

import logging

from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def bootstrap_data() -> None:
    """按顺序执行各个幂等初始化；任一失败只记录，不阻断服务启动。"""
    db = SessionLocal()
    try:
        from app.services.audit_retention import purge_expired_logs
        from app.services.pet_catalog_defaults import ensure_shop_catalog
        from app.services.pet_points_service import PetPointsService
        from app.services.admin_service import AdminPublicProblemService
        from app.services.knowledge_point_service import KnowledgePointService

        purge_expired_logs(db)
        ensure_shop_catalog(db)
        PetPointsService(db)._ensure_config()
        AdminPublicProblemService(db).reconcile_public_catalog()
        KnowledgePointService(db).ensure_catalog()
    except IntegrityError:
        # 已被其它进程抢先写入，视为成功
        db.rollback()
        logger.warning("bootstrap_data: concurrent seed detected, skipped", exc_info=True)
    except Exception:
        db.rollback()
        logger.exception("bootstrap_data failed")
    finally:
        db.close()
