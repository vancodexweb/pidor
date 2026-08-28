from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.main_bot.keyboards.keyboards import SETTINGS_BUTTON
from app.database.repositories.bot_repository import BotRepository


async def show_settings(message: Message, session: AsyncSession) -> None:
    bots = await BotRepository(session).list_by_owner(message.from_user.id)
    text = (
        "⚙️ Настройки\n\n"
        f"Ваш Telegram ID: {message.from_user.id}\n"
        f"🤖 Подключено ботов: {len(bots)}\n\n"
        "Тексты, sticker, изображения и часовой пояс каждого бота настраиваются "
        "в его собственной админ-панели — откройте бота и нажмите «👩‍💼 Админ-панель»."
    )
    await message.answer(text)


def register(router: Router) -> None:
    router.message.register(show_settings, F.text == SETTINGS_BUTTON)
