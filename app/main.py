"""
Kargos - KOBİ Lojistik ve Sipariş Otomasyon Platformu.

FastAPI uygulama giriş noktası.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

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

# Şablonlar ve statik dosyalar
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

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


@app.get("/", response_class=HTMLResponse, tags=["Sistem"])
def root(request: Request):
    """Chatbot arayüzünü (Frontend) render et."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", tags=["Sistem"])
def health_check() -> dict:
    """Detaylı sağlık kontrolü."""
    return {"status": "healthy", "database": "connected"}
