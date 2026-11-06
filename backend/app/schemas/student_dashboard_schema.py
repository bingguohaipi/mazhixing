from pydantic import BaseModel

from app.schemas.leaderboard_schema import LeaderboardEntry


class KnowledgeProgressItem(BaseModel):
    name: str
    mastery_rate: float
    status: str


class StudentDashboardOverview(BaseModel):
    completed_problems: int
    week_new_problems: int
    accuracy: float
    class_avg_accuracy: float
    wrong_pending_count: int
    class_rank: int | None
    class_student_count: int
    streak_days: int
    knowledge_progress: list[KnowledgeProgressItem]
    leaderboard_preview: list[LeaderboardEntry]
