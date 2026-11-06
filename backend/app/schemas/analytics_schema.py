from datetime import datetime

from pydantic import BaseModel, Field
from typing import Literal

AnalyticsPeriod = Literal["week", "month", "semester", "all"]
SubmissionTrendRange = Literal["7d", "1m", "3m", "6m", "1y", "2y", "3y"]
TrendGranularity = Literal["day", "week", "month"]
TrendChartType = Literal["bar", "line"]


class TeacherDashboardOverview(BaseModel):
    class_count: int
    student_count: int
    problem_count: int
    active_homework_count: int
    week_submission_count: int
    week_pass_rate: float
    recent_homeworks: list["RecentHomeworkBrief"]


class RecentHomeworkBrief(BaseModel):
    id: int
    title: str
    class_names: list[str]
    end_time: datetime
    status: str
    completion_rate: float
    submitted_count: int
    total_students: int


class KnowledgePointStat(BaseModel):
    name: str
    mastery_rate: float
    attempted_count: int
    ac_count: int


class DailyTrendItem(BaseModel):
    date: str
    label: str
    count: int


class SubmissionTrendResponse(BaseModel):
    range: SubmissionTrendRange
    granularity: TrendGranularity
    chart_type: TrendChartType
    items: list[DailyTrendItem]


class TopWrongProblem(BaseModel):
    problem_id: int
    title: str
    knowledge_point: str | None
    wrong_count: int


class StudentSubmissionRow(BaseModel):
    student_id: int
    student_name: str
    homework_id: int | None
    homework_title: str | None
    problem_id: int
    problem_title: str
    status: str
    submitted_at: datetime
    is_late: bool


class StudentSubmissionStatItem(BaseModel):
    student_name: str
    submission_count: int
    ac_count: int
    accuracy_rate: float
    problems_attempted: int
    last_submitted_at: datetime | None = None


class AttentionStudent(BaseModel):
    student_id: int
    student_name: str
    recent_scores: str
    weak_knowledge_points: list[str]
    suggestion: str


class ClassAnalytics(BaseModel):
    class_id: int
    class_name: str
    period: AnalyticsPeriod
    completion_rate: float
    average_accuracy: float
    total_submissions: int
    late_submission_count: int
    student_count: int
    knowledge_points: list[KnowledgePointStat]
    daily_trend: list[DailyTrendItem]
    top_wrong_problems: list[TopWrongProblem]
    student_submissions: list[StudentSubmissionRow]
    late_submissions: list[StudentSubmissionRow]
    student_submission_stats: list[StudentSubmissionStatItem] = Field(default_factory=list)
    late_submission_stats: list[StudentSubmissionStatItem] = Field(default_factory=list)
    attention_students: list[AttentionStudent]


class AnalyticsExportQuery(BaseModel):
    class_id: int | None = None
    homework_id: int | None = None
    period: AnalyticsPeriod = "week"


class WrongSummaryStudentBrief(BaseModel):
    student_id: int
    student_name: str
    real_name: str | None = None
    wrong_count: int
    last_status: str
    last_error_at: datetime


class ClassWrongProblemDetail(BaseModel):
    problem_id: int
    title: str
    knowledge_point: str | None
    wrong_count: int
    affected_student_count: int
    students: list[WrongSummaryStudentBrief]


class ClassWrongSummary(BaseModel):
    class_id: int
    class_name: str
    period: AnalyticsPeriod
    total_wrong_submissions: int
    problem_count: int
    student_count: int
    problems: list[ClassWrongProblemDetail]


class ClassProblemWrongCodeItem(BaseModel):
    student_id: int
    student_name: str
    submission_id: int
    status: str
    language: str
    code: str
    submitted_at: datetime


class ClassProblemWrongCodesResponse(BaseModel):
    class_id: int
    problem_id: int
    problem_title: str
    items: list[ClassProblemWrongCodeItem]
