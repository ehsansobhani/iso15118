from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    customer_ids: list[int] = Field(min_length=1)


class ScoreItem(BaseModel):
    customer_id: int
    uplift_score: float


class RankResponse(BaseModel):
    ranked: list[ScoreItem]


class HealthResponse(BaseModel):
    status: str
    model_name: str
