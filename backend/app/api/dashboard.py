from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter()

@router.get("/incidents", response_model=List[schemas.Incident])
def get_incidents(role: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Incident)
    
    if role:
        # Filter by owner role (HR or Security)
        query = query.filter(models.Incident.owner_role == role)
        
    if status:
        query = query.filter(models.Incident.status == status)
        
    return query.all()

@router.get("/incidents/{incident_id}", response_model=schemas.Incident)
def get_incident(incident_id: int, db: Session = Depends(database.get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/incidents/{incident_id}", response_model=schemas.Incident)
def update_incident(incident_id: int, update_data: schemas.IncidentUpdate, db: Session = Depends(database.get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if update_data.status:
        incident.status = update_data.status
    if update_data.resolution_notes:
        incident.resolution_notes = update_data.resolution_notes
        
    db.commit()
    db.refresh(incident)
    return incident

@router.get("/stats")
def get_stats(db: Session = Depends(database.get_db)):
    total = db.query(models.Incident).count()
    hr_pending = db.query(models.Incident).filter(models.Incident.owner_role == "HR", models.Incident.status == "Pending").count()
    sec_pending = db.query(models.Incident).filter(models.Incident.owner_role == "Security", models.Incident.status == "Pending").count()
    resolved = db.query(models.Incident).filter(models.Incident.status == "Resolved").count()
    
    return {
        "total_incidents": total,
        "hr_pending": hr_pending,
        "security_pending": sec_pending,
        "resolved": resolved
    }

@router.get("/logs")
def get_logs(limit: int = 100, db: Session = Depends(database.get_db)):
    logs = db.query(models.Log).order_by(models.Log.timestamp.desc()).limit(limit).all()
    return logs
