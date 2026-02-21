import os
from sqlmodel import create_engine, SQLModel
from sqlalchemy.orm import sessionmaker

# Use persistent path on Fly.io, local path otherwise
if os.environ.get("FLY_APP_NAME"):
    sqlite_file_name = "/app/data/database.db"
else:
    sqlite_file_name = "database.db"

sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session
