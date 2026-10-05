from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, create_engine, make_url

from app.db.base import Base
from app.models.lead import Lead  # noqa: F401


def init_db(database_url: str) -> Engine:
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    if is_sqlite and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url, connect_args={"check_same_thread": False} if is_sqlite else {}
    )
    Base.metadata.create_all(bind=engine)
    return engine


def get_db(request: Request):
    with request.app.state.session_factory() as db:
        yield db
