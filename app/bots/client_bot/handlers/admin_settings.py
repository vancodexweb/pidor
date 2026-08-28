from zoneinfo import available_timezones

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.filters.is_owner import IsOwner
from app.bots.client_bot.keyboards.admin_kb import FIELD_LABELS, SETTINGS_BUTTON, settings_menu_kb
from app.bots.client_bot.states.settings_states import SettingsStates
from app.callbacks.factories import SettingsFieldCallback
from app.database.models.bot import Bot as BotModel
from app.services.settings_service import SettingsService


async def open_settings_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("⚙️ Настройки\n\nЧто хотите изменить?", reply_markup=settings_menu_kb())


async def pick_settings_field(callback: CallbackQuery, callback_data: SettingsFieldCallback, state: FSMContext) -> None:
    field = callback_data.field
    if not SettingsService.is_editable(field):
        await callback.answer("Недоступно", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_value)
    await state.update_data(field=field)

    label = FIELD_LABELS.get(field, field)
    if field == "welcome_sticker_file_id":
        prompt = f"Отправьте новый sticker для «{label}»."
    elif field == "welcome_image_file_id":
        prompt = f"Отправьте новое изображение для «{label}»."
    elif field == "timezone":
        prompt = "Отправьте часовой пояс в формате IANA, например: Europe/Moscow"
    else:
        prompt = f"Отправьте новый текст для «{label}»."

    await callback.message.answer(prompt)
    await callback.answer()


async def process_new_value(message: Message, state: FSMContext, child_bot: BotModel, session: AsyncSession) -> None:
    data = await state.get_data()
    field = data["field"]

    if field == "welcome_sticker_file_id":
        if not message.sticker:
            await message.answer("Пожалуйста, отправьте именно sticker.")
            return
        value = message.sticker.file_id
    elif field == "welcome_image_file_id":
        if not message.photo:
            await message.answer("Пожалуйста, отправьте изображение.")
            return
        value = message.photo[-1].file_id
    elif field == "timezone":
        value = (message.text or "").strip()
        if value not in available_timezones():
            await message.answer("❌ Неизвестный часовой пояс. Пример: Europe/Moscow")
            return
    else:
        value = (message.text or "").strip()
        if not value:
            await message.answer("Текст не может быть пустым.")
            return

    await SettingsService(session).update(child_bot.id, field, value)
    await state.clear()
    await message.answer("✅ Настройка сохранена.")


def register(router: Router) -> None:
    router.message.register(open_settings_menu, F.text == SETTINGS_BUTTON, IsOwner())
    router.callback_query.register(pick_settings_field, SettingsFieldCallback.filter(), IsOwner())
    router.message.register(process_new_value, SettingsStates.waiting_value, IsOwner())
