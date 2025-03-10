import openai
import requests
import os

# 🔑 Set API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# 📌 Function to gather OSINT information
def get_osint_info(person_name):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are OSINT-GPT, an expert in gathering open-source intelligence."},
            {"role": "user", "content": f"Find detailed and recent information about {person_name}."}
        ]
    )
    return response['choices'][0]['message']['content']

# 📌 Function to create podcast scripts
def create_podcast_scripts(osint_info, person_name):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a podcast scriptwriter."},
            {"role": "user", "content": f"Based on the following information about {person_name}, write an engaging podcast intro and outro:\n{osint_info}"}
        ]
    )
    return response['choices'][0]['message']['content']

# 📌 Function to convert text to speech using ElevenLabs API
def text_to_speech(script):
    url = "https://api.elevenlabs.io/v1/text-to-speech/default"
    headers = {
        "xi-api-key": elevenlabs_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": script,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        with open("podcast_intro_outro.mp3", "wb") as audio_file:
            audio_file.write(response.content)
        print("Audio saved as podcast_intro_outro.mp3")
    else:
        print("Error:", response.status_code)
