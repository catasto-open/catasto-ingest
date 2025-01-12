from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EventTypeEnum(str, Enum):
    """File event types enumeration."""

    created = "created"
    modified = "modified"


class EventFile(BaseModel):
    """
    Represents a file event with its metadata.
    """

    event_type: EventTypeEnum | None = None
    date_time: datetime
    filename: str

    def __str__(self) -> str:
        return f"{self.event_type.value}: {self.filename} at {self.date_time.strftime('%Y-%m-%d %H:%M:%S')}"
