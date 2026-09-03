from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RowRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    provider: str
    event_time: datetime
    payload: str


class RowStaging(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    event_time: datetime
    amount: float
