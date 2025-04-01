# src\backend\utils\text_utils.py
import openai
import logging
import subprocess
import re
import subprocess
from transformers import pipeline
import os
from pathlib import Path
import requests
from typing import List

API_BASE_URL = os.getenv("API_BASE_URL")
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
    
# Emotion/Sentence classifiers (load only once)
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

        # 🧼 Clean extra bullet points or symbols if needed
        lines = [line.strip("•–—-• \n\"") for line in quotes_raw.split("\n") if line.strip()]
        return "\n\n".join(lines[:3])  # Join into one string

    except Exception as e:
        logger.error(f"❌ Error generating quotes: {e}")
        return f"Error generating quotes: {str(e)}"

def generate_quote_images(quotes: List[str]) -> List[str]:
    """
    Generate DALL·E 3 images for a list of quotes and return image URLs.

    :param quotes: A list of short quotes (1–2 sentences each).
    :return: List of image URLs (or empty string for failed ones).
    """
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
