"""
Sipariş (Order) Pydantic şemaları.

API request ve response modellerini tanımlar.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.order import ShippingStatus


class OrderCreate(BaseModel):
    """Yeni sipariş oluşturma şeması."""

    order_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Benzersiz sipariş numarası",
        examples=["SIP-2026-0001"],
    )
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Müşteri adı",
        examples=["Ahmet Yılmaz"],
    )
    product_info: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ürün bilgisi / açıklaması",
        examples=["iPhone 15 Pro Max - 256GB Siyah"],
    )
    shipping_status: ShippingStatus = Field(
        default=ShippingStatus.HAZIRLANIYOR,
        description="Kargo durumu",
    )
    tracking_number: str | None = Field(
        default=None,
        max_length=100,
        description="Kargo takip numarası",
        examples=["TR123456789"],
    )


class OrderUpdate(BaseModel):
    """
    Sipariş güncelleme şeması.

    Tüm alanlar opsiyoneldir (partial update).
    """

    customer_name: str | None = Field(default=None, max_length=150)
    product_info: str | None = Field(default=None, max_length=500)
    shipping_status: ShippingStatus | None = Field(default=None)
    tracking_number: str | None = Field(default=None, max_length=100)


class OrderResponse(BaseModel):
    """Sipariş response şeması."""

    id: int
    order_number: str
    customer_name: str
    product_info: str
    shipping_status: ShippingStatus
    tracking_number: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Sipariş listesi response şeması."""

    total: int = Field(description="Toplam sipariş sayısı")
    orders: list[OrderResponse]
