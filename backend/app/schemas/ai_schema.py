from pydantic import BaseModel


class AiAnalysisResponse(BaseModel):
    content: str
    remaining_today: int
    highlight_lines: list[int] = []
