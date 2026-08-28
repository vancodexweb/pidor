import re

from aiogram import Bot as AiogramBot
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.main_bot.keyboards.keyboards import CREATE_BOT_BUTTON, main_menu_kb
from app.bots.main_bot.states.connect_bot import ConnectBotStates
from app.core.security import encrypt_token
from app.database.repositories.bot_repository import BotRepository
from app.database.repositories.bot_settings_repository import BotSettingsRepository
from app.database.repositories.user_repository import UserRepository
from app.services.bot_manager import BotManager

# BotFather tokens look like "123456789:AAExampleHash...", but the exact hash
# length isn't a stable contract, so this is a loose sanity check only — the
# real validation is the getMe() call against the Telegram API below.
TOKEN_RE = re.compile(r"^\d{6,12}:[A-Za-z0-9_-]{30,50}$")

INSTRUCTIONS = (
    "🤖 Создание нового бота\n\n"
    "1. Откройте @BotFather\n"
    "2. Создайте Telegram-бота\n"
    "3. Скопируйте BOT TOKEN\n"
    "4. Отправьте токен сюда"
)

INVALID_TOKEN_TEXT = "❌ Неверный BOT TOKEN.\n\nПроверьте токен и попробуйте снова."


async def start_create_bot(message: Message, state: FSMContext) -> None:
    await state.set_state(ConnectBotStates.waiting_for_token)
    await message.answer(INSTRUCTIONS)


async def process_token(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot_manager: BotManager,
    encryption_key: str,
) -> None:
    raw_token = (message.text or "").strip()

    try:
        await message.delete()
    except TelegramAPIError:
        pass  # best-effort: the token must never linger visibly in chat history

    if not TOKEN_RE.match(raw_token):
        await message.answer(INVALID_TOKEN_TEXT)
        return

    temp_bot = AiogramBot(token=raw_token)
    try:
        bot_user = await temp_bot.get_me()
    except TelegramUnauthorizedError:
        await message.answer(INVALID_TOKEN_TEXT)
        return
    except TelegramAPIError:
        await message.answer("❌ Не удалось проверить токен. Попробуйте ещё раз чуть позже.")
        return
    finally:
        await temp_bot.session.close()

    bot_repo = BotRepository(session)
    existing = await bot_repo.get_by_telegram_bot_id(bot_user.id)
    if existing is not None and existing.owner_id != message.from_user.id:
        await message.answer("❌ Этот бот уже подключён другим пользователем.")
        return

    await UserRepository(session).get_or_create(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    token_encrypted = encrypt_token(raw_token, encryption_key)

    if existing is not None:
        await bot_repo.update_token(existing.id, token_encrypted)
        await bot_repo.set_active(existing.id, True)
        bot_row = existing
    else:
        bot_row = await bot_repo.create(
            owner_id=message.from_user.id,
            telegram_bot_id=bot_user.id,
            username=bot_user.username,
            first_name=bot_user.first_name or bot_user.username,
            token_encrypted=token_encrypted,
        )
        await BotSettingsRepository(session).create_default(bot_row.id)

    await state.clear()
    await bot_manager.start_bot(bot_row.id, raw_token)

    await message.answer(
        f"✅ Бот @{bot_user.username} подключён и уже работает!\n\n"
        "Откройте его и настройте через собственную «👩‍💼 Админ-панель».",
        reply_markup=main_menu_kb(),
    )


def register(router: Router) -> None:
    router.message.register(start_create_bot, F.text == CREATE_BOT_BUTTON)
    router.message.register(process_token, ConnectBotStates.waiting_for_token, F.text)
