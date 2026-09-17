"""
operaciones en RDS
"""
from datetime import date
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from config import DB_ENDPOINT, DB_PORT, DB_NAME
from secrets_manager import get_db_credentials

engine: Optional[Engine] = None

def get_engine() -> Engine:
    global engine
    if engine is None:
        creds = get_db_credentials()
        url = (
            f"postgresql+psycopg2://{creds['username']}:{creds['password']}"
            f"@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"
        )
        engine = create_engine(url, pool_pre_ping=True)
    return engine

def create_event(client_name: str, event_type: str, event_date: date) -> str:
    query = text(
        """
        INSERT INTO events (client_name, event_type, event_date)
        VALUES (:client_name, :event_type, :event_date)
        RETURNING event_id
        """
    )
    with get_engine().begin() as conn:
        result = conn.execute(
            query,
            {"client_name": client_name, "event_type": event_type, "event_date": event_date},
        )
        event_id = result.scalar_one()
    return str(event_id)

def get_event(event_id: str) -> Optional[dict]:
    query = text(
        """
        SELECT event_id, client_name, event_type, event_date
        FROM events WHERE event_id = :event_id
        """
    )
    with get_engine().connect() as conn:
        row = conn.execute(query, {"event_id": event_id}).mappings().first()
    if row is None:
        return None
    return {
        "event_id": str(row["event_id"]),
        "client_name": row["client_name"],
        "event_type": row["event_type"],
        "event_date": row["event_date"].isoformat(),
    }

def add_photo(event_id: str, original_key: str, polaroid_key: str, message: str) -> str:
    query = text(
        """
        INSERT INTO photos (event_id, original_key, polaroid_key, message)
        VALUES (:event_id, :original_key, :polaroid_key, :message)
        RETURNING photo_id
        """
    )
    with get_engine().begin() as conn:
        result = conn.execute(
            query,
            {
                "event_id": event_id,
                "original_key": original_key,
                "polaroid_key": polaroid_key,
                "message": message,
            },
        )
        photo_id = result.scalar_one()
    return str(photo_id)

def get_photos(event_id: str) -> list[dict]:
    query = text(
        """
        SELECT photo_id, event_id, original_key, polaroid_key, message
        FROM photos WHERE event_id = :event_id
        """
    )
    with get_engine().connect() as conn:
        rows = conn.execute(query, {"event_id": event_id}).mappings().all()
    return [
        {
            "photo_id": str(r["photo_id"]),
            "event_id": str(r["event_id"]),
            "original_key": r["original_key"],
            "polaroid_key": r["polaroid_key"],
            "message": r["message"],
        }
        for r in rows
    ]

def count_photos(event_id: str) -> int:
    query = text("SELECT COUNT(*) FROM photos WHERE event_id = :event_id")
    with get_engine().connect() as conn:
        return conn.execute(query, {"event_id": event_id}).scalar_one()