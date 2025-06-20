# Moises-like Telegram Bot

A Telegram bot that performs Moises-like audio separation and analysis.

## Features
- 🎵 Upload an audio file (MP3, WAV, etc.)
- 🧠 Perform vocal/instrument separation (Spleeter)
- 🎼 Extract key, tempo, and chords (Librosa)
- 📥 Send back processed stems and metadata

## Stack
- python-telegram-bot
- Spleeter
- Librosa
- ffmpeg-python
- Python 3.8+

## Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a Telegram bot token from [BotFather](https://t.me/botfather)
4. Add your token to `bot.py`
5. Run the bot:
   ```bash
   python bot.py
   ```

## Usage
- Send an audio file to the bot.
- Wait for processing.
- Receive separated stems and analysis results. 