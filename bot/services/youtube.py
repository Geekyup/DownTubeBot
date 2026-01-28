import yt_dlp
from typing import Dict
from bot.utils.logger import logger


class YouTubeService:
    QUALITY_FORMATS = {
        '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        'audio': 'bestaudio/best',
    }
    
    @staticmethod
    async def get_video_info(url: str) -> Dict:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                logger.info(
                    "video_info_extracted",
                    video_id=info.get('id'),
                    title=info.get('title')
                )
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                }
        except Exception as e:
            logger.error("video_info_extraction_failed", error=str(e), url=url)
            raise
    
    @staticmethod
    def get_format_string(quality: str) -> str:
        return YouTubeService.QUALITY_FORMATS.get(quality, YouTubeService.QUALITY_FORMATS['720'])
