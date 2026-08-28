from datetime import date as date_
from datetime import time as time_

from sqlalchemy import distinct, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.time_slot import SlotStatus, TimeSlot


class SlotAlreadyExistsError(Exception):
    pass


class TimeSlotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, slot_id: int) -> TimeSlot | None:
        result = await self.session.execute(select(TimeSlot).where(TimeSlot.id == slot_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, slot_id: int) -> TimeSlot | None:
        result = await self.session.execute(
            select(TimeSlot).where(TimeSlot.id == slot_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_by_date(self, bot_id: int, date: date_) -> list[TimeSlot]:
        result = await self.session.execute(
            select(TimeSlot)
            .where(TimeSlot.bot_id == bot_id, TimeSlot.date == date)
            .order_by(TimeSlot.start_time)
        )
        return list(result.scalars().all())

    async def list_available_by_date(self, bot_id: int, date: date_) -> list[TimeSlot]:
        result = await self.session.execute(
            select(TimeSlot)
            .where(
                TimeSlot.bot_id == bot_id,
                TimeSlot.date == date,
                TimeSlot.status == SlotStatus.AVAILABLE,
            )
            .order_by(TimeSlot.start_time)
        )
        return list(result.scalars().all())

    async def list_available_dates(self, bot_id: int, from_date: date_) -> list[date_]:
        result = await self.session.execute(
            select(distinct(TimeSlot.date))
            .where(
                TimeSlot.bot_id == bot_id,
                TimeSlot.status == SlotStatus.AVAILABLE,
                TimeSlot.date >= from_date,
            )
            .order_by(TimeSlot.date)
        )
        return list(result.scalars().all())

    async def create(self, bot_id: int, date: date_, start_time: time_) -> TimeSlot:
        """Create one slot.

        Uses a SAVEPOINT (begin_nested) rather than a plain commit/rollback
        so that a duplicate-slot failure only undoes this one insert. A bare
        session.rollback() would expire every object in the session's
        identity map — including slots already committed earlier in the same
        bulk-add batch (see SlotService.add_slots), which would then raise
        MissingGreenlet the next time their attributes are read outside an
        await (e.g. formatting the "added" list for the owner).
        """
        slot = TimeSlot(bot_id=bot_id, date=date, start_time=start_time, status=SlotStatus.AVAILABLE)
        try:
            async with self.session.begin_nested():
                self.session.add(slot)
                await self.session.flush()
        except IntegrityError as exc:
            raise SlotAlreadyExistsError(f"Slot {date} {start_time} already exists") from exc
        await self.session.commit()
        return slot

    async def set_status(self, slot_id: int, status: SlotStatus) -> None:
        slot = await self.get_by_id(slot_id)
        if slot is None:
            return
        slot.status = status
        await self.session.commit()

    async def delete(self, slot_id: int) -> bool:
        slot = await self.get_by_id(slot_id)
        if slot is None:
            return False
        await self.session.delete(slot)
        await self.session.commit()
        return True
