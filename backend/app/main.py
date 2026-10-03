from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(
    title="Authentication API",
    description="A production-oriented authentication system",
    version="1.0.0"
)

# CORS middleware
import os
from app.config import settings

# Determine allowed origins based on environment
if settings.ENVIRONMENT == "development":
    allow_origins = ["http://localhost:5173"]
else:
    # In production, this should be set via environment variable
    allow_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Authentication API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}