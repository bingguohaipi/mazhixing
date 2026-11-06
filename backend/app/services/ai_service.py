"""AI error analysis for WA/RE submissions."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.forbidden import raise_forbidden
from app.models.ai_usage import AiDailyUsage
from app.services.ai_analysis_format import pack_ai_analysis, parse_model_json, unpack_ai_analysis
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionCaseResult, SubmissionStatus
from app.models.user import User, UserRole


AI_ELIGIBLE_STATUSES = {SubmissionStatus.WA, SubmissionStatus.RE}


class AiService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def analyze_submission(self, user_id: int, submission_id: int) -> tuple[str, int, list[int]]:
        if not self.settings.ai_enabled:
            raise AppException(503, "解析暂时失败，请稍后刷新重试", status_code=503)

        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            raise AppException(404, "提交记录不存在")
        if submission.user_id != user_id:
            raise_forbidden(self.db, user_id, "ai_analysis", f"submission_id={submission_id}")

        if submission.status not in AI_ELIGIBLE_STATUSES:
            raise AppException(400, "仅 WA/RE 错误可触发 AI 解析")

        cached_text, cached_lines = unpack_ai_analysis(submission.ai_analysis)
        if cached_text.strip():
            remaining = self._remaining_today(user_id)
            return cached_text, remaining, cached_lines

        remaining = self._remaining_today(user_id)
        if remaining <= 0:
            raise AppException(429, "今日 AI 解析次数已达上限，请明日再来", status_code=429)

        # 防止并发重复调用 AI、重复扣次
        locked = (
            self.db.query(Submission)
            .filter(Submission.id == submission_id)
            .with_for_update()
            .first()
        )
        if locked is None:
            raise AppException(404, "提交记录不存在")
        submission = locked

        cached_text, cached_lines = unpack_ai_analysis(submission.ai_analysis)
        if cached_text.strip():
            return cached_text, self._remaining_today(user_id), cached_lines

        problem = self.db.get(Problem, submission.problem_id)
        if problem is None:
            raise AppException(404, "题目不存在")

        case_results = (
            self.db.query(SubmissionCaseResult)
            .filter(SubmissionCaseResult.submission_id == submission.id)
            .order_by(SubmissionCaseResult.case_index.asc())
            .all()
        )

        analysis_text, highlight_lines = self._call_ai(problem, submission, case_results)
        if not analysis_text.strip():
            raise AppException(503, "解析暂时失败，请稍后刷新重试", status_code=503)

        submission.ai_analysis = pack_ai_analysis(analysis_text, highlight_lines)
        self._increment_usage(user_id)
        self.db.commit()

        return analysis_text, self._remaining_today(user_id), highlight_lines

    def _daily_limit(self, user_id: int) -> int:
        user = self.db.get(User, user_id)
        if user is not None and user.role in (UserRole.TEACHER, UserRole.ADMIN):
            return self.settings.ai_teacher_daily_limit
        return self.settings.ai_daily_limit

    def _remaining_today(self, user_id: int) -> int:
        today = datetime.now(timezone.utc).date()
        usage = (
            self.db.query(AiDailyUsage)
            .filter(AiDailyUsage.user_id == user_id, AiDailyUsage.usage_date == today)
            .first()
        )
        used = usage.count if usage else 0
        return max(self._daily_limit(user_id) - used, 0)

    def _increment_usage(self, user_id: int) -> None:
        today = datetime.now(timezone.utc).date()
        usage = (
            self.db.query(AiDailyUsage)
            .filter(AiDailyUsage.user_id == user_id, AiDailyUsage.usage_date == today)
            .first()
        )
        if usage is None:
            self.db.add(AiDailyUsage(user_id=user_id, usage_date=today, count=1))
        else:
            usage.count += 1

    def _call_ai(
        self,
        problem: Problem,
        submission: Submission,
        case_results: list[SubmissionCaseResult],
    ) -> tuple[str, list[int]]:
        if self.settings.openai_api_key:
            try:
                raw = self._call_openai(problem, submission, case_results)
                return parse_model_json(raw)
            except Exception:  # noqa: BLE001
                fallback = self._fallback_analysis(problem, submission, case_results)
                if fallback:
                    text, lines = fallback
                    return text, lines
                raise AppException(503, "解析暂时失败，请稍后刷新重试", status_code=503) from None

        return self._fallback_analysis(problem, submission, case_results)

    def _call_openai(
        self,
        problem: Problem,
        submission: Submission,
        case_results: list[SubmissionCaseResult],
    ) -> str:
        case_summary = []
        for case in case_results:
            if case.actual_output:
                case_summary.append(
                    f"用例{case.case_index + 1}: {case.status.value}, 输出={case.actual_output}"
                )
            else:
                case_summary.append(f"用例{case.case_index + 1}: {case.status.value}")

        numbered_code = "\n".join(
            f"{index + 1:4d}| {line}" for index, line in enumerate(submission.code.splitlines())
        )
        prompt = f"""你是一位少儿编程老师，请用简洁易懂的中文帮学生分析代码错误。

