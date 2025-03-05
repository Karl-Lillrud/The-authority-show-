import whisper


def transcribe_audio(audio_path, episode_id):
    """ Transcribe audio using Whisper AI and save the result to MongoDB """
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path, language="sv", word_timestamps=True)

    # Create transcript data in the expected format
    transcript_data = [
        {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        }
        for segment in result["segments"]
    ]
    print("Audio transcription completed.")

    # Save the transcript to MongoDB
    transcript_document = {
        "episodeId": str(episode_id),
        "transcript": transcript_data
    }

    transcripts_collection.insert_one(transcript_document)
    print("Transcript uploaded successfully.")
    return transcript_data