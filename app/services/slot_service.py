from dataclasses import dataclass, field
from datetime import date as date_
from datetime import time as time_

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.time_slot import SlotStatus, TimeSlot
from app.database.repositories.time_slot_repository import SlotAlreadyExistsError, TimeSlotRepository


@dataclass
class BulkAddResult:
    created: list[TimeSlot] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)  # human-readable reasons


class SlotService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.slots = TimeSlotRepository(session)

    async def add_slots(self, bot_id: int, entries: list[tuple[date_, time_]]) -> BulkAddResult:
        result = BulkAddResult()
        for entry_date, entry_time in entries:
            try:
                slot = await self.slots.create(bot_id, entry_date, entry_time)
                result.created.append(slot)
            except SlotAlreadyExistsError:
                result.failed.append(f"{entry_date.strftime('%d.%m.%Y')} {entry_time.strftime('%H:%M')} — уже существует")
        return result

    async def list_for_date(self, bot_id: int, date: date_) -> list[TimeSlot]:
        return await self.slots.list_by_date(bot_id, date)

    async def list_available_for_date(self, bot_id: int, date: date_) -> list[TimeSlot]:
        return await self.slots.list_available_by_date(bot_id, date)

    async def list_available_dates(self, bot_id: int, from_date: date_) -> list[date_]:
        return await self.slots.list_available_dates(bot_id, from_date)

    async def delete_available_slot(self, bot_id: int, slot_id: int) -> bool:
        slot = await self.slots.get_by_id(slot_id)
        if slot is None or slot.bot_id != bot_id:
            return False
        if slot.status != SlotStatus.AVAILABLE:
            return False
        return await self.slots.delete(slot_id)
