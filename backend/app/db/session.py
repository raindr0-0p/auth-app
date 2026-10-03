from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.base import Base

# Create engine
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,  # Enable connection health checks
    echo=settings.ENVIRONMENT == "development",  # Log SQL in dev
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()