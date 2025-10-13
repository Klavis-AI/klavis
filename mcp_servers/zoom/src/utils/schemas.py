# src/utils/schemas.py
from pydantic import BaseModel, Field, constr, conint
from typing import Optional, Dict, Any, List

EmailOrId = constr(strip_whitespace=True, min_length=1)

class ListMeetingsInput(BaseModel):
    user_id_or_email: EmailOrId = Field(..., description="Zoom user email or userId")
    type: constr(strip_whitespace=True) = Field("upcoming", description='"upcoming" | "scheduled" | "past"')
    page_size: conint(ge=1, le=100) = 10

class MeetingItem(BaseModel):
    id: int
    topic: str
    start_time: Optional[str] = None
    join_url: Optional[str] = None

class ListMeetingsOutput(BaseModel):
    meetings: List[MeetingItem]
    next_page_token: Optional[str] = None

class CreateMeetingInput(BaseModel):
    user_id_or_email: EmailOrId
    topic: constr(strip_whitespace=True, min_length=1)
    start_time_iso: constr(strip_whitespace=True, min_length=10)  # ISO8601
    duration_minutes: conint(ge=1, le=1440) = 30
    timezone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class CreateMeetingOutput(BaseModel):
    meeting_id: int
    join_url: str
    start_url: str
    password: Optional[str] = None
