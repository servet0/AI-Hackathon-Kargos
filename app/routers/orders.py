"""
Sipariş (Order) API endpoint'leri.

Tüm sipariş CRUD operasyonları bu router üzerinden sunulur.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.orders import OrderCRUD
from app.database import get_db
from app.models.order import ShippingStatus
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)

router = APIRouter(
    prefix="/orders",
    tags=["Siparişler"],
    responses={404: {"description": "Sipariş bulunamadı"}},
)


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Siparişleri listele",
    description="Tüm siparişleri sayfalama ve opsiyonel durum filtresi ile listeler.",
)
def list_orders(
    skip: int = Query(default=0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(
        default=50, ge=1, le=100, description="Sayfa başına kayıt sayısı"
    ),
    status: ShippingStatus | None = Query(
        default=None, description="Kargo durumu filtresi"
    ),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    """Siparişleri listele."""
    orders, total = OrderCRUD.get_orders(
        db, skip=skip, limit=limit, status=status
    )
    return OrderListResponse(total=total, orders=orders)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Sipariş detayı",
    description="Belirtilen ID'ye sahip siparişin detaylarını getirir.",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Tek bir siparişi getir."""
    db_order = OrderCRUD.get_order_by_id(db, order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {order_id} ile sipariş bulunamadı.",
        )
    return db_order


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni sipariş oluştur",
    description="Sisteme yeni bir sipariş kaydı ekler.",
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Yeni sipariş oluştur."""
    existing = OrderCRUD.get_order_by_number(db, order_data.order_number)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{order_data.order_number}' sipariş numarası zaten mevcut.",
        )
    return OrderCRUD.create_order(db, order_data)


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Siparişi güncelle",
    description="Mevcut bir siparişin bilgilerini kısmi olarak günceller.",
)
def update_order(
    order_id: int,
    update_data: OrderUpdate,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Siparişi güncelle (partial update)."""
    db_order = OrderCRUD.get_order_by_id(db, order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {order_id} ile sipariş bulunamadı.",
        )
    return OrderCRUD.update_order(db, db_order, update_data)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Siparişi sil",
    description="Belirtilen ID'ye sahip siparişi sistemden siler.",
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Siparişi sil."""
    db_order = OrderCRUD.get_order_by_id(db, order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {order_id} ile sipariş bulunamadı.",
        )
    OrderCRUD.delete_order(db, db_order)
