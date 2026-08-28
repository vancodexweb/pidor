import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.booking import Booking, BookingStatus
from app.database.models.time_slot import SlotStatus
from app.database.repositories.booking_repository import BookingRepository
from app.database.repositories.time_slot_repository import TimeSlotRepository

logger = logging.getLogger(__name__)


class SlotUnavailableError(Exception):
    """Raised when the requested slot is no longer available for booking."""


class BookingService:
    """Owns the transactional logic that prevents double-booking a slot."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.slots = TimeSlotRepository(session)
        self.bookings = BookingRepository(session)

    async def create_booking(
        self,
        bot_id: int,
        slot_id: int,
        client_telegram_id: int,
        client_name: str,
        phone: str,
    ) -> Booking:
        """Atomically book a slot.

        Locks the slot row with SELECT ... FOR UPDATE so two concurrent
        requests for the same slot can never both succeed. A partial unique
        index on bookings(slot_id) WHERE status='confirmed' backstops this
        at the database level in case of any other race.

        Note: relies on the session's implicit "autobegin" transaction
        rather than an explicit `session.begin()`, because this session is
        shared for the whole update (BotContextMiddleware already ran a
        query on it before the handler ever reaches this service).

        The insert itself runs inside a SAVEPOINT (begin_nested), not a
        plain commit/rollback. A bare session.rollback() would expire every
        object in the session's identity map — including `child_bot` and
        `bot_settings`, which BotContextMiddleware already loaded on this
        same session before the handler ran. The caller's except-branch
        reads bot_settings.timezone synchronously right after catching
        SlotUnavailableError; if that object were expired, the lazy-reload
        would need an await it doesn't have, raising MissingGreenlet instead
        of the intended "please pick another time" message.
        """
        slot = await self.slots.get_by_id_for_update(slot_id)
        if slot is None or slot.bot_id != bot_id or slot.status != SlotStatus.AVAILABLE:
            raise SlotUnavailableError("Slot is not available")

        slot.status = SlotStatus.BOOKED
        booking = Booking(
            bot_id=bot_id,
            slot_id=slot_id,
            client_telegram_id=client_telegram_id,
            client_name=client_name,
            phone=phone,
            status=BookingStatus.CONFIRMED,
        )

        try:
            async with self.session.begin_nested():
                self.session.add(booking)
                await self.session.flush()
        except IntegrityError as exc:
            logger.warning("Race detected while booking slot_id=%s: %s", slot_id, exc)
            raise SlotUnavailableError("Slot was just booked by someone else") from exc

        await self.session.commit()
        return booking

    async def cancel_booking(self, booking_id: int, bot_id: int) -> Booking | None:
        booking = await self.bookings.get_by_id(booking_id)
        if booking is None or booking.bot_id != bot_id or booking.status != BookingStatus.CONFIRMED:
            return None

        booking.status = BookingStatus.CANCELLED
        slot = await self.slots.get_by_id_for_update(booking.slot_id)
        if slot is not None:
            slot.status = SlotStatus.AVAILABLE

        await self.session.commit()
        await self.session.refresh(booking)
        return booking
