import re

def extract_highlights(description):
    # Example logic to extract key highlights from the description
    highlights = []
    sentences = re.split(r'(?<=[.!?]) +', description)
    for sentence in sentences:
        if "important" in sentence.lower() or "key" in sentence.lower():
            highlights.append(sentence)
    return highlights

def process_default_tasks(data):
    # Ensure defaultTasks is None if it's an empty list
    if "defaultTasks" in data and isinstance(data["defaultTasks"], list):
        if len(data["defaultTasks"]) == 0:
            data["defaultTasks"] = None
        else:
            # Save defaultTasks as regular tasks to episodes
            data["tasks"] = data["defaultTasks"]
            data["defaultTasks"] = None
    return data