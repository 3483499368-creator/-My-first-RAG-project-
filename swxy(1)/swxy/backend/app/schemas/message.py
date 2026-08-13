from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# 同时兼容 Pydantic v1 和 v2
try:
    from pydantic import ConfigDict
    _PYDANTIC_V2 = True
except ImportError:
    _PYDANTIC_V2 = False


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    user_question: str
    model_answer: str
    created_at: datetime
    documents: Optional[list] = None
    recommended_questions: Optional[list] = None
    think: Optional[str] = None

    if _PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class FilestResponse(BaseModel):
    user_id: str
    file_name: str
    created_at: str
    updated_at: str
    number: int = 0
    method: str = "General"
    status: str = "success"


class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    user_id: str
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    user_id: str
    sessions: List[SessionResponse]
