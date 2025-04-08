# src/backend/utils/text_utils.py

import os
import re
import openai
import logging
import subprocess
import base64
import random
from transformers import pipeline
import streamlit as st  # Needed for download_button_text

API_BASE_URL = os.getenv("API_BASE_URL")
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
    """
    Translate the given text to the target language using GPT.
    """
    if not text.strip():
        return ""

    prompt = f"Translate the following transcript to {target_language}:\n\n{text}"

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
        logger.error(f"❌ Translation failed: {str(e)}")
        return f"Error during translation: {str(e)}"

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



def generate_quote_images(quotes: list[str]) -> list[str]:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    urls = []

    STYLE_REFERENCES = [
        "https://drive.google.com/uc?export=view&id=1Iz9QF_2KrmkRnUSDbDDf44QBCZJAOCNC",
        "https://drive.google.com/uc?export=view&id=1tUZSOpyiFgMJJdeDLjWu6UlhOvOGbJ2h",
        "https://drive.google.com/uc?export=view&id=1LOJHp71b6On3mvKtgdHIVlJ_WSNFHLFs",
        "https://drive.google.com/uc?export=view&id=1I6TWdJ4kJChY2pqZPn4zcI05pZIPOgKm",
        "https://drive.google.com/uc?export=view&id=1OBUIrn1MnVVwLawXvIwG9_OoEz83jeJJ",
        "https://drive.google.com/uc?export=view&id=1iUxfmwJsVqNLYDx6Ljbg9MyaSKXQpJWQ"
            # Add more as needed
    ]

    for quote in quotes:
        reference_image = random.choice(STYLE_REFERENCES)

        # 🎨 Define multiple prompt templates
        prompt_variants = [
            f"Design a podcast-themed quote card background with a clean layout and modern style. "
            f"Leave a clearly defined empty space in the center or top half for a quote. "
            f"Use this image as a reference for style: {reference_image}. "
            f"The background should visually reflect the meaning or feeling of this quote: \"{quote}\". "
            f"Do not include any text in the image. This quote is for layout context only.",

            f"Create a modern, minimalistic podcast quote card background. Make sure the layout includes open space for a future quote. "
            f"Use this reference image for aesthetic inspiration: {reference_image}. "
            f"Let the visual theme be influenced by the emotional or thematic content of this quote: \"{quote}\". "
            f"Do not include any text in the image. This quote is for layout context only.",

            f"Generate a social media-ready podcast quote background with room for text in the center or top. "
            f"The composition should reflect the tone or message of the following quote: \"{quote}\". "
            f"Use the visual style of this reference image: {reference_image}. "
            f"Do not include any text in the image. This quote is for layout context only.",

            f"Create an artistic podcast quote card background using this reference image for style: {reference_image}. "
            f"The visual atmosphere should echo the energy or sentiment of this quote: \"{quote}\". "
            f"Leave visual space for a text overlay, but do not include any text. This quote is for layout context only."
        ]


        prompt = random.choice(prompt_variants)

        try:
            response = openai.Image.create(
                prompt=prompt,
                model="dall-e-3",
                n=1,
                size="1024x1024"
            )
            generated_url = response["data"][0]["url"]
            urls.append(generated_url)
        except Exception as e:
            logger.error(f"❌ Failed to generate image for quote: {quote} | Error: {e}")
            urls.append("")

    return urls
