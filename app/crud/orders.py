"""
Sipariş CRUD işlemleri.

Veritabanı sorguları ve veri manipülasyonu bu katmanda yapılır.
Router'lar doğrudan veritabanı ile iletişim kurmaz.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.order import Order, ShippingStatus
from app.schemas.order import OrderCreate, OrderUpdate


class OrderCRUD:
    """Sipariş CRUD operasyonları."""

    @staticmethod
    def get_orders(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: ShippingStatus | None = None,
    ) -> tuple[list[Order], int]:
        """
        Siparişleri listele.

        Args:
            db: Veritabanı oturumu.
            skip: Atlanacak kayıt sayısı (pagination).
            limit: Maksimum döndürülecek kayıt sayısı.
            status: Opsiyonel kargo durumu filtresi.

        Returns:
            Sipariş listesi ve toplam sayı tuple'ı.
        """
        query = select(Order)
        count_query = select(func.count(Order.id))

        if status is not None:
            query = query.where(Order.shipping_status == status)
            count_query = count_query.where(Order.shipping_status == status)

        total = db.execute(count_query).scalar() or 0

        orders = (
            db.execute(
                query.order_by(Order.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(orders), total

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Order | None:
        """
        ID ile sipariş getir.

        Args:
            db: Veritabanı oturumu.
            order_id: Sipariş ID'si.

        Returns:
            Bulunan sipariş veya None.
        """
        return db.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Order | None:
        """
        Sipariş numarası ile sipariş getir.

        Args:
            db: Veritabanı oturumu.
            order_number: Sipariş numarası.

        Returns:
            Bulunan sipariş veya None.
        """
        return db.execute(
            select(Order).where(Order.order_number == order_number)
        ).scalar_one_or_none()

    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        """
        Yeni sipariş oluştur.

        Args:
            db: Veritabanı oturumu.
            order_data: Sipariş oluşturma verileri.

        Returns:
            Oluşturulan sipariş.
        """
        db_order = Order(**order_data.model_dump())
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def update_order(
        db: Session,
        db_order: Order,
        update_data: OrderUpdate,
    ) -> Order:
        """
        Mevcut siparişi güncelle (partial update).

        Args:
            db: Veritabanı oturumu.
            db_order: Güncellenecek sipariş ORM nesnesi.
            update_data: Güncelleme verileri.

        Returns:
            Güncellenen sipariş.
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_order, field, value)

        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def delete_order(db: Session, db_order: Order) -> None:
        """
        Siparişi sil.

        Args:
            db: Veritabanı oturumu.
            db_order: Silinecek sipariş ORM nesnesi.
        """
        db.delete(db_order)
        db.commit()
