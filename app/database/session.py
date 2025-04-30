from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import get_settings  

settings = get_settings()
DATABASE_URL = settings.database.service_url

# Fix potential dialect naming issue
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency generator for FastAPI
# Provides a database session to path operation functions and ensures cleanup

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

