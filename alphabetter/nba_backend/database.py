from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
#TODO REMOVE
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:BigStink44@localhost/nba_stats"
)
# DATABASE_URL = "postgresql://alphabettor_user:eMuCfB0r0sw5Rr3aeQxnyXWz2kqrR2Oy@dpg-cvhobs2qgecs73d2s4d0-a.oregon-postgres.render.com/alphabettor"
#DATABASE_URL = "postgresql://postgres:BigStink44@localhost/nba_stats"
# Connect to PostgreSQL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
