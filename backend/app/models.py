import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)  # 'user', 'hr', 'security', 'admin'

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    recipient = Column(String)
    original_text = Column(Text)
    violation_type = Column(String, nullable=True) # 'Toxicity', 'PII', 'Adversarial'
    violation_details = Column(Text, nullable=True)
    risk_level = Column(String, default="Low") # Low, Medium, High, Critical
    status = Column(String, default="Pending") # Pending, Resolved, Ignored
    owner_role = Column(String) # 'HR', 'Security'
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, nullable=True)
    agent = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
