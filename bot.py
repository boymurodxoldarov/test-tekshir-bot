"""
bot.py — Asosiy kirish nuqtasi.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import admin, commands, check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


async def on_startup() -> None:
    await init_db()
    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s", me.username)


async def on_shutdown() -> None:
    await bot.session.close()
    logger.info("Bot to'xtatildi.")


async def main() -> None:
    # Tartib muhim: admin va commands buyruqlari catch-all dan oldin
    dp.include_router(admin.router)
    dp.include_router(commands.router)
    dp.include_router(check.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Chiqildi.")
