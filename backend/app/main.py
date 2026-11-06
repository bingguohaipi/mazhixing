from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.response import success
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.monitoring.health import check_database, check_redis
from app.monitoring.metrics import PrometheusMiddleware, metrics_response
from app.db.migrate import run_migrations
from app.middleware.origin_guard import OriginGuardMiddleware
from app.models import (  # noqa: F401
    ai_usage,
    arena,
    audit,
    class_model,
    event_log,
    homework,
    problem,
    submission,
    suggestion,
    suggestion_reply,
    user,
    verification_code,
    wrong_book,
    notice,
    leaderboard_snapshot,
    pet,
    knowledge_point,
)
from app.services.audit_retention import purge_expired_logs
from app.services.judge0_client import check_judge0_health
from app.scripts.seed import seed_demo_data


def _run_alembic_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.validate_production()
    settings.validate_judge_config()

    if settings.is_production:
        # Migrations run once in scripts/start_gunicorn.sh before gunicorn workers boot.
        pass
    else:
        Base.metadata.create_all(bind=engine)
        run_migrations()

    if settings.should_seed:
        # Avoid duplicate seed work across gunicorn workers in production.
        if not settings.is_production:
            seed_demo_data()

    db = SessionLocal()
    try:
        purge_expired_logs(db)
        from app.services.pet_catalog_defaults import ensure_shop_catalog
        from app.services.pet_points_service import PetPointsService

        ensure_shop_catalog(db)
        PetPointsService(db)._ensure_config()
        from app.services.admin_service import AdminPublicProblemService

        AdminPublicProblemService(db).reconcile_public_catalog()
        from app.services.knowledge_point_service import KnowledgePointService

        KnowledgePointService(db).ensure_catalog()
    finally:
        db.close()

    yield


def create_app() -> FastAPI:
    settings = get_settings()
    expose_docs = settings.should_expose_openapi

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if expose_docs else None,
        redoc_url="/redoc" if expose_docs else None,
        openapi_url="/openapi.json" if expose_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(OriginGuardMiddleware)
    if settings.metrics_enabled:
        app.add_middleware(PrometheusMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    uploads_path = Path(__file__).resolve().parent.parent / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount("/api/v1/media", StaticFiles(directory=str(uploads_path)), name="media")

    @app.get("/health")
    def health_check():
        judge_health = check_judge0_health()
        db = SessionLocal()
        try:
            db_health = check_database(db)
        finally:
            db.close()
        redis_health = check_redis()

        dependencies = {
            "database": {"ok": db_health.ok, "message": db_health.message},
            "redis": {"ok": redis_health.ok, "message": redis_health.message},
            "judge": {
                "ok": judge_health.reachable or not judge_health.enabled,
                "mode": judge_health.mode,
                "enabled": judge_health.enabled,
                "reachable": judge_health.reachable,
                "url": judge_health.url,
                "message": judge_health.message,
            },
        }
        all_ok = all(item["ok"] for item in dependencies.values())
        payload = {
            "status": "ok" if all_ok else "degraded",
            "debug": settings.debug,
            "dependencies": dependencies,
        }
        if all_ok:
            return success(payload)
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "service degraded", "data": payload},
        )

    if settings.metrics_enabled:

        @app.get("/metrics")
        def prometheus_metrics(authorization: str | None = Header(default=None)):
            if settings.metrics_token:
                expected = f"Bearer {settings.metrics_token}"
                if authorization != expected:
                    raise HTTPException(status_code=401, detail="Unauthorized")
            return metrics_response()

    return app


app = create_app()
