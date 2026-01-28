from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_quality_keyboard(video_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    qualities = [
        ("🎬 1080p (Full HD)", "1080"),
        ("🎥 720p (HD)", "720"),
        ("📹 480p (SD)", "480"),
        ("📱 360p (Low)", "360"),
        ("🎵 Только аудио", "audio"),
    ]
    
    for label, quality in qualities:
        builder.button(
            text=label,
            callback_data=f"dl:{video_id}:{quality}"
        )
    
    builder.adjust(1)
    return builder.as_markup()
