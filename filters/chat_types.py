from aiogram.filters import Filter
from aiogram import Bot, types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return message.from_user.id in bot.my_admins_list


class UserAuth(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, session: AsyncSession) -> bool:
        all_user_id_db = await orm_get_user(session)
        return message.from_user.id not in [user.user_id for user in all_user_id_db]
