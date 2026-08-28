import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Defense in depth against double-booking: even if two requests race
        # past the row-level lock somehow, Postgres itself rejects a second
        # CONFIRMED booking for the same slot.
        Index(
            "uq_booking_active_slot",
            "slot_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
        ),
        Index("ix_bookings_bot_id", "bot_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id", ondelete="CASCADE"), nullable=False)
    client_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        # values_callable: see the identical comment on TimeSlot.status.
        Enum(BookingStatus, name="booking_status", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        default=BookingStatus.CONFIRMED,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bot: Mapped["Bot"] = relationship(back_populates="bookings")  # noqa: F821
    slot: Mapped["TimeSlot"] = relationship(back_populates="booking")  # noqa: F821
