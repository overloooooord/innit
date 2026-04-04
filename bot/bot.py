import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import init_db
from config import BOT_TOKEN
from database import init_db
from handlers import router
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await init_db()
    logger.info("Database initialized")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
    print("Таблицы успешно созданы в Supabase!")
