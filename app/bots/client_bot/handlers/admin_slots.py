from datetime import date as date_
from datetime import time as time_

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.client_bot.filters.is_owner import IsOwner
from app.bots.client_bot.keyboards.admin_kb import (
    ADD_SLOT_BUTTON,
    DELETE_SLOT_BUTTON,
    VIEW_SLOTS_BUTTON,
    confirm_delete_slot_kb,
    deletable_slots_kb,
    slots_status_text,
)
from app.bots.client_bot.keyboards.calendar_kb import build_calendar
from app.bots.client_bot.states.add_slot_states import AddSlotStates
from app.callbacks.factories import CalendarDayCallback, CalendarNavCallback, SlotCallback
from app.database.models.bot import Bot as BotModel
from app.database.models.bot_settings import BotSettings
from app.database.models.time_slot import SlotStatus
from app.services.slot_service import SlotService
from app.utils.datetime_utils import format_date_ru_full, parse_date_time_line, parse_time_line, today_in_timezone

SLOT_PURPOSES = {"add_slot", "view_slots", "delete_slot"}

TIMES_PROMPT = (
    "📅 Вы выбрали {date}.\n\n"
    "Отправьте свободные времена, например:\n\n"
    "10:00\n11:30\n13:00\n15:30\n17:00\n\n"
    "Также можно указать дату прямо в строке, если хотите добавить время "
    "на другой день в этом же сообщении:\n29.08.2026 15:30"
)


async def open_add_slot_calendar(message: Message, state: FSMContext, bot_settings: BotSettings) -> None:
    await state.clear()
    today = today_in_timezone(bot_settings.timezone)
    await message.answer(
        "➕ Добавление времени\n\nВыберите дату:",
        reply_markup=build_calendar("add_slot", today.year, today.month, today),
    )


async def open_view_slots_calendar(message: Message, state: FSMContext, bot_settings: BotSettings) -> None:
    await state.clear()
    today = today_in_timezone(bot_settings.timezone)
    await message.answer(
        "📅 Свободные окна\n\nВыберите дату:",
        reply_markup=build_calendar("view_slots", today.year, today.month, today),
    )


async def open_delete_slot_calendar(message: Message, state: FSMContext, bot_settings: BotSettings) -> None:
    await state.clear()
    today = today_in_timezone(bot_settings.timezone)
    await message.answer(
        "❌ Удаление времени\n\nВыберите дату:",
        reply_markup=build_calendar("delete_slot", today.year, today.month, today),
    )


async def navigate_calendar(callback: CallbackQuery, callback_data: CalendarNavCallback, bot_settings: BotSettings) -> None:
    today = today_in_timezone(bot_settings.timezone)
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(callback_data.purpose, callback_data.year, callback_data.month, today)
    )
    await callback.answer()


async def pick_day(callback: CallbackQuery, callback_data: CalendarDayCallback, state: FSMContext, child_bot: BotModel, session: AsyncSession) -> None:
    picked_date = date_.fromisoformat(callback_data.date)

    if callback_data.purpose == "add_slot":
        await state.set_state(AddSlotStates.waiting_times)
        await state.update_data(add_slot_date=picked_date.isoformat())
        await callback.message.answer(TIMES_PROMPT.format(date=format_date_ru_full(picked_date)))
        await callback.answer()
        return

    slots = await SlotService(session).list_for_date(child_bot.id, picked_date)

    if callback_data.purpose == "view_slots":
        await callback.message.answer(slots_status_text(format_date_ru_full(picked_date), slots))
        await callback.answer()
        return

    if callback_data.purpose == "delete_slot":
        available = [s for s in slots if s.status == SlotStatus.AVAILABLE]
        if not available:
            await callback.message.answer(f"📅 {format_date_ru_full(picked_date)}\n\nНет свободных окон для удаления.")
        else:
            await callback.message.answer(
                f"📅 {format_date_ru_full(picked_date)}\n\nВыберите время для удаления:",
                reply_markup=deletable_slots_kb(available),
            )
        await callback.answer()


async def process_times_input(message: Message, state: FSMContext, child_bot: BotModel, session: AsyncSession) -> None:
    data = await state.get_data()
    default_date = date_.fromisoformat(data["add_slot_date"])

    entries: list[tuple[date_, time_]] = []
    invalid_lines: list[str] = []

    for raw_line in (message.text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        full = parse_date_time_line(line)
        if full is not None:
            entries.append(full)
            continue

        bare_time = parse_time_line(line)
        if bare_time is not None:
            entries.append((default_date, bare_time))
            continue

        invalid_lines.append(line)

    if not entries and not invalid_lines:
        await message.answer("Не удалось распознать ни одной строки. Пришлите время в формате 10:00 или 29.08.2026 15:30.")
        return

    result = await SlotService(session).add_slots(child_bot.id, entries)

    lines = []
    if result.created:
        lines.append("✅ Добавлено:")
        lines.extend(f"{s.date.strftime('%d.%m.%Y')} {s.start_time.strftime('%H:%M')}" for s in result.created)
    if result.failed:
        lines.append("\n⚠️ Не удалось добавить:")
        lines.extend(result.failed)
    if invalid_lines:
        lines.append("\n❌ Не распознано:")
        lines.extend(invalid_lines)

    await message.answer("\n".join(lines))
    await state.clear()


async def request_delete_slot(callback: CallbackQuery, callback_data: SlotCallback) -> None:
    await callback.message.answer("Удалить свободное окно?", reply_markup=confirm_delete_slot_kb(callback_data.slot_id))
    await callback.answer()


async def cancel_delete_slot(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Отменено.")
    await callback.answer()


async def confirm_delete_slot(callback: CallbackQuery, callback_data: SlotCallback, child_bot: BotModel, session: AsyncSession) -> None:
    deleted = await SlotService(session).delete_available_slot(child_bot.id, callback_data.slot_id)
    if deleted:
        await callback.message.edit_text("✅ Окно удалено.")
    else:
        await callback.message.edit_text("❌ Не удалось удалить — окно уже занято или не найдено.")
    await callback.answer()


def register(router: Router) -> None:
    router.message.register(open_add_slot_calendar, F.text == ADD_SLOT_BUTTON, IsOwner())
    router.message.register(open_view_slots_calendar, F.text == VIEW_SLOTS_BUTTON, IsOwner())
    router.message.register(open_delete_slot_calendar, F.text == DELETE_SLOT_BUTTON, IsOwner())

    router.callback_query.register(navigate_calendar, CalendarNavCallback.filter(F.purpose.in_(SLOT_PURPOSES)), IsOwner())
    router.callback_query.register(pick_day, CalendarDayCallback.filter(F.purpose.in_(SLOT_PURPOSES)), IsOwner())

    router.message.register(process_times_input, AddSlotStates.waiting_times, F.text, IsOwner())

    router.callback_query.register(request_delete_slot, SlotCallback.filter(F.action == "delete"), IsOwner())
    router.callback_query.register(confirm_delete_slot, SlotCallback.filter(F.action == "delete_confirm"), IsOwner())
    router.callback_query.register(cancel_delete_slot, SlotCallback.filter(F.action == "delete_cancel"), IsOwner())
