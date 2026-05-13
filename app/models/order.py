"""
Sipariş (Order) ORM modeli.

Veritabanındaki 'orders' tablosunu temsil eder.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ShippingStatus(str, enum.Enum):
    """Kargo durumu seçenekleri."""

    HAZIRLANIYOR = "Hazırlanıyor"
    KARGOYA_VERILDI = "Kargoya Verildi"
    GECIKMEDE = "Gecikmede"


class Order(Base):
    """
    Sipariş modeli.

    Attributes:
        id: Birincil anahtar.
        order_number: Benzersiz sipariş numarası.
        customer_name: Müşteri adı.
        product_info: Ürün bilgisi / açıklaması.
        shipping_status: Kargo durumu (Hazırlanıyor, Kargoya Verildi, Gecikmede).
        tracking_number: Kargo takip numarası (opsiyonel).
        created_at: Oluşturulma tarihi.
        updated_at: Son güncellenme tarihi.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_info: Mapped[str] = mapped_column(String(500), nullable=False)
    shipping_status: Mapped[ShippingStatus] = mapped_column(
        Enum(ShippingStatus),
        nullable=False,
        default=ShippingStatus.HAZIRLANIYOR,
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, order_number='{self.order_number}', "
            f"status='{self.shipping_status.value}')>"
        )
