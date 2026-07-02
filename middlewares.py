from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import Database


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db

    async def __call__(self, handler, event, data):
        data["db"] = self.db
        return await handler(event, data)


class RoleMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        db: Database = data["db"]
        user_id = event.from_user.id
        user = await db.get_user(user_id)
        data["user"] = user
        data["is_admin"] = user is not None and user["role"] == "admin"
        return await handler(event, data)
