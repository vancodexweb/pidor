from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

DEFAULT_WELCOME_TEXT = "🌸 Добро пожаловать!\n\nЗдесь вы можете выбрать удобное время для записи 💅"
DEFAULT_START_BUTTON_TEXT = "💅 Записаться"
DEFAULT_NAME_QUESTION = "Как вас зовут? 😊"
DEFAULT_PHONE_QUESTION = "📱 Отправьте номер телефона."
DEFAULT_CONFIRMATION_TEXT = "📋 Проверьте данные:"
DEFAULT_SUCCESS_TEXT = "🎉 Вы успешно записаны!"
DEFAULT_TIMEZONE = "Europe/Moscow"


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("bots.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    welcome_text: Mapped[str] = mapped_column(Text, default=DEFAULT_WELCOME_TEXT, nullable=False)
    welcome_sticker_file_id: Mapped[str | None] = mapped_column(String(255))
    welcome_image_file_id: Mapped[str | None] = mapped_column(String(255))
    start_button_text: Mapped[str] = mapped_column(String(64), default=DEFAULT_START_BUTTON_TEXT, nullable=False)
    name_question: Mapped[str] = mapped_column(Text, default=DEFAULT_NAME_QUESTION, nullable=False)
    phone_question: Mapped[str] = mapped_column(Text, default=DEFAULT_PHONE_QUESTION, nullable=False)
    confirmation_text: Mapped[str] = mapped_column(Text, default=DEFAULT_CONFIRMATION_TEXT, nullable=False)
    success_text: Mapped[str] = mapped_column(Text, default=DEFAULT_SUCCESS_TEXT, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default=DEFAULT_TIMEZONE, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bot: Mapped["Bot"] = relationship(back_populates="settings")  # noqa: F821
