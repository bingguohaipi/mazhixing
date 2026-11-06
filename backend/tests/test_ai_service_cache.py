"""AI 解析：空缓存不视为已完成."""

from unittest.mock import patch

from app.models.submission import Submission, SubmissionStatus
from app.services.ai_analysis_format import pack_ai_analysis
from app.services.ai_service import AiService


def test_analyze_regenerates_when_cached_text_empty(db, teacher, problem) -> None:
    submission = Submission(
        user_id=teacher.id,
        problem_id=problem.id,
        code="print(1)",
        language="Python",
        status=SubmissionStatus.WA,
        ai_analysis=pack_ai_analysis("", []),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    service = AiService(db)

    with patch.object(
        service,
        "_call_ai",
        return_value=("## 分析\n第 1 行需修改", [1]),
    ):
        text, remaining, lines = service.analyze_submission(teacher.id, submission.id)

    assert "分析" in text
    assert lines == [1]
    assert remaining == 9
