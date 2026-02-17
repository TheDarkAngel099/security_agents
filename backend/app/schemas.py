from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class IncidentBase(BaseModel):
    original_text: str
    sender: str
    recipient: str

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None

class Incident(IncidentBase):
    id: int
    violation_type: Optional[str]
    violation_details: Optional[str]
    risk_level: str
    status: str
    owner_role: Optional[str]
    resolution_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ScanRequest(BaseModel):
    text: str
    sender: str
    recipient: str

class ScanResponse(BaseModel):
    violation_detected: bool
    violation_type: Optional[str]
    violation_details: Optional[str]
    nudge_message: Optional[str]
    suggested_rewrite: Optional[str]

class SubmitActionRequest(BaseModel):
    text: str
    action: str # "Edit" or "Override"
    sender: str
    recipient: str
    previous_violation_type: Optional[str]
    previous_violation_details: Optional[str]

class SubmitActionResponse(BaseModel):
    status: str
    incident_id: Optional[int]
