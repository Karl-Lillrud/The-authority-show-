import re

def slugify(text):
    """
    Convert a string to a URL-friendly slug.
    Example: "My Awesome Podcast!" -> "my-awesome-podcast"
    """
    if text is None:
        return ""
    text = str(text).lower()
    text = re.sub(r'\s+', '-', text)  # Replace spaces with -
    text = re.sub(r'[^\w\-]', '', text)  # Remove all non-word chars (letters, numbers, underscore) except -
    text = re.sub(r'\-{2,}', '-', text)  # Replace multiple - with single -
    text = text.strip('-')  # Remove leading/trailing -
    return text

