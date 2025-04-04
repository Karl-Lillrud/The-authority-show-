# ai_utils.py
import re
import openai
import logging
from textblob import TextBlob
from textstat import textstat

logger = logging.getLogger(__name__)

def remove_filler_words(text: str) -> str:
    """
    Removes timestamps and speaker tags, then uses GPT-4 to remove filler words.
    """
    # Remove timestamps (e.g. 00:01, [00:01:23], (00:00), etc.)
    text = re.sub(r'\[?\(?\b\d{1,2}:\d{2}(?::\d{2})?\b\)?\]?', '', text)

    # Remove speaker tags (e.g., "Speaker 1:", "Interviewer:", etc.)
    text = re.sub(r'\b(Speaker \d+|Interviewer|Interviewee|Host|Guest):', '', text, flags=re.IGNORECASE)

    # Strip extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Ask GPT to remove filler words
    prompt = f"Remove unnecessary filler words (um, uh, ah, like, you know, etc.) from this text:\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error removing filler words: {str(e)}")
        return text  # fallback

def analyze_sentiment(text: str) -> str:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

def calculate_clarity_score(cleaned_transcript: str) -> str:
    """
    Calculate clarity: Flesch-Kincaid + filler penalty, etc.
    Return a text explanation.
    """
    # Example
    readability_score = textstat.flesch_kincaid_grade(cleaned_transcript)
    filler_count = sum(cleaned_transcript.lower().count(w) for w in ["um","uh","like","you know"])
    filler_penalty = filler_count * 0.2
    clarity_val = 100 - readability_score - filler_penalty
    return (
        f"Clarity Score: {max(0, clarity_val)}\n"
        f"Filler Words Detected: {filler_count}\n"
        f"Readability (Flesch-Kincaid Score): {readability_score}\n"
        f"Filler Word Penalty: {filler_penalty}\n"
    )
