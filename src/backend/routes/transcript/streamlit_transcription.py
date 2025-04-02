# src/backend/routes/transcript/streamlit_transcription.py
import streamlit as st
import requests
import base64
import os
import logging
import tempfile
from dotenv import load_dotenv
import sys

# Load environment variables early
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL")

# ----------------------------
# Helper Functions
# ----------------------------
def format_transcription(transcription):
    """Convert list of dictionaries to a readable string."""
    if isinstance(transcription, list):
        return "\n".join(
            [f"[{item['start']}-{item['end']}] {item['speaker']}: {item['text']}" for item in transcription]
        )
    return transcription

def download_button(label, file_path, filename):
    """Generate a download button for processed files."""
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = filename.split(".")[-1]
        href = f'<a href="data:file/{ext};base64,{b64}" download="{filename}">{label}</a>'
        return st.markdown(href, unsafe_allow_html=True)
    return st.warning("Processed file not found. Try again.")

def download_button_text(label, text, filename):
    if isinstance(text, list):
        text = format_transcription(text)
    b64 = base64.b64encode(text.encode()).decode()
    return st.download_button(label, text, filename, key=filename)

def download_button_image(label, image_path, filename):
    """Creates a download button for an image."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode()
        ext = filename.split(".")[-1]
        mime = f"image/{ext if ext != 'jpg' else 'jpeg'}"
        href = f'<a href="data:{mime};base64,{b64}" download="{filename}">{label}</a>'
        return st.markdown(href, unsafe_allow_html=True)
    else:
        return st.warning("Image not found.")

def translate_text(text, target_language):
    if not text.strip():
        return text
    try:
        response = requests.post(
            f"{API_BASE_URL}/translate",
            json={"text": text, "language": target_language},
        )
        if response.status_code == 200:
            return response.json().get("translated_text", "Translation failed")
        else:
            return f"Translation failed: {response.text}"
    except Exception as e:
        return f"Error contacting translation API: {e}"

# ----------------------------
# Initialize Session State
# ----------------------------
for key in ["transcription", "transcription_no_fillers", "ai_suggestions", "show_notes", "quotes", "quote_images"]:
    if key not in st.session_state:
        st.session_state[key] = ""
    if f"{key}_translated" not in st.session_state:
        st.session_state[f"{key}_translated"] = ""

# ----------------------------
# App Header & Description
# ----------------------------
st.markdown(
    "<h1 style='display: inline;'>PodManagerAI - </h1><h3 style='display: inline;'>Transcription & AI Enhancement</h3>",
    unsafe_allow_html=True,
)
st.write("Upload an audio file to get an AI-enhanced transcription with show notes.")

# ----------------------------
# Tabs for Navigation
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "🎙 AI-Powered Transcription",
    "🎵 AI Audio Enhancement & Cutting Editor",
    "📹 AI Video Enhancement & Cutting Editor"
])

# ----------------------------
# Tab 1: AI-Powered Transcription
# ----------------------------
with tab1:
    st.subheader("🎙 AI-Powered Transcription")

    # Initialize extra session_states to control visibility
    if "show_clean_transcript" not in st.session_state:
        st.session_state.show_clean_transcript = False
    if "show_ai_suggestions" not in st.session_state:
        st.session_state.show_ai_suggestions = False
    if "show_show_notes" not in st.session_state:
        st.session_state.show_show_notes = False
    if "show_quotes" not in st.session_state:
        st.session_state.show_quotes = False
    if "show_quote_images" not in st.session_state:
        st.session_state.show_quote_images = False

    # File upload
    uploaded_file = st.file_uploader(
        "📂 Choose an audio or video file",
        type=["wav", "mp3", "m4a", "ogg", "mp4", "mov", "avi", "mkv", "webm"],
        key="file_uploader",
    )

    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        is_video = file_ext in ["mp4", "mov", "avi", "mkv", "webm"]

        # Show audio or video player
        if not is_video:
            st.audio(uploaded_file, format="audio/wav")
        else:
            st.video(uploaded_file)

        if st.button("▶ Transcribe"):
            with st.spinner("🔄 Transcribing... Please wait."):
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                try:
                    response = requests.post(f"{API_BASE_URL}/transcribe", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.raw_transcription = result.get("raw_transcription", "")
                        st.session_state.transcription_no_fillers = result.get("transcription_no_fillers", "")
                        st.session_state.ai_suggestions = result.get("ai_suggestions", "")
                        st.session_state.show_notes = result.get("show_notes", "")
                        st.session_state.quotes = result.get("quotes", "")
                        st.session_state.quote_images = result.get("quote_images", [])

                        # Reset display flags so that older data is not shown
                        st.session_state.show_clean_transcript = False
                        st.session_state.show_ai_suggestions = False
                        st.session_state.show_show_notes = False
                        st.session_state.show_quotes = False
                        st.session_state.show_quote_images = False

                        st.success("✅ Transcription complete!")
                    else:
                        st.error(f"❌ Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")

    # Language list
    languages = ["English", "Spanish", "French", "German", "Swedish", "Japanese", "Chinese", "Italian", "Portuguese"]

    # Show transcription
    if st.session_state.get("raw_transcription", ""):
        # ---- Raw transcription ----
        st.markdown("## 📜 Raw Transcription")
        transcription_text = st.session_state.get("transcription_translated") or st.session_state.raw_transcription
        st.text_area("Raw Transcription", value=transcription_text, height=200)

        # Translate transcript
        language_transcription = st.selectbox("🌍 Translate Raw Transcription to:", languages)
        if st.button("Translate Raw Transcription"):
            st.session_state["transcription_translated"] = translate_text(
                st.session_state.raw_transcription,
                language_transcription
            )
            st.experimental_rerun()

        # Download button
        download_button_text(
            "⬇ Download Raw Transcription",
            st.session_state.get("transcription_translated", st.session_state.raw_transcription),
            "raw_transcription.txt"
        )

        # ---- Transcription Enhancement Tools ----
        st.markdown("---")
        st.markdown("## 🔧 Transcription Enhancement Tools")

        # 1) Clean Transcript
        st.markdown("### 🧹 Clean Transcript")
        st.write("Removes filler words and unnecessary expressions from your transcript.")
        if st.button("Generate Clean Transcript"):
            payload = {"transcript": st.session_state.raw_transcription}
            response = requests.post(f"{API_BASE_URL}/clean", json=payload)
            if response.status_code == 200:
                st.session_state.transcription_no_fillers = response.json().get("clean_transcript", "")
                st.session_state.show_clean_transcript = True  # Show field
                st.success("Clean transcript generated!")
            else:
                st.error("Failed to clean transcript.")

        # Show clean transcript
        if st.session_state.show_clean_transcript and st.session_state.transcription_no_fillers:
            st.text_area("Clean Transcript", value=st.session_state.transcription_no_fillers, height=200)

        # 2) AI Suggestions
        st.markdown("### 🤖 AI Suggestions")
        st.write("Get ideas or improvements for your transcript, e.g. better phrasing or structure.")
        if st.button("Generate AI Suggestions"):
            payload = {"transcript": st.session_state.raw_transcription}
            response = requests.post(f"{API_BASE_URL}/ai_suggestions", json=payload)
            if response.status_code == 200:
                st.session_state.ai_suggestions = response.json().get("ai_suggestions", "")
                st.session_state.show_ai_suggestions = True
                st.success("AI suggestions generated!")
            else:
                st.error("Failed to generate AI suggestions.")

        if st.session_state.show_ai_suggestions and st.session_state.ai_suggestions:
            st.text_area("AI Suggestions", value=st.session_state.ai_suggestions, height=200)

        # 3) Show Notes
        st.markdown("### 📝 Show Notes")
        st.write("Automatically summarize the main points in the transcript for easy reference.")
        if st.button("Generate Show Notes"):
            payload = {"transcript": st.session_state.raw_transcription}
            response = requests.post(f"{API_BASE_URL}/show_notes", json=payload)
            if response.status_code == 200:
                st.session_state.show_notes = response.json().get("show_notes", "")
                st.session_state.show_show_notes = True
                st.success("Show notes generated!")
            else:
                st.error("Failed to generate show notes.")

        if st.session_state.show_show_notes and st.session_state.show_notes:
            st.text_area("Show Notes", value=st.session_state.show_notes, height=200)

        # 4) Quotes
        st.markdown("### 💬 Generate Quotes")
        st.write("Extract memorable quotes from your transcript.")
        if st.button("Generate Quotes"):
            payload = {"transcript": st.session_state.raw_transcription}
            response = requests.post(f"{API_BASE_URL}/quotes", json=payload)
            if response.status_code == 200:
                st.session_state.quotes = response.json().get("quotes", "")
                st.session_state.show_quotes = True
                st.success("Quotes generated!")
            else:
                st.error("Failed to generate quotes.")

        # Show quotes
        if st.session_state.show_quotes and st.session_state.quotes:
            st.text_area("Quotes", value=st.session_state.quotes, height=200)

            # 5) Quote Images (only shown after "Generate Quotes")
            st.markdown("### 🖼️ Generate Quote Images")
            st.write("Turn the extracted quotes into shareable images.")
            if st.button("Generate Quote Images"):
                payload = {"quotes": st.session_state.quotes}
                response = requests.post(f"{API_BASE_URL}/quote_images", json=payload)
                if response.status_code == 200:
                    st.session_state.quote_images = response.json().get("quote_images", [])
                    st.session_state.show_quote_images = True
                    st.success("Quote images generated!")
                else:
                    st.error("Failed to generate quote images.")

            # Show generated images
            if st.session_state.show_quote_images and st.session_state.get("quote_images", []):
                st.markdown("#### Your Quote Images")
                for i, url in enumerate(st.session_state.quote_images, 1):
                    if url:
                        st.image(url, use_column_width=True)
                        st.markdown(f"[⬇ Download Image {i}]({url})", unsafe_allow_html=True)
                        
# ----------------------------
# Tab 2: AI Audio Enhancement
# ----------------------------

with tab2:
    st.subheader("🎙 Audio Enhancement & AI analysis")
    
    # **Upload audio file for enhancement**
    audio_file = st.file_uploader("📂 Upload an audio file", type=["wav", "mp3"], key="audio_uploader")

    if audio_file:
        st.audio(audio_file, format="audio/wav")
        st.text("🔊 Original Audio File")

        if st.button("Enhance Audio"):
            with st.spinner("🔄 Enhancing audio..."):
                files = {"audio": audio_file}
                try:
                    # Send the file to the backend API for enhancement
                    response = requests.post(f"{API_BASE_URL}/audio/enhancement", files=files)

                    # Log the response status code
                    logger.info(f"Response from /audio/enhancement: {response.status_code}")

                    if response.status_code == 200:
                        # Get the file ID of the enhanced audio from GridFS
                        enhanced_audio_file_id = response.json().get("enhanced_audio")
                        logger.info(f"Enhanced audio file ID: {enhanced_audio_file_id}")

                        if enhanced_audio_file_id:
                            st.success("✅ Audio enhancement completed!")

                            # Log the file ID before making the request
                            logger.info(f"🆔 Fetching enhanced audio with ID: {enhanced_audio_file_id}")
                            print(f"🆔 Fetching enhanced audio with ID: {enhanced_audio_file_id}")  # Print to console

                            # Request the enhanced audio file from GridFS
                            # Log the request before sending
                            logger.info(f"📡 Fetching enhanced audio from {API_BASE_URL}/get_file/{enhanced_audio_file_id}")

                            # Fetch the file
                            enhanced_audio_response = requests.get(f"{API_BASE_URL}/get_file/{enhanced_audio_file_id}")

                            # Log the response status
                            logger.info(f"📩 Response status: {enhanced_audio_response.status_code}")

                            # Check if response is OK
                            if enhanced_audio_response.status_code == 200:
                                logger.info(f"✅ File received! Size: {len(enhanced_audio_response.content)} bytes")
                                st.audio(enhanced_audio_response.content, format="audio/wav")

                                # Store in session state
                                st.session_state["enhanced_audio"] = enhanced_audio_response.content

                                # Add download button
                                st.download_button(
                                    label="📥 Download Enhanced Audio",
                                    data=enhanced_audio_response.content,
                                    file_name="enhanced_audio.wav",
                                    mime="audio/wav"
                                )
                            else:
                                logger.error(f"❌ Failed to fetch file. Response: {enhanced_audio_response.text}")
                                st.error("❌ Failed to fetch the enhanced audio file. Please try again.")

                        else:
                            logger.error("Processed audio file ID not found in the response.")
                            st.error("❌ Processed audio file not found.")
                    else:
                        logger.error(f"Error enhancing audio. Status code: {response.status_code}")
                        st.error("❌ Error enhancing audio.")
                except requests.exceptions.RequestException as e:
                    # Log any exception that occurs during the request
                    logger.error(f"Request failed: {e}")
                    st.error("❌ Error enhancing audio. Please check your network or try again.")

    # **Show AI Emotion and Sentiment Analysis Only If Enhancement Is Done**
    if "enhanced_audio" in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 AI Analysis")

        # **Button to analyze emotion, sentiment, clarity, background noise, and speech rate**
        if st.button("📊 Analyze"):
            with st.spinner("🔄 Analyzing..."):
                # Create a temporary file to store the enhanced audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                    temp_audio_file.write(st.session_state["enhanced_audio"])
                    temp_audio_file_path = temp_audio_file.name  # Get the temporary file path

                logger.info(f"📝 Temporary file created for analysis: {temp_audio_file_path}")

                # Send the file to the analysis API
                with open(temp_audio_file_path, "rb") as f:
                    response = requests.post(f"{API_BASE_URL}/audio_analysis", files={"audio": f})

                # Delete the temporary file after use
                os.remove(temp_audio_file_path)
                logger.info(f"🗑️ Temporary file deleted: {temp_audio_file_path}")

                if response.status_code == 200:
                    emotion = response.json().get("emotion")
                    sentiment = response.json().get("sentiment")
                    clarity_score = response.json().get("clarity_score")
                    background_noise = response.json().get("background_noise")
                    speech_rate = response.json().get("speech_rate")

                    st.success("✅ Analysis completed!")
                    st.write(f"📊 **Detected Emotion**: {emotion}")
                    st.write(f"📊 **Sentiment**: {sentiment}")
                    # Display Clarity Score Breakdown in a readable format
                    # 🧠 Handle Clarity Score Breakdown Safely
                    if clarity_score and isinstance(clarity_score, str):
                        clarity_lines = clarity_score.split("\n")

                        if len(clarity_lines) >= 4:
                            st.write(f"📊 **Clarity Score**: {clarity_lines[0]}")
                            st.write(f"**Filler Words Detected**: {clarity_lines[1]}")
                            st.write(f"**Readability (Flesch-Kincaid Score)**: {clarity_lines[2]}")
                            st.write(f"**Filler Word Penalty**: {clarity_lines[3]}")
                        else:
                            st.warning("⚠️ Incomplete clarity score data received.")
                    else:
                        st.error("❌ No clarity score data available from backend.")

                    # ✅ Extract Flesch-Kincaid Score safely
                    try:
                        clarity_lines = clarity_score.split("\n") if clarity_score and isinstance(clarity_score, str) else []

                        flesch_kincaid_line = next((line for line in clarity_lines if "Flesch-Kincaid" in line), None)
                        if flesch_kincaid_line:
                            flesch_kincaid_score = float(flesch_kincaid_line.split(": ")[1])
                        else:
                            flesch_kincaid_score = None
                    except (IndexError, ValueError, TypeError) as e:
                        st.warning(f"⚠️ Could not extract Flesch-Kincaid Score. Error: {e}")
                        flesch_kincaid_score = None

                    # ✅ Explain the score
                    if flesch_kincaid_score is not None:
                        if flesch_kincaid_score <= 5:
                            grade_level = "easy to understand"
                            example_text = "This is an example of a simple sentence: 'The cat sleeps.'"
                        elif flesch_kincaid_score <= 8:
                            grade_level = "understandable for middle school students"
                            example_text = "This is an example of a slightly more complex sentence: 'The cat sleeps on the chair, enjoying the sun.'"
                        else:
                            grade_level = "for high school or above"
                            example_text = "This is an example of a more complex sentence: 'The feline, basking in the sunlight, curled up on the chair, exhibiting a peaceful demeanor.'"

                        st.write(f"**Flesch-Kincaid Score Explanation**: A score of {flesch_kincaid_score} indicates that the text is {grade_level}.")
                        st.write(f"**Example of Readability**: {example_text}")
                    st.write("**Filler Words Penalty**: A higher number of filler words results in a lower clarity score.")

                    # Tips
                    st.write("**Tips to Improve Clarity**:")
                    st.write("- Avoid filler words such as 'um', 'ah', 'like', 'you know', etc.")
                    st.write("- Keep sentences short and clear to improve readability.")
                    st.write("- Ensure the speech flows smoothly, without unnecessary pauses.")

                    # Display background noise result
                    st.write(f"📊 **Background Noise Detection**: {background_noise}") 

                    # Display speech rate (WPM)
                    st.write(f"📊 **Speech Rate**: {speech_rate}")

                    # Explanation of Speech Rate (WPM)
                    st.write("**What Speech Rate (WPM) Means**:")
                    st.write(f"**Speech Rate**: The speech rate is calculated as the number of words spoken per minute (WPM).")
                    st.write(f"A speech rate of **{speech_rate}** WPM means that the speaker spoke approximately **{speech_rate}** words every minute.")
                    st.write("**How to interpret the number**:")
                    st.write("- **Below 100 WPM**: Slower pace, with more pauses between words. Might indicate deliberate speech or careful articulation.")
                    st.write("- **100–130 WPM**: Typical for casual conversation. Common in everyday discussions.")
                    st.write("- **130–160 WPM**: A bit faster pace, common in public speaking, presentations, or storytelling.")
                    st.write("- **Above 160 WPM**: Indicates faster speech, possibly rushed or energetic. Often seen in fast talkers or during rapid discussions.")
                    st.write("- **Ideal Range**: For comfortable understanding, a speech rate around **120–150 WPM** is usually considered ideal in conversation.")

                    # Enable listening and downloading the enhanced audio after analysis
                    st.audio(st.session_state["enhanced_audio"], format="audio/wav")
                    st.download_button(
                        label="📥 Download Enhanced Audio",
                        data=st.session_state["enhanced_audio"],
                        file_name="enhanced_audio.wav",
                        mime="audio/wav"
                    )

                else:
                    st.error("❌ Error analyzing emotion, sentiment, clarity, or background noise.")
                    
    st.markdown("---")
    st.subheader("🎤 Voice Isolation (Powered by ElevenLabs)")

    # Upload audio file for voice isolation
    voice_file = st.file_uploader("📂 Upload an audio file for voice isolation", type=["wav", "mp3"], key="voice_isolator")

    if voice_file:
        st.audio(voice_file, format="audio/wav")
        st.text("🎧 Original Audio (Before Isolation)")

        if st.button("🎙️ Isolate Voice"):
            with st.spinner("🔄 Isolating voice using ElevenLabs..."):
                try:
                    files = {"audio": voice_file}
                    response = requests.post(f"{API_BASE_URL}/voice_isolate", files=files)

                    if response.status_code == 200:
                        isolated_id = response.json().get("isolated_file_id")
                        st.success("✅ Voice isolation completed!")

                        # Fetch the isolated file from MongoDB
                        fetch_url = f"{API_BASE_URL}/get_file/{isolated_id}"
                        logger.info(f"📡 Fetching isolated voice file from: {fetch_url}")
                        isolated_response = requests.get(fetch_url)

                        if isolated_response.status_code == 200:
                            st.audio(isolated_response.content, format="audio/wav")
                            st.session_state["isolated_voice"] = isolated_response.content

                            st.download_button(
                                label="📥 Download Isolated Voice",
                                data=isolated_response.content,
                                file_name="isolated_voice.wav",
                                mime="audio/wav"
                            )
                        else:
                            st.error("❌ Failed to fetch isolated voice file.")
                    else:
                        st.error(f"❌ Isolation failed: {response.text}")

                except Exception as e:
                    logger.error(f"Voice isolation request failed: {e}")
                    st.error("❌ Voice isolation failed. Please try again.")

                    
    # Audio Cutting Section
    st.markdown("---")  # Adds a separator
    st.subheader("✂ Audio Cutting")

    # Upload audio file for cutting
    audio_file_cut = st.file_uploader("📂 Upload an audio file for cutting", type=["wav", "mp3"], key="audio_uploader_cut")

    if audio_file_cut:
        # Display audio player
        st.audio(audio_file_cut, format="audio/wav")
        st.text("🔊 Audio File for Cutting")

        # **Check if file is already uploaded using session state**
        if "uploaded_audio_id" not in st.session_state:
            with st.spinner("🔄 Uploading file to MongoDB..."):
                files = {"audio": audio_file_cut}
                response = requests.post(f"{API_BASE_URL}/get_audio_info", files=files)

                if response.status_code == 200:
                    result = response.json()
                    st.session_state["uploaded_audio_id"] = result["audio_file_id"]  # Store in session state
                    st.session_state["waveform_file_id"] = result["waveform"]  # Store waveform ID
                    st.session_state["audio_duration"] = result["duration"]  # Store duration

                    print(f"🆔 Stored audio file ID: {st.session_state['uploaded_audio_id']}")
                    print(f"🆔 Stored waveform file ID: {st.session_state['waveform_file_id']}")

        # Get values from session state (avoiding re-upload)
        audio_file_id = st.session_state.get("uploaded_audio_id")
        waveform_file_id = st.session_state.get("waveform_file_id")
        duration = st.session_state.get("audio_duration")

        # Fetch waveform image from MongoDB
        if waveform_file_id:
            waveform_response = requests.get(f"{API_BASE_URL}/get_file/{waveform_file_id}")
            print(f"📡 Waveform fetch status: {waveform_response.status_code}")

            if waveform_response.status_code == 200:
                st.markdown("### 🎚 Audio Waveform")
                st.image(waveform_response.content, use_container_width=True)

        # **Audio Clipping Section**
        st.markdown("### ✂ Select & Cut Audio")

        # **Sliders for start & end time**
        start_time = st.slider("Start Time (seconds)", 0.0, duration, 0.0, step=0.1, key="start_time_cut")
        end_time = st.slider("End Time (seconds)", 0.0, duration, duration, step=0.1, key="end_time_cut")

        # Prevent invalid selections
        if start_time >= end_time:
            st.warning("⚠ Start time must be less than end time.")

        if st.button("✂ Cut Audio"):
            with st.spinner("🔄 Processing audio..."):
                if not audio_file_id:
                    st.error("❌ Error: No audio file ID found!")
                    st.stop()

                data = {"file_id": audio_file_id, "clips": [{"start": start_time, "end": end_time}]}

                response = requests.post(f"{API_BASE_URL}/clip_audio", json=data)

                print(f"📡 Clip request sent. Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    clipped_audio_file_id = result.get("clipped_audio")
                    print(f"🆔 Clipped audio file ID: {clipped_audio_file_id}")

                    if clipped_audio_file_id:
                        st.success("✅ Audio clipping completed!")
                        clipped_audio_response = requests.get(f"{API_BASE_URL}/get_file/{clipped_audio_file_id}")

                        print(f"📡 Clipped audio fetch status: {clipped_audio_response.status_code}")

                        if clipped_audio_response.status_code == 200:
                            st.audio(clipped_audio_response.content, format="audio/wav")
                            st.download_button(label="📥 Download Clipped Audio",
                                            data=clipped_audio_response.content,
                                            file_name="clipped_audio.wav",
                                            mime="audio/wav")
                        else:
                            st.error("❌ Error fetching clipped audio file.")
                    else:
                        st.error("❌ Error: Clipped file ID not found.")
                else:
                    print(f"❌ Error clipping audio. Response: {response.text}")
                    st.error("❌ Error clipping audio. Try again.")



    # ---- AI Audio Cutting Section ---- #
    st.markdown("---")  # Adds a separator
    st.subheader("✂ AI Audio Cutting")

    # Upload audio file for AI cutting
    audio_file_cut_ai = st.file_uploader("📂 Upload an audio file for AI cutting", type=["wav", "mp3"], key="audio_uploader_cut_ai")

    if audio_file_cut_ai:
        # ✅ Prevent multiple uploads by checking if we already have a file_id
        if "file_id" not in st.session_state:
            with st.spinner("🔄 Uploading file to MongoDB..."):
                # Send file to backend to store in MongoDB
                files = {"audio": audio_file_cut_ai}
                upload_response = requests.post(f"{API_BASE_URL}/get_audio_info", files=files)

                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    st.session_state.file_id = upload_result.get("audio_file_id")
                    st.session_state.waveform_id = upload_result.get("waveform")  # Store waveform file ID
                    st.session_state.duration = upload_result.get("duration", 60.0)  # Default to 60s

                    st.text("🔊 Audio File Uploaded. Click 'Analyze Audio' to start AI processing.")
                else:
                    st.error("❌ Error uploading file to MongoDB.")
                    st.stop()
        else:
            st.text("✅ File already uploaded. Click 'Analyze Audio' to start AI processing.")

    # **Analyze Audio Button (Only show if file is uploaded)**
    if "file_id" in st.session_state:
        if st.button("Analyze Audio"):
            with st.spinner("🔄 Using AI to process audio..."):
                if "file_id" not in st.session_state:
                    st.error("❌ No audio file ID found. Please upload an audio file first.")
                    st.stop()

                file_id = st.session_state.file_id

                # Step 1: Fetch waveform from MongoDB
                waveform_response = requests.get(f"{API_BASE_URL}/get_file/{st.session_state.waveform_id}")

                if waveform_response.status_code == 200:
                    st.session_state.waveform_path = waveform_response.content
                else:
                    st.error("❌ Error fetching waveform.")

                # Step 2: Analyze audio with AI using MongoDB file ID (No duplicate uploads!)
                response = requests.post(f"{API_BASE_URL}/ai_cut_audio", json={"file_id": file_id, "clips": []})

                if response.status_code == 200:
                    result = response.json()

                    st.session_state.cleaned_transcript = result.get("cleaned_transcript", "No transcript available.")
                    st.session_state.background_noise = result.get("background_noise", "No noise detected.")
                    st.session_state.suggested_cuts = result.get("suggested_cuts", [])
                    st.session_state.sentence_certainty_scores = result.get("sentence_certainty_scores", [])
                    st.session_state.sentence_timestamps = result.get("sentence_timestamps", [])
                    st.session_state.long_pauses = result.get("long_pauses", [])
                    st.session_state.selected_sentences = []  # Initialize bulk selection list
                    st.session_state.removed_sentences = []  # Store removed sentences for Undo Last
                    st.session_state.original_transcript = result.get("sentence_certainty_scores", [])[:]  # Store Original State for Undo All

                    # ✅ Add AI Sentiment Analysis & Show Notes
                    st.session_state.ai_sentiment = result.get("sentiment", "Unknown")  # Store sentiment
                    st.session_state.ai_show_notes = result.get("ai_show_notes", "No notes available.")  # Store AI-generated show notes

                    st.session_state.analyzed = True  # Flag that analysis was completed
                else:
                    st.error("❌ Error processing AI analysis.")



    # Ensure the analysis has been done before trying to show results
    if st.session_state.get("analyzed", False):

        # Display long pauses detected by AI
        st.write("⏸ **Detected Long Pauses**", unsafe_allow_html=True)
        if st.session_state.long_pauses:
            for pause in st.session_state.long_pauses:
                st.write(f"⏳ Pause from {pause['start']}s to {pause['end']}s")
        else:
            st.text("✅ No long pauses detected.")

         # 🎭 Display AI Sentiment Analysis
        st.write("🤖 **AI Sentiment Analysis**", unsafe_allow_html=True)
        st.write(f"**Overall Sentiment:** {st.session_state.get('ai_sentiment', 'Unknown')}")

        # Display background noise result
        st.write("🔊 **Background Noise Detection**", unsafe_allow_html=True)
        st.text(st.session_state.background_noise if "background_noise" in st.session_state else "No noise detected.")

        # Display suggested AI cuts
        st.write("✂ **Suggested AI Cuts**", unsafe_allow_html=True)
        if st.session_state.suggested_cuts:
            for cut in st.session_state.suggested_cuts:
                st.write(f"**Sentence:** {cut['sentence']}")
                st.write(f"**Certainty Level:** {cut['certainty_level']} (Start: {cut['start']}s, End: {cut['end']}s)")
        else:
            st.text("✅ No suggested cuts found.")



        # **Toggle for full transcript view**
        full_transcript_view = st.checkbox("Show Full Transcript (Including Low Certainty)", value=False)

        # **Filter transcript by 60% certainty level by default**
        displayed_sentences = st.session_state.sentence_certainty_scores if full_transcript_view else [
            entry for entry in st.session_state.sentence_certainty_scores if entry["certainty"] >= 0.6
        ]

        st.markdown("### 📝 AI Processed Transcript")
        for idx, entry in enumerate(displayed_sentences):
            sentence_id = entry.get("id", hash(entry["sentence"]))  # Ensure unique ID
            is_selected = sentence_id in st.session_state.selected_sentences

            # **Checkbox for Bulk Selection**
            if st.checkbox(f"Select", key=f"select_{idx}", value=is_selected):
                if sentence_id not in st.session_state.selected_sentences:
                    st.session_state.selected_sentences.append(sentence_id)
            else:
                if sentence_id in st.session_state.selected_sentences:
                    st.session_state.selected_sentences.remove(sentence_id)

            # **Manual Editing of Sentence**
            new_sentence = st.text_input(f"Edit Sentence {idx + 1}", entry['sentence'], key=f"edit_{idx}")
            entry["sentence"] = new_sentence  # Update stored sentence

            st.write(f"**Certainty Level:** {entry['certainty_level']} (Score: {entry['certainty']})")

            certainty_percent = entry['certainty'] * 100
            color = {
                "Green": "green",
                "Light Green": "lightgreen",
                "Yellow": "yellow",
                "Orange": "orange",
                "Dark Orange": "darkorange",
                "Red": "red"
            }.get(entry["certainty_level"], "gray")

            st.markdown(
                f"""
                <div style="background-color: #ddd; border-radius: 10px; width: 100%;">
                    <div style="background-color: {color}; height: 20px; width: {certainty_percent}%; border-radius: 10px;"></div>
                </div>
                """, unsafe_allow_html=True
            ) 

            # 🎵 Play & Rewind Sentence Controls
            sentence_id = entry.get("id", idx)  

            timestamp = next((s for s in st.session_state.sentence_timestamps if s["id"] == sentence_id), None)

            if timestamp:
                start_time = timestamp["start"]
                rewind_time = max(0, start_time - 5)  # Prevent negative times

                # Play Sentence Button
                if st.button(f"▶ Play {entry['sentence'][:10]}...", key=f"play_{idx}"):
                    if "file_id" in st.session_state:
                        file_id = st.session_state.file_id
                        audio_response = requests.get(f"{API_BASE_URL}/get_file/{file_id}")

                        if audio_response.status_code == 200:
                            st.audio(audio_response.content, format="audio/wav", start_time=rewind_time)
                        else:
                            st.error("❌ Failed to fetch audio from MongoDB.")

                # Rewind 5 Seconds Button
                if st.button(f"🔙 Rewind 5s Before {entry['sentence'][:10]}...", key=f"rewind_{idx}"):
                    # Fetch audio for rewind from MongoDB
                    if "file_id" in st.session_state:
                        file_id = st.session_state.file_id
                        audio_response = requests.get(f"{API_BASE_URL}/get_file/{file_id}")

                        if audio_response.status_code == 200:
                            st.audio(audio_response.content, format="audio/wav", start_time=rewind_time)
                        else:
                            st.error("❌ Failed to fetch audio from MongoDB.")

            else:
                st.warning(f"⚠ No timestamp found for Sentence {idx + 1}")

            st.markdown("")  # Adds a separator



        # **Apply Bulk Deletion**
        # Remove Selected Sentences
        if st.button("🗑 Remove Selected Sentences", key="remove_selected"):
            st.session_state.removed_sentences = st.session_state.sentence_certainty_scores[:]  # Save for Undo Last
            st.session_state.sentence_certainty_scores = [
                entry for entry in st.session_state.sentence_certainty_scores
                if entry.get("id") not in st.session_state.selected_sentences
            ]
            st.session_state.selected_sentences = []  # Clear selection
            st.rerun()

        # Undo Last Removal
        if st.button("⏪ Undo Last Removal", key="undo_last_removal"):
            if st.session_state.removed_sentences:
                st.session_state.sentence_certainty_scores = st.session_state.removed_sentences[:]  # Restore last removed
                st.session_state.removed_sentences = []  # Clear undo history
                st.rerun()

        # Undo All Removals
        if st.button("⏪⏪ Undo All Removals", key="undo_all_removals"):
            st.session_state.sentence_certainty_scores = st.session_state.original_transcript[:]  # Restore full transcript
            st.session_state.removed_sentences = []
            st.session_state.selected_sentences = []
            st.rerun()

        st.markdown("## ❓ What is Magic Cut Threshold?")
        st.info("""
        **Magic Cut Threshold** is an AI-powered editing tool that removes sentences based on a **certainty score** (0-100%).

        🔍 **How It Works:**
        - AI assigns each sentence a certainty score.
        - A **higher score** means it's more likely unnecessary.
        - The **threshold slider** determines which sentences to cut.
        - **Example:** At **70%**, sentences with 70% certainty or higher are removed.

        ⚡ **How to Use:**
        1. Adjust the **Magic Cut Threshold** slider.
        2. Click **"Magic Cut"** to remove high-certainty sentences.
        3. Undo removals anytime.

        🚨 **Tip:**
        - **Lower threshold (0.4-0.6):** Keeps more content.
        - **Higher threshold (0.8-1.0):** Stricter cut.
        - **You can check your Certaninty score on each sentence ex down below
        - **Certainty Level: Light Green (Score: 0.2499719113111496) then the score is 0.25 = (25%)
        - **So to remove all 25% sentences place the Treshhold Slider under 0.25 and press magic cut button. 
        """)

         # Certainty Color Scheme Explanation
        st.markdown("## 🎨 Certainty Level Color Scheme")

        st.info("""
        Each sentence is analyzed by AI and assigned a **certainty level**, which indicates the likelihood of removal.

        🔍 **Certainty Levels & Colors**
        - **🟢 0-20% (Green)** → Very unlikely to be removed (important content).
        - **🟡 20-40% (Light Green)** → Slightly off-topic but likely valuable.
        - **🟠 40-60% (Yellow)** → Potential filler, context-dependent.
        - **🟧 60-80% (Orange)** → Strong removal suggestion (repetitive/off-topic).
        - **🔶 80-90% (Dark Orange)** → Highly likely to be removed.
        - **🔴 90-100% (Red)** → Almost certain removal (filler, unnecessary words).

        ✂ **How to Use This**
        - **Lower threshold (0.4-0.6)** → Keeps more content.
        - **Higher threshold (0.8-1.0)** → Removes more aggressively.
        - **Check each sentence's color before making final cuts!**
        """)

        # **Certainty Threshold Slider for Magic Cut**
        st.session_state.certainty_threshold = st.slider("Magic Cut Threshold", 0.0, 1.0, 0.6, step=0.1)

        # **Magic Cut Button**
        if st.button("✂ Magic Cut Sentences Above Threshold", key="magic_cut_button"):
            st.session_state.removed_sentences = st.session_state.sentence_certainty_scores[:]  # Save for Undo Last
            st.session_state.sentence_certainty_scores = [
                entry for entry in st.session_state.sentence_certainty_scores
                if entry["certainty"] < st.session_state.certainty_threshold  # ✅ Corrected filtering
            ]
            st.session_state.selected_sentences = []  # Clear selection
            st.rerun()




        st.markdown("---")  # Adds a separator



        # ✅ **Final Transcript & Export Section (Placed Below Magic Cut)**
        st.markdown("### 📝 Final Transcript & Export")

        # Display final cleaned transcript
        cleaned_sentences = [entry["sentence"] for entry in st.session_state.sentence_certainty_scores]
        final_transcript = "\n".join(cleaned_sentences)

        st.text_area("Final Processed Transcript", value=final_transcript, height=250)

        # **Download Transcript Button**
        st.download_button("📥 Download Transcript (.txt)", data=final_transcript, file_name="final_transcript.txt", mime="text/plain")

        # 📝 Display AI-Generated Show Notes
        st.markdown("### 📝 AI-Generated Show Notes")
        ai_notes = st.session_state.get("ai_show_notes", "No notes available.")
        st.text_area("Show Notes", value=ai_notes, height=250)

        # 📥 Download AI Show Notes
        st.download_button("📥 Download AI Show Notes", data=ai_notes, file_name="ai_show_notes.txt", mime="text/plain")

        st.markdown("---")  # Adds a separator


        # ✅ Display waveform image above the sliders
        if st.session_state.waveform_path:
            st.markdown("### 🎚 Audio Waveform")
            st.image(st.session_state.waveform_path, use_container_width=True)
        else:
            st.warning("⚠ No waveform available.")

        st.markdown("### 🎚 AI Cutting Controls")

        # Sliders for selecting start and end times
        start_time = st.slider("Start Time (seconds)", 0.0, st.session_state.duration, 0.0, step=0.1)
        end_time = st.slider("End Time (seconds)", 0.0, st.session_state.duration, st.session_state.duration, step=0.1)

        if start_time >= end_time:
            st.warning("⚠ Start time must be less than end time.")

       # Ensure `file_id` is set correctly from previous AI processing
        file_id = st.session_state.get("file_id")

        # **Cut & Export Button**
        if st.button("✂ Cut & Preview Audio", key="cut_preview_audio"):
            if file_id:
                with st.spinner("🔄 Processing cut..."):
                    cut_data = {"file_id": file_id, "clips": [{"start": start_time, "end": end_time}]}

                    final_response = requests.post(
                        f"{API_BASE_URL}/clip_audio",
                        json=cut_data  # ✅ Send MongoDB file_id instead of re-uploading
                    )

                    if final_response.status_code == 200:
                        final_result = final_response.json()
                        clipped_audio_file_id = final_result.get("clipped_audio")

                        # ✅ Store the new clipped file ID in session state
                        if clipped_audio_file_id:
                            st.session_state.final_audio_file_id = clipped_audio_file_id

        # **Preview & Download Cut Audio**
        if "final_audio_file_id" in st.session_state:
            clipped_audio_file_id = st.session_state.final_audio_file_id
            clipped_audio_response = requests.get(f"{API_BASE_URL}/get_file/{clipped_audio_file_id}")

            if clipped_audio_response.status_code == 200:
                st.audio(clipped_audio_response.content, format="audio/wav")

                st.download_button(
                    "📥 Download Cut Audio",
                    data=clipped_audio_response.content,
                    file_name="cut_audio.wav",
                    mime="audio/wav"
                )
            else:
                st.error("❌ Error fetching clipped audio file.")
        else:
            st.warning("⚠ No processed audio available. Please cut the audio first.")



# ----------------------------
# Tab 3: AI Video Enhancement & Analysis
# ----------------------------

with tab3:
    st.subheader("📹 Video Enhancement & AI Analysis")

    # ---- Video Upload Section ----
    video_file = st.file_uploader("📂 Upload a video file", type=["mp4", "mov", "mkv"], key="video_uploader")
    if video_file:
        st.video(video_file)
        st.text("🎬 Original Video File")

        # Upload video to MongoDB if not already uploaded
        if "video_id" not in st.session_state:
            with st.spinner("🔄 Uploading video to MongoDB..."):
                files = {"video": video_file}
                upload_response = requests.post(f"{API_BASE_URL}/ai_videoedit", files=files)
                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    st.session_state["video_id"] = upload_result.get("video_id")
                    st.text("✅ Video Uploaded! Click 'Enhance Video' to start processing.")
                else:
                    st.error("❌ Error uploading video.")
                    st.stop()
        else:
            st.text("✅ Video already uploaded. Click 'Enhance Video' to start processing.")

        # ---- Video Enhancement Section ----
        if st.button("Enhance Video"):
            with st.spinner("🔄 Enhancing video..."):
                video_id = st.session_state["video_id"]
                response = requests.post(f"{API_BASE_URL}/ai_videoenhance", json={"video_id": video_id})
                if response.status_code == 200:
                    processed_video_id = response.json().get("processed_video_id")
                    if processed_video_id:
                        st.success("✅ Video enhancement completed!")
                        st.session_state["processed_video_id"] = processed_video_id
                        # Update video URL using /get_video endpoint
                        processed_video_url = f"{API_BASE_URL}/get_video/{processed_video_id}"
                        st.video(processed_video_url)
                        st.markdown(f"[📥 Download Enhanced Video]({processed_video_url})", unsafe_allow_html=True)
                    else:
                        st.error("❌ Processed video file not found.")
                else:
                    st.error("❌ Error enhancing video.")

    # ---- AI Video Analysis Section ----
    if "processed_video_id" in st.session_state:
        st.markdown("---")
        st.subheader("📊 AI Video Analysis")
        if st.button("Analyze Video"):
            with st.spinner("🔄 Analyzing video..."):
                video_id = st.session_state["processed_video_id"]
                response = requests.post(f"{API_BASE_URL}/ai_videoanalysis", json={"video_id": video_id})
                if response.status_code == 200:
                    analysis_results = response.json()
                    st.success("✅ Video analysis completed!")
                    
                    st.write("📜 **Transcript:**")
                    st.write(analysis_results.get("transcript", "No transcript available"))
                    
                    st.write("🔊 **Background Noise Detection:**")
                    st.write(analysis_results.get("background_noise", "No data available"))
                    
                    st.write("🗣 **Sentiment Analysis:**")
                    st.write(analysis_results.get("sentiment", "No sentiment available"))
                    
                    # Optional: Visual Quality
                    visual_quality = analysis_results.get("visual_quality")
                    if visual_quality:
                        st.write("🎨 **Visual Quality:**")
                        st.write(f"Sharpness: {visual_quality.get('sharpness', 'N/A')}")
                        st.write(f"Contrast: {visual_quality.get('contrast', 'N/A')}")
                    
                    # Optional: Speech Rate
                    speech_rate = analysis_results.get("speech_rate")
                    if speech_rate:
                        st.write("⏱ **Speech Rate:**")
                        st.write(speech_rate)
                else:
                    st.error("❌ Error analyzing video.")

    # ---- Video Cutting Section ----
    st.markdown("---")
    st.subheader("✂ Video Cutting")
    video_file_cut = st.file_uploader("📂 Upload a video file for cutting", type=["mp4", "mov", "mkv"], key="video_uploader_cut")
    if video_file_cut:
        st.video(video_file_cut)
        st.text("🎬 Original Video File for Cutting")

        # Upload video for cutting if not already uploaded
        if "uploaded_video_id" not in st.session_state:
            with st.spinner("🔄 Uploading video to MongoDB..."):
                files = {"video": video_file_cut}
                upload_response = requests.post(f"{API_BASE_URL}/ai_videoedit", files=files)
                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    st.session_state["uploaded_video_id"] = upload_result.get("video_id")
                    st.text("✅ Video Uploaded! You can now cut it.")
                else:
                    st.error("❌ Error uploading video.")
                    st.stop()
        else:
            st.text("✅ Video already uploaded for cutting.")

        video_id = st.session_state.get("uploaded_video_id")
        if video_id:
            st.markdown("### ✂ Select & Cut Video")
            duration = st.number_input("Enter total duration of video (seconds)", min_value=1.0, step=0.1)
            start_time_video = st.slider("Start Time (seconds)", 0.0, duration, 0.0, step=0.1, key="start_time_video_cut")
            end_time_video = st.slider("End Time (seconds)", 0.0, duration, duration, step=0.1, key="end_time_video_cut")
            
            if start_time_video >= end_time_video:
                st.warning("⚠ Start time must be less than end time.")
            
            if st.button("✂ Cut Video"):
                with st.spinner("🔄 Processing video..."):
                    data = {"video_id": video_id, "clips": [{"start": start_time_video, "end": end_time_video}]}
                    response = requests.post(f"{API_BASE_URL}/clip_video", json=data)
                    if response.status_code == 200:
                        result = response.json()
                        clipped_video_id = result.get("clipped_video")
                        if clipped_video_id:
                            st.success("✅ Video clipping completed!")
                            clipped_video_url = f"{API_BASE_URL}/get_video/{clipped_video_id}"
                            st.video(clipped_video_url)
                            st.markdown(f"[📥 Download Clipped Video]({clipped_video_url})", unsafe_allow_html=True)
                        else:
                            st.error("❌ Error: Clipped file ID not found.")
                    else:
                        st.error("❌ Error clipping video. Try again.")

# # Initialize session state variables
# for key in ["transcription", "transcription_no_fillers", "ai_suggestions", "show_notes", "quotes"]:
#     if key not in st.session_state:
#         st.session_state[key] = ""
#     if f"{key}_translated" not in st.session_state:
#         st.session_state[f"{key}_translated"] = ""

# # 📌 **Sidhuvud**
# st.markdown("<h1 style='display: inline;'>PodManagerAI - </h1><h3 style='display: inline;'>Transcription & AI Enhancement</h3>", unsafe_allow_html=True)

# st.write("Upload an audio file to get an AI-enhanced transcription with show notes.")

# # 📌 **Flikar för navigering**
# tab1, tab2, tab3 = st.tabs(["🎙 AI-Powered Transcription", "🎵 AI Audio Enhancement & cutting editor", "📹 AI Video Enhancement & cutting editor"])

# # 🎙 **Flik 1: AI-Powered Transcription**
# with tab1:
#     st.subheader("🎙 AI-Powered Transcription")
#     uploaded_file = st.file_uploader(
#         "📂 Choose an audio or video file", 
#         type=["wav", "mp3", "m4a", "ogg", "mp4", "mov", "avi", "mkv", "webm"], 
#         key="file_uploader"
#     )

#     if uploaded_file is not None:
#         file_ext = uploaded_file.name.split(".")[-1].lower()
#         is_video = file_ext in ["mp4", "mov", "avi", "mkv", "webm"]

#         # 🎵 If it's an audio file, show an audio player
#         if not is_video:
#             st.audio(uploaded_file, format="audio/wav")

#         # 🎬 If it's a video file, show the video
#         else:
#             st.video(uploaded_file)

#         if st.button("▶ Transcribe"):
#             with st.spinner("🔄 Transcribing... Please wait."):
#                 files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

#                 try:
#                     response = requests.post(f"{API_BASE_URL}/transcribe", files=files)
#                     result = response.json()

#                     if response.status_code == 200:
#                         result = response.json()

#                         # ✅ Correct keys
#                         st.session_state.raw_transcription = result.get("raw_transcription", "")
#                         st.session_state.transcription_no_fillers = result.get("transcription_no_fillers", "")
#                         st.session_state.ai_suggestions = result.get("ai_suggestions", "")
#                         st.session_state.show_notes = result.get("show_notes", "")
#                         st.session_state.quotes = result.get("quotes", [])
#                         st.session_state.quote_images = result.get("quote_images", [])

#                         # ✅ Also assign to short keys (optional for legacy)
#                         st.session_state["transcription"] = st.session_state.raw_transcription
#                         st.session_state["transcription_no_fillers"] = st.session_state.transcription_no_fillers

#                         st.success("✅ Transcription complete!")

#                     else:
#                         st.error(f"❌ Error: {response.status_code} - {response.text}")

#                 except Exception as e:
#                     st.error(f"Request failed: {str(e)}")

#     # Language selection
#     languages = ["English", "Spanish", "French", "German", "Swedish", "Japanese", "Chinese", "Italian", "Portuguese"]

#     # Display stored transcriptions if available
#     if "raw_transcription" in st.session_state:
#             st.subheader("📜 Raw Transcription")
            
#             # ✅ Use the correct key: `raw_transcription`
#             transcription_text = st.session_state.get("transcription_translated")
#             if not transcription_text:
#                 transcription_text = st.session_state.get("raw_transcription", "")

#             if transcription_text:
#                 st.text_area("📜 Raw Transcription", value=transcription_text, height=200, key="raw_transcription_display")
#             else:
#                 st.warning("⚠️ No transcription available. Please transcribe a file first.")

#             # Translation dropdown & button
#             language_transcription = st.selectbox("🌍 Translate Raw Transcription to:", languages, key="lang_transcription")
#             if st.button("Translate Raw Transcription"):
#                 st.session_state["transcription_translated"] = translate_text(st.session_state.raw_transcription, language_transcription)
#                 st.rerun()  

#             # Download button
#             download_button_text("⬇ Download Raw Transcription", st.session_state.get("transcription_translated", st.session_state.raw_transcription), "raw_transcription.txt")

        
#             with st.expander("🤖 AI cleaned trancript + Suggested Transcription"):
#                 ai_suggestions_text = st.session_state.get("ai_suggestions_translated", st.session_state.ai_suggestions)
#                 ai_suggestions_text = st.text_area("", ai_suggestions_text, height=200, key="ai_suggestions")

#                 language_ai_suggestions = st.selectbox("🌍 Translate AI-Suggested Transcription to:", languages, key="lang_ai_suggestions")
#                 if st.button("Translate AI-Suggested Transcription"):
#                     st.session_state["ai_suggestions_translated"] = translate_text(st.session_state.ai_suggestions, language_ai_suggestions)
#                     st.rerun()  

#                 download_button_text("⬇ Download AI-Suggested Transcription", st.session_state.get("ai_suggestions_translated", st.session_state.ai_suggestions), "ai_suggestions.txt")

#             # 🔹 AI-Generated Show Notes
#             with st.expander("📝 AI-Generated Show Notes & Marketing Snippets"):
#                 show_notes_text = st.session_state.get("show_notes_translated", st.session_state.show_notes)
#                 show_notes_text = st.text_area("", show_notes_text, height=200, key="show_notes")

#                 language_show_notes = st.selectbox("🌍 Translate AI-Generated Show Notes to:", languages, key="lang_show_notes")
#                 if st.button("Translate AI-Generated Show Notes"):
#                     st.session_state["show_notes_translated"] = translate_text(st.session_state.show_notes, language_show_notes)
#                     st.rerun()  

#                 download_button_text("⬇ Download AI-Generated Show Notes", st.session_state.get("show_notes_translated", st.session_state.show_notes), "ai_show_notes.txt")
            

#             with st.expander("💬 AI-Generated Quotes"):
#                 quotes_text = st.session_state.get("quotes_translated", st.session_state.quotes) or ""
#                 st.text_area("💬 Quotes", value=quotes_text, height=200, key="quotes")

#                 language_quotes = st.selectbox("🌍 Translate Quotes to:", languages, key="lang_quotes")
#                 if st.button("Translate Quotes"):
#                     st.session_state["quotes_translated"] = translate_text(quotes_text, language_quotes)
#                     st.rerun()

#                 download_button_text("⬇ Download AI-Generated Quotes", st.session_state.get("quotes_translated", quotes_text), "ai_quotes.txt")

#                 # 🖼️ Display quote images (from URLs)
#                 quote_images = st.session_state.get("quote_images", [])
#                 if quote_images:
#                     st.markdown("### 🖼️ Quote Images")
#                     for i, url in enumerate(quote_images, 1):
#                         if url:
#                             st.image(url, use_column_width=True)
#                             st.markdown(f"[⬇ Download Image {i}]({url})", unsafe_allow_html=True)