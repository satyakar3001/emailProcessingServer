from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class EmailBase(BaseModel):
    sender: str
    recipient: str
    subject: str
    content: str
    received_date: datetime

class EmailCreate(EmailBase):
    email_id: str

class EmailResponse(EmailBase):
    id: int
    email_id: str
    is_problem: bool
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailClassification(BaseModel):
    email_id: str
    is_problem: bool
    category: Optional[str] = None
    confidence_score: Optional[float] = None

class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    database: str
    scheduler: str
