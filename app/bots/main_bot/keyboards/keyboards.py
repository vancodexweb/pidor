from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.callbacks.factories import MyBotCallback
from app.database.models.bot import Bot

MY_BOTS_BUTTON = "🤖 Мои боты"
CREATE_BOT_BUTTON = "➕ Создать бота"
SETTINGS_BUTTON = "⚙️ Настройки"
HELP_BUTTON = "❓ Помощь"
STATS_BUTTON = "📊 Статистика"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MY_BOTS_BUTTON), KeyboardButton(text=CREATE_BOT_BUTTON)],
            [KeyboardButton(text=STATS_BUTTON), KeyboardButton(text=SETTINGS_BUTTON)],
            [KeyboardButton(text=HELP_BUTTON)],
        ],
        resize_keyboard=True,
    )


def my_bots_kb(bots: list[Bot]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'🟢' if b.active else '🔴'} @{b.username}",
                callback_data=MyBotCallback(action="open", bot_id=b.id).pack(),
            )
        ]
        for b in bots
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bot_detail_kb(bot: Bot) -> InlineKeyboardMarkup:
    toggle_text = "⏸ Остановить" if bot.active else "▶️ Запустить"
    toggle_action = "stop" if bot.active else "start"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data=MyBotCallback(action=toggle_action, bot_id=bot.id).pack())],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=MyBotCallback(action="delete", bot_id=bot.id).pack())],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=MyBotCallback(action="back", bot_id=bot.id).pack())],
        ]
    )


def confirm_delete_bot_kb(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=MyBotCallback(action="delete_confirm", bot_id=bot_id).pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=MyBotCallback(action="open", bot_id=bot_id).pack()),
            ]
        ]
    )
