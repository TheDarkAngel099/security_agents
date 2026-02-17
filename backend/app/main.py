from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api import auth, dashboard, workflow

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Security Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])

@app.get("/")
def read_root():
    return {"message": "Security Agent API is running"}
