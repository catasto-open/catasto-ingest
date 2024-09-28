from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EventTypeEnum(str, Enum):
    created = "created"
    modified = "modified"


class EventFile(BaseModel):
    event_type: EventTypeEnum | None = None
    date_time: datetime
    filename: str
