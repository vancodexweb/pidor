from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.bot_settings import BotSettings

# Fields the owner is allowed to edit from the admin settings menu.
EDITABLE_FIELDS = {
    "welcome_text",
    "welcome_sticker_file_id",
    "welcome_image_file_id",
    "start_button_text",
    "name_question",
    "phone_question",
    "confirmation_text",
    "success_text",
    "timezone",
}


class BotSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_bot_id(self, bot_id: int) -> BotSettings | None:
        result = await self.session.execute(select(BotSettings).where(BotSettings.bot_id == bot_id))
        return result.scalar_one_or_none()

    async def create_default(self, bot_id: int) -> BotSettings:
        settings = BotSettings(bot_id=bot_id)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def update_field(self, bot_id: int, field: str, value: str) -> BotSettings | None:
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Field '{field}' is not editable")
        settings = await self.get_by_bot_id(bot_id)
        if settings is None:
            return None
        setattr(settings, field, value)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings
