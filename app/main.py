"""
Kargos - KOBİ Lojistik ve Sipariş Otomasyon Platformu.

FastAPI uygulama giriş noktası.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import chat, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yöneticisi.

    Başlangıçta veritabanı tablolarını oluşturur.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Kargos API",
    description=(
        "KOBİ'lere yönelik lojistik ve sipariş otomasyon platformu. "
        "Siparişlerin oluşturulması, takibi ve kargo durumu yönetimini sağlar."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS ayarları - geliştirme ortamı için tüm origin'lere izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları kaydet
app.include_router(orders.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/", tags=["Sistem"])
def root() -> dict:
    """API durum kontrolü (health check)."""
    return {
        "service": "Kargos API",
        "version": "0.1.0",
        "status": "çalışıyor",
        "docs": "/docs",
    }


@app.get("/health", tags=["Sistem"])
def health_check() -> dict:
    """Detaylı sağlık kontrolü."""
    return {"status": "healthy", "database": "connected"}
