import os
import logging
import networkx as nx
import numpy as np
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure necessary NLTK resources are available
nltk.download('punkt')

def textrank_summary(text, num_sentences=3):
    """
    Extracts the most important sentences from the text using TextRank.
    """
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return sentences
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    similarity_matrix = np.dot(tfidf_matrix, tfidf_matrix.T).toarray()
    
    graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(graph)
    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    
    summary = [s[1] for s in ranked_sentences[:num_sentences]]
    return summary


def generate_accurate_quote(text):
    """
    Generates an accurate quote based on the extracted key sentences.
    """
    key_sentences = textrank_summary(text, num_sentences=2)
    quote = ' '.join(key_sentences)
    logger.info(f"Generated Quote: {quote}")
    return quote

# # Example usage
# if __name__ == "__main__":
#     sample_text = """Machine learning is a method of data analysis that automates analytical model building. 
#     It is a branch of artificial intelligence based on the idea that systems can learn from data, 
#     identify patterns and make decisions with minimal human intervention."""
    
#     print(generate_accurate_quote(sample_text))
