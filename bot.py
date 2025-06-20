import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
from audio_processing import separate_stems, analyze_audio

DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', 'downloads')
STEMS_DIR = os.getenv('STEMS_DIR', 'stems')

# Set up logging for your bot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress noisy logs from third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# Load environment variables from .env file (if present)
env_path = os.getenv('ENV_PATH', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise EnvironmentError('Please set the TELEGRAM_BOT_TOKEN environment variable.')

def get_username(update):
    user = update.effective_user
    if user:
        return user.full_name or user.username or str(user.id)
    return 'Unknown User'

def start(update: Update, context):
    username = get_username(update)
    logger.info(f"{username} started the bot.")
    update.message.reply_text('Welcome! Send me an audio file (MP3, WAV, etc.) to separate vocals and instruments and analyze the track.')

def handle_audio(update: Update, context):
    # Ensure download and stems directories exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(STEMS_DIR, exist_ok=True)

    file = None
    if update.message.audio:
        file = update.message.audio
    elif update.message.voice:
        file = update.message.voice
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('audio'):
        file = update.message.document

    username = get_username(update)

    if not file:
        logger.warning(f"{username} tried to send a non-audio file.")
        update.message.reply_text('Please send a valid audio file.')
        return

    logger.info(f"{username} sent an audio file. File ID: {file.file_id}")

    file_id = file.file_id
    try:
        new_file = context.bot.get_file(file_id)
        file_ext = os.path.splitext(file.file_name)[-1] if hasattr(file, 'file_name') and file.file_name else '.ogg'
        local_path = os.path.join(DOWNLOAD_DIR, f'{file_id}{file_ext}')
        new_file.download(local_path)
        logger.info(f"Audio from {username} saved as '{local_path}'")
        update.message.reply_text(f'Audio file received. Starting separation...')

        # Separate stems using Spleeter
        logger.info(f"Starting stem separation for {username}...")
        update.message.reply_text('Separating vocals and accompaniment. This may take a minute...')
        try:
            stem_paths = separate_stems(local_path, STEMS_DIR)
            logger.info(f"Separation complete for {username}. Stems: {stem_paths}")
            # Send MP3 stems back to user
            for stem_name, paths in stem_paths.items():
                mp3_path = paths.get('mp3')
                if mp3_path and os.path.exists(mp3_path):
                    with open(mp3_path, 'rb') as stem_file:
                        update.message.reply_audio(audio=stem_file, filename=os.path.basename(mp3_path), caption=f"{stem_name.title()} track (MP3)")
            update.message.reply_text('All stems have been sent!')
        except Exception as e:
            logger.error(f"Error during separation for {username}: {e}")
            update.message.reply_text(f'An error occurred during separation: {e}')
            return

        # Analyze audio and send results
        logger.info(f"Starting analysis for {username}...")
        update.message.reply_text('Analyzing audio for tempo, key, and chords...')
        try:
            analysis = analyze_audio(local_path)
            logger.info(f"Analysis for {username}: {analysis}")
            analysis_msg = (
                f"Audio Analysis Results:\n"
                f"Tempo: {analysis['tempo']:.2f} BPM\n"
                f"Key: {analysis['key']}\n"
                f"Chords: {analysis['chords']}"
            )
            update.message.reply_text(analysis_msg)
        except Exception as e:
            logger.error(f"Error during analysis for {username}: {e}")
            update.message.reply_text(f'An error occurred during analysis: {e}')

    except BadRequest as e:
        logger.error(f"Error downloading file for {username}: {e}")
        if 'File is too big' in str(e):
            update.message.reply_text('The file you sent is too large. Please send an audio file smaller than 20 MB.')
        else:
            update.message.reply_text(f'An error occurred: {e}')

def main():
    logger.info('Bot is starting...')
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.audio | Filters.voice | Filters.document.audio, handle_audio))
    print('Bot is running...')
    logger.info('Bot is running and ready to receive audio files!')
    updater.start_polling()
    updater.idle()
    print("Bot main() has exited!")  # This should never print unless the bot is stopped
    logger.info("Bot main() has exited!")

if __name__ == '__main__':
    main()
