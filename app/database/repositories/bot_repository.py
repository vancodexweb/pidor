from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.bot import Bot


class BotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, bot_id: int) -> Bot | None:
        result = await self.session.execute(select(Bot).where(Bot.id == bot_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_bot_id(self, telegram_bot_id: int) -> Bot | None:
        result = await self.session.execute(
            select(Bot)
            .where(Bot.telegram_bot_id == telegram_bot_id)
            .options(selectinload(Bot.settings))
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: int, active_only: bool = False) -> list[Bot]:
        query = select(Bot).where(Bot.owner_id == owner_id).order_by(Bot.created_at)
        if active_only:
            query = query.where(Bot.active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_active(self) -> list[Bot]:
        result = await self.session.execute(select(Bot).where(Bot.active.is_(True)))
        return list(result.scalars().all())

    async def create(
        self,
        owner_id: int,
        telegram_bot_id: int,
        username: str,
        first_name: str,
        token_encrypted: str,
    ) -> Bot:
        bot = Bot(
            owner_id=owner_id,
            telegram_bot_id=telegram_bot_id,
            username=username,
            first_name=first_name,
            token_encrypted=token_encrypted,
            active=True,
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        return bot

    async def set_active(self, bot_id: int, active: bool) -> None:
        bot = await self.get_by_id(bot_id)
        if bot is None:
            return
        bot.active = active
        await self.session.commit()

    async def update_token(self, bot_id: int, token_encrypted: str) -> None:
        bot = await self.get_by_id(bot_id)
        if bot is None:
            return
        bot.token_encrypted = token_encrypted
        await self.session.commit()
