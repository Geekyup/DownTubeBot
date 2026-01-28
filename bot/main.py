import asyncio
import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.utils.logger import logger
from bot.handlers import start, download
from bot.middlewares.rate_limit import RateLimitMiddleware


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    
    dp.message.middleware(RateLimitMiddleware(redis_client))
    
    dp.include_router(start.router)
    dp.include_router(download.router)
    
    dp['redis'] = redis_client
    
    logger.info("bot_started")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await redis_client.close()


if __name__ == '__main__':
    asyncio.run(main())
