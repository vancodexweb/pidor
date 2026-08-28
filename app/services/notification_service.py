import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.database.models.booking import Booking
from app.database.models.time_slot import TimeSlot
from app.utils.datetime_utils import format_date_ru, format_time

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends notifications through the same child Bot instance that received the update."""

    @staticmethod
    async def notify_owner_new_booking(bot: Bot, owner_id: int, booking: Booking, slot: TimeSlot) -> None:
        text = (
            "🔔 Новая запись!\n\n"
            f"👤 Клиент: {booking.client_name}\n"
            f"📱 Телефон: {booking.phone}\n"
            f"📅 {format_date_ru(slot.date)}\n"
            f"🕐 {format_time(slot.start_time)}"
        )
        try:
            await bot.send_message(owner_id, text)
        except TelegramAPIError:
            logger.warning("Could not notify owner_id=%s about new booking", owner_id, exc_info=True)

    @staticmethod
    async def notify_owner_booking_cancelled(bot: Bot, owner_id: int, booking: Booking, slot: TimeSlot) -> None:
        text = (
            "❌ Запись отменена клиентом\n\n"
            f"👤 Клиент: {booking.client_name}\n"
            f"📅 {format_date_ru(slot.date)}\n"
            f"🕐 {format_time(slot.start_time)}"
        )
        try:
            await bot.send_message(owner_id, text)
        except TelegramAPIError:
            logger.warning("Could not notify owner_id=%s about cancellation", owner_id, exc_info=True)
