from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.bot_settings import BotSettings
from app.database.repositories.bot_settings_repository import EDITABLE_FIELDS, BotSettingsRepository


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings_repo = BotSettingsRepository(session)

    async def get(self, bot_id: int) -> BotSettings | None:
        return await self.settings_repo.get_by_bot_id(bot_id)

    async def update(self, bot_id: int, field: str, value: str) -> BotSettings | None:
        return await self.settings_repo.update_field(bot_id, field, value)

    @staticmethod
    def is_editable(field: str) -> bool:
        return field in EDITABLE_FIELDS
