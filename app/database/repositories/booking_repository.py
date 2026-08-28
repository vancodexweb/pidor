from datetime import date as date_

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.booking import Booking, BookingStatus
from app.database.models.time_slot import TimeSlot


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(Booking.id == booking_id).options(selectinload(Booking.slot))
        )
        return result.scalar_one_or_none()

    async def list_by_bot_and_date(self, bot_id: int, date: date_) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .join(TimeSlot, Booking.slot_id == TimeSlot.id)
            .where(
                Booking.bot_id == bot_id,
                TimeSlot.date == date,
                Booking.status == BookingStatus.CONFIRMED,
            )
            .options(selectinload(Booking.slot))
            .order_by(TimeSlot.start_time)
        )
        return list(result.scalars().all())

    async def list_upcoming_by_client(self, bot_id: int, client_telegram_id: int, from_date: date_) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .join(TimeSlot, Booking.slot_id == TimeSlot.id)
            .where(
                Booking.bot_id == bot_id,
                Booking.client_telegram_id == client_telegram_id,
                Booking.status == BookingStatus.CONFIRMED,
                TimeSlot.date >= from_date,
            )
            .options(selectinload(Booking.slot))
            .order_by(TimeSlot.date, TimeSlot.start_time)
        )
        return list(result.scalars().all())

    async def count_by_bot_and_status(self, bot_id: int, status: BookingStatus | None = None) -> int:
        query = select(Booking).where(Booking.bot_id == bot_id)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def cancel(self, booking_id: int) -> Booking | None:
        booking = await self.get_by_id(booking_id)
        if booking is None:
            return None
        booking.status = BookingStatus.CANCELLED
        await self.session.commit()
        return booking
