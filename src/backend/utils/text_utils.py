# text_utils.py
import openai
import logging
import subprocess

logger = logging.getLogger(__name__)

def format_transcription(transcription):
    """Convert list of dictionaries to a readable string."""
    if isinstance(transcription, list):
        return "\n".join([
            f"[{item['start']}-{item['end']}] {item['speaker']}: {item['text']}"
            for item in transcription
        ])
    return transcription  # Already a string

def generate_ai_suggestions(text):
    prompt = f"""
    Review the following transcription and provide suggestions for improvement.
    Focus on removing filler words, grammar/spelling corrections, rewriting awkward phrases:
    {text}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def generate_show_notes(text):
    prompt = f"""
    Generate concise show notes for this transcript:
    {text}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def transcribe_with_whisper(audio_path: str) -> str:
    """
    Example of calling openai.Audio.transcribe for a local file.
    """
    try:
        with open(audio_path, "rb") as f:
            response = openai.Audio.transcribe("whisper-1", file=f)
        return response["text"]
    except Exception as e:
        logger.error(f"Error in Whisper transcription: {str(e)}")
        return ""
