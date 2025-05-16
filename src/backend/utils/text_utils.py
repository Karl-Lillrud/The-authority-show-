# src/backend/utils/text_utils.py

import os
import re
import json
import csv
from openai import OpenAI
import logging
import subprocess
import base64
import requests
import time
import random
import math
from pathlib import Path
from typing import List
from transformers import pipeline
from io import BytesIO
import streamlit as st  
from pydub import AudioSegment
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import difflib

client = OpenAI()

API_BASE_URL = os.getenv("API_BASE_URL")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
logger = logging.getLogger(__name__)

def format_transcription(transcription):
    if isinstance(transcription, list):
        return "\n".join([
            f"[{item['start']}-{item['end']}] {item['speaker']}: {item['text'].strip()}"
            for item in transcription
        ])
    return transcription

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
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{retries} failed: {e}")
            time.sleep(1)
    logger.error("Translation permanently failed after retries.")
    return "Failed to translate. Try again later."

import tiktoken
import time
from openai import OpenAIError, BadRequestError

def truncate_to_token_limit(text, model="gpt-4", max_tokens=7000):
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return enc.decode(tokens[:max_tokens]) if len(tokens) > max_tokens else text

def gpt_with_fallback(prompt: str, primary_model="gpt-4", fallback_model="gpt-3.5-turbo-16k") -> str:
    try:
        return _safe_gpt_call(prompt, primary_model)
    except BadRequestError as e:
        if "context_length_exceeded" in str(e):
            print("⚠️ Too long for GPT-4, falling back to gpt-3.5-turbo-16k")
            return _safe_gpt_call(prompt, fallback_model)
        raise e

def _safe_gpt_call(prompt: str, model: str, max_tokens: int = 7000, retries: int = 2) -> str:
    prompt = truncate_to_token_limit(prompt, model=model, max_tokens=max_tokens)
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            if "rate limit" in str(e).lower():
                if model == "gpt-4":
                    logger.warning("⚠️ GPT-4 TPM limit hit — falling back to gpt-3.5-turbo-16k.")
                    return _safe_gpt_call(prompt, "gpt-3.5-turbo-16k")
                time.sleep((attempt + 1) * 5)
            else:
                raise e
    raise RuntimeError("GPT call failed after retries.")

def generate_ai_suggestions(text):
    prompt = f"""
    Review the following transcription and provide suggestions for improvement.
    Focus on removing filler words, grammar/spelling corrections, and awkward phrasing.

    {text}
    """
    return gpt_with_fallback(prompt)

def generate_show_notes(text):
    prompt = f"""
    Generate clear, concise podcast show notes based on this transcript:

    {text}
    """
    return gpt_with_fallback(prompt)

def transcribe_with_whisper(audio_path: str) -> str:
    try:
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return response.text
    except Exception as e:
        logger.error(f"Error in Whisper transcription: {str(e)}")
        return ""

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

def detect_filler_words(transcription):
    filler_words = [
        "um", "uh", "ah", "like", "you know", "so", "well", "I mean",
        "sort of", "kind of", "okay", "right"
    ]
    sentences = transcription.split(". ")
    return [
        sentence for sentence in sentences
        if any(re.search(rf"\\b{word}\\b", sentence, re.IGNORECASE) for word in filler_words)
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

def get_sentence_timestamps(sentence, word_timings, prev_end_time=0.0):
    def normalize(word):
        return word.strip().lower().strip(",.?!():;\"'")

    words = [normalize(w) for w in sentence.split()]
    if not words:
        return {"start": prev_end_time, "end": prev_end_time + 2.0}

    first_word = words[0]
    last_word = words[-1]

    start = next(
        (w["start"] for w in word_timings if normalize(w["word"]) == first_word and w["start"] >= prev_end_time),
        prev_end_time
    )
    end = next(
        (w["end"] for w in word_timings if normalize(w["word"]) == last_word and w["end"] >= start),
        start + 2.0
    )

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
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional podcast assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating show notes: {e}")
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
        output = gpt_with_fallback(prompt, primary_model="gpt-4", fallback_model="gpt-3.5-turbo-16k")
        # Clean up formatting
        lines = [line.strip("•–—-• \n\"") for line in output.split("\n") if line.strip()]
        return "\n\n".join(lines[:3])
    except Exception as e:
        logger.error(f"Error generating quotes: {e}")
        return f"Error generating quotes: {str(e)}"

def generate_quote_images_dalle(quotes: List[str]) -> List[str]:
    urls = []
    for quote in quotes:
        prompt = f"Create a visually striking, artistic background that reflects this quote’s emotion: \"{quote}\". No text in the image."
        try:
            response = client.images.generate(
                prompt=prompt,
                model="dall-e-3",
                n=1,
                size="1024x1024"
            )
            url = response.data[0].url
            urls.append(url)
        except Exception as e:
            logger.error(f"Failed to generate image for quote: {quote} | Error: {e}")
            urls.append("")
    return urls

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def render_quote_images_local(quotes: List[str]) -> List[str]:
    output_dir = os.path.join(BASE_DIR, "src", "Frontend", "static", "quote_images")
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    available_templates = list(FONT_MAPPING.keys())
    random.shuffle(available_templates)

    used_templates = set()
    i = 0  # Index för quote

    while i < len(quotes) and len(image_paths) < 3 and available_templates:
        template_key = available_templates.pop()
        template_name = f"{template_key}.jpg"
        layout_key = template_name

        # Skip duplicates
        if template_key in used_templates:
            continue
        used_templates.add(template_key)

        font_name = FONT_MAPPING.get(template_key)
        image_path = find_image_path(template_name, TEMPLATE_DIR)
        font_path = get_matching_font_path(font_name, FONT_FOLDER)

        if not image_path or not os.path.exists(image_path):
            logger.warning(f"⚠️ Skipped {template_key} — image not found")
            continue
        if not font_path:
            logger.warning(f"⚠️ Skipped {template_key} — font not found or mapping missing")
            continue
        if layout_key not in LAYOUTS:
            logger.warning(f"⚠️ Skipped {template_key} — no layout found in template_layouts.json")
            continue

        try:
            image = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(font_path, 40)

            def wrap(text, font, max_width=400):
                words = text.split()
                lines = []
                if not words:
                    return ""
                line = words.pop(0)
                for word in words:
                    test = f"{line} {word}"
                    if draw.textlength(test, font=font) <= max_width:
                        line = test
                    else:
                        lines.append(line)
                        line = word
                lines.append(line)
                return "\n".join(lines)

            wrapped = wrap(quotes[i], font)
            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
            x = LAYOUTS[layout_key]["x"]
            y = LAYOUTS[layout_key]["y"] - (bbox[3] - bbox[1]) // 2

            # Draw text with shadow
            draw.multiline_text((x+2, y+2), wrapped, font=font, fill=(0, 0, 0, 180), anchor="mm", align="center")
            draw.multiline_text((x, y), wrapped, font=font, fill=(255, 255, 255, 255), anchor="mm", align="center")

            output_path = os.path.join(output_dir, f"quote_local_{i+1}.jpg")
            image.convert("RGB").save(output_path)
            image_paths.append(f"/static/quote_images/quote_local_{i+1}.jpg")
            logger.info(f"✅ Saved: {output_path} with font {os.path.basename(font_path)}")

            i += 1

        except Exception as e:
            logger.error(f"❌ Error rendering template {template_key}: {e}")

    if len(image_paths) < 3:
        logger.warning(f"⚠️ Only {len(image_paths)} quote images generated (wanted 3).")

    return image_paths

def fetch_sfx_for_emotion(
    emotion: str,
    category: str,
    *,
    loop_src_seconds: int = 8,
    target_duration:  int = 30,
    crossfade_ms:     int = 250
) -> List[str]:
    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {"xi-api-key": ELEVENLABS_API_KEY,
               "Content-Type": "application/json"}
    payload = {
        "text":
            f"Create a perfectly seamless {loop_src_seconds}-second loop of "
            f"ambient background music for a {category} podcast with a "
            f"{emotion} mood. The first and last 250 ms must share the same pad tone.",
        "duration_seconds": loop_src_seconds,
        "prompt_influence": 1
    }

    res = requests.post(url, headers=headers, json=payload)
    if "audio/mpeg" not in res.headers.get("Content-Type", ""):
        logger.warning("ElevenLabs returnerade inte audio/mpeg – ingen SFX.")
        return []

    seg = AudioSegment.from_file(BytesIO(res.content), format="mp3")

    if crossfade_ms:
        head = seg[:crossfade_ms].fade_out(crossfade_ms)
        tail = seg[-crossfade_ms:].fade_in(crossfade_ms)
        seg  = head.overlay(tail) + seg[crossfade_ms:-crossfade_ms]

    need_ms  = target_duration * 1000
    repeats  = math.ceil(need_ms / len(seg))
    long_seg = (seg * repeats)[:need_ms]

    buf = BytesIO()
    long_seg.export(buf, format="mp3", bitrate="192k")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return [f"data:audio/mpeg;base64,{b64}"]

def suggest_sound_effects(
    emotion_data,
    *,
    category: str = "general",
    target_duration: int = 30
):
    cache, suggestions = {}, []
    for entry in emotion_data:
        emotion = entry["emotions"][0]["label"]
        if emotion not in cache:
            cache[emotion] = fetch_sfx_for_emotion(
                emotion, category, target_duration=target_duration
            )
        suggestions.append({
            "timestamp_text": entry["text"],
            "emotion":       emotion,
            "sfx_options":   cache[emotion]
        })
    return suggestions

def mix_background(
    original_wav_bytes: bytes,
    bg_b64_url: str,
    *,
    bg_gain_db: float = -45.0
) -> bytes:
    original = AudioSegment.from_file(BytesIO(original_wav_bytes), format="wav")

    bg_mp3   = base64.b64decode(bg_b64_url.split(",", 1)[1])
    bg_seg   = AudioSegment.from_file(BytesIO(bg_mp3), format="mp3") + bg_gain_db

    repeats  = math.ceil(len(original) / len(bg_seg))
    bg_long  = (bg_seg * repeats)[:len(original)]

    mixed    = original.overlay(bg_long)

    out_buf  = BytesIO()
    mixed.export(out_buf, format="wav")
    return out_buf.getvalue()

def pick_dominant_emotion(emotion_data: list) -> str:
    labels = [e["emotions"][0]["label"] for e in emotion_data]
    return Counter(labels).most_common(1)[0][0] if labels else "neutral"

def get_osint_info(guest_name: str) -> str:
    """
    Uses GPT-4 to retrieve OSINT-style background information about a guest.
    """
    client = OpenAI()

    prompt = f"Find detailed and recent public information about {guest_name}. Focus on professional achievements, background, and any recent mentions in news or social media."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are OSINT-GPT, an expert in gathering open-source intelligence."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

def create_podcast_scripts_paid(osint_info: str, guest_name: str, transcript: str = "") -> str:
    prompt = f"""
You are a professional podcast scriptwriter.

Write a compelling **podcast intro and outro** based on the following episode transcript.

Start with the **topics and tone** from the transcript, then enrich it with background details about the guest ({guest_name}).

Transcript:
{transcript}

Guest background info:
{osint_info}

The intro should briefly tease the main topic(s) of the episode, using an engaging tone.
The outro should reflect on the discussion and invite the listener to tune in again.
"""

    try:
        return gpt_with_fallback(prompt, primary_model="gpt-4", fallback_model="gpt-3.5-turbo-16k").strip()
    except Exception as e:
        logger.error(f"Error generating intro/outro: {e}")
        return f"Error: {str(e)}"

def text_to_speech_with_elevenlabs(script: str, voice_id: str = "TX3LPaxmHKxFdv7VOQHJ") -> bytes:

    api_key = os.getenv("ELEVENLABS_API_KEY")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": script,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.content 
    else:
        raise RuntimeError(f"ElevenLabs error {response.status_code}: {response.text}")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

TEMPLATE_DIR = os.path.join(BASE_DIR, "src", "frontend", "static", "images", "clean_templates")
LAYOUTS_FILE = os.path.join(BASE_DIR, "src", "frontend", "static", "json", "template_layouts.json")
FONT_MAPPING_FILE = os.path.join(BASE_DIR, "src", "frontend", "static", "csv", "font_mapping_clean.csv")
FONT_FOLDER = os.path.join(BASE_DIR, "src", "frontend", "static", "fonts_flat")

# === Ladda mallpositioner ===
try:
    with open(LAYOUTS_FILE, encoding="utf-8") as f:
        LAYOUTS = json.load(f)
except FileNotFoundError:
    print(f"⚠️  Warning: Layouts file not found at {LAYOUTS_FILE}")
    LAYOUTS = {}

# === Ladda fontmapping ===
FONT_MAPPING = {}
try:
    with open(FONT_MAPPING_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["Filename"].strip()
            font_name = row["Font name"].strip()
            FONT_MAPPING[filename] = font_name
except FileNotFoundError:
    print(f"❌ Font mapping file not found at {FONT_MAPPING_FILE}")

def find_image_path(filename, template_dir):
    path = os.path.join(template_dir, filename)
    return path if os.path.exists(path) else None

def get_matching_font_path(font_name, font_folder):
    if not font_name:
        return None
    font_files = [f for f in os.listdir(font_folder) if f.lower().endswith(('.ttf', '.otf'))]
    
    # Försök exakt startswith-match först
    for f in font_files:
        if f.lower().startswith(font_name.lower()):
            return os.path.join(font_folder, f)

    # Fallback till fuzzy match
    matches = difflib.get_close_matches(font_name.lower(), [f.lower() for f in font_files], n=1, cutoff=0.6)
    if matches:
        best_match = next((f for f in font_files if f.lower() == matches[0]), None)
        if best_match:
            return os.path.join(font_folder, best_match)

    logger.warning(f"⚠️ No matching font found for: {font_name}")
    return None