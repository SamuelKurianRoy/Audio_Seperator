import streamlit as st
import threading
import time
from bot import main as run_bot

st.title("Telegram Spleeter Bot Controller")

# Global state for the bot thread
if 'bot_thread' not in st.session_state:
    st.session_state['bot_thread'] = None
if 'bot_running' not in st.session_state:
    st.session_state['bot_running'] = False

def start_bot():
    if not st.session_state['bot_running']:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        st.session_state['bot_thread'] = bot_thread
        st.session_state['bot_running'] = True
        st.success("Bot started!")
    else:
        st.warning("Bot is already running.")

def stop_bot():
    # Streamlit Cloud does not support killing threads, so just mark as stopped
    if st.session_state['bot_running']:
        st.session_state['bot_running'] = False
        st.session_state['bot_thread'] = None
        st.success("Bot stopped! (Thread will exit when polling loop ends)")
    else:
        st.warning("Bot is not running.")

if st.button("Start Bot"):
    start_bot()

if st.button("Stop Bot"):
    stop_bot()

if st.session_state['bot_running']:
    st.info("Bot is running in the background.")
else:
    st.info("Bot is stopped.") 