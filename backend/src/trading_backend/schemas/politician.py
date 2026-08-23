import uuid

from pydantic import BaseModel, ConfigDict

from trading_backend.models.enums import Chamber


class PoliticianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    chamber: Chamber
    party: str | None
    state: str | None
    is_active: bool
