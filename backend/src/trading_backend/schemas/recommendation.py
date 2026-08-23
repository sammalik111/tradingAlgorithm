import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from trading_backend.models.enums import ConvictionLevel, RecommendationDirection


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticker: str
    generated_at: datetime
    signal_score: float
    conviction: ConvictionLevel
    direction: RecommendationDirection
    rationale_text: str | None
    model_version: str