题目：{problem.title}
描述：{problem.description}
语言：{submission.language}
判题结果：{submission.status.value}
{"编译信息：" + submission.compile_output if submission.compile_output else ""}
{"运行错误：" + submission.error_message if submission.error_message else ""}
测试用例：{"; ".join(case_summary) if case_summary else "无"}

学生代码（左侧为行号，仅供分析）：
```
{numbered_code}
```

请仅输出 JSON（不要 markdown 代码块），格式：
{{
  "highlight_lines": [行号整数, ...],
  "analysis": "Markdown 正文：1)错误原因 2)修改建议 3)思路提示（不要给出完整可提交答案）"
}}

要求：
- highlight_lines 必须指向最可能出错的 1~5 行（行号与上面代码行号一致）
- analysis 中请用「第 N 行」明确引用问题位置"""

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": "你是码智星 OJ 平台的编程辅导老师，面向少儿信奥学员。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        }

        with httpx.Client(
            base_url=self.settings.openai_base_url.rstrip("/"),
            timeout=self.settings.ai_timeout_seconds,
        ) as client:
            response = client.post("/chat/completions", json=payload, headers=headers)
            if response.status_code >= 400:
                raise AppException(503, "解析暂时失败，请稍后刷新重试", status_code=503)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()

    def _fallback_analysis(
        self,
        problem: Problem,
        submission: Submission,
        case_results: list[SubmissionCaseResult],
    ) -> tuple[str, list[int]]:
        highlight_lines: list[int] = []
        lines = ["## 错误分析（系统提示）", ""]

        if submission.status == SubmissionStatus.WA:
            lines.append("**错误类型**：答案错误 (WA)")
            lines.append("")
            lines.append("你的程序已成功运行，但输出结果与预期不符。请检查：")
            lines.append("- 输出格式是否正确（空格、换行、大小写）")
            lines.append("- 边界条件是否考虑周全")
            lines.append("- 算法逻辑是否存在遗漏")
            failed = next((c for c in case_results if c.status == SubmissionStatus.WA), None)
            if failed and failed.actual_output:
                lines.append(f"- 样例实际输出：`{failed.actual_output}`")
        elif submission.status == SubmissionStatus.RE:
            lines.append("**错误类型**：运行异常 (RE)")
            lines.append("")
            lines.append("程序在运行过程中发生了异常，常见原因：")
            lines.append("- 数组越界或访问了未初始化的变量")
            lines.append("- 除以零")
            lines.append("- 输入输出方式不正确")
            if submission.error_message:
                lines.append(f"- 错误信息：`{submission.error_message[:200]}`")

        if problem.hint:
            lines.extend(["", f"**题目提示**：{problem.hint}"])

        lines.extend(["", "*配置 OPENAI_API_KEY 后可获得更详细的 AI 解析*"])
        markdown = "\n".join(lines)
        if submission.error_message:
            for match in re.finditer(r"line\s*(\d+)", submission.error_message, re.I):
                highlight_lines.append(int(match.group(1)))
        return markdown, sorted(set(highlight_lines))
