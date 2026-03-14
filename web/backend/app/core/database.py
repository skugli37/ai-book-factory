from sqlalchemy import create_engine # pyre-ignore[21]
from sqlalchemy.ext.declarative import declarative_base # pyre-ignore[21]
from sqlalchemy.orm import sessionmaker # pyre-ignore[21]
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./web_factory.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
