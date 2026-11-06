from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.submission_service import SubmissionService


@celery_app.task(name="judge_submission", bind=True, max_retries=2, default_retry_delay=3)
def judge_submission_task(self, submission_id: int) -> str:
    db = SessionLocal()
    try:
        service = SubmissionService(db)
        service.run_judge(submission_id)
        return f"judged:{submission_id}"
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
