import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
import yt_dlp

# ЗАМЕНИТЕ НА ВАШ ТОКЕН ОТ @BotFather
BOT_TOKEN = "7804005145:AAGacePNYRqNffVdHnZCzmaQIhW60r6jNuY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

video_cache = {}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я помогу скачать видео с YouTube.\n\n"
        "Просто отправь мне ссылку на видео.\n\n"
        "Поддерживаются форматы:\n"
        "• 720p, 480p, 360p\n"
        "• Только аудио"
    )


@dp.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_youtube_link(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("🔍 Анализирую видео...")
    
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
            
            video_id = str(message.message_id)
            video_cache[video_id] = {
                'url': url,
                'title': info['title']
            }
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎥 720p (HD)", callback_data=f"dl_{video_id}_720")],
                [InlineKeyboardButton(text="📱 480p (SD)", callback_data=f"dl_{video_id}_480")],
                [InlineKeyboardButton(text="📉 360p", callback_data=f"dl_{video_id}_360")],
                [InlineKeyboardButton(text="🎵 Только аудио", callback_data=f"dl_{video_id}_audio")]
            ])
            
            duration = info.get('duration', 0)
            duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"
            
            await status_msg.edit_text(
                f"📺 <b>{info['title']}</b>\n\n"
                f"⏱ Длительность: {duration_str}\n"
                f"👤 Автор: {info.get('uploader', 'N/A')}\n\n"
                f"Выберите качество для скачивания:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: CallbackQuery):
    await callback.answer()
    
    _, video_id, quality = callback.data.split("_")
    
    if video_id not in video_cache:
        await callback.message.edit_text("❌ Видео не найдено. Отправьте ссылку заново.")
        return
    
    video_info = video_cache[video_id]
    url = video_info['url']
    title = video_info['title']
    
    await callback.message.edit_text(f"⏬ Скачиваю видео в качестве {quality}...")
    
    try:
        filename = f"video_{video_id}"
        
        if quality == "audio":
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': f'{filename}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
        else:
            ydl_opts = {
                'format': f'(bv*[height<={quality}]+ba/b[height<={quality}])[filesize<?2G]',
                'outtmpl': f'{filename}.%(ext)s',
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
            ydl.download([url])
        
        # Находим скачанный файл
        downloaded_file = None
        for file in os.listdir('.'):
            if file.startswith(filename):
                downloaded_file = file
                break
        
        if not downloaded_file:
            await callback.message.edit_text("❌ Файл не найден после скачивания")
            return
        
        # Проверяем что файл не пустой
        file_size = os.path.getsize(downloaded_file)
        if file_size == 0:
            os.remove(downloaded_file)
            await callback.message.edit_text(
                "❌ YouTube заблокировал скачивание.\n"
                "Попробуйте другое видео или обновите yt-dlp:\n"
                "<code>pip install -U yt-dlp</code>",
                parse_mode="HTML"
            )
            return
        
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > 2000:
            await callback.message.edit_text(
                f"❌ Файл слишком большой ({file_size_mb:.0f} MB).\n"
                f"Попробуйте выбрать меньшее качество."
            )
            os.remove(downloaded_file)
            return
        
        await callback.message.edit_text(f"📤 Отправляю файл ({file_size_mb:.1f} MB)...")
        
        # Отправляем файл через FSInputFile
        if quality == "audio":
            audio_file = FSInputFile(downloaded_file)
            await callback.message.answer_audio(
                audio=audio_file,
                title=title,
                performer="YouTube"
            )
        else:
            video_file = FSInputFile(downloaded_file)
            await callback.message.answer_video(
                video=video_file,
                caption=f"{title}\n\nКачество: {quality}p"
            )
        
        # Удаляем файл
        os.remove(downloaded_file)
        await callback.message.delete()
        
        # Очищаем кэш
        del video_cache[video_id]
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при скачивании:\n{str(e)}")
        
        # Очищаем файлы при ошибке
        for file in os.listdir('.'):
            if file.startswith(filename):
                try:
                    os.remove(file)
                except:
                    pass


async def main():
    print("🚀 Бот запущен и готов к работе!")
    print("Нажмите Ctrl+C для остановки")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
