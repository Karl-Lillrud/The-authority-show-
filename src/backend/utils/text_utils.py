# src/backend/utils/text_utils.py

import os
import re
import openai
import logging
import subprocess
import base64
import requests
import time
from pathlib import Path
from typing import List
from transformers import pipeline
from io import BytesIO
import streamlit as st  # Needed for download_button_text

API_BASE_URL = os.getenv("API_BASE_URL")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
logger = logging.getLogger(__name__)

def format_transcription(transcription):
    """Convert list of dictionaries to a readable string."""
    if isinstance(transcription, list):
        return "\n".join([
            f"[{item['start']}-{item['end']}] {item['speaker']}: {item['text'].strip()}"
            for item in transcription
        ])
    return transcription  # Already a string

def download_button_text(label, text, filename, key_prefix=""):
    if isinstance(text, list):
        text = format_transcription(text)
    b64 = base64.b64encode(text.encode()).decode()
    key = f"{key_prefix}_{filename}" if key_prefix else filename
    return st.download_button(label, text, filename, key=key)


def translate_text(text: str, target_language: str) -> str:
    prompt = f"Translate the following transcript to {target_language}:\n\n{text}"
    retries = 3
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{retries} failed: {e}")
            time.sleep(1)
    logger.error("❌ Translation permanently failed after retries.")
    return "⚠️ Failed to translate. Try again later."

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
    try:
        with open(audio_path, "rb") as f:
            response = openai.Audio.transcribe("whisper-1", file=f)
        return response["text"]
    except Exception as e:
        logger.error(f"Error in Whisper transcription: {str(e)}")
        return ""

classifier = pipeline(
    "zero-shot-classification",
    model="nreimers/MiniLM-L6-H384-uncased"
)

def detect_filler_words(transcription):
    filler_words = [
        "um", "uh", "ah", "like", "you know", "so", "well", "I mean",
        "sort of", "kind of", "okay", "right"
    ]
    sentences = transcription.split(". ")
    return [
        sentence for sentence in sentences
        if any(re.search(rf"\b{word}\b", sentence, re.IGNORECASE) for word in filler_words)
    ]

def classify_sentence_relevance(transcription):
    sentences = transcription.split(". ")
    results = []
    labels = ["important", "filler", "off-topic", "redundant"]
    for s in sentences:
        result = classifier(s, candidate_labels=labels)
        results.append({
            "sentence": s,
            "category": result["labels"][0],
            "score": result["scores"][0]
        })
    return results

def analyze_certainty_levels(transcription):
    sentences = transcription.split(". ")
    labels = ["filler", "important", "redundant", "off-topic"]
    result_list = []

    for s in sentences:
        if not s.strip():
            continue
        result = classifier(s, candidate_labels=labels)
        certainty = result["scores"][result["labels"].index("important")]
        level = (
            "Green" if certainty <= 0.2 else
            "Light Green" if certainty <= 0.4 else
            "Yellow" if certainty <= 0.6 else
            "Orange" if certainty <= 0.8 else
            "Dark Orange" if certainty <= 0.9 else "Red"
        )
        result_list.append({
            "sentence": s,
            "certainty": certainty,
            "certainty_level": level
        })
    return result_list

def get_sentence_timestamps(sentence, word_timings, prev_end_time=0):
    words = sentence.split()
    if not words:
        return {"start": prev_end_time, "end": prev_end_time + 2.0}

    first_word, last_word = words[0], words[-1]

    start = next((w["start"] for w in word_timings if w["word"] == first_word and w["start"] >= prev_end_time), prev_end_time)
    end = next((w["end"] for w in word_timings if w["word"] == last_word and w["end"] >= start), start + 2.0)

    if end - start < 0.5:
        end += 0.5

    return {"start": start, "end": end}

def detect_long_pauses(audio_path, threshold=2.0):
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-af", f"silencedetect=noise=-40dB:d={threshold}",
        "-f", "null", "-"
    ]
    process = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    output = process.stderr

    starts = [float(m.group(1)) for m in re.finditer(r"silence_start: ([0-9.]+)", output)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end: ([0-9.]+)", output)]

    return [{"start": s, "end": e} for s, e in zip(starts, ends)]

def generate_ai_show_notes(transcript):
    prompt = f"""
    Generate professional show notes for this podcast episode.
    - A brief summary of the discussion.
    - Key topics covered (bullet points).
    - Any important timestamps (if available).
    - Guest highlights (if mentioned).

    Transcript:
    {transcript}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional podcast assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"❌ Error generating show notes: {e}")
        return f"Error generating show notes: {str(e)}"

def generate_ai_quotes(transcript: str) -> str:
    prompt = f"""
    From the following podcast transcript, extract 3 impactful, quotable moments or sentences.
    - Keep each quote short and standalone (1–2 sentences).
    - The quotes should be insightful, funny, emotional, or thought-provoking.
    - Do NOT include speaker labels, just the raw quote text.

    Transcript:
    {transcript}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're an expert podcast editor and copywriter."},
                {"role": "user", "content": prompt}
            ]
        )
        quotes_raw = response["choices"][0]["message"]["content"].strip()
        lines = [line.strip("•–—-• \n\"") for line in quotes_raw.split("\n") if line.strip()]
        return "\n\n".join(lines[:3])
    except Exception as e:
        logger.error(f"❌ Error generating quotes: {e}")
        return f"Error generating quotes: {str(e)}"

def generate_quote_images(quotes: List[str]) -> List[str]:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    urls = []

    for quote in quotes:
        prompt = f"Create a visually striking, artistic background that reflects this quote’s emotion: \"{quote}\". No text in the image."
        try:
            response = openai.Image.create(
                prompt=prompt,
                model="dall-e-3",
                n=1,
                size="1024x1024"
            )
            url = response["data"][0]["url"]
            urls.append(url)
        except Exception as e:
            logger.error(f"❌ Failed to generate image for quote: {quote} | Error: {e}")
            urls.append("")
    return urls

def fetch_sfx_for_emotion(emotion: str, limit=1) -> List[str]:
    try:
        generation_url = "https://api.elevenlabs.io/v1/sound-generation"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "text": f"{emotion} sound effect",
            "duration_seconds": 4,
            "prompt_influence": 0.6
        }

        # 🔄 Send request
        res = requests.post(generation_url, headers=headers, json=payload)
        print("📡 SFX gen status:", res.status_code)
        print("📥 SFX headers:", res.headers)

        if "audio/mpeg" in res.headers.get("Content-Type", ""):
            audio_data = res.content
            buffer = BytesIO(audio_data)

            # Encode audio data to base64 string for frontend embedding
            b64_audio = base64.b64encode(buffer.read()).decode("utf-8")
            return [f"data:audio/mpeg;base64,{b64_audio}"]

        else:
            print("⚠️ Unexpected content type:", res.headers.get("Content-Type"))
            return []

    except Exception as e:
        print(f"⚠️ Failed to fetch SFX for '{emotion}': {e}")
        return []

def suggest_sound_effects(emotion_data):
    suggestions = []

    for entry in emotion_data:
        emotion = entry["emotions"][0]["label"]
        text = entry["text"]

        sfx_options = fetch_sfx_for_emotion(emotion)

        suggestions.append({
            "timestamp_text": text,
            "emotion": emotion,
            "sfx_options": sfx_options
        })

    return suggestions




