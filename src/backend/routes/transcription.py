#  * Developer Full Stack: Peter Molén 
#  *
#  * Create Date: 2025-03-03
#  *     Program : transcription.py
#  *   Path Name : THE-AUTHORITY-SHOW-/src/backend/
#  *       
#          Tools : Python, Flask, OpenAI GPT-4, ElevenLabs, Whisper, FFmpeg, 
#          Pyannote, Hugging Face Transformers, Azure Speech-to-Text, TextBlob, 
#          Matplotlib, NumPy, SoundFile, Noisereduce, TextStat, Torchaudio
#  *
#  * Description:
#  * - AI-powered transcription and audio/video processing tool.
#  * - Supports transcription with speaker diarization using Whisper and ElevenLabs.
#  * - Performs AI-enhanced noise reduction, clarity improvement, and auto-editing.
#  * - Detects filler words, sentiment analysis, and background noise classification.
#  * - Generates AI-powered show notes and marketing snippets.
#  * - Provides audio and video enhancement features, including AI-driven analysis.
#  * - Allows timestamp-based audio and video trimming using FFmpeg.
#  * - Supports multi-language translation using OpenAI API.






#backend for PodManager AI Transcription tool
from flask import Blueprint, request, jsonify, Response, send_file
import whisper
import os
import time
import torchaudio
import azure.cognitiveservices.speech as speechsdk
from pyannote.audio import Pipeline
from dotenv import load_dotenv
from threading import Thread
import json
import openai
import soundfile as sf
import noisereduce as nr
from textblob import TextBlob
import matplotlib.pyplot as plt
import numpy as np
import subprocess
from transformers import pipeline
from textstat import textstat
import logging
import wave
from io import BytesIO
from elevenlabs.client import ElevenLabs
import cv2
from PIL import Image
import torch
# from transformers import CLIPProcessor, CLIPModel
import re
from datetime import datetime
from backend.database.mongo_connection import get_db, get_fs
from bson import ObjectId  
import gridfs
import tempfile


#initatlizing section

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
# Load environment variables
load_dotenv()

# API Keys
HF_TOKEN = os.getenv("HF_TOKEN")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not HF_TOKEN or not AZURE_SPEECH_KEY or not AZURE_REGION or not OPENAI_API_KEY:
    raise ValueError("❌ API keys are missing. Add them to your .env file.")

# Create Flask Blueprint
transcription_bp = Blueprint("transcription", __name__)


# Initialize emotion analysis model from HuggingFace
emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")


# Use a smaller, more efficient model like DistilBERT (for ai audio cetrainly level)
classifier = pipeline("zero-shot-classification", model="nreimers/MiniLM-L6-H384-uncased")


# Initialize ElevenLabs client with API key
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))



# Initialize MongoDB and GridFS
db = get_db()  # Get the database object from mongo_connection.py
fs = get_fs()  # Get the GridFS object from mongo_connection.py

# Create TTL index inside metadata.upload_timestamp // delete files in mongo db after 24h
def create_ttl_index():
    """Ensure TTL index only applies to transcription files."""
    db = get_db()  # Retrieve database connection inside the function
    db.fs.files.create_index(
        [("metadata.upload_timestamp", 1)], 
        expireAfterSeconds=86400,  # 24 hours
        partialFilterExpression={"metadata.type": "transcription"},  # Only apply to transcription files
        name="transcription_TTL"
    )
    print("✅ TTL Index for 'transcription' files is set.")

# Call the function at startup
create_ttl_index()


# Define a route to retrieve a file from GridFS by its file_id.
# The file_id is passed as part of the URL, and it will be used to locate the file in GridFS.
# The method for this route is GET, meaning this route will be used to fetch a file.

# audio
@transcription_bp.route("/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    logger.info(f"📢 Request received to fetch file with ID: {file_id} (Type: {type(file_id)})")

    try:
        # Log file_id type before conversion
        logger.info(f"🔍 Raw file_id received: {file_id} (Type: {type(file_id)})")

        # Convert file_id to ObjectId if needed
        try:
            object_id = ObjectId(file_id)
            logger.info(f"🔄 Converted file_id to ObjectId: {object_id}")
        except Exception as e:
            object_id = file_id  # Use as a string if ObjectId conversion fails
            logger.warning(f"⚠️ Using string ID instead: {file_id}. Error: {e}")

        # Log MongoDB file search attempt
        logger.info(f"🔍 Searching for file in GridFS with ID: {object_id} (Type: {type(object_id)})")

        # Fetch file from GridFS
        file_obj = fs.get(object_id)

        if not file_obj:
            logger.error(f"❌ File with ID {object_id} not found in GridFS.")
            return jsonify({"error": "File not found."}), 404

        # Read file data
        file_data = file_obj.read()
        logger.info(f"✅ File found in GridFS: {file_obj.filename}")
        logger.info(f"📏 File size: {len(file_data)} bytes")
        logger.info(f"📂 File metadata: {file_obj.metadata if hasattr(file_obj, 'metadata') else 'No metadata available'}")

        # Send file back to frontend
        logger.info(f"📤 Sending file {file_obj.filename} (Size: {len(file_data)} bytes) to frontend")
        return Response(file_data, mimetype="audio/wav", headers={"Content-Disposition": "attachment; filename=enhanced_audio.wav"})

    except gridfs.errors.NoFile:
        logger.error(f"❌ File with ID {file_id} not found in GridFS.")
        return jsonify({"error": "File not found."}), 404

    except Exception as e:
        logger.error(f"❌ Error fetching file with ID {file_id}: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500



#video
@transcription_bp.route("/get_video/<video_id>", methods=["GET"])
def get_video(video_id):
    """Serve the processed video from MongoDB GridFS."""
    logger.info(f"📢 Request received to fetch video with ID: {video_id}")

    try:
        # Convert video_id to ObjectId
        try:
            object_id = ObjectId(video_id)
            logger.info(f"🔄 Converted video_id to ObjectId: {object_id}")
        except Exception as e:
            logger.warning(f"⚠️ Using string ID instead: {video_id}. Error: {e}")
            object_id = video_id  # Use as a string if ObjectId conversion fails

        # Fetch video from GridFS
        video_file = fs.get(object_id)

        if not video_file:
            logger.error(f"❌ Video with ID {object_id} not found in GridFS.")
            return jsonify({"error": "Video not found."}), 404

        # Read video data
        file_data = video_file.read()
        logger.info(f"✅ Video found in GridFS: {video_file.filename} (Size: {len(file_data)} bytes)")

        # Ensure the file is an MP4
        if not video_file.filename.endswith(".mp4"):
            logger.warning(f"⚠️ Requested file is not an MP4: {video_file.filename}")
            return jsonify({"error": "File is not a video."}), 400

        # Return the video file to the client
        return Response(
            file_data,
            mimetype="video/mp4",
            headers={"Content-Disposition": f"inline; filename={video_file.filename}"}
        )

    except gridfs.errors.NoFile:
        logger.error(f"❌ Video with ID {video_id} not found in GridFS.")
        return jsonify({"error": "Video not found."}), 404

    except Exception as e:
        logger.error(f"❌ Error fetching video with ID {video_id}: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500

#************************************************************************************



# Transcription route


# AI Suggestions
def generate_ai_suggestions(text):
    """ Generate AI suggestions to improve transcription, remove filler words, and enhance readability """
    prompt = f"""
    Review the following transcription and provide suggestions for improvement. Focus on:
    - Removing filler words like "um", "ah", "you know", and similar.
    - Fixing any grammar or spelling mistakes.
    - Rewriting unclear or awkward sentences for better readability.
    - Removing repetitive sentences or off-topic content.
    Provide a cleaner version of the transcription and a list of suggested changes.
    \n\n{text}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]

    # AI Show Notes and Marketing Snippets
def generate_show_notes(text):
    """ Generate AI show notes and marketing snippets based on the transcription, including key takeaways and highlights """
    prompt = f"""
    Generate concise and engaging show notes or a summary for this transcription. Include:
    - A brief description of the episode’s key topics and takeaways.
    - Actionable insights or tips mentioned in the episode.
    - Any quotes, key moments, or funny exchanges (e.g., "(laughs)").
    - Generate 2-3 marketing snippets that could be used on social media or promotional material, keeping them short and catchy.
    Limit the summary to 200-300 words for the show notes, and make the marketing snippets 1-2 sentences long.
    \n\n{text}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]


@transcription_bp.route("/transcribe", methods=["POST"])
def transcribe():
    """ Transcribe both audio and video files while keeping the original working structure for audio """

    if "file" not in request.files:
        logging.error("No file provided.")
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename
    file_ext = os.path.splitext(filename)[-1].lower()
    
    # Determine if it's a video file
    is_video = file_ext in ["mp4", "mov", "avi", "mkv", "webm"]

    file_id = None
    extracted_audio = None

    try:
        if is_video:
            # ✅ Extract audio BEFORE saving to MongoDB
            temp_video_path = f"/tmp/{filename}"
            temp_audio_path = temp_video_path.replace(file_ext, ".wav")

            with open(temp_video_path, "wb") as temp_video:
                temp_video.write(file.read())

            # Use FFmpeg to extract audio
            ffmpeg_command = f'ffmpeg -i "{temp_video_path}" -ac 1 -ar 16000 "{temp_audio_path}" -y'
            subprocess.run(ffmpeg_command, shell=True, check=True)

            # Read extracted audio into memory
            with open(temp_audio_path, "rb") as audio_file:
                extracted_audio = audio_file.read()

            # Clean up temporary files
            os.remove(temp_video_path)
            os.remove(temp_audio_path)

        else:
            # ✅ If it's audio, just read it
            extracted_audio = file.read()

        # ✅ Save extracted (or direct) audio to MongoDB
        file_id = fs.put(
            extracted_audio,
            filename=filename.replace(file_ext, ".wav"),
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
        )
        logging.info(f"📤 File uploaded to MongoDB GridFS with ID: {file_id}")

        # ✅ Retrieve the file for ElevenBase processing
        file_data = fs.get(file_id).read()
        logging.info(f"📥 File retrieved from MongoDB GridFS with ID: {file_id}, size: {len(file_data)} bytes")

        audio_data = BytesIO(file_data)  # Convert to BytesIO for ElevenBase processing

        # ✅ Send audio to ElevenBase for transcription
        logging.info("🎙 Sending audio to ElevenBase for transcription.")
        transcription_result = client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            num_speakers=2,
            diarize=True,
            timestamps_granularity="word"
        )

        # ✅ Process transcription output
        raw_transcription_with_timestamps = []
        words_with_timestamps = transcription_result.words
        transcription_no_fillers = transcription_result.text.strip() if transcription_result.text else "N/A"

        speaker_map = {}
        speaker_counter = 1

        for word_info in words_with_timestamps:
            word = word_info.text.strip()
            start_time = round(word_info.start, 2)
            end_time = round(word_info.end, 2)
            speaker_id = word_info.speaker_id

            if speaker_id not in speaker_map:
                speaker_map[speaker_id] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            speaker_label = speaker_map[speaker_id]

            if word:
                raw_transcription_with_timestamps.append(f"[{start_time}-{end_time}] {speaker_label}: {word}")

        raw_transcription = " ".join(raw_transcription_with_timestamps)

        # ✅ Generate AI suggestions and show notes
        ai_suggestions = generate_ai_suggestions(transcription_no_fillers)
        show_notes = generate_show_notes(transcription_no_fillers)

        return jsonify({
            "raw_transcription": raw_transcription,  # ✅ Now correctly mapped
            "ai_suggestions": ai_suggestions,
            "show_notes": show_notes
        })

    except Exception as e:
        logging.error(f"❌ Error during transcription: {e}", exc_info=True)
        return jsonify({"error": "Transcription failed", "details": str(e)}), 500





@transcription_bp.route("/translate", methods=["POST"])
def translate():
    """ Translate text using OpenAI API """
    data = request.json
    text = data.get("text")
    target_language = data.get("language")

    if not text or not target_language:
        return jsonify({"error": "Missing text or language"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Translate this to {target_language}:\n{text}"}]
        )
        translated_text = response["choices"][0]["message"]["content"]
        return jsonify({"translated_text": translated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#************************************************************************************

# **Audio Enhancement Route**

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@transcription_bp.route("/audio/enhancement", methods=["POST"])
def audio_enhancement():
    """Enhance audio quality using noise reduction and volume normalization via FFmpeg."""
    
    logger.info("Starting audio enhancement process...")

    if "audio" not in request.files:
        logger.error("No audio file provided.")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    logger.info(f"Received file: {audio_file.filename}, content type: {audio_file.content_type}")

    try:
        # Step 1: Save the original file to MongoDB GridFS with upload_timestamp
        file_id = fs.put(
            audio_file.read(), 
            filename=audio_file.filename, 
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # ✅ Ensure TTL works
        )
        logger.info(f"📤 Original file saved to MongoDB GridFS with ID: {file_id}")

        # Step 2: Retrieve the file from GridFS for enhancement
        file_data = fs.get(file_id).read()  # Get the file from GridFS
        logger.info(f"📥 Retrieved original file from GridFS with ID: {file_id}, size: {len(file_data)} bytes")

        # Step 3: Save to a temporary file for FFmpeg processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        logger.info(f"📂 Temporary file created at: {temp_file_path}")

        # Output file path for the enhanced audio
        enhanced_audio_path = temp_file_path.replace(".wav", "_enhanced.wav")

        # Step 4: Enhance audio with FFmpeg
        logger.info(f"🎛 Enhancing audio with FFmpeg from {temp_file_path}")
        enhanced_audio = enhance_audio_with_ffmpeg(temp_file_path, enhanced_audio_path)

        if enhanced_audio:
            logger.info(f"✅ Enhanced audio saved to temporary file: {enhanced_audio_path}")

            # Step 5: **Detect background noise using temporary file**
            noise_detection_result = detect_background_noise(temp_file_path)

            # Step 6: **Transcribe audio before calculating speech rate**
            with open(temp_file_path, "rb") as f:
                response = openai.Audio.transcribe("whisper-1", file=f)
            transcript = response["text"]

            # Step 7: **Calculate speech rate now that transcript is available**
            speech_rate = calculate_speech_rate(temp_file_path, transcript)

            # Step 8: Save the enhanced audio back to MongoDB GridFS
            with open(enhanced_audio_path, "rb") as enhanced_file:
                enhanced_audio_data = enhanced_file.read()
            
            enhanced_file_id = fs.put(enhanced_audio_data, filename=f"enhanced_{audio_file.filename}")
            logger.info(f"🔍 Enhanced audio saved to GridFS with ID: {enhanced_file_id} (Type: {type(enhanced_file_id)})")

            # Cleanup temp files
            os.remove(temp_file_path)
            os.remove(enhanced_audio_path)

            return jsonify({
                "message": "✅ Audio enhancement completed!",
                "enhanced_audio": str(enhanced_file_id),  # Send back the ID of the enhanced file
                "background_noise": noise_detection_result,  # ✅ Background noise now works
                "speech_rate": speech_rate  # ✅ Speech rate now works
            })
        else:
            logger.error("❌ Error enhancing audio with FFmpeg.")
            return jsonify({"error": "Error enhancing audio with FFmpeg."}), 500

    except Exception as e:
        logger.error(f"❌ Error during enhancement: {str(e)}")
        return jsonify({"error": f"Error during enhancement: {str(e)}"}), 500 






#functions for audio anylziz:
def enhance_audio_with_ffmpeg(input_file_path, output_file_path):
    """Enhance audio using FFmpeg for noise reduction and volume normalization with hum removal."""
    try:
        # FFmpeg command for:
        # - Notch filter to remove hum at 50 Hz and 60 Hz (stronger gain reduction)
        # - General noise reduction filter (arnndn) to remove background noise
        # - High-pass filter to remove unwanted low-frequency rumbling
        # - Loudness normalization (loudnorm) to ensure consistent volume

        ffmpeg_command = [
            "ffmpeg",
            "-i", input_file_path,  # Input file path
            "-af", (
                "arnndn=nf=-40,"  # General noise reduction with noise floor of -40 dB (stronger)
                "highpass=f=50,"  # Apply high-pass filter at 50 Hz to remove low-frequency hum
                "highpass=f=60,"  # Apply high-pass filter at 60 Hz to remove low-frequency hum
                "highpass=f=70,"  # Apply high-pass filter at 70 Hz to remove extra low frequencies (optional)
                "equalizer=f=50:t=q:w=1:g=-40,"  # Notch filter at 50 Hz to remove hum with stronger gain reduction
                "equalizer=f=60:t=q:w=1:g=-40,"  # Notch filter at 60 Hz to remove hum with stronger gain reduction
                "highpass=f=100,"  # High-pass filter at 100 Hz to remove rumbling low frequencies (optional)
            ),
            "-filter:a", "loudnorm",  # Volume normalization filter
            output_file_path  # Output file path
        ]

        # Run the command
        logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_command)}")
        subprocess.run(ffmpeg_command, check=True)

        logger.info(f"📢 Audio enhanced and saved to: {output_file_path}")
        return output_file_path

    except Exception as e:
        logger.error(f"❌ Error during FFmpeg processing: {e}")
        return None 




# Function to remove filler words using GPT-4
def remove_filler_words(text):
    """ AI removes filler words like 'um', 'ah', 'like', etc. """
    prompt = f"Remove unnecessary filler words (such as 'um', 'ah', 'like', etc.) from the following transcription and improve clarity:\n{text}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]

# Function to calculate clarity score
def calculate_clarity_score(transcript):
    """ Calculate clarity score based on Flesch-Kincaid readability and filler word removal. """
    # Calculate Flesch-Kincaid readability score
    readability_score = textstat.flesch_kincaid_grade(transcript)
    
    # Count filler words (simple method)
    filler_word_count = transcript.lower().count('um') + transcript.lower().count('ah') + transcript.lower().count('like') + transcript.lower().count('you know')
    filler_penalty = filler_word_count * 0.2
    
    clarity_score = 100 - filler_penalty - readability_score  # Final clarity score
    
    # Ensure score doesn't go below 0
    clarity_score = max(0, clarity_score)
    
    return clarity_score, filler_word_count, readability_score, filler_penalty

#function to detect background noise
def detect_background_noise(audio_path, threshold=1000, max_freq=500):
    """Detects background noise in a WAV file by analyzing its frequency content using FFT."""
    try:
        with wave.open(audio_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

        fft_result = np.fft.fft(audio_array)
        fft_freq = np.fft.fftfreq(len(fft_result), 1/sample_rate)
        magnitude = np.abs(fft_result)
        low_freqs = magnitude[:max_freq]
        avg_magnitude = np.mean(low_freqs)

        if avg_magnitude > threshold:
            hum_detected = False
            if np.any((fft_freq > 49) & (fft_freq < 51)) or np.any((fft_freq > 59) & (fft_freq < 61)):
                hum_detected = True

            if hum_detected:
                return "Background noise detected: Hum (50 Hz or 60 Hz)"
            elif np.any((fft_freq > 100) & (fft_freq < 1000)):
                return "Background noise detected: Traffic or environmental noise"
            else:
                return "Background noise detected: Broadband noise (static/wind)"

        return "No significant background noise detected"

    except Exception as e:
        logging.error(f"Error in background noise detection: {e}")
        return f"Error in background noise detection: {str(e)}" 

        
# Speech rate calculation (WPM) (updated to retrieve audio from GridFS)
def calculate_speech_rate(audio_path, transcript):
    """
    Calculate speech rate (WPM) based on transcription and audio duration.
    """
    try:
        with wave.open(audio_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            duration = wf.getnframes() / sample_rate  # Convert frames to seconds

        # Ensure there's a valid transcript
        if not transcript.strip():
            return "Speech rate calculation skipped (empty transcript)."

        # Count words in the transcript
        word_count = len(transcript.split())

        # Calculate words per minute (WPM)
        words_per_minute = word_count / (duration / 60)
        return f"Speech rate: {words_per_minute:.2f} WPM"

    except Exception as e:
        logging.error(f"❌ Error during speech rate calculation: {e}")
        return "Error calculating speech rate." 


    
# API route for audio analysis
@transcription_bp.route("/audio_analysis", methods=["POST"])
def audio_analysis():
    """Analyze emotion, sentiment, and clarity in the transcription."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]

    try:
        # Step 1: Save audio file to MongoDB GridFS with upload_timestamp
        file_id = fs.put(
            audio_file.read(), 
            filename=audio_file.filename, 
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # ✅ Ensure TTL works
        )
        logger.info(f"📤 Audio file saved to MongoDB GridFS with ID: {file_id}")

        file_data = fs.get(file_id).read()  # Retrieve the file from GridFS for processing

        # Step 2: **Save to temporary file for processing**
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            temp_audio_file.write(file_data)
            temp_audio_file_path = temp_audio_file.name  # Get the temp file path

        logger.info(f"📝 Temporary file created for processing: {temp_audio_file_path}")

        # Step 3: **Transcribe audio (using Whisper or another model)**
        with open(temp_audio_file_path, "rb") as f:
            response = openai.Audio.transcribe("whisper-1", file=f)

        transcript = response["text"]

        # Step 4: Perform emotion analysis on the transcription
        emotion_result = emotion_analyzer(transcript)

        # Step 5: Perform sentiment analysis on the transcription using TextBlob
        blob = TextBlob(transcript)
        sentiment_score = blob.sentiment.polarity  # Positive, Neutral, Negative

        if sentiment_score > 0:
            sentiment = "Positive"
        elif sentiment_score < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # Step 6: Calculate clarity score
        cleaned_transcript = remove_filler_words(transcript)  # Remove filler words for clarity
        clarity_score, filler_word_count, readability_score, filler_penalty = calculate_clarity_score(cleaned_transcript)

        clarity_text = (
            f"Clarity Score: {clarity_score}\n"
            f"Filler Words Detected: {filler_word_count}\n"
            f"Readability (Flesch-Kincaid Score): {readability_score}\n"
            f"Filler Word Penalty: {filler_penalty}\n\n"
            "Tips to Improve Clarity:\n"
            "- Avoid filler words such as 'um', 'ah', 'like', 'you know', etc.\n"
            "- Keep sentences short and clear to improve readability.\n"
            "- Ensure the speech flows smoothly, without unnecessary pauses."
        )

        # Step 7: **Detect background noise using the temporary file**
        noise_detection_result = detect_background_noise(temp_audio_file_path)

        # Step 8: **Calculate speech rate (now that transcript is available)**
        speech_rate = calculate_speech_rate(temp_audio_file_path, transcript)

        # Step 9: **Return analysis results**
        result = {
            "message": "✅ Emotion, Sentiment, Clarity, Background Noise, and Speech Rate analysis completed!",
            "emotion": emotion_result[0]['label'],  # Emotion result
            "sentiment": sentiment,  # Sentiment result
            "clarity_score": clarity_text,  # Clarity score with plain text explanation
            "background_noise": noise_detection_result,  # ✅ Background noise now works
            "speech_rate": speech_rate  # ✅ Speech rate now works
        }

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}")
        result = {"error": f"Error during analysis: {str(e)}"}

    finally:
        # ✅ Ensure the temporary file is deleted after processing
        if os.path.exists(temp_audio_file_path):
            os.remove(temp_audio_file_path)
            logger.info(f"🗑️ Temporary file deleted: {temp_audio_file_path}")

    return jsonify(result)


    
#*************************************************************************************************************************


#audio clip enviroment:

# Function to check if a file already exists in MongoDB GridFS
def file_exists(filename):
    existing_file = fs.find_one({"filename": filename})
    return existing_file if existing_file else None

#get audio info
@transcription_bp.route("/get_audio_info", methods=["POST"])
def get_audio_info():
    """Generate waveform and get duration of uploaded audio file, now using MongoDB GridFS."""

    if "audio" not in request.files:
        logger.error("❌ ERROR: No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    try:
        # Retrieve the uploaded file
        audio_file = request.files["audio"]
        filename = audio_file.filename

        # Save the original file to MongoDB
        file_id = fs.put(
            audio_file.read(),
            filename=filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # Add type
        )

        # Retrieve the file from GridFS for processing
        file_data = fs.get(file_id).read()
        logger.info(f"📥 Retrieved original file from GridFS with ID: {file_id}")

        # Save to a temporary file for analysis
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        logger.info(f"📂 Temporary file created at: {temp_file_path}")

        # Load audio using SoundFile
        data, sample_rate = sf.read(temp_file_path)

        # Check if the audio is empty
        if data is None or len(data) == 0:
            logger.error("❌ ERROR: Loaded audio is empty")
            return jsonify({"error": "Loaded audio is empty"}), 500

        duration = len(data) / sample_rate
        logger.info(f"🕒 Audio duration: {duration} seconds")

        # Generate waveform image
        waveform_filename = f"waveform_{filename}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as wf_temp:
            waveform_path = wf_temp.name

        fig, ax = plt.subplots(figsize=(10, 3))
        time_axis = np.linspace(0, duration, num=len(data))
        ax.plot(time_axis, data, color="blue")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Amplitude")
        plt.savefig(waveform_path)
        plt.close(fig)

        # Save waveform to MongoDB GridFS with upload_timestamp
        with open(waveform_path, "rb") as wf:
            waveform_file_id = fs.put(
                wf.read(),
                filename=waveform_filename,
                metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # Add type
            )


        logger.info(f"📤 Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")


        logger.info(f"📤 Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")

        # Cleanup temp files
        os.remove(temp_file_path)
        os.remove(waveform_path)

        return jsonify({
            "duration": duration,
            "audio_file_id": str(file_id),  # Send correct file ID for actual audio
            "waveform": str(waveform_file_id)  # Send waveform file ID
            
        })

    except Exception as e:
        logger.error(f"❌ ERROR: Failed to process audio - {str(e)}")
        return jsonify({"error": f"Failed to process audio: {str(e)}"}), 500



@transcription_bp.route("/clip_audio", methods=["POST"])
def clip_audio():
    """Trim selected timestamps from an audio file using FFmpeg and avoid saving duplicate clipped files in MongoDB."""

    logger.info("📥 Received request for audio clipping.")

    # Log full request data
    logger.info(f"📡 Request JSON data: {request.json}")

    if not request.json:
        logger.error("❌ ERROR: No JSON data received in request.")
        return jsonify({"error": "No JSON data received"}), 400

    data = request.json
    file_id = data.get("file_id")
    clips_to_remove = data.get("clips")

    if not file_id:
        logger.error("❌ ERROR: No file_id provided in request.")
        return jsonify({"error": "No file_id provided"}), 400

    if not clips_to_remove or not isinstance(clips_to_remove, list):
        logger.error("❌ ERROR: No valid timestamps provided in request.")
        return jsonify({"error": "No valid timestamps provided"}), 400

    try:
        start_time = clips_to_remove[0].get("start")
        end_time = clips_to_remove[0].get("end")

        if start_time is None or end_time is None or start_time >= end_time:
            logger.error(f"❌ ERROR: Invalid timestamps received. Start: {start_time}, End: {end_time}")
            return jsonify({"error": "Invalid timestamps received"}), 400

        logger.info(f"🆔 Cutting audio file with MongoDB ID: {file_id}")
        logger.info(f"🕒 Cutting from {start_time}s to {end_time}s")

        # Retrieve file from MongoDB
        try:
            logger.info(f"📡 Fetching file from MongoDB GridFS with ID: {file_id}")
            file_data = fs.get(ObjectId(file_id)).read()
            logger.info(f"✅ Successfully fetched file from MongoDB. Size: {len(file_data)} bytes")
        except Exception as e:
            logger.error(f"❌ ERROR: Failed to fetch file {file_id} from MongoDB: {str(e)}")
            return jsonify({"error": f"Failed to fetch file from MongoDB: {str(e)}"}), 500

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name

        logger.info(f"📂 Temporary file created at: {temp_file_path}")

        # Define the output file
        clipped_audio_filename = f"clipped_{file_id}.wav"
        clipped_audio_path = temp_file_path.replace(".wav", "_clipped.wav")

        # **Check if clipped file already exists in MongoDB**
        existing_clipped_file = fs.find_one({"filename": clipped_audio_filename})

        if existing_clipped_file:
            clipped_file_id = existing_clipped_file._id
            logger.info(f"✅ Using existing clipped file in MongoDB: {clipped_audio_filename} (ID: {clipped_file_id})")
        else:
            # Run FFmpeg to cut the file
            ffmpeg_cmd = f'ffmpeg -y -i "{temp_file_path}" -ss {start_time} -to {end_time} -c copy "{clipped_audio_path}"'
            logger.info(f"🔄 Running FFmpeg Command: {ffmpeg_cmd}")

            process = subprocess.run(ffmpeg_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_output = process.stdout.decode()
            stderr_output = process.stderr.decode()

            logger.info(f"📜 FFmpeg stdout:\n{stdout_output}")
            logger.error(f"⚠️ FFmpeg stderr:\n{stderr_output}")

            if process.returncode != 0:
                logger.error(f"❌ ERROR: FFmpeg process failed with code {process.returncode}")
                return jsonify({"error": f"FFmpeg failed to process audio. FFmpeg stderr: {stderr_output}"}), 500

            # Verify if FFmpeg actually created the file
            if not os.path.exists(clipped_audio_path) or os.path.getsize(clipped_audio_path) == 0:
                logger.error("❌ ERROR: FFmpeg did not produce a valid output file")
                return jsonify({"error": "FFmpeg failed to process audio"}), 500

            file_size = os.path.getsize(clipped_audio_path)
            logger.info(f"✅ Clipped audio successfully created at {clipped_audio_path}, size: {file_size} bytes")

            # Save clipped audio to MongoDB
            with open(clipped_audio_path, "rb") as clipped_file:
                clipped_file_id = fs.put(
                    clipped_file.read(),
                    filename=clipped_audio_filename,
                    metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # Add type
                )
                logger.info(f"📤 Clipped audio saved to MongoDB with ID: {clipped_file_id}")


        # Cleanup temp files
        os.remove(temp_file_path)
        os.remove(clipped_audio_path)
        logger.info(f"🗑️ Temporary files deleted: {temp_file_path}, {clipped_audio_path}")

        return jsonify({"message": "✅ Audio clipped successfully!", "clipped_audio": str(clipped_file_id)})

    except Exception as e:
        logger.error(f"❌ ERROR: Failed to process audio - {str(e)}")
        return jsonify({"error": f"Failed to process audio: {str(e)}"}), 500


#*************************************************************************************************************************
#ai audio cutting:
# Background Noise Detection using FFT
def detect_background_noise(audio_path, threshold=1000, max_freq=500):
    """Detects background noise in a WAV file by analyzing its frequency content using FFT."""
    try:
        with wave.open(audio_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

        fft_result = np.fft.fft(audio_array)
        fft_freq = np.fft.fftfreq(len(fft_result), 1/sample_rate)
        magnitude = np.abs(fft_result)
        low_freqs = magnitude[:max_freq]
        avg_magnitude = np.mean(low_freqs)

        if avg_magnitude > threshold:
            hum_detected = False
            if np.any((fft_freq > 49) & (fft_freq < 51)) or np.any((fft_freq > 59) & (fft_freq < 61)):
                hum_detected = True

            if hum_detected:
                return "Background noise detected: Hum (50 Hz or 60 Hz)"
            elif np.any((fft_freq > 100) & (fft_freq < 1000)):
                return "Background noise detected: Traffic or environmental noise"
            else:
                return "Background noise detected: Broadband noise (static/wind)"

        return "No significant background noise detected"

    except Exception as e:
        logging.error(f"Error in background noise detection: {e}")
        return f"Error in background noise detection: {str(e)}"

# Detect Long Pauses using FFmpeg
def detect_long_pauses(audio_path, threshold=2.0):
    """Detects long pauses (silences of 2+ seconds) in an audio file using FFmpeg."""
    cmd = [
        "ffmpeg", "-i", audio_path, "-af",
        f"silencedetect=noise=-40dB:d={threshold}",
        "-f", "null", "-"
    ]
    process = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    output = process.stderr

    silence_start_times = [float(match.group(1)) for match in re.finditer(r"silence_start: ([0-9.]+)", output)]
    silence_end_times = [float(match.group(1)) for match in re.finditer(r"silence_end: ([0-9.]+)", output)]

    return [{"start": start, "end": end} for start, end in zip(silence_start_times, silence_end_times)]

# Analyze certainty levels
def analyze_certainty_levels(transcription):
    """Analyze certainty of each sentence in the transcription with Zero-Shot Classification."""
    if not transcription.strip():
        logging.error("🚨 ERROR: Transcription is empty!")
        return []

    sentences = transcription.split(". ")
    sentence_certainty_scores = []

    candidate_labels = ["filler", "important", "redundant", "off-topic"]

    for sentence in sentences:
        if not sentence.strip():
            continue

        result = classifier(sentence, candidate_labels=candidate_labels)

        if "labels" not in result or "scores" not in result:
            logging.error(f"🚨 ERROR: Classification failed for sentence: {sentence}")
            continue

        certainty_score = result['scores'][result['labels'].index('important')]

        certainty_level = (
            "Green" if certainty_score <= 0.2 else
            "Light Green" if certainty_score <= 0.4 else
            "Yellow" if certainty_score <= 0.6 else
            "Orange" if certainty_score <= 0.8 else
            "Dark Orange" if certainty_score <= 0.9 else "Red"
        )

        sentence_certainty_scores.append({
            "sentence": sentence,
            "certainty": certainty_score,
            "certainty_level": certainty_level
        })

    return sentence_certainty_scores

# Detect Filler Words in Transcript
def detect_filler_words(transcription):
    """Identifies filler words (um, ah, like, etc.) in a transcript."""
    filler_words = ["um", "uh", "ah", "like", "you know", "so", "well", "I mean", "sort of", "kind of", "okay", "right"]
    sentences = transcription.split(". ")
    return [sentence for sentence in sentences if any(re.search(rf"\b{word}\b", sentence, re.IGNORECASE) for word in filler_words)]

# Classify Sentence Importance
def classify_sentence_relevance(transcription):
    """Classifies sentences as 'important', 'filler', 'off-topic', or 'redundant'."""
    sentences = transcription.split(". ")
    sentence_analysis = []
    candidate_labels = ["important", "filler", "off-topic", "redundant"]

    for sentence in sentences:
        classification = classifier(sentence, candidate_labels=candidate_labels)
        highest_label = classification["labels"][0]

        sentence_analysis.append({
            "sentence": sentence,
            "category": highest_label,
            "score": classification["scores"][0]
        })

    return sentence_analysis

# Assign timestamps based on word-level timestamps
def get_sentence_timestamps(sentence, word_timings):
    """Find start and end timestamps for a sentence based on word-level timings."""
    words = sentence.split()
    if not words:
        return {"start": 0, "end": 0}

    first_word, last_word = words[0], words[-1]
    start_timestamp = next((w["start"] for w in word_timings if w["word"] == first_word), 0.0)
    end_timestamp = next((w["end"] for w in word_timings if w["word"] == last_word), start_timestamp + 2.0)

    return {"start": start_timestamp, "end": end_timestamp}


# sentiment analyze function
def analyze_sentiment(transcript):
    """Analyzes sentiment of a transcript and returns an emoji-based result."""
    blob = TextBlob(transcript)
    sentiment_score = blob.sentiment.polarity  # -1 (Negative) to +1 (Positive)

    if sentiment_score > 0.2:
        return "Positive 😊"
    elif sentiment_score < -0.2:
        return "Negative 😡"
    else:
        return "Neutral 😐"

# generate show notes function
def generate_ai_show_notes(transcript):
    """Generates AI-powered podcast show notes using GPT-4."""
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
            messages=[{"role": "system", "content": "You are a professional podcast assistant."},
                      {"role": "user", "content": prompt}]
        )

        ai_show_notes = response["choices"][0]["message"]["content"]
        return ai_show_notes.strip()

    except Exception as e:
        return f"❌ Error generating show notes: {str(e)}"

# AI Audio Cutting API
@transcription_bp.route("/ai_cut_audio", methods=["POST"])
def ai_cut_audio():
    """Handles AI-based audio cutting, transcription, NLP-based trimming suggestions, background noise detection, sentiment analysis, and AI-generated show notes."""

    try:
        # ✅ Handle requests where only file_id is sent (No re-uploading)
        if "file_id" in request.json:
            file_id = request.json["file_id"]

            try:
                # Retrieve the file from MongoDB GridFS
                file_data = fs.get(ObjectId(file_id)).read()
                logging.info(f"📥 Retrieved audio file from MongoDB GridFS with ID: {file_id}")

                # Save to a temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(file_data)
                    temp_file_path = temp_file.name  # Get the temp file path

                logging.info(f"📂 Temporary file created at: {temp_file_path}")

            except Exception as e:
                logging.error(f"❌ ERROR: Failed to fetch file {file_id} from MongoDB - {str(e)}")
                return jsonify({"error": f"Failed to fetch file from MongoDB: {str(e)}"}), 500

        # ✅ Handle direct file upload
        elif "audio" in request.files:
            # Step 1: Save the uploaded audio file to MongoDB GridFS
            audio_file = request.files["audio"]
            file_name = audio_file.filename

            # ✅ **Check if audio file already exists in MongoDB**
            existing_audio = fs.find_one({"filename": file_name})
            if existing_audio:
                file_id = existing_audio._id
                logging.info(f"📂 Audio file already exists in MongoDB with ID: {file_id}")
            else:
                # ✅ **Save the file only if it doesn't exist**
                file_id = fs.put(
                    audio_file.read(),
                    filename=file_name,
                    metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}  # ✅ Ensure TTL works
                )
                logging.info(f"📤 Audio file uploaded to MongoDB GridFS with ID: {file_id}")

            # Save to a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(fs.get(file_id).read())
                temp_file_path = temp_file.name  # Get the temp file path

            logging.info(f"📂 Temporary file created at: {temp_file_path}")

        else:
            return jsonify({"error": "No audio file provided"}), 400

        # 🎙 Step 3: Transcription with timestamps
        transcription_result = client.speech_to_text.convert(
            file=open(temp_file_path, "rb"),
            model_id="scribe_v1",
            num_speakers=2,
            diarize=True,
            timestamps_granularity="word"
        )
        transcription = transcription_result.text.strip()

        # ✅ LOG the full transcription before processing
        logging.info(f"📜 FULL TRANSCRIPT BEFORE PROCESSING: {transcription}")

        # Extract word-level timestamps
        word_timings = [
            {"word": w.text, "start": w.start, "end": w.end}
            for w in transcription_result.words
            if hasattr(w, "start") and hasattr(w, "end")
        ]

        # 🧹 Step 4: Remove filler words
        cleaned_transcript = remove_filler_words(transcription)

        # 🔊 Step 5: Detect background noise
        noise_detection_result = detect_background_noise(temp_file_path)  # ✅ Process directly from temp file

        # 🛑 Step 6: Detect filler words
        filler_sentences = detect_filler_words(transcription)

        # 🎯 Step 7: Sentence classification
        sentence_analysis = classify_sentence_relevance(transcription)

        # 🎯 Step 8: Certainty level analysis
        sentence_certainty_scores = analyze_certainty_levels(transcription)

        # ✅ LOG all sentences stored in `sentence_certainty_scores`
        logging.info(f"📋 SENTENCE CERTAINTY SCORES: {sentence_certainty_scores}")

        # Assign timestamps to sentences dynamically
        sentence_timestamps = []
        for idx, entry in enumerate(sentence_certainty_scores):  # Add an ID to each sentence
            timestamps = get_sentence_timestamps(entry["sentence"], word_timings)
            entry["start"] = timestamps["start"]
            entry["end"] = timestamps["end"]
            entry["id"] = idx  # Add unique ID

            sentence_timestamps.append({
                "id": idx,  # Add ID to timestamps too
                "sentence": entry["sentence"],
                "start": timestamps["start"],
                "end": timestamps["end"]
            })

        # ✂ Step 9: Suggested AI cuts with timestamps
        suggested_cuts = [
            {
                "sentence": entry["sentence"],
                "certainty_level": entry["certainty_level"],
                "certainty_score": entry["certainty"],
                "start": entry["start"],
                "end": entry["end"]
            }
            for entry in sentence_certainty_scores if entry["certainty"] >= 0.6
        ]

        # 🎭 Step 10: AI Sentiment Analysis
        sentiment_result = analyze_sentiment(transcription)

        # ✍ Step 11: AI Show Notes Generation
        ai_show_notes = generate_ai_show_notes(transcription)

        # ✅ Bulk selection storage
        selected_sentences = []  # To track sentences selected for removal

        # 🔄 Final Response
        return jsonify({
            "message": "✅ AI Audio processing completed successfully",
            "file_id": str(file_id),
            "cleaned_transcript": cleaned_transcript,
            "background_noise": noise_detection_result,
            "sentence_certainty_scores": sentence_certainty_scores,
            "sentence_timestamps": sentence_timestamps,
            "long_pauses": detect_long_pauses(temp_file_path),
            "suggested_cuts": suggested_cuts,
            "selected_sentences": selected_sentences,
            "sentiment": sentiment_result,
            "ai_show_notes": ai_show_notes
        }), 200



    except Exception as e:
        logging.error(f"❌ ERROR: Failed to process audio - {str(e)}")
        return jsonify({"error": f"Failed to process audio: {str(e)}"}), 500

    finally:
        if temp_file_path:  # Kontrollera om filen skapades
            try:
                os.remove(temp_file_path)
                logging.info(f"🗑️ Temporary file deleted: {temp_file_path}")
            except PermissionError:
                logging.warning(f"⚠️ Could not delete {temp_file_path} as it is in use. Retrying in 1 second...")
                time.sleep(1)
                try:
                    os.remove(temp_file_path)
                    logging.info(f"✅ Successfully deleted temp file after retry: {temp_file_path}")
                except Exception as e:
                    logging.error(f"❌ Failed to delete temp file: {str(e)}")




#***************************************************************************************************

#ai video enhancemnt and video analyz

#ai video enhancment
@transcription_bp.route("/ai_videoedit", methods=["POST"])
def ai_videoedit():
    """Upload video to MongoDB GridFS without processing it immediately."""
    
    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400

        video_file = request.files["video"]
        video_id = fs.put(
            video_file.read(),
            filename=video_file.filename,
            metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
        )

        logger.info(f"📤 Video uploaded to MongoDB GridFS with ID: {video_id}")

        return jsonify({
            "message": "✅ Video uploaded successfully!",
            "video_id": str(video_id)
        })

    except Exception as e:
        logger.error(f"❌ Error uploading video: {str(e)}")
        return jsonify({"error": "Video upload failed", "details": str(e)}), 500

#video enahnchance route
@transcription_bp.route("/ai_videoenhance", methods=["POST"])
def ai_videoenhance():
    """Enhance an existing video stored in MongoDB and save the processed version."""

    temp_video_path = None  
    processed_video_path = None

    try:
        data = request.get_json()
        if "video_id" not in data:
            return jsonify({"error": "No video_id provided"}), 400

        video_id = ObjectId(data["video_id"])
        logger.info(f"✅ Fetching video from MongoDB GridFS with ID: {video_id}")

        # ✅ Retrieve video from MongoDB
        video_file = fs.get(video_id)
        if not video_file:
            return jsonify({"error": "Video not found in MongoDB"}), 404

        # ✅ Save video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(video_file.read())  # Read video data from MongoDB
            temp_video.flush()  # Ensure all data is written
            temp_video_path = temp_video.name

        logger.info(f"📂 Temporary video file created at: {temp_video_path}")

        # ✅ Ensure file exists before processing
        if not os.path.exists(temp_video_path):
            raise FileNotFoundError(f"Temporary file {temp_video_path} was not created.")

        # ✅ Process video (Color Correction & Loudness Normalization)
        processed_video_path = temp_video_path.replace(".mp4", "_processed.mp4")
        ffmpeg_command = f'ffmpeg -i "{temp_video_path}" -vf "eq=contrast=1.05:brightness=0.05" -af "loudnorm" "{processed_video_path}"'
        
        logger.info(f"🔄 Running FFmpeg command: {ffmpeg_command}")
        os.system(ffmpeg_command)

        # ✅ Ensure processed video exists
        if not os.path.exists(processed_video_path):
            raise FileNotFoundError(f"Processed file {processed_video_path} was not created.")

        logger.info(f"✅ Video processing completed: {processed_video_path}")

        # ✅ Save processed video to MongoDB GridFS
        with open(processed_video_path, "rb") as processed_file:
            processed_video_id = fs.put(processed_file.read(), filename=f"processed_{video_id}.mp4")

        logger.info(f"📤 Processed video saved to MongoDB GridFS with ID: {processed_video_id}")

        return jsonify({
            "message": "✅ Video processed successfully!",
            "processed_video_id": str(processed_video_id)
        })

    except FileNotFoundError as fnf_error:
        logger.error(f"❌ File not found: {str(fnf_error)}")
        return jsonify({"error": "File not found", "details": str(fnf_error)}), 500

    except Exception as e:
        logger.error(f"❌ Error during video processing: {str(e)}")
        return jsonify({"error": "Video processing failed", "details": str(e)}), 500

    finally:
        # ✅ Cleanup: Delete temporary files if they exist
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"🗑️ Temporary file deleted: {temp_video_path}")

        if processed_video_path and os.path.exists(processed_video_path):
            os.remove(processed_video_path)
            logger.info(f"🗑️ Processed file deleted: {processed_video_path}")





#start of video analyzis part

# Load Whisper Model
print("🔄 Loading Whisper base model...")
model = whisper.load_model("base")
print("✅ Whisper base loaded!")


# Extract audio from video
def extract_audio(video_path, audio_path):
    try:
        subprocess.run(['ffmpeg', '-i', video_path, '-ac', '1', '-ar', '16000', audio_path], check=True)
        logger.info(f"🔊 Audio extracted to: {audio_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error extracting audio: {e}")


# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    try:
        whisper_result = model.transcribe(audio_path)
        transcription = whisper_result.get("text", "").strip()

        if not transcription:
            transcription = "N/A"

        logger.info(f"📝 Whisper Transcription: {transcription}")
        return transcription

    except Exception as e:
        return f"Error during transcription: {str(e)}"


# Background Noise Detection using FFT
def detect_background_noise(audio_path):
    try:
        with wave.open(audio_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()

            audio_data = wf.readframes(n_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Apply FFT to the audio signal
        fft_result = np.fft.fft(audio_array)
        fft_freq = np.fft.fftfreq(len(fft_result), 1 / sample_rate)

        # Focus on low frequencies to detect noise
        low_freqs = np.abs(fft_result[:500])
        avg_magnitude = np.mean(low_freqs)

        threshold = 1000
        if avg_magnitude > threshold:
            return "Background noise detected: Likely Hum or Low Frequency Noise"
        
        return "No significant background noise detected"

    except Exception as e:
        return f"Error in background noise detection: {str(e)}"


# Sentiment Analysis using TextBlob and your transcription
def analyze_sentiment(transcription):
    # Perform sentiment analysis on the transcript using TextBlob
    blob = TextBlob(transcription)
    sentiment_score = blob.sentiment.polarity  # Positive, Neutral, Negative

    if sentiment_score > 0:
        sentiment = "Positive"
    elif sentiment_score < 0:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment


# Calculate visual quality (sharpness and contrast)
def calculate_visual_quality(video_path):
    cap = cv2.VideoCapture(video_path)
    
    sharpness = []
    contrast = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to grayscale for processing
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate sharpness (using Laplacian variance)
        laplacian_var = cv2.Laplacian(gray_frame, cv2.CV_64F).var()
        sharpness.append(laplacian_var)

        # Calculate contrast (standard deviation of pixel values)
        contrast_value = frame.std()
        contrast.append(contrast_value)

    cap.release()

    # Calculate average sharpness and contrast
    avg_sharpness = np.mean(sharpness)
    avg_contrast = np.mean(contrast)

    return avg_sharpness, avg_contrast


# Calculate speech rate (WPM)
def calculate_speech_rate(audio_path, transcription):
    try:
        # Get the duration of the audio (in seconds)
        with wave.open(audio_path, 'rb') as wf:
            duration = wf.getnframes() / wf.getframerate()

        # Count the number of words in the transcription
        word_count = len(transcription.split())

        # Calculate words per minute (WPM)
        words_per_minute = word_count / (duration / 60)
        return f"Speech rate: {words_per_minute:.2f} WPM"

    except Exception as e:
        logger.error(f"❌ Error during speech rate calculation: {e}")
        return "Error calculating speech rate."

#video analysis route
@transcription_bp.route("/ai_videoanalysis", methods=["POST"])
def ai_video_analysis():
    """Analyze video quality, sentiment, and background noise using AI."""

    temp_video_path = None  
    processed_audio_path = None

    try:
        data = request.get_json()
        if "video_id" not in data:
            return jsonify({"error": "No video_id provided"}), 400

        video_id = ObjectId(data["video_id"])
        logger.info(f"🔍 Fetching video from MongoDB GridFS with ID: {video_id}")

        # ✅ Fetch video from GridFS
        video_file = fs.get(video_id)

        if not video_file:
            logger.error(f"❌ Video with ID {video_id} not found in MongoDB.")
            return jsonify({"error": "Video not found in database."}), 404

        # ✅ Write video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(video_file.read())  # Read video data from MongoDB
            temp_video.flush()  # Ensure all data is written
            temp_video_path = temp_video.name

        logger.info(f"📂 Temporary video file created at: {temp_video_path}")

        # ✅ Ensure file exists before proceeding
        if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
            raise FileNotFoundError(f"Temporary file {temp_video_path} was not created or is empty.")

        # ✅ Extract audio for background noise detection
        processed_audio_path = temp_video_path.replace(".mp4", ".wav")
        extract_audio(temp_video_path, processed_audio_path)

        # ✅ Perform background noise detection
        background_noise = detect_background_noise(processed_audio_path)

        # ✅ Perform sentiment analysis on transcription
        transcription = transcribe_audio(processed_audio_path)
        sentiment_analysis = analyze_sentiment(transcription)

        # ✅ Perform visual quality detection (sharpness, contrast)
        sharpness, contrast = calculate_visual_quality(temp_video_path)

        # ✅ Perform speech rate calculation (WPM)
        speech_rate = calculate_speech_rate(processed_audio_path, transcription)

        return jsonify({
            "message": "✅ Video analysis completed successfully!",
            "video_id": str(video_id),
            "background_noise": background_noise,
            "sentiment_analysis": sentiment_analysis,
            "visual_quality": {
                "sharpness": sharpness,
                "contrast": contrast
            },
            "speech_rate": speech_rate
        })

    except FileNotFoundError as fnf_error:
        logger.error(f"❌ File not found: {str(fnf_error)}")
        return jsonify({"error": "File not found", "details": str(fnf_error)}), 500

    except Exception as e:
        logger.error(f"❌ Error during video analysis: {str(e)}")
        return jsonify({"error": "Video analysis failed", "details": str(e)}), 500

    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"🗑️ Temporary file deleted: {temp_video_path}")

        if processed_audio_path and os.path.exists(processed_audio_path):
            os.remove(processed_audio_path)
            logger.info(f"🗑️ Processed audio file deleted: {processed_audio_path}")






#*************************************************************************************************************************


    #video cutting:

@transcription_bp.route("/clip_video", methods=["POST"])
def clip_video():
    """Trim selected timestamps from a video file using FFmpeg and save it to MongoDB GridFS."""

    try:
        # Ensure request has a video ID and clip timestamps
        data = request.json
        video_id = data.get("video_id")
        clips_to_remove = data.get("clips")

        if not video_id:
            return jsonify({"error": "No video_id provided"}), 400

        if not clips_to_remove or not isinstance(clips_to_remove, list):
            return jsonify({"error": "No valid timestamps provided"}), 400

        # Extract start and end time for clipping
        start_time = clips_to_remove[0]["start"]
        end_time = clips_to_remove[0]["end"]

        if start_time >= end_time:
            return jsonify({"error": "Invalid timestamps: start time must be before end time"}), 400

        logger.info(f"🎬 Clipping video with ID: {video_id} (Start: {start_time}s, End: {end_time}s)")

        # ✅ Retrieve video from MongoDB
        try:
            video_file = fs.get(ObjectId(video_id))
            logger.info(f"✅ Successfully fetched video from MongoDB: {video_file.filename}")
        except Exception as e:
            logger.error(f"❌ ERROR: Failed to fetch video {video_id} from MongoDB: {str(e)}")
            return jsonify({"error": f"Failed to fetch video from MongoDB: {str(e)}"}), 500

        # ✅ Save video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(video_file.read())
            temp_video.flush()
            temp_video_path = temp_video.name

        logger.info(f"📂 Temporary video file created at: {temp_video_path}")

        # ✅ Define the output path for the clipped video
        clipped_video_path = temp_video_path.replace(".mp4", "_clipped.mp4")

        # **Run FFmpeg to trim the video correctly**
        ffmpeg_cmd = f'ffmpeg -y -i "{temp_video_path}" -ss {start_time} -to {end_time} -c copy "{clipped_video_path}"'
        logger.info(f"🔄 Running FFmpeg Command: {ffmpeg_cmd}")
        os.system(ffmpeg_cmd)

        # ✅ Ensure FFmpeg successfully created the file
        if not os.path.exists(clipped_video_path) or os.path.getsize(clipped_video_path) == 0:
            logger.error("❌ ERROR: FFmpeg failed to create a valid output file")
            return jsonify({"error": "FFmpeg failed to process video"}), 500

        logger.info(f"✅ Clipped video saved at: {clipped_video_path}")

        # ✅ Save the trimmed video to MongoDB GridFS
        with open(clipped_video_path, "rb") as clipped_file:
            clipped_video_id = fs.put(
                clipped_file.read(),
                filename=f"clipped_{video_id}.mp4",
                metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
            )

        logger.info(f"📤 Clipped video saved to MongoDB GridFS with ID: {clipped_video_id}")

        # ✅ Clean up temporary files
        os.remove(temp_video_path)
        os.remove(clipped_video_path)
        logger.info(f"🗑️ Temporary files deleted: {temp_video_path}, {clipped_video_path}")

        return jsonify({"message": "✅ Video clipped successfully!", "clipped_video": str(clipped_video_id)})

    except Exception as e:
        logger.error(f"❌ ERROR: Failed to process video - {str(e)}")
        return jsonify({"error": f"Failed to process video: {str(e)}"}), 500

    
#*********************************************************************************************************

# Ai media cut editor


# get waveform
# @transcription_bp.route("/get_media_info", methods=["POST"])
# def get_media_info():
#     """Handles media (audio/video) file uploads, extracts metadata, and generates waveform (if applicable)."""

#     if "media" not in request.files:
#         logger.error("❌ ERROR: No media file provided")
#         return jsonify({"error": "No media file provided"}), 400

#     try:
#         # Retrieve uploaded file
#         media_file = request.files["media"]
#         filename = media_file.filename
#         file_ext = os.path.splitext(filename)[1].lower()

#         # ✅ Determine file type
#         is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv"]
#         is_audio = file_ext in [".wav", ".mp3"]

#         if not is_audio and not is_video:
#             logger.error("❌ ERROR: Unsupported file format")
#             return jsonify({"error": "Unsupported file format"}), 400

#         # ✅ Save original file to MongoDB GridFS
#         file_id = fs.put(
#             media_file.read(),
#             filename=filename,
#             metadata={"upload_timestamp": datetime.utcnow(), "type": "media"}
#         )

#         # ✅ Retrieve the file from GridFS for processing
#         file_data = fs.get(file_id).read()
#         logger.info(f"📥 Retrieved original file from GridFS with ID: {file_id}")

#         # ✅ Save to a temporary file for analysis
#         with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
#             temp_file.write(file_data)
#             temp_file_path = temp_file.name
#         logger.info(f"📂 Temporary file created at: {temp_file_path}")

#         # ✅ Extract duration
#         if is_audio:
#             data, sample_rate = sf.read(temp_file_path)
#             duration = len(data) / sample_rate
#         elif is_video:
#             cmd = [
#                 "ffprobe", "-i", temp_file_path, "-show_entries",
#                 "format=duration", "-v", "quiet", "-of", "csv=p=0"
#             ]
#             duration_output = subprocess.check_output(cmd, text=True).strip()
#             duration = float(duration_output) if duration_output else 0.0

#         logger.info(f"🕒 Media duration: {duration} seconds")

#         # ✅ Generate waveform (only for audio files)
#         waveform_file_id = None
#         if is_audio:
#             waveform_filename = f"waveform_{filename}"
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as wf_temp:
#                 waveform_path = wf_temp.name

#             fig, ax = plt.subplots(figsize=(10, 3))
#             time_axis = np.linspace(0, duration, num=len(data))
#             ax.plot(time_axis, data, color="blue")
#             ax.set_xlabel("Time (seconds)")
#             ax.set_ylabel("Amplitude")
#             plt.savefig(waveform_path)
#             plt.close(fig)

#             # Save waveform to MongoDB GridFS
#             with open(waveform_path, "rb") as wf:
#                 waveform_file_id = fs.put(
#                     wf.read(),
#                     filename=waveform_filename,
#                     metadata={"upload_timestamp": datetime.utcnow(), "type": "waveform"}
#                 )

#             os.remove(waveform_path)
#             logger.info(f"📤 Waveform saved to MongoDB GridFS with ID: {waveform_file_id}")

#         # ✅ Cleanup temporary file
#         os.remove(temp_file_path)

#         return jsonify({
#             "duration": duration,
#             "media_file_id": str(file_id),  # Send correct file ID for both audio & video
#             "waveform": str(waveform_file_id) if waveform_file_id else None,  # Send waveform ID if available
#             "media_type": "video" if is_video else "audio"
#         })

#     except Exception as e:
#         logger.error(f"❌ ERROR: Failed to process media - {str(e)}")
#         return jsonify({"error": f"Failed to process media: {str(e)}"}), 500

# #background noise detection
# def detect_background_noise(media_path, threshold=1000, max_freq=500):
#     """Detects background noise in an audio or video file. If video, extracts audio first."""
#     try:
#         file_ext = os.path.splitext(media_path)[1].lower()
#         is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv"]

#         # ✅ Extract audio from video if needed
#         if is_video:
#             audio_path = media_path.replace(file_ext, ".wav")
#             cmd = ["ffmpeg", "-i", media_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
#             subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#             media_path = audio_path  # Use extracted audio path

#         with wave.open(media_path, 'rb') as wf:
#             sample_rate = wf.getframerate()
#             n_frames = wf.getnframes()
#             audio_data = wf.readframes(n_frames)
#             audio_array = np.frombuffer(audio_data, dtype=np.int16)

#         fft_result = np.fft.fft(audio_array)
#         fft_freq = np.fft.fftfreq(len(fft_result), 1/sample_rate)
#         magnitude = np.abs(fft_result)
#         low_freqs = magnitude[:max_freq]
#         avg_magnitude = np.mean(low_freqs)

#         if avg_magnitude > threshold:
#             hum_detected = False
#             if np.any((fft_freq > 49) & (fft_freq < 51)) or np.any((fft_freq > 59) & (fft_freq < 61)):
#                 hum_detected = True

#             if hum_detected:
#                 result = "Background noise detected: Hum (50 Hz or 60 Hz)"
#             elif np.any((fft_freq > 100) & (fft_freq < 1000)):
#                 result = "Background noise detected: Traffic or environmental noise"
#             else:
#                 result = "Background noise detected: Broadband noise (static/wind)"
#         else:
#             result = "No significant background noise detected"

#         # ✅ Cleanup extracted audio if needed
#         if is_video and os.path.exists(audio_path):
#             os.remove(audio_path)

#         return result

#     except Exception as e:
#         logging.error(f"Error in background noise detection: {e}")
#         return f"Error in background noise detection: {str(e)}"

# #detect long pauses:
# def detect_long_pauses(media_path, threshold=2.0):
#     """Detects long pauses in an audio or video file using FFmpeg. Extracts audio if needed."""
#     file_ext = os.path.splitext(media_path)[1].lower()
#     is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv"]

#     # ✅ Extract audio from video if necessary
#     if is_video:
#         audio_path = media_path.replace(file_ext, ".wav")
#         cmd = ["ffmpeg", "-i", media_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
#         subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         media_path = audio_path

#     cmd = [
#         "ffmpeg", "-i", media_path, "-af",
#         f"silencedetect=noise=-40dB:d={threshold}",
#         "-f", "null", "-"
#     ]
#     process = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
#     output = process.stderr

#     silence_start_times = [float(match.group(1)) for match in re.finditer(r"silence_start: ([0-9.]+)", output)]
#     silence_end_times = [float(match.group(1)) for match in re.finditer(r"silence_end: ([0-9.]+)", output)]

#     # ✅ Cleanup extracted audio if needed
#     if is_video and os.path.exists(audio_path):
#         os.remove(audio_path)

#     return [{"start": start, "end": end} for start, end in zip(silence_start_times, silence_end_times)]

# # Analyze certainty levels
# def analyze_certainty_levels(transcription):
#     """Analyze certainty of each sentence in the transcription with Zero-Shot Classification."""
#     if not transcription.strip():
#         logging.error("🚨 ERROR: Transcription is empty!")
#         return []

#     sentences = transcription.split(". ")
#     sentence_certainty_scores = []

#     candidate_labels = ["filler", "important", "redundant", "off-topic"]

#     for sentence in sentences:
#         if not sentence.strip():
#             continue

#         result = classifier(sentence, candidate_labels=candidate_labels)

#         if "labels" not in result or "scores" not in result:
#             logging.error(f"🚨 ERROR: Classification failed for sentence: {sentence}")
#             continue

#         certainty_score = result['scores'][result['labels'].index('important')]

#         certainty_level = (
#             "Green" if certainty_score <= 0.2 else
#             "Light Green" if certainty_score <= 0.4 else
#             "Yellow" if certainty_score <= 0.6 else
#             "Orange" if certainty_score <= 0.8 else
#             "Dark Orange" if certainty_score <= 0.9 else "Red"
#         )

#         sentence_certainty_scores.append({
#             "sentence": sentence,
#             "certainty": certainty_score,
#             "certainty_level": certainty_level
#         })

#     return sentence_certainty_scores

# # Detect Filler Words in Transcript
# def detect_filler_words(transcription):
#     """Identifies filler words (um, ah, like, etc.) in a transcript."""
#     filler_words = ["um", "uh", "ah", "like", "you know", "so", "well", "I mean", "sort of", "kind of", "okay", "right"]
#     sentences = transcription.split(". ")
#     return [sentence for sentence in sentences if any(re.search(rf"\b{word}\b", sentence, re.IGNORECASE) for word in filler_words)]

# # Classify Sentence Importance
# def classify_sentence_relevance(transcription):
#     """Classifies sentences as 'important', 'filler', 'off-topic', or 'redundant'."""
#     sentences = transcription.split(". ")
#     sentence_analysis = []
#     candidate_labels = ["important", "filler", "off-topic", "redundant"]

#     for sentence in sentences:
#         classification = classifier(sentence, candidate_labels=candidate_labels)
#         highest_label = classification["labels"][0]

#         sentence_analysis.append({
#             "sentence": sentence,
#             "category": highest_label,
#             "score": classification["scores"][0]
#         })

#     return sentence_analysis

# # Assign timestamps based on word-level timestamps
# def get_sentence_timestamps(sentence, word_timings, prev_end_time=0):
#     """Finds the most accurate timestamps for a sentence by matching words dynamically."""
#     words = sentence.split()
#     if not words:
#         return {"start": prev_end_time, "end": prev_end_time + 2.0}  # Ensure a valid fallback time

#     first_word, last_word = words[0], words[-1]

#     # ✅ Find the closest matching timestamp AFTER the previous sentence's end time
#     start_timestamp = next(
#         (w["start"] for w in word_timings if w["word"] == first_word and w["start"] > prev_end_time),
#         prev_end_time  # Default fallback
#     )

#     # ✅ Find the last matching word's end time, ensuring it's AFTER the start
#     end_timestamp = next(
#         (w["end"] for w in word_timings if w["word"] == last_word and w["end"] > start_timestamp),
#         start_timestamp + 2.0  # Default fallback to avoid zero-length clips
#     )

#     # ✅ Ensure end_timestamp does not overlap with the next sentence's start
#     if end_timestamp - start_timestamp < 0.5:  # Minimum duration safeguard
#         end_timestamp += 0.5

#     return {"start": start_timestamp, "end": end_timestamp}





# # sentiment analyze function
# def analyze_sentiment(transcript):
#     """Analyzes sentiment of a transcript and returns an emoji-based result."""
#     blob = TextBlob(transcript)
#     sentiment_score = blob.sentiment.polarity  # -1 (Negative) to +1 (Positive)

#     if sentiment_score > 0.2:
#         return "Positive 😊"
#     elif sentiment_score < -0.2:
#         return "Negative 😡"
#     else:
#         return "Neutral 😐"

# # generate show notes function
# def generate_ai_show_notes(transcript):
#     """Generates AI-powered podcast show notes using GPT-4."""
#     prompt = f"""
#     Generate professional show notes for this podcast episode.
#     - A brief summary of the discussion.
#     - Key topics covered (bullet points).
#     - Any important timestamps (if available).
#     - Guest highlights (if mentioned).

#     Transcript:
#     {transcript}
#     """

#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[{"role": "system", "content": "You are a professional podcast assistant."},
#                       {"role": "user", "content": prompt}]
#         )

#         ai_show_notes = response["choices"][0]["message"]["content"]
#         return ai_show_notes.strip()

#     except Exception as e:
#         return f"❌ Error generating show notes: {str(e)}"

# #cut video for sentences
# def cut_video_clip(video_path, start_time, end_time, output_path):
#     """Cuts a precise section from a video file while ensuring full sentence capture."""
#     min_clip_length = 1.5  # Ensure at least 1.5s clips to avoid cutting too short

#     if end_time - start_time < min_clip_length:
#         end_time += (min_clip_length - (end_time - start_time))  # Extend to minimum duration

#     buffer_time = 0.15  # Small buffer to avoid missing words due to frame delays

#     cmd = [
#         "ffmpeg", "-i", video_path,
#         "-ss", str(max(0, start_time - buffer_time)),  # Ensure start time isn't negative
#         "-to", str(end_time + buffer_time),  # Add buffer to avoid cutting last words
#         "-c:v", "libx264", "-preset", "fast", "-crf", "23",  # Optimize for speed & quality
#         "-c:a", "aac", "-b:a", "128k", "-strict", "experimental",
#         "-movflags", "+faststart",  # Improve playback responsiveness
#         "-y", output_path
#     ]
    
#     subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     return output_path


# #ai media cutter (funnkar nästan 80-90%)
# @transcription_bp.route("/ai_cut_media", methods=["POST"])
# def ai_cut_media():
#     """Handles AI-based media (audio/video) processing: 
#        - Transcription
#        - NLP-based trimming suggestions
#        - Background noise detection
#        - Sentiment analysis
#        - AI-generated show notes
#     """

#     try:
#         temp_file_path = None
#         file_id = None

#         is_video = False  # ✅ Ensure `is_video` is always defined

#         # ✅ Check if file_id is provided (No re-uploading needed)
#         if "file_id" in request.json:
#             file_id = request.json["file_id"]
#             try:
#                 file_data = fs.get(ObjectId(file_id)).read()
#                 logging.info(f"📥 Retrieved media file from MongoDB GridFS with ID: {file_id}")

#                 # Save to a temporary file
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
#                     temp_file.write(file_data)
#                     temp_file_path = temp_file.name

#                 logging.info(f"📂 Temporary file created at: {temp_file_path}")

#             except Exception as e:
#                 logging.error(f"❌ ERROR: Failed to fetch file {file_id} from MongoDB - {str(e)}")
#                 return jsonify({"error": f"Failed to fetch file from MongoDB: {str(e)}"}), 500

#         # ✅ Handle direct file upload
#         elif "media" in request.files:
#             media_file = request.files["media"]
#             file_name = media_file.filename
#             file_ext = os.path.splitext(file_name)[1].lower()

#             # ✅ Determine file type (audio or video)
#             is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv"]

#             # ✅ Check if file already exists in MongoDB
#             existing_file = fs.find_one({"filename": file_name})
#             if existing_file:
#                 file_id = existing_file._id
#                 logging.info(f"📂 File already exists in MongoDB with ID: {file_id}")
#             else:
#                 file_id = fs.put(
#                     media_file.read(),
#                     filename=file_name,
#                     metadata={"upload_timestamp": datetime.utcnow(), "type": "transcription"}
#                 )
#                 logging.info(f"📤 File uploaded to MongoDB GridFS with ID: {file_id}")

#             # Save to temporary file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
#                 temp_file.write(fs.get(file_id).read())
#                 temp_file_path = temp_file.name

#             logging.info(f"📂 Temporary file created at: {temp_file_path}")

#         else:
#             return jsonify({"error": "No media file provided"}), 400

#         # ✅ Extract audio from video if necessary
#         if is_video:
#             audio_path = temp_file_path.replace(file_ext, ".wav")
#             cmd = ["ffmpeg", "-i", temp_file_path, "-q:a", "0", "-map", "a", audio_path, "-y"]
#             subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#             logging.info(f"🎥 Extracted audio from video: {audio_path}")
#         else:
#             audio_path = temp_file_path

#         # 🎙 Step 3: Transcription with timestamps
#         transcription_result = client.speech_to_text.convert(
#             file=open(audio_path, "rb"),
#             model_id="scribe_v1",
#             num_speakers=2,
#             diarize=True,
#             timestamps_granularity="word"
#         )
#         transcription = transcription_result.text.strip()

        

#         # Extract word-level timestamps
#         word_timings = [
#             {"word": w.text, "start": w.start, "end": w.end}
#             for w in transcription_result.words
#             if hasattr(w, "start") and hasattr(w, "end")
#         ]

#         # 🧹 Step 4: Remove filler words
#         cleaned_transcript = remove_filler_words(transcription)

#         # 🔊 Step 5: Detect background noise
#         noise_detection_result = detect_background_noise(audio_path)

#         # 🛑 Step 6: Detect filler words
#         filler_sentences = detect_filler_words(transcription)

#         # 🎯 Step 7: Sentence classification
#         sentence_analysis = classify_sentence_relevance(transcription)

#         # 🎯 Step 8: Certainty level analysis
#         sentence_certainty_scores = analyze_certainty_levels(transcription)

#         # Assign timestamps to sentences dynamically
#         sentence_timestamps = []
#         video_clips = {}

#         for idx, entry in enumerate(sentence_certainty_scores):
#             timestamps = get_sentence_timestamps(entry["sentence"], word_timings)
#             entry["start"] = timestamps["start"]
#             entry["end"] = timestamps["end"]
#             entry["id"] = idx  # Add unique ID

#             sentence_timestamps.append({
#                 "id": idx,
#                 "sentence": entry["sentence"],
#                 "start": timestamps["start"],
#                 "end": timestamps["end"]
#             })

#             # ✅ Generate standard video clip
#             if is_video:
#                 clip_path = f"/tmp/clip_{idx}.mp4"
#                 cut_video_clip(temp_file_path, timestamps["start"], timestamps["end"], clip_path)
#                 video_clips[idx] = clip_path  # Store normal clip path

#                 # ✅ Generate rewinded video clip (5 seconds earlier)
#                 rewind_start_time = max(0, timestamps["start"] - 5)  # Prevent negative values
#                 rewind_clip_path = f"/tmp/rewind_clip_{idx}.mp4"
#                 cut_video_clip(temp_file_path, rewind_start_time, timestamps["end"], rewind_clip_path)
#                 video_clips[f"rewind_{idx}"] = rewind_clip_path  # Store rewinded clip path

#         # ✂ Step 9: Suggested AI cuts with timestamps
#         suggested_cuts = [
#             {
#                 "sentence": entry["sentence"],
#                 "certainty_level": entry["certainty_level"],
#                 "certainty_score": entry["certainty"],
#                 "start": entry["start"],
#                 "end": entry["end"]
#             }
#             for entry in sentence_certainty_scores if entry["certainty"] >= 0.6
#         ]

#         # 🎭 Step 10: AI Sentiment Analysis
#         sentiment_result = analyze_sentiment(transcription)

#         # ✍ Step 11: AI Show Notes Generation
#         ai_show_notes = generate_ai_show_notes(transcription)

#         # ✅ Bulk selection storage
#         selected_sentences = []  # To track sentences selected for removal

#         logging.info(f"🔍 FULL AUDIO TRANSCRIPT: {json.dumps(sentence_certainty_scores, indent=2)}")

#         # 🔄 Final Response
#         return jsonify({
#             "message": "✅ AI Media processing completed successfully",
#             "file_id": str(file_id),
#             "cleaned_transcript": cleaned_transcript,
#             "background_noise": noise_detection_result,
#             "sentence_certainty_scores": sentence_certainty_scores,
#             "sentence_timestamps": sentence_timestamps,
#             "long_pauses": detect_long_pauses(audio_path),
#             "suggested_cuts": suggested_cuts,
#             "selected_sentences": selected_sentences,
#             "sentiment": sentiment_result,
#             "ai_show_notes": ai_show_notes,
#             "video_clips": video_clips  
#         })

#     except Exception as e:
#         logging.error(f"❌ ERROR: Failed to process media - {str(e)}")
#         return jsonify({"error": f"Failed to process media: {str(e)}"}), 500

#     finally:
#         if temp_file_path:
#             try:
#                 if temp_file_path and os.path.exists(temp_file_path):
#                     os.remove(temp_file_path)  # ✅ Ensure file is closed before deleting
#                     logging.info(f"🗑️ Temporary file deleted: {temp_file_path}")
#             except PermissionError:
#                 logging.warning(f"⚠️ Unable to delete temp file: {temp_file_path}, it might still be in use.")
#         if is_video and os.path.exists(audio_path):
#             os.remove(audio_path)  # ✅ Cleanup extracted audio
#             logging.info(f"🗑️ Extracted audio file deleted: {audio_path}")

