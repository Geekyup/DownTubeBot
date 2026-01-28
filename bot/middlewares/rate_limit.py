from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import redis.asyncio as aioredis
from bot.config import settings
from bot.utils.logger import logger


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        key = f"rate_limit:{user_id}"
        
        current = await self.redis.get(key)
        
        if current and int(current) >= settings.rate_limit_requests:
            logger.warning("rate_limit_exceeded", user_id=user_id)
            await event.answer("⚠️ Слишком много запросов. Подождите немного.")
            return
        
        await self.redis.incr(key)
        await self.redis.expire(key, settings.rate_limit_period)
        
        return await handler(event, data)
