import enum
from datetime import date as date_, datetime
from datetime import time as time_

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"


class TimeSlot(Base):
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("bot_id", "date", "start_time", name="uq_slot_bot_date_time"),
        Index("ix_time_slots_bot_date", "bot_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    start_time: Mapped[time_] = mapped_column(Time, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        # values_callable: bind the enum's lowercase *values* ("available", ...)
        # instead of SQLAlchemy's default of the member *names* ("AVAILABLE", ...),
        # to match the Postgres enum labels created in the migration.
        Enum(SlotStatus, name="slot_status", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        default=SlotStatus.AVAILABLE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bot: Mapped["Bot"] = relationship(back_populates="time_slots")  # noqa: F821
    booking: Mapped["Booking"] = relationship(back_populates="slot", uselist=False)  # noqa: F821
