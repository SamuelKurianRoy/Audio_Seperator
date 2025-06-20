import os
from spleeter.separator import Separator
import logging
import librosa
from pydub import AudioSegment

def wav_to_mp3(wav_path, mp3_path):
    logger = logging.getLogger(__name__)
    logger.info(f"Converting {wav_path} to MP3 at {mp3_path} (bitrate 64k)")
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3", bitrate="64k")
    logger.info(f"MP3 saved at {mp3_path}")
    return mp3_path

def separate_stems(audio_path, output_dir):
    """
    Separate the audio file into stems (vocals, accompaniment, etc.) using Spleeter.
    Args:
        audio_path (str): Path to the input audio file.
        output_dir (str): Directory to save the separated stems.
    Returns:
        dict: Paths to separated stems (both wav and mp3).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Spleeter: Separating stems for {audio_path}")
    separator = Separator('spleeter:2stems')
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    track_output_dir = os.path.join(output_dir, base_name)
    os.makedirs(track_output_dir, exist_ok=True)
    separator.separate_to_file(audio_path, track_output_dir)
    # Spleeter saves as track_output_dir/base_name/vocals.wav and accompaniment.wav
    stems = {}
    for stem in ['vocals', 'accompaniment']:
        wav_path = os.path.join(track_output_dir, base_name, f'{stem}.wav')
        mp3_path = os.path.join(track_output_dir, base_name, f'{stem}.mp3')
        if os.path.exists(wav_path):
            wav_to_mp3(wav_path, mp3_path)
            stems[stem] = {'wav': wav_path, 'mp3': mp3_path}
    logger.info(f"Spleeter: Stems saved at {stems}")
    return stems

def analyze_audio(audio_path):
    """
    Analyze the audio file to extract key, tempo, and chords using Librosa.
    Args:
        audio_path (str): Path to the input audio file.
    Returns:
        dict: Analysis results (key, tempo, chords, etc.).
    """
    logger = logging.getLogger(__name__)
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