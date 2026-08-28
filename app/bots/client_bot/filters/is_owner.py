from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.database.models.bot import Bot


class IsOwner(BaseFilter):
    """Server-side check that the current Telegram user owns this child bot.

    Never trust callback_data alone for admin actions — always re-verify
    against the bot's owner_id loaded from the database for this update.
    """

    async def __call__(self, event: TelegramObject, child_bot: Bot) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id == child_bot.owner_id
