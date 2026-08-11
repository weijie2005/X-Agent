"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from urllib.parse import quote_plus

settings = get_settings()

password = quote_plus(settings.PG_PASSWORD)
DATABASE_URL = f"postgresql+psycopg://{settings.PG_USER}:{password}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    数据库会话依赖
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()