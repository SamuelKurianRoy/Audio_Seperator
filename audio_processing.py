import os
import logging
import streamlit as st
from spleeter.separator import Separator
import librosa
from pydub import AudioSegment
import urllib.request
import zipfile

def ensure_model_downloaded(model_dir, model_url=None):
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
    # Check for model files (basic check: model directory not empty)
    if not os.listdir(model_dir):
        if model_url:
            try:
                st.info(f"Downloading Spleeter model from {model_url}...")
                zip_path = os.path.join(model_dir, 'model.zip')
                urllib.request.urlretrieve(model_url, zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(model_dir)
                os.remove(zip_path)
                st.success("Model downloaded and extracted.")
            except Exception as e:
                st.error(f"Failed to download or extract model: {e}")
                raise
        else:
            st.error("Model directory is empty and no URL provided.")
            raise FileNotFoundError("Model directory is empty and no URL provided.")

def wav_to_mp3(wav_path, mp3_path):
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Converting {wav_path} to MP3 at {mp3_path} (bitrate 64k)")
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3", bitrate="64k")
        logger.info(f"MP3 saved at {mp3_path}")
        return mp3_path
    except Exception as e:
        logger.error(f"Error converting WAV to MP3: {e}")
        st.error(f"Error converting WAV to MP3: {e}")
        raise

def separate_stems(audio_path, output_dir):
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Spleeter: Separating stems for {audio_path}")
        # Ensure model is downloaded
        model_dir = st.secrets.get('SPLEETER_MODEL_DIR', 'pretrained_models/2stems')
        model_url = st.secrets.get('SPLEETER_MODEL_URL', 'https://github.com/deezer/spleeter/releases/download/v1.4.0/2stems.zip')
        ensure_model_downloaded(model_dir, model_url)
        separator = Separator(model_dir)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        track_output_dir = os.path.join(output_dir, base_name)
        os.makedirs(track_output_dir, exist_ok=True)
        separator.separate_to_file(audio_path, track_output_dir)
        stems = {}
        for stem in ['vocals', 'accompaniment']:
            wav_path = os.path.join(track_output_dir, base_name, f'{stem}.wav')
            mp3_path = os.path.join(track_output_dir, base_name, f'{stem}.mp3')
            if os.path.exists(wav_path):
                wav_to_mp3(wav_path, mp3_path)
                stems[stem] = {'wav': wav_path, 'mp3': mp3_path}
        logger.info(f"Spleeter: Stems saved at {stems}")
        return stems
    except Exception as e:
        logger.error(f"Error during stem separation: {e}")
        st.error(f"Error during stem separation: {e}")
        raise

def analyze_audio(audio_path):
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Librosa: Analyzing {audio_path}")
        y, sr = librosa.load(audio_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # Ensure tempo is a float (in case it's a numpy array)
        if hasattr(tempo, '__len__') and not isinstance(tempo, str):
            tempo_value = float(tempo[0]) if len(tempo) > 0 else 0.0
        else:
            tempo_value = float(tempo)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        key_index = chroma_mean.argmax()
        key_list = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = key_list[key_index]
        chords = 'Chord extraction not implemented'
        logger.info(f"Librosa: Analysis complete. Tempo: {tempo_value:.2f} BPM, Key: {key}")
        return {
            'tempo': tempo_value,
            'key': key,
            'chords': chords
        }
    except Exception as e:
        logger.error(f"Error during audio analysis: {e}")
        st.error(f"Error during audio analysis: {e}")
        raise 