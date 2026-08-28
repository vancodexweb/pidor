from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.keyboards.client_kb import persistent_menu_kb, start_booking_kb
from app.database.models.bot import Bot as BotModel
from app.database.models.bot_settings import BotSettings
from app.database.repositories.user_repository import UserRepository


async def cmd_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    child_bot: BotModel,
    bot_settings: BotSettings,
) -> None:
    await state.clear()
    await UserRepository(session).get_or_create(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )

    if bot_settings.welcome_sticker_file_id:
        await message.answer_sticker(bot_settings.welcome_sticker_file_id)
    if bot_settings.welcome_image_file_id:
        await message.answer_photo(bot_settings.welcome_image_file_id)

    await message.answer(bot_settings.welcome_text, reply_markup=start_booking_kb(bot_settings.start_button_text))

    is_owner = message.from_user.id == child_bot.owner_id
    await message.answer("Меню 👇", reply_markup=persistent_menu_kb(is_owner))


def register(router: Router) -> None:
    router.message.register(cmd_start, CommandStart())
