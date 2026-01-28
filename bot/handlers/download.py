from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import redis.asyncio as aioredis
import json

from bot.services.youtube import YouTubeService
from bot.keyboards.quality import get_quality_keyboard
from bot.utils.logger import logger
from tasks.download import download_and_send_video

router = Router(name='download')


@router.message(F.text.regexp(r'(youtube\.com|youtu\.be)'))
async def handle_youtube_url(message: Message, redis: aioredis.Redis):
    url = message.text.strip()
    status_msg = await message.answer("🔍 Анализирую видео...")
    
    try:
        video_info = await YouTubeService.get_video_info(url)
        
        cache_key = f"video:{video_info['id']}"
        await redis.setex(
            cache_key,
            600,
            json.dumps({
                **video_info,
                'url': url,
                'user_id': message.from_user.id,
                'chat_id': message.chat.id
            })
        )
        
        duration_str = f"{video_info['duration'] // 60}:{video_info['duration'] % 60:02d}" if video_info['duration'] else "N/A"
        
        await status_msg.edit_text(
            f"📺 <b>{video_info['title']}</b>\n\n"
            f"👤 {video_info['uploader']}\n"
            f"⏱ Длительность: {duration_str}\n\n"
            f"Выберите качество для скачивания:",
            reply_markup=get_quality_keyboard(video_info['id']),
            parse_mode="HTML"
        )
        
        logger.info(
            "video_processed",
            user_id=message.from_user.id,
            video_id=video_info['id']
        )
        
    except Exception as e:
        logger.error("video_processing_failed", error=str(e), url=url)
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("dl:"))
async def process_download(callback: CallbackQuery, redis: aioredis.Redis):
    await callback.answer()
    
    try:
        _, video_id, quality = callback.data.split(":")
        
        cache_key = f"video:{video_id}"
        cached_data = await redis.get(cache_key)
        
        if not cached_data:
            await callback.message.edit_text("❌ Видео не найдено в кэше. Отправьте ссылку заново.")
            return
        
        video_data = json.loads(cached_data)
        
        await callback.message.edit_text(
            f"⏬ Скачиваю видео в качестве {quality}...\n"
            f"Это может занять несколько минут."
        )
        
        task = download_and_send_video.delay(
            url=video_data['url'],
            quality=quality,
            chat_id=video_data['chat_id'],
            message_id=callback.message.message_id,
            title=video_data['title']
        )
        
        logger.info(
            "download_task_created",
            task_id=task.id,
            video_id=video_id,
            quality=quality
        )
        
    except Exception as e:
        logger.error("download_failed", error=str(e))
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
