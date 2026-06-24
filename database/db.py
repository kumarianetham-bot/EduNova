from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set!")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Required for Supabase connection pooler
if "pooler.supabase.com" in DATABASE_URL and "pgbouncer" not in DATABASE_URL:
    DATABASE_URL += "?pgbouncer=true"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # detect dropped connections
    pool_recycle=300,          # recycle connections every 5 mins
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()