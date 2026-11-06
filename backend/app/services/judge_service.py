"""Local code judge for development; optional Judge0 when configured."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.models.submission import SubmissionStatus


@dataclass
class CaseJudgeResult:
    case_index: int
    status: SubmissionStatus
    actual_output: str | None = None
    runtime_ms: int | None = None


@dataclass
class JudgeResult:
    status: SubmissionStatus
    runtime_ms: int | None = None
    memory_kb: int | None = None
    error_message: str | None = None
    compile_output: str | None = None
    case_results: list[CaseJudgeResult] = field(default_factory=list)


def normalize_output(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines)


class JudgeService:
    MAX_TIMEOUT_SEC = 10

    def judge(
        self,
        code: str,
        language: str,
        test_cases: list[tuple[int, str, str, bool]],
        time_limit_ms: int,
        memory_limit_mb: int = 256,
    ) -> JudgeResult:
        settings = get_settings()
        if settings.judge0_url:
            result = self._judge_with_judge0(
                code, language, test_cases, time_limit_ms, memory_limit_mb, settings
            )
            unreachable = result.error_message == "判题服务不可用，请稍后重试"
            if not unreachable:
                return result
            if settings.judge0_required or not settings.judge0_allow_local_fallback:
                return result

        if settings.judge0_required:
            return JudgeResult(
                status=SubmissionStatus.RE,
                error_message="判题服务不可用，请稍后重试",
            )

        if language == "Python":
            return self._judge_python(code, test_cases, time_limit_ms)
        if language == "C++":
            return self._judge_cpp(code, test_cases, time_limit_ms)
        return JudgeResult(
            status=SubmissionStatus.RE,
            error_message=f"不支持的语言: {language}",
        )

    def _timeout_sec(self, time_limit_ms: int) -> float:
        return min(time_limit_ms / 1000.0, self.MAX_TIMEOUT_SEC)

    def _judge_python(
        self,
        code: str,
        test_cases: list[tuple[int, str, str, bool]],
        time_limit_ms: int,
    ) -> JudgeResult:
        python_bin = shutil.which("python3") or shutil.which("python")
        if not python_bin:
            return JudgeResult(status=SubmissionStatus.RE, error_message="服务器未安装 Python 运行环境")

        timeout_sec = self._timeout_sec(time_limit_ms)
        case_results: list[CaseJudgeResult] = []
        max_runtime = 0
        final_status = SubmissionStatus.AC

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "solution.py")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

            for case_index, input_data, expected_output, _is_sample in test_cases:
                start = time.perf_counter()
                try:
                    proc = subprocess.run(
                        [python_bin, source_path],
                        input=input_data,
                        capture_output=True,
                        text=True,
                        timeout=timeout_sec,
                        cwd=tmpdir,
                    )
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    max_runtime = max(max_runtime, elapsed_ms)

                    if proc.returncode != 0:
                        stderr = (proc.stderr or "").strip()
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.RE,
                                actual_output=stderr[:500] if stderr else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                        final_status = SubmissionStatus.RE
                        break

                    actual = normalize_output(proc.stdout or "")
                    expected = normalize_output(expected_output)
                    if actual == expected:
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.AC,
                                actual_output=actual if _is_sample else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                    else:
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.WA,
                                actual_output=actual if _is_sample else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                        final_status = SubmissionStatus.WA
                        break
                except subprocess.TimeoutExpired:
                    case_results.append(
                        CaseJudgeResult(case_index=case_index, status=SubmissionStatus.TLE)
                    )
                    final_status = SubmissionStatus.TLE
                    break
                except Exception as exc:  # noqa: BLE001
                    case_results.append(
                        CaseJudgeResult(
                            case_index=case_index,
                            status=SubmissionStatus.RE,
                            actual_output=str(exc)[:500],
                        )
                    )
                    final_status = SubmissionStatus.RE
                    break

        return JudgeResult(
            status=final_status,
            runtime_ms=max_runtime or None,
            memory_kb=None,
            case_results=case_results,
        )

    def _judge_cpp(
        self,
        code: str,
        test_cases: list[tuple[int, str, str, bool]],
        time_limit_ms: int,
    ) -> JudgeResult:
        gpp_bin = shutil.which("g++")
        if not gpp_bin:
            return JudgeResult(status=SubmissionStatus.RE, error_message="服务器未安装 C++ 编译环境")

        timeout_sec = self._timeout_sec(time_limit_ms)
        case_results: list[CaseJudgeResult] = []
        max_runtime = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "main.cpp")
            binary_path = os.path.join(tmpdir, "main")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

            compile_proc = subprocess.run(
                [gpp_bin, "-O2", "-std=c++17", source_path, "-o", binary_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if compile_proc.returncode != 0:
                return JudgeResult(
                    status=SubmissionStatus.CE,
                    compile_output=(compile_proc.stderr or compile_proc.stdout or "编译失败")[:2000],
                )

            final_status = SubmissionStatus.AC
            for case_index, input_data, expected_output, is_sample in test_cases:
                start = time.perf_counter()
                try:
                    proc = subprocess.run(
                        [binary_path],
                        input=input_data,
                        capture_output=True,
                        text=True,
                        timeout=timeout_sec,
                        cwd=tmpdir,
                    )
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    max_runtime = max(max_runtime, elapsed_ms)

                    if proc.returncode != 0:
                        stderr = (proc.stderr or "").strip()
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.RE,
                                actual_output=stderr[:500] if stderr else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                        final_status = SubmissionStatus.RE
                        break

                    actual = normalize_output(proc.stdout or "")
                    expected = normalize_output(expected_output)
                    if actual == expected:
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.AC,
                                actual_output=actual if is_sample else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                    else:
                        case_results.append(
                            CaseJudgeResult(
                                case_index=case_index,
                                status=SubmissionStatus.WA,
                                actual_output=actual if is_sample else None,
                                runtime_ms=elapsed_ms,
                            )
                        )
                        final_status = SubmissionStatus.WA
                        break
                except subprocess.TimeoutExpired:
                    case_results.append(
                        CaseJudgeResult(case_index=case_index, status=SubmissionStatus.TLE)
                    )
                    final_status = SubmissionStatus.TLE
                    break
                except Exception as exc:  # noqa: BLE001
                    case_results.append(
                        CaseJudgeResult(
                            case_index=case_index,
                            status=SubmissionStatus.RE,
                            actual_output=str(exc)[:500],
                        )
                    )
                    final_status = SubmissionStatus.RE
                    break

        return JudgeResult(
            status=final_status,
            runtime_ms=max_runtime or None,
            memory_kb=None,
            case_results=case_results,
        )

    def _judge_with_judge0(
        self,
        code: str,
        language: str,
        test_cases: list[tuple[int, str, str, bool]],
        time_limit_ms: int,
        memory_limit_mb: int,
        settings,
    ) -> JudgeResult:
        try:
            import httpx
        except ImportError:
            return JudgeResult(
                status=SubmissionStatus.RE,
                error_message="判题服务不可用，请稍后重试",
            )

        language_id = 71 if language == "Python" else 54
        case_results: list[CaseJudgeResult] = []
        max_runtime = 0
        max_memory_kb = 0
        final_status = SubmissionStatus.AC
        compile_output: str | None = None

        headers: dict[str, str] = {}
        if settings.judge0_auth_token:
            headers["X-Auth-Token"] = settings.judge0_auth_token

        with httpx.Client(
            base_url=settings.judge0_url.rstrip("/"),
            timeout=30.0,
            headers=headers,
        ) as client:
            for case_index, input_data, expected_output, is_sample in test_cases:
                response = client.post(
                    "/submissions?base64_encoded=false&wait=true",
                    json={
                        "source_code": code,
                        "language_id": language_id,
                        "stdin": input_data,
                        "expected_output": expected_output,
                        "cpu_time_limit": min(time_limit_ms / 1000.0, self.MAX_TIMEOUT_SEC),
                        "memory_limit": memory_limit_mb * 1024,
                    },
                )
                if response.status_code >= 400:
                    return JudgeResult(
                        status=SubmissionStatus.RE,
                        error_message="判题服务不可用，请稍后重试",
                    )

                data = response.json()
                status_id = data.get("status", {}).get("id", 0)
                stdout = data.get("stdout") or ""
                stderr = data.get("stderr") or ""
                compile_err = data.get("compile_output") or ""
                time_sec = data.get("time")
                memory_kb_raw = data.get("memory")
                elapsed_ms = int(float(time_sec) * 1000) if time_sec else None
                if elapsed_ms:
                    max_runtime = max(max_runtime, elapsed_ms)
                if memory_kb_raw is not None:
                    max_memory_kb = max(max_memory_kb, int(memory_kb_raw))

                if status_id == 6:
                    compile_output = compile_err[:2000]
                    return JudgeResult(status=SubmissionStatus.CE, compile_output=compile_output)

                if status_id == 5:
                    case_results.append(CaseJudgeResult(case_index=case_index, status=SubmissionStatus.TLE))
                    final_status = SubmissionStatus.TLE
                    break

                if status_id == 13:
                    internal_msg = (data.get("message") or "Judge0 内部错误")[:500]
                    return JudgeResult(
                        status=SubmissionStatus.RE,
                        error_message="判题沙箱异常，请稍后重试" if settings.judge0_required else internal_msg,
                    )

                if status_id in (11, 12):
                    case_results.append(
                        CaseJudgeResult(
                            case_index=case_index,
                            status=SubmissionStatus.RE,
                            actual_output=(stderr or stdout)[:500] if is_sample else None,
                            runtime_ms=elapsed_ms,
                        )
                    )
                    final_status = SubmissionStatus.RE
                    break

                actual = normalize_output(stdout)
                expected = normalize_output(expected_output)
                if actual == expected:
                    case_results.append(
                        CaseJudgeResult(
                            case_index=case_index,
                            status=SubmissionStatus.AC,
                            actual_output=actual if is_sample else None,
                            runtime_ms=elapsed_ms,
                        )
                    )
                else:
                    case_results.append(
                        CaseJudgeResult(
                            case_index=case_index,
                            status=SubmissionStatus.WA,
                            actual_output=actual if is_sample else None,
                            runtime_ms=elapsed_ms,
                        )
                    )
                    final_status = SubmissionStatus.WA
                    break

        return JudgeResult(
            status=final_status,
            runtime_ms=max_runtime or None,
            memory_kb=max_memory_kb or None,
            compile_output=compile_output,
            case_results=case_results,
        )
