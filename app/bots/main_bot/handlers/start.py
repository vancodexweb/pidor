from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.main_bot.keyboards.keyboards import main_menu_kb
from app.database.repositories.user_repository import UserRepository

WELCOME_TEXT = (
    "👋 Добро пожаловать в конструктор Telegram-ботов!\n\n"
    "Здесь вы можете подключить своего бота (созданного через @BotFather) "
    "для приёма заявок и записи клиентов.\n\n"
    "Выберите действие в меню ниже 👇"
)


async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await UserRepository(session).get_or_create(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


def register(router: Router) -> None:
    router.message.register(cmd_start, CommandStart())
