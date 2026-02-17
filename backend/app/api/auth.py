from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter()

@router.post("/login")
def login(user_data: schemas.UserBase, db: Session = Depends(database.get_db)):
    # Simple login for demo: create user if not exists
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user:
        user = models.User(username=user_data.username, role=user_data.role)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # In a real app, return JWT token. Here, just return user info.
    return {"id": user.id, "username": user.username, "role": user.role}
