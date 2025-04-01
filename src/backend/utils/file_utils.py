# file_utils.py
import os
import subprocess
import wave
import numpy as np
import logging
import tempfile
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def enhance_audio_with_ffmpeg(input_path: str, output_path: str) -> bool:
    try:
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-af",
            "afftdn=nf=-25,highpass=f=50,highpass=f=60,highpass=f=70,"
            "equalizer=f=50:t=q:w=1:g=-40,equalizer=f=60:t=q:w=1:g=-40,"
            "highpass=f=100,loudnorm",
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        return os.path.exists(output_path)
    except Exception as e:
        logger.error(f"Error during FFmpeg audio enhancement: {str(e)}")
        return False


def detect_background_noise(audio_path: str, threshold=1000, max_freq=500) -> str:
    """
    Analyze frequency content for background noise.  
    """
    try:
        with wave.open(audio_path, "rb") as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

        fft_result = np.fft.fft(audio_array)
        magnitude = np.abs(fft_result)
        low_freqs = magnitude[:max_freq]
        avg_magnitude = np.mean(low_freqs)

        if avg_magnitude > threshold:
            return "Background noise detected"
        else:
            return "No significant background noise detected"
    except Exception as e:
        logger.error(f"Error in background noise detection: {str(e)}")
        return f"Error: {str(e)}"

def extract_audio(video_path: str, audio_path: str):
    """
    Extract WAV audio from video using FFmpeg.
    """
    cmd = [
        "ffmpeg", "-i", video_path,
        "-ac", "1", "-ar", "16000", audio_path, "-y"
    ]
    subprocess.run(cmd, check=True)

def convert_audio_to_wav(file_bytes: bytes, original_ext=".mp3") -> str:
    """Converts any audio format to a .wav temp file and returns the path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as input_file:
        input_file.write(file_bytes)
        input_path = input_file.name

    output_path = input_path.replace(original_ext, ".wav")

    try:
        # Convert using pydub
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise FileNotFoundError(f"Conversion failed, file not found or empty: {output_path}")

        logger.info(f"✅ Converted to WAV: {output_path}")
        return output_path
    finally:
        os.remove(input_path)