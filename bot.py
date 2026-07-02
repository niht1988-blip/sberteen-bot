import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import Database
from middlewares import DatabaseMiddleware, RoleMiddleware
from handlers import (
    start_router,
    schedule_router,
    profile_router,
    homework_router,
    admin_router,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    db = Database()
    await db.connect()
    logger.info("Database connected")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Middleware
    db_middleware = DatabaseMiddleware(db)
    role_middleware = RoleMiddleware()

    dp.message.middleware(db_middleware)
    dp.message.middleware(role_middleware)
    dp.callback_query.middleware(db_middleware)
    dp.callback_query.middleware(role_middleware)

    # Routers
    dp.include_router(start_router)
    dp.include_router(schedule_router)
    dp.include_router(profile_router)
    dp.include_router(homework_router)
    dp.include_router(admin_router)

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
