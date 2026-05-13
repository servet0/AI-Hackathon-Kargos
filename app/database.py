"""
Veritabanı bağlantı ve oturum yönetimi.

SQLite kullanarak yerel bir veritabanı dosyası oluşturur.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./kargos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tüm ORM modelleri için temel sınıf."""

    pass


def get_db():
    """
    Veritabanı oturumu dependency'si.

    Her istek için yeni bir oturum açar ve istek
    tamamlandığında otomatik olarak kapatır.

    Yields:
        Session: SQLAlchemy veritabanı oturumu.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
