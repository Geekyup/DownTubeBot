from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name='start')


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я помогу скачать видео с YouTube.\n\n"
        "Просто отправь мне ссылку на видео, и я предложу "
        "выбрать качество для скачивания.\n\n"
        "Поддерживаются форматы:\n"
        "• 1080p, 720p, 480p, 360p\n"
        "• Только аудио (MP3)"
    )
