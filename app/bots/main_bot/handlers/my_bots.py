from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.main_bot.keyboards.keyboards import MY_BOTS_BUTTON, bot_detail_kb, confirm_delete_bot_kb, my_bots_kb
from app.callbacks.factories import MyBotCallback
from app.core.security import decrypt_token
from app.database.repositories.bot_repository import BotRepository
from app.services.bot_manager import BotManager


async def show_my_bots(message: Message, session: AsyncSession) -> None:
    bots = await BotRepository(session).list_by_owner(message.from_user.id)
    if not bots:
        await message.answer('У вас пока нет подключённых ботов. Нажмите "➕ Создать бота", чтобы добавить первого.')
        return
    await message.answer("🤖 Ваши боты:", reply_markup=my_bots_kb(bots))


async def open_bot_detail(callback: CallbackQuery, callback_data: MyBotCallback, session: AsyncSession) -> None:
    bot = await BotRepository(session).get_by_id(callback_data.bot_id)
    if bot is None or bot.owner_id != callback.from_user.id:
        await callback.answer("Бот не найден", show_alert=True)
        return

    status = "🟢 активен" if bot.active else "🔴 остановлен"
    await callback.message.edit_text(f"🤖 @{bot.username}\n\nСтатус: {status}", reply_markup=bot_detail_kb(bot))
    await callback.answer()


async def back_to_list(callback: CallbackQuery, session: AsyncSession) -> None:
    bots = await BotRepository(session).list_by_owner(callback.from_user.id)
    if not bots:
        await callback.message.edit_text("У вас пока нет подключённых ботов.")
    else:
        await callback.message.edit_text("🤖 Ваши боты:", reply_markup=my_bots_kb(bots))
    await callback.answer()


async def toggle_bot(
    callback: CallbackQuery,
    callback_data: MyBotCallback,
    session: AsyncSession,
    bot_manager: BotManager,
    encryption_key: str,
) -> None:
    bot_repo = BotRepository(session)
    bot = await bot_repo.get_by_id(callback_data.bot_id)
    if bot is None or bot.owner_id != callback.from_user.id:
        await callback.answer("Бот не найден", show_alert=True)
        return

    if callback_data.action == "start":
        await bot_repo.set_active(bot.id, True)
        token = decrypt_token(bot.token_encrypted, encryption_key)
        await bot_manager.start_bot(bot.id, token)
    else:
        await bot_repo.set_active(bot.id, False)
        await bot_manager.stop_bot(bot.id)

    await session.refresh(bot)
    status = "🟢 активен" if bot.active else "🔴 остановлен"
    await callback.message.edit_text(f"🤖 @{bot.username}\n\nСтатус: {status}", reply_markup=bot_detail_kb(bot))
    await callback.answer()


async def request_delete_bot(callback: CallbackQuery, callback_data: MyBotCallback, session: AsyncSession) -> None:
    bot = await BotRepository(session).get_by_id(callback_data.bot_id)
    if bot is None or bot.owner_id != callback.from_user.id:
        await callback.answer("Бот не найден", show_alert=True)
        return
    await callback.message.edit_text(
        f"Отключить бота @{bot.username}?\n\nЗаписи и настройки сохранятся, но бот перестанет отвечать клиентам.",
        reply_markup=confirm_delete_bot_kb(bot.id),
    )
    await callback.answer()


async def confirm_delete_bot(
    callback: CallbackQuery, callback_data: MyBotCallback, session: AsyncSession, bot_manager: BotManager
) -> None:
    bot_repo = BotRepository(session)
    bot = await bot_repo.get_by_id(callback_data.bot_id)
    if bot is None or bot.owner_id != callback.from_user.id:
        await callback.answer("Бот не найден", show_alert=True)
        return

    await bot_manager.remove_bot(bot.id)
    await bot_repo.set_active(bot.id, False)

    await callback.message.edit_text(f"🗑 Бот @{bot.username} отключён.")
    await callback.answer()


def register(router: Router) -> None:
    router.message.register(show_my_bots, F.text == MY_BOTS_BUTTON)
    router.callback_query.register(open_bot_detail, MyBotCallback.filter(F.action == "open"))
    router.callback_query.register(back_to_list, MyBotCallback.filter(F.action == "back"))
    router.callback_query.register(toggle_bot, MyBotCallback.filter(F.action.in_({"start", "stop"})))
    router.callback_query.register(request_delete_bot, MyBotCallback.filter(F.action == "delete"))
    router.callback_query.register(confirm_delete_bot, MyBotCallback.filter(F.action == "delete_confirm"))
