import os
import yt_dlp
from celery import Task
from tasks.celery_app import celery_app
from bot.config import settings
from bot.utils.logger import logger
import requests


class DownloadTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(base=DownloadTask, bind=True)
def download_and_send_video(self, url: str, quality: str, chat_id: int, message_id: int, title: str):
    from bot.services.youtube import YouTubeService
    
    task_id = self.request.id
    filename = None
    
    try:
        logger.info("download_started", task_id=task_id, quality=quality)
        
        os.makedirs(settings.download_path, exist_ok=True)
        output_template = f"{settings.download_path}/{task_id}.%(ext)s"
        
        if quality == 'audio':
            ydl_opts = {
                'format': YouTubeService.get_format_string('audio'),
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
            expected_ext = 'mp3'
        else:
            ydl_opts = {
                'format': YouTubeService.get_format_string(quality),
                'outtmpl': output_template,
                'merge_output_format': 'mp4',
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
            expected_ext = 'mp4'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        filename = f"{settings.download_path}/{task_id}.{expected_ext}"
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Downloaded file not found: {filename}")
        
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        
        if file_size_mb > settings.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB")
        
        logger.info("download_completed", task_id=task_id, file_size_mb=file_size_mb)
        
        _send_file_to_telegram(filename, chat_id, message_id, title, quality, expected_ext)
        
        logger.info("file_sent", task_id=task_id, chat_id=chat_id)
        
    except Exception as e:
        logger.error("download_task_failed", task_id=task_id, error=str(e))
        _send_error_to_telegram(chat_id, message_id, str(e))
        raise
    
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
            logger.info("file_cleaned", task_id=task_id)


def _send_file_to_telegram(filename: str, chat_id: int, message_id: int, title: str, quality: str, file_type: str):
    from bot.config import settings
    
    url = f"https://api.telegram.org/bot{settings.bot_token}/send{'Audio' if file_type == 'mp3' else 'Video'}"
    
    with open(filename, 'rb') as f:
        files = {file_type: f}
        data = {
            'chat_id': chat_id,
            'caption': f"{title}\n\nКачество: {quality}p" if file_type == 'mp4' else f"{title}",
            'reply_to_message_id': message_id,
        }
        
        response = requests.post(url, files=files, data=data, timeout=300)
        response.raise_for_status()
    
    delete_url = f"https://api.telegram.org/bot{settings.bot_token}/deleteMessage"
    requests.post(delete_url, json={'chat_id': chat_id, 'message_id': message_id})


def _send_error_to_telegram(chat_id: int, message_id: int, error: str):
    from bot.config import settings
    
    url = f"https://api.telegram.org/bot{settings.bot_token}/editMessageText"
    requests.post(url, json={
        'chat_id': chat_id,
        'message_id': message_id,
        'text': f"❌ Ошибка при скачивании:\nde>{error[:100]}</code>",
        'parse_mode': 'HTML'
    })
