from aiogram import F, Router
from aiogram.types import Message

from app.bots.main_bot.keyboards.keyboards import HELP_BUTTON

HELP_TEXT = (
    "❓ Помощь\n\n"
    "Этот бот — конструктор Telegram-ботов для приёма заявок и записи клиентов.\n\n"
    "🤖 Мои боты — список ваших подключённых ботов и управление ими\n"
    "➕ Создать бота — подключить нового бота по токену от @BotFather\n"
    "📊 Статистика — сводная статистика по вашим ботам\n"
    "⚙️ Настройки — информация об аккаунте\n\n"
    "После подключения бота откройте его и настройте тексты, sticker, изображение, "
    "часовой пояс и свободное время через его собственную «👩‍💼 Админ-панель»."
)


async def show_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


def register(router: Router) -> None:
    router.message.register(show_help, F.text == HELP_BUTTON)
