from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL, ensure_dirs

ensure_dirs()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 轻量迁移：create_all 不会给已有表加列，这里补齐新增字段
_QSO_NEW_COLUMNS = {
    "their_equipment": "VARCHAR(200) NOT NULL DEFAULT ''",
    "their_antenna": "VARCHAR(200) NOT NULL DEFAULT ''",
    "their_power": "VARCHAR(50) NOT NULL DEFAULT ''",
}


def run_migrations() -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        existing = {
            row[1] for row in conn.execute(text("PRAGMA table_info(qsos)")).fetchall()
        }
        for name, ddl in _QSO_NEW_COLUMNS.items():
            if existing and name not in existing:
                conn.execute(text(f"ALTER TABLE qsos ADD COLUMN {name} {ddl}"))
