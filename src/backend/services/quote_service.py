import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.sentiment import SentimentIntensityAnalyzer
import re
import string

#-----------------------------------------------------------------------------
# CONFIGURATION AND SETUP
#-----------------------------------------------------------------------------

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('vader_lexicon')

# Constants
IDEAL_QUOTE_MIN_LENGTH = 8
IDEAL_QUOTE_MAX_LENGTH = 25
ACCEPTABLE_QUOTE_MAX_LENGTH = 35
MIN_MEANINGFUL_WORDS = 5
SIMILARITY_THRESHOLD_DEFAULT = 0.3

# Insight-related keywords
INSIGHT_KEYWORDS = [
    'learn', 'discover', 'realize', 'understand', 'insight',
    'important', 'key', 'essential', 'critical', 'crucial',
    'strategy', 'technique', 'method', 'approach', 'process',
    'experience', 'challenge', 'opportunity', 'problem', 'solution',
    'success', 'failure', 'mistake', 'lesson', 'advice',
    'recommend', 'suggest', 'tip', 'trick', 'hack'
]

# Insight patterns for detection
INSIGHT_PATTERNS = [
    # Lesson learned patterns
    r"(learned|learnt|discover(ed)?|realiz(e|ed)|understand|understood|know|notice(d)?)",
    # Advice/suggestion patterns
    r"(should|must|need to|have to|important to|remember to|don't forget|key is to)",
    # Reflection patterns
    r"(reflect(ing|ed)?|think(ing)? (about|back)|looking back|in (hindsight|retrospect))",
    # Conclusion/summary patterns
    r"(bottom line|in (conclusion|summary|essence)|to sum( it)? up|ultimately|finally)",
    # Personal insight patterns
    r"(what I('ve)? (found|learned|discovered|realized)|my (take|opinion|perspective|view))",
    # Process/method patterns
    r"(the (way|process|method|approach) (is|to)|how (to|you can|I))",
    # Experimental patterns
    r"(experiment(ing|ed)?|try(ing|ed)?|test(ing|ed)?|attempt(ing|ed)?)"
]

# Phrases that commonly introduce insights
INSIGHT_PHRASES = [
    "i think", "i believe", "i found", "i've found", "i've learned",
    "the key is", "the important thing", "what matters", 
    "the lesson", "my advice", "i recommend", "you should",
    "always remember", "never forget", "the best way", 
    "the truth is", "the reality is", "the fact is",
    "in my experience", "what i discovered"
]

# Quotable indicators
QUOTABLE_INDICATORS = [
    'important', 'key', 'remember', 'takeaway', 'learn', 
    'advice', 'tip', 'insight', 'lesson', 'experience',
    'recommend', 'suggestion', 'experiment', 'try', 'discover',
    'essential', 'crucial', 'critical', 'fundamental', 'principle',
    'strategy', 'technique', 'method', 'approach', 'process',
    'secret', 'trick', 'hack', 'shortcut', 'mindset'
]

#-----------------------------------------------------------------------------
# TEXT CLEANING AND PREPROCESSING
#-----------------------------------------------------------------------------

def clean_text(text):
    """
    Clean the text by removing unnecessary whitespace and formatting.
    
    Args:
        text (str): Raw input text
        
    Returns:
        str: Cleaned text with normalized whitespace
    """
    # Replace multiple spaces, newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove any leading/trailing whitespace
    return text.strip()

def extract_sentences(text):
    """
    Extract and clean sentences from text.
    
    Args:
        text (str): Input text to process
        
    Returns:
        list: List of cleaned, meaningful sentences
    """
    text = clean_text(text)
    sentences = sent_tokenize(text)
    
    # Further clean sentences
    clean_sentences = []
    for sentence in sentences:
        # Remove sentences that are too short or likely not meaningful
        if len(sentence.split()) > MIN_MEANINGFUL_WORDS and not sentence.startswith(('um', 'uh', 'eh')):
            # Remove filler words at the beginning
            sentence = re.sub(r'^(um|uh|like|you know|I mean|so)\s+', '', sentence, flags=re.IGNORECASE)
            clean_sentences.append(sentence.strip())
    
    return clean_sentences

#-----------------------------------------------------------------------------
# KEYWORD AND INSIGHT DETECTION
#-----------------------------------------------------------------------------

def identify_important_keywords(text, custom_keywords=None):
    """
    Extract important keywords from the text.
    
    Args:
        text (str): The text to analyze
        custom_keywords (list, optional): Additional keywords to include
        
    Returns:
        list: Important keywords from the text
    """
    # Tokenize and convert to lowercase
    words = word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words and word not in string.punctuation]
    
    # Get frequency distribution
    fdist = FreqDist(words)
    
    # Get top keywords from text
    top_keywords = [word for word, _ in fdist.most_common(30)]
    
    # Combine keywords
    combined_keywords = list(set(top_keywords + INSIGHT_KEYWORDS))
    
    # Add custom keywords if provided
    if custom_keywords:
        combined_keywords.extend(custom_keywords)
    
    return combined_keywords

def detect_insight_patterns(sentence):
    """
    Detect common patterns that indicate insights or key takeaways.
    
    Args:
        sentence (str): The sentence to analyze
        
    Returns:
        int: Score based on how likely the sentence contains an insight
    """
    insight_score = 0
    
    # Check each pattern
    for pattern in INSIGHT_PATTERNS:
        if re.search(pattern, sentence.lower()):
            insight_score += 1
    
    # Check for phrases
    for phrase in INSIGHT_PHRASES:
        if phrase in sentence.lower():
            insight_score += 1
    
    return insight_score

#-----------------------------------------------------------------------------
# SENTENCE SCORING
#-----------------------------------------------------------------------------

def score_sentence_importance(sentence, important_keywords, sia, title_keywords=None):
    """
    Score a sentence based on multiple factors for importance.
    
    Args:
        sentence (str): The sentence to score
        important_keywords (list): List of important keywords from the text
        sia: SentimentIntensityAnalyzer instance
        title_keywords (list, optional): Keywords from the title for extra weight
        
    Returns:
        float: Importance score for the sentence
    """
    # Initialize score
    score = 0
    
    # 1. Length factor - not too short, not too long
    words = word_tokenize(sentence.lower())
    if IDEAL_QUOTE_MIN_LENGTH <= len(words) <= IDEAL_QUOTE_MAX_LENGTH:
        score += 3  # Ideal quote length
    elif IDEAL_QUOTE_MAX_LENGTH < len(words) <= ACCEPTABLE_QUOTE_MAX_LENGTH:
        score += 1  # Acceptable but longer
    elif len(words) > ACCEPTABLE_QUOTE_MAX_LENGTH:
        score -= len(words) // 15  # Penalize very long sentences
    
    # 2. Keyword presence
    keyword_count = sum(1 for word in words if word in important_keywords)
    score += keyword_count * 1.5
    
    # 3. Title keyword presence (if provided)
    if title_keywords:
        title_keyword_count = sum(1 for word in words if word in title_keywords)
        score += title_keyword_count * 2  # Extra weight for title words
    
    # 4. Sentiment intensity (stronger sentiment = potentially more quotable)
    sentiment = sia.polarity_scores(sentence)
    score += abs(sentiment['compound']) * 2  # Higher score for stronger sentiment
    
    # 5. Contains quotable phrases or indicators
    for indicator in QUOTABLE_INDICATORS:
        if indicator in words:
            score += 1.5
    
    # 6. Check for insight patterns
    insight_pattern_score = detect_insight_patterns(sentence)
    score += insight_pattern_score * 2
    
    # 7. Bonus for sentences that seem like conclusions or insights based on structure
    if re.search(r'^(so|therefore|thus|hence|consequently|as a result|this means|this shows|this indicates)', sentence.lower()):
        score += 2
    
    return score

#-----------------------------------------------------------------------------
# UNPUNCTUATED TRANSCRIPT PROCESSING
#-----------------------------------------------------------------------------

def segment_unpunctuated_transcript(transcript):
    """
    Segments an unpunctuated transcript into sentence-like units.
    """
    # Clean the transcript
    transcript = transcript.strip().lower()
    
    # Define pause patterns
    pause_patterns = [
        r'\s+(?:um|uh|er|mm)\s+',  # Filler words
        r'\.\.\.',                  # Ellipsis
        r'\s+(?:and|but|so)\s+',    # Common conjunctions
        r'\s+(?:then|next|after that|later)\s+',  # Temporal markers
        r'\s+(?:well|actually|basically|essentially)\s+',  # Discourse markers
        r'\s+(?:you know|I mean|like)\s+'  # Conversational markers
    ]
    
    # Join patterns
    combined_pattern = '|'.join(pause_patterns)
    
    # Use regex to split on potential sentence boundaries
    segments = re.split(combined_pattern, transcript)
    
    # Clean segments
    clean_segments = []
    for segment in segments:
        # Skip empty or very short segments
        if segment and len(segment.split()) > 3:
            # Clean up the segment
            segment = segment.strip()
            
            # Add period if not present
            if not segment.endswith(('.', '!', '?')):
                segment = segment + '.'
                
            # Capitalize first letter
            segment = segment[0].upper() + segment[1:] if segment else segment
            
            clean_segments.append(segment)
    
    return clean_segments

def merge_short_segments(segments, min_length=6):
    """
    Merges short segments to create more meaningful units.
    """
    if not segments:
        return []
        
    merged = []
    current = segments[0]
    
    for i in range(1, len(segments)):
        # If current segment is too short, merge with next
        if len(current.split()) < min_length:
            current = current[:-1] + ' ' + segments[i]  # Remove period before concatenating
        else:
            merged.append(current)
            current = segments[i]
    
    # Add the last segment
    merged.append(current)
    
    return merged

#-----------------------------------------------------------------------------
# UNPUNCTUATED TRANSCRIPT PROCESSING - IMPROVED
#-----------------------------------------------------------------------------

def is_unpunctuated_text(text):
    """
    Enhanced detection for unpunctuated text with multiple heuristics.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        bool: True if text is likely unpunctuated
    """
    # Skip very short texts
    if len(text) < 100:
        return False
    
    # Check for sentence markers relative to text length
    sentence_markers = sum(1 for char in text if char in ['.', '!', '?'])
    words = text.split()
    word_count = len(words)
    
    # Multiple criteria to detect unpunctuated text:
    
    # 1. Very few punctuation marks relative to word count
    punctuation_ratio = sentence_markers / max(1, word_count)
    if punctuation_ratio < 0.01:  # Fewer than 1 sentence marker per 100 words
        return True
    
    # 2. Look for long stretches of text without sentence-ending punctuation
    segments = re.split(r'[.!?]', text)
    if any(len(segment.split()) > 50 for segment in segments):  # Very long segments
        return True
    
    # 3. Check for lowercase letters after potential sentence boundaries
    # In properly punctuated text, capital letters usually follow period+space
    sentence_boundaries = re.findall(r'[.!?]\s+\w', text)
    if sentence_boundaries:
        lowercase_after_boundary = sum(1 for boundary in sentence_boundaries 
                                      if boundary[-1].islower())
        if lowercase_after_boundary / len(sentence_boundaries) > 0.7:
            return True
    
    # 4. Check for filler words that indicate spoken language without punctuation
    filler_pattern = r'\b(um|uh|like|you know|I mean)\b'
    filler_count = len(re.findall(filler_pattern, text, re.IGNORECASE))
    if filler_count > 5 and (filler_count / word_count) > 0.03:  # More than 3% filler words
        return True
    
    return False

def segment_unpunctuated_transcript(transcript):
    """
    Enhanced segmentation for unpunctuated transcripts using improved patterns.
    
    Args:
        transcript (str): The unpunctuated transcript
        
    Returns:
        list: Segmented text in sentence-like units
    """
    # Clean the transcript
    transcript = transcript.strip()
    
    # Define more sophisticated pause patterns
    pause_patterns = [
        # Strong breaks - likely sentence boundaries
        r'\s+(?:but|so|however|anyway|actually)\s+',  # Conjunctions/transitions
        r'\s+(?:first|second|third|finally|next|then|after that|later)\s+',  # Sequential markers
        r'\s+(?:for example|such as|like when|additionally)\s+',  # Elaboration markers
        r'\s+(?:now|today|yesterday|tomorrow)\s+',  # Time markers
        
        # Medium breaks - potential phrase boundaries
        r'\s+(?:and|or|because|since|as)\s+',  # Conjunctions
        r'\s+(?:although|while|when|if|unless)\s+',  # Subordinating conjunctions
        
        # Weak breaks - potential for pauses within statements
        r'\s+(?:um|uh|er|mm|hmm)\s+',  # Filler words
        r'\s+(?:you know|I mean|like|basically|literally)\s+',  # Conversational fillers
        r'\s+(?:I think|I guess|I suppose|maybe|perhaps)\s+'  # Hedging phrases
    ]
    
    # First apply strong breaks to identify main segments
    strong_pattern = '|'.join(pause_patterns[:4])  # First 4 patterns are strong breaks
    main_segments = re.split(strong_pattern, transcript)
    
    # Then further segment using medium and weak breaks
    all_segments = []
    medium_pattern = '|'.join(pause_patterns[4:6])  # Medium breaks
    
    for segment in main_segments:
        # Further segment only if it's relatively long
        if len(segment.split()) > 25:
            sub_segments = re.split(medium_pattern, segment)
            all_segments.extend(sub_segments)
        else:
            all_segments.append(segment)
    
    # Clean and format segments
    clean_segments = []
    for segment in all_segments:
        # Skip empty or very short segments
        if segment and len(segment.split()) > 3:
            # Clean up the segment
            segment = segment.strip()
            
            # Remove fillers at beginning of segment
            segment = re.sub(r'^(um|uh|er|like|you know|I mean)\s+', '', segment, flags=re.IGNORECASE)
            
            # Add period if not present
            if not segment.endswith(('.', '!', '?')):
                segment = segment + '.'
                
            # Capitalize first letter
            if segment:
                segment = segment[0].upper() + segment[1:] if segment[0].islower() else segment
            
            clean_segments.append(segment)
    
    return clean_segments

def merge_short_segments(segments, min_length=8, max_merged_length=30):
    """
    Merge short segments more intelligently to create meaningful units.
    
    Args:
        segments (list): List of text segments
        min_length (int): Minimum desired segment length (in words)
        max_merged_length (int): Maximum length after merging
        
    Returns:
        list: List of merged segments
    """
    if not segments:
        return []
        
    merged = []
    current = segments[0]
    current_word_count = len(current.split())
    
    for i in range(1, len(segments)):
        next_segment = segments[i]
        next_word_count = len(next_segment.split())
        combined_count = current_word_count + next_word_count
        
        # Decide whether to merge based on multiple criteria
        should_merge = (
            # Merge if current segment is too short
            (current_word_count < min_length) or
            # Or if combining would create an ideally sized segment
            (combined_count <= max_merged_length) or
            # Or if there's a clear continuation pattern
            (re.search(r'\b(and|but|or|because|so|which|that|who|where|when)$', current.rstrip('.'), re.IGNORECASE))
        )
        
        if should_merge:
            # Remove period before concatenating
            if current.endswith('.'):
                current = current[:-1] + ' ' + next_segment
            else:
                current = current + ' ' + next_segment
            current_word_count = len(current.split())
        else:
            merged.append(current)
            current = next_segment
            current_word_count = next_word_count
    
    # Add the last segment
    merged.append(current)
    
    # Final cleanup pass - check for segments still too short
    final_merged = []
    for i, segment in enumerate(merged):
        if len(segment.split()) < min_length and i < len(merged) - 1:
            # Merge with next segment if this one is still too short
            combined = segment.rstrip('.') + ' ' + merged[i+1]
            final_merged.append(combined)
            # Skip the next segment since we've merged it
            merged[i+1] = ''
        elif segment:  # Only add non-empty segments
            final_merged.append(segment)
    
    return [seg for seg in final_merged if seg]  # Filter out any empty segments

def filter_incomplete_thoughts(segments):
    """
    Filter out segments that appear to be incomplete thoughts or false starts.
    
    Args:
        segments (list): List of text segments
        
    Returns:
        list: Filtered segments
    """
    filtered_segments = []
    
    # Patterns that suggest incomplete thoughts
    incomplete_patterns = [
        r'^(So|Um|Uh|Well|And|But|Or)\s+.{0,20}$',  # Short segment starting with filler
        r'^I (was going to|wanted to|thought I would|think I|mean I).{0,15}$',  # Abandoned first-person statements
        r'^\w+\s+\w+\s+\w+\s*$',  # Very short, likely fragment (3 words or less)
        r'.*\b(like|sort of|kind of)\s*$',  # Ends with hedge words without completion
        r'^\s*(the|this|that|these|those|it|they|we|I)\s+.{0,10}$'  # Pronoun/article with minimal content
    ]
    
    for segment in segments:
        # Skip if it matches incomplete patterns
        if any(re.match(pattern, segment, re.IGNORECASE) for pattern in incomplete_patterns):
            continue
            
        # Skip if it has an unusually high ratio of filler words
        filler_count = len(re.findall(r'\b(um|uh|like|you know|I mean)\b', segment, re.IGNORECASE))
        word_count = len(segment.split())
        
        if word_count > 0 and (filler_count / word_count) > 0.2:  # More than 20% fillers
            continue
            
        # Skip segments that end abruptly with prepositions or articles
        if re.search(r'\b(of|in|on|with|the|a|an|to)\s*$', segment.rstrip('.'), re.IGNORECASE):
            continue
            
        filtered_segments.append(segment)
    
    return filtered_segments



def parse_speaker_based_transcript(transcript_text):
    """
    Parse a transcript with speaker annotations and timestamps into a format
    suitable for quote extraction.
    
    Format expected: "[start-end] Speaker N: text content"
    
    Args:
        transcript_text (str): The speaker-annotated transcript
        
    Returns:
        dict: Dictionary with 'text' (clean transcript), 'speakers' (speaker segments)
    """
    lines = transcript_text.strip().split('\n')
    clean_text = []
    speaker_segments = []
    current_speaker = None
    current_segment = ""
    
    for line in lines:
        # Try to match the timestamp and speaker pattern
        match = re.search(r'\[([0-9.]+)-([0-9.]+)\]\s+(Speaker\s+\d+):\s+(.*)', line)
        
        if match:
            start_time, end_time, speaker, content = match.groups()
            
            # If we're starting a new speaker segment, save the previous one
            if current_speaker and current_speaker != speaker and current_segment.strip():
                speaker_segments.append({
                    'speaker': current_speaker,
                    'text': current_segment.strip()
                })
                current_segment = ""
            
            # Update the current speaker and append to current segment
            current_speaker = speaker
            current_segment += " " + content
            
            # Add to the clean text regardless
            clean_text.append(content)
        else:
            # For lines without speaker annotation, just add them to both collections
            clean_text.append(line)
            if current_speaker:
                current_segment += " " + line
    
    # Add the last segment if it exists
    if current_speaker and current_segment.strip():
        speaker_segments.append({
            'speaker': current_speaker,
            'text': current_segment.strip()
        })
    
    return {
        'text': ' '.join(clean_text),
        'speakers': speaker_segments
    }

def _clean_and_format_quote(quote):
    """
    Clean up a quote for presentation, thoroughly removing all timestamps, speaker annotations,
    named entity references, and filler words.
    
    Args:
        quote (str): The raw quote
        
    Returns:
        str: Cleaned and formatted quote
    """
    # Remove timestamp pattern with speaker identifier
    cleaned = re.sub(r'\[\d+\.\d+-\d+\.\d+\]\s+Speaker\s+\d+:', '', quote)
    
    # Remove just timestamp pattern (without speaker)
    cleaned = re.sub(r'\[\d+\.\d+-\d+\.\d+\]', '', cleaned)
    
    # Remove speaker identifier at beginning of line
    cleaned = re.sub(r'^Speaker\s+\d+:', '', cleaned)
    
    # Remove speaker identifier anywhere in text
    cleaned = re.sub(r'Speaker\s+\d+:', '', cleaned)
    
    # Remove references to specific people that might not have context
    # Expanded common names pattern to catch more potential named entities
    cleaned = re.sub(r'\b(Maria|Tom|John|Sarah|David|Michael|Jennifer|Robert|Jessica|Alex|Karen)\'s\b', '', cleaned)
    cleaned = re.sub(r'\b(Maria|Tom|John|Sarah|David|Michael|Jennifer|Robert|Jessica|Alex|Karen)\b', '', cleaned)
    
    # Remove possessive references that might lack context
    cleaned = re.sub(r'\b(his|her|their)( approach| method| technique| strategy| perspective| opinion)\b', 'this approach', cleaned)
    
    # Remove filler words and clean up whitespace
    cleaned = re.sub(r'\b(um|uh|like|you know|I mean)\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Make sure the quote ends with proper punctuation
    if not cleaned.endswith(('.', '!', '?')):
        cleaned += '.'
    
    # Capitalize first letter if it's lowercase
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
        
    return cleaned


# ---- The pattern-based contextless reference detection function ----

def has_contextless_references(quote):
    """
    Check if a quote contains references that would lack context without relying on name lists.
    Uses linguistic patterns and structural analysis instead of hardcoded names.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote contains potentially confusing references
    """
    # Pattern 1: Possessive noun followed by concept word
    # This catches "Emma's approach" or "Raj's strategy" without hardcoding names
    possessive_noun_pattern = r'\b([A-Z][a-z]+\'s)\s+(approach|method|technique|strategy|perspective|opinion|view|idea|theory|concept|philosophy|thinking|point|position|stance)\b'
    if re.search(possessive_noun_pattern, quote):
        return True
    
    # Pattern 2: Standalone capitalized word at start that's likely a name
    # This catches quotes starting with a proper noun that might be a name
    starting_capitalized_word = r'^\s*([A-Z][a-z]+)\s+(is|was|has|had|says|said|believes|believed|thinks|thought|argues|argued|suggests|suggested|recommends|recommended)'
    if re.search(starting_capitalized_word, quote):
        return True
    
    # Pattern 3: Possessive references that likely refer to specific people
    possessive_pattern = r'\b(his|her|their)\s+(approach|method|technique|strategy|perspective|opinion|view|idea)\b'
    if re.search(possessive_pattern, quote):
        return True
    
    # Pattern 4: Start with "The X approach is" where X could be a person's adjective
    # e.g., "The Socratic approach is" or "The Cartesian approach is"
    named_approach_pattern = r'^\s*The\s+([A-Z][a-z]+)(ian|esque|ist)?\s+approach\s+is'
    if re.search(named_approach_pattern, quote):
        return True
    
    # Pattern 5: "According to X" or similar attribution patterns
    attribution_pattern = r'\b(according to|as per|as stated by|as mentioned by|as noted by|as explained by)\s+([A-Z][a-z]+)'
    if re.search(attribution_pattern, quote):
        return True
    
    # Pattern 6: Catches uses of "approach" where the context is likely missing
    standalone_pattern = r'^\s*(The|This|Their)\s+(approach|method|technique|strategy|perspective|view)\s+is\b'
    if re.search(standalone_pattern, quote, re.IGNORECASE):
        # Check if the quote is a complete thought about an approach in general
        if len(quote.split()) < 12: # Short references to an approach are likely missing context
            return True
        
        # Check if it sounds like a general principle rather than specific reference
        general_principles = ['focuses on', 'emphasizes', 'prioritizes', 'centers around', 
                             'based on', 'revolves around', 'involves', 'consists of']
        if not any(principle in quote.lower() for principle in general_principles):
            return True
    
    return False


# ---- Enhanced standalone value function with improved pattern-based detection ----

def has_standalone_value(quote):
    """
    Determines if a quote can stand alone without needing additional context.
    Now uses pattern-based reference detection instead of name lists.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote is likely to have standalone value
    """
    # First check for contextless references
    if has_contextless_references(quote):
        return False
    
    # Check for pronouns that might refer to people mentioned earlier
    contextual_pronouns_pattern = r'^\s*(he|she|they|his|her|their|this person|these people)\s+'
    if re.match(contextual_pronouns_pattern, quote.lower()):
        return False
    
    # Check for phrases that imply a response to something mentioned before
    response_phrases = [
        r'^\s*(yes|no|maybe|indeed|exactly|precisely|that\'s right|that\'s correct)',
        r'^\s*(I agree|I disagree|as mentioned|as stated|like I said)',
        r'^\s*(to answer that|responding to|in that case)'
    ]
    for pattern in response_phrases:
        if re.match(pattern, quote.lower()):
            return False
    
    # Check for incomplete comparisons that need context
    incomplete_comparison = r'\b(better|worse|more|less|bigger|smaller) than\b'
    if re.search(incomplete_comparison, quote.lower()) and not re.search(r'than\s+(the|a|an|when|if)', quote.lower()):
        return False
    
    # Check for demonstrative references without clear antecedents
    demonstrative_without_noun = r'\b(this|that|these|those)\b\s+(?!(is|are|was|were|can|could|will|would|should|may|might))'
    if re.search(demonstrative_without_noun, quote.lower()):
        # Only flag as problematic if the demonstrative appears to be referring to an external concept
        words_after = re.search(demonstrative_without_noun + r'\s+(\w+)', quote.lower())
        if words_after and words_after.group(1) not in ['approach', 'concept', 'idea', 'point', 'thing', 'perspective', 'view']:
            return False
    
    # Avoid quotes that start with "approach is" or similar contextless phrases
    if re.match(r'^\s*approach is', quote.lower()):
        return False
        
    return True


# ---- Improved cleaning function with pattern-based reference handling ----

def _clean_and_format_quote(quote):
    """
    Clean up a quote for presentation, removing timestamps, speaker annotations,
    and contextless references without relying on name lists.
    
    Args:
        quote (str): The raw quote
        
    Returns:
        str: Cleaned and formatted quote
    """
    # Remove timestamp pattern with speaker identifier
    cleaned = re.sub(r'\[\d+\.\d+-\d+\.\d+\]\s+Speaker\s+\d+:', '', quote)
    
    # Remove just timestamp pattern (without speaker)
    cleaned = re.sub(r'\[\d+\.\d+-\d+\.\d+\]', '', cleaned)
    
    # Remove speaker identifier at beginning of line
    cleaned = re.sub(r'^Speaker\s+\d+:', '', cleaned)
    
    # Remove speaker identifier anywhere in text
    cleaned = re.sub(r'Speaker\s+\d+:', '', cleaned)
    
    # Remove possessive patterns that likely refer to specific people
    # Instead of removing names, generalize the references
    cleaned = re.sub(r'\b([A-Z][a-z]+)\'s\s+(approach|method|technique|strategy|perspective|opinion|view|idea|theory|concept)', 
                    'This \\2', cleaned)
    
    # Remove possessive pronouns that might lack context
    cleaned = re.sub(r'\b(his|her|their)\s+(approach|method|technique|strategy|perspective|opinion|view|idea)', 
                    'this \\2', cleaned)
    
    # Remove attribution patterns
    cleaned = re.sub(r'\b(according to|as per|as stated by|as mentioned by)\s+([A-Z][a-z]+)',
                    'it has been suggested that', cleaned)
    
    # Remove filler words and clean up whitespace
    cleaned = re.sub(r'\b(um|uh|like|you know|I mean)\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Make sure the quote ends with proper punctuation
    if not cleaned.endswith(('.', '!', '?')):
        cleaned += '.'
    
    # Capitalize first letter if it's lowercase
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
        
    return cleaned


# ---- Updated extract_quotes_from_transcript function with pattern-based filtering ----
# Add these functions to the existing code - they will enhance grammatical integrity in quotes using pattern-based approaches

def check_grammatical_integrity(quote):
    """
    Check that a quote has proper grammatical structure and doesn't have obvious missing words.
    Uses pattern-based detection without relying on specific names or cultural references.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote appears grammatically sound
    """
    # Check for common language patterns that suggest missing words
    problematic_patterns = [
        # Missing subjects - look for verbs without subjects
        r'(?<!\w)\s(is|are|was|were|have|has|had|do|does|did)\s+\b(not\s+)?\b(a|an|the|this|that|these|those)',
        # Look for adjacent prepositions which often indicate a missing word
        r'\b(of|in|on|at|by|for|with|about|from|to|into|onto|upon)\s+\b(of|in|on|at|by|for|with|about|from|to|into|onto|upon)\b',
        # Incomplete comparisons - "what and don't" pattern (missing "you know")
        r'\b(what|where|when|why|how)\s+and\s+\b(don\'t|do not|can\'t|cannot|won\'t|will not)\b',
        # "that and" instead of "that X and"
        r'\b(that|this|those|these)\s+and\s+\b(don\'t|do not|can\'t|cannot|won\'t|will not)\b',
        # Potential missing words between determiners and conjunctions
        r'\b(the|a|an|this|that|those|these|my|your|our|their)\s+\b(and|or|but)\b',
        # Missing objects after transitive verbs
        r'\b(know|understand|learn|see|find|make|take|give|put)\s+\b(and|or|but|because|since|if|while)\b',
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, quote, re.IGNORECASE):
            return False
    
    # Check for overall sentence balance
    # Count opening/closing parentheses, quotes, etc.
    opening_count = sum(1 for c in quote if c in '([{')
    closing_count = sum(1 for c in quote if c in ')]}')
    if opening_count != closing_count:
        return False
    
    # Count quotation marks - should generally be even
    quote_marks = sum(1 for c in quote if c in '\'"')
    if quote_marks % 2 != 0:
        return False
    
    # Check for verbs - a proper sentence should contain at least one verb
    words = word_tokenize(quote.lower())
    # Common verbs to check for - language-agnostic approach focusing on structure
    common_verbs = {'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did',
                   'can', 'could', 'will', 'would', 'should', 'may', 'might',
                   'make', 'take', 'go', 'get', 'know', 'think', 'see', 'come', 'want',
                   'look', 'use', 'find', 'need', 'learn', 'become', 'include',
                   'work', 'feel', 'try', 'leave', 'call'}
    
    # For linguistic universality, also check for common verb endings
    verb_patterns = [r'\w+ing\b', r'\w+ed\b', r'\w+s\b']
    
    has_verb = any(word in common_verbs for word in words)
    if not has_verb:
        # Check for verb patterns if no common verb found
        has_verb_pattern = any(re.search(pattern, quote, re.IGNORECASE) for pattern in verb_patterns)
        if not has_verb_pattern:
            return False
    
    return True

def check_noun_verb_balance(quote):
    """
    Check that a quote has a reasonable balance of nouns and verbs,
    which is a language-agnostic way to validate sentence structure.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote has a reasonable noun-verb balance
    """
    words = word_tokenize(quote.lower())
    
    # Simplified POS detection using common patterns rather than full POS tagging
    # This is more language-agnostic than relying on specific POS taggers
    
    # Common determiners across many languages
    determiners = {'the', 'a', 'an', 'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their'}
    
    # Common verbs (auxiliary and main)
    verbs = {'is', 'are', 'was', 'were', 'be', 'been', 'being',  
         'have', 'has', 'had', 'do', 'does', 'did',  
         'can', 'could', 'shall', 'should', 'will', 'would', 'may', 'might', 'must',  
         'make', 'take', 'go', 'get', 'put', 'bring', 'keep', 'leave', 'let',  
         'tell', 'say', 'ask', 'show', 'call', 'help', 'try', 'start', 'stop',  
         'use', 'need', 'feel', 'seem', 'know', 'think', 'believe',  
         'want', 'like', 'love', 'hate', 'prefer', 'understand', 'remember'}
    
    # Count determiners and verbs as a proxy for nouns and verbs
    determiner_count = sum(1 for word in words if word in determiners)
    verb_count = sum(1 for word in words if word in verbs)
    
    # Also count words ending with common verb suffixes
    verb_suffix_count = sum(1 for word in words if re.search(r'(ing|ed|s)$', word) and word not in determiners)
    
    total_verb_indicators = verb_count + verb_suffix_count
    
    # If we have determiners but no verb indicators, or vice versa, the sentence might be incomplete
    if (determiner_count > 0 and total_verb_indicators == 0) or (determiner_count == 0 and total_verb_indicators > 2):
        return False
        
    return True

def fix_quotes_with_missing_words(quotes):
    """
    Filter out quotes that appear to have grammatical issues or missing words.
    
    Args:
        quotes (list): List of candidate quotes
        
    Returns:
        list: Filtered quotes that pass grammatical checks
    """
    filtered_quotes = []
    
    for quote in quotes:
        # Apply both grammatical checks
        if check_grammatical_integrity(quote) and check_noun_verb_balance(quote):
            filtered_quotes.append(quote)
    
    return filtered_quotes

# Add these additional filtering functions to the existing code

def is_question(quote):
    """
    Detects if a quote is actually a question rather than an insight.
    Uses pattern-based detection to identify interrogative structures.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote appears to be a question
    """
    # Check if the text ends with a question mark
    if quote.strip().endswith('?'):
        return True
    
    # Look for question starters at the beginning of the quote
    question_starters = [
        r'^(what|how|when|where|who|why|which|do|does|did|is|are|was|were|will|would|can|could|should|may|might)',
        r'^(have|has|had|hasn\'t|haven\'t|didn\'t|don\'t|doesn\'t|won\'t|wouldn\'t|isn\'t|aren\'t|wasn\'t|weren\'t)',
    ]
    
    for pattern in question_starters:
        if re.match(pattern, quote.lower().strip()):
            # Check if it's a rhetorical question that provides an answer (these can be insightful)
            # Rhetorical questions often contain their own answers
            rhetorical_patterns = [
                r'(because|the answer is|here\'s why|the reason is)',
                r'(let me tell you|i\'ll explain|that\'s because)',
            ]
            
            has_answer = any(re.search(pattern, quote.lower()) for pattern in rhetorical_patterns)
            if not has_answer:
                return True
    
    # Check for host questions seeking opinions/recommendations
    host_question_patterns = [
        r'(what\'s your|what is your|how would you|what do you|how do you)',
        r'(would you recommend|could you share|can you tell us|what advice)',
        r'(as we wrap up|to conclude|before we finish|one final question)',
        r'(what would you say to|what\'s one takeaway|what lesson|key message)',
    ]
    
    for pattern in host_question_patterns:
        if re.search(pattern, quote.lower()):
            return True
    
    return False

def has_ambiguous_references(quote):
    """
    Checks if a quote contains ambiguous references like "this approach" 
    without proper context.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote contains ambiguous references
    """
    # Look for demonstrative pronouns followed by nouns without prior context
    ambiguous_patterns = [
        # "this X" or "that X" at the beginning of a quote is often ambiguous
        r'^(this|that|these|those)\s+(approach|strategy|method|technique|idea|concept|process|tool|framework|principle|perspective|view|theory|way)',
        # "it" at the beginning
        r'^it\s+(is|was|has|had|can|could|will|would)',
        # References to "the X" without prior context
        r'^the\s+(approach|strategy|method|technique|idea|concept|process|tool|framework|principle|perspective|view|theory|way)',
    ]
    
    # If these patterns appear at the start of a quote, they're likely ambiguous
    for pattern in ambiguous_patterns:
        if re.match(pattern, quote.lower().strip()):
            return True
    
    return False

def has_first_person_experience_without_context(quote):
    """
    Checks if a quote describes a personal experience that lacks sufficient context.
    Often these are anecdotes that don't stand well on their own.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote contains personal experience without context
    """
    # Check for personal experience markers
    experience_patterns = [
        r'(I experienced|I went through|I had a|in my experience|during my|at my|when I was)',
        r'(we experienced|we went through|we had a|in our experience|at our company|in our company)',
        r'(I remember when|I recall|I was working on|I was dealing with)',
    ]
    
    # If these appear in a relatively short quote, they likely lack context
    for pattern in experience_patterns:
        if re.search(pattern, quote, re.IGNORECASE):
            # If the quote is short, it's more likely to lack context
            if len(quote.split()) < 20:
                # Look for specific contextual markers that might make it standalone
                contextual_markers = [
                    r'(taught me that|learned that|realized that|discovered that)',
                    r'(the lesson was|what I learned was|this showed me that)',
                    r'(changed my perspective|shifted my thinking|transformed my approach)',
                ]
                
                has_context = any(re.search(pattern, quote, re.IGNORECASE) for pattern in contextual_markers)
                if not has_context:
                    return True
    
    return False

def has_host_prompt_or_transition(quote):
    """
    Detects if the quote is actually a podcast host prompt, transition,
    or outro that wasn't caught by the podcast structural element filter.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote appears to be a host prompt or transition
    """
    # Host transition patterns
    host_patterns = [
        r'(as we wrap up|to wrap up|to conclude|in conclusion|before we finish|to finish up)',
        r'(one last question|final question|final thoughts|final word|final advice)',
        r'(tell our listeners|tell our audience|takeaway for our listeners|message for our audience)',
        r'(thank you for|thanks for joining|appreciate your time|grateful for your insights)',
        r'(let\'s move on to|let\'s switch gears|moving on to|turning to)',
        r'(I\'d like to ask you|I wanted to ask|could you share|would you mind telling us|would you say)',
        r'(before we go|before we end|one thing I\'m curious about|something I\'ve been wondering)',
        r'(I\'m interested in|I\'d love to hear|tell us more about|share with us)'
        r'(if you\'re just joining us|for those just tuning in|to catch you up)',
        r'(talking with|speaking to|interviewing|our guest|with us today|joining us)',
    ]
    
    for pattern in host_patterns:
        if re.search(pattern, quote, re.IGNORECASE):
            return True
    
    return False

def has_trailing_transition(quote):
    """
    Checks if a quote ends with a transition phrase that suggests
    it's incomplete or part of a larger thought.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote ends with a transition phrase
    """
    # Transition phrases that indicate an incomplete thought
    transition_endings = [
        r'(for example|such as|like|including)$',
        r'(so that|in order to|so)$',
        r'(because|since|as)$',
        r'(and then|after that|next)$',
    ]
    
    # Remove final punctuation for the check
    clean_ending = quote.rstrip('.!?').lower()
    
    for pattern in transition_endings:
        if re.search(pattern, clean_ending):
            return True
    
    return False

def has_coherent_insight(quote):
    """
    Positively checks if a quote contains a coherent insight rather than
    just filtering out bad quotes. This helps ensure we keep valuable content.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote appears to contain a coherent insight
    """
    # Insight patterns - looking for complete thoughts with wisdom
    insight_patterns = [
        # Cause-effect insights
        r'(leads to|results in|causes|creates|produces|generates|enables|facilitates)',
        # Comparative insights
        r'(better than|worse than|more effective than|more powerful than|stronger than|weaker than)',
        # Conditional insights with complete structure
        r'(if you .+, then you|when you .+, you|unless you .+, you won\'t)',
        # Perspective shifts
        r'(instead of .+, focus on|rather than .+, consider|shift from .+, to)',
        # Principle statements
        r'(the key is to|the secret is to|what matters is|what\'s important is|the most critical aspect is)',
        # Priority insights
        r'(focus on|prioritize|concentrate on|pay attention to|emphasize|the most important thing is)',
        # Learning insights
        r'(I\'ve learned that|we\'ve discovered that|research shows that|studies indicate that|data suggests that)',
        # Counterintuitive insights
        r'(surprisingly|counter to what most people think|despite popular belief|although it seems|contrary to)',
        # Clarification insights
        r'(in other words|to put it simply|to clarify|to be precise|more specifically|in essence)',
    ]
    
    # Check for the presence of insight patterns
    for pattern in insight_patterns:
        if re.search(pattern, quote, re.IGNORECASE):
            return True
    
    return False

def is_well_formed_quote(quote):
    """
    Comprehensive check to determine if a quote is well-formed and valuable.
    Combines multiple filtering criteria.
    
    Args:
        quote (str): The quote to analyze
        
    Returns:
        bool: True if the quote is well-formed and valuable
    """
    # Must pass these negative filters (not be any of these)
    if (is_question(quote) or 
        has_ambiguous_references(quote) or 
        has_first_person_experience_without_context(quote) or
        has_host_prompt_or_transition(quote) or
        has_trailing_transition(quote) or
        not check_grammatical_integrity(quote) or  # From existing code
        not check_noun_verb_balance(quote)):       # From existing code
        return False
    
    # Must have some positive indicators of value
    if (has_coherent_insight(quote) or 
        has_insight_markers(quote)):    # From existing code
        return True
    
    # Default - if it passes negative filters but doesn't have strong positive indicators
    # We'll be conservative and exclude it
    return False

def extract_quotes_with_context(transcript_text, quote, context_window=50):
    """
    Extract a quote with its surrounding context from a transcript.
    
    Args:
        transcript_text (str): The full transcript text
        quote (str): The quote to find in the transcript
        context_window (int): Number of characters before and after the quote to include
        
    Returns:
        dict or None: The quote with context and timestamp if found, None otherwise
    """
    quote = quote.strip()
    index = transcript_text.find(quote)
    
    if index == -1:
        return None
    
    # Calculate start and end positions for the context
    start = max(0, index - context_window)
    end = min(len(transcript_text), index + len(quote) + context_window)
    
    # Extract the context with the quote
    context = transcript_text[start:end]
    
    # Estimate timestamp based on position in the transcript
    words_before = len(transcript_text[:index].split())
    words_per_minute = 150  # Average speaking rate
    timestamp_minutes = words_before / words_per_minute
    timestamp = f"{int(timestamp_minutes // 60):02}:{int(timestamp_minutes % 60):02}"
    
    return {
        'quote': quote,
        'context': context,
        'position': index,
        'timestamp': timestamp,
        'verified': True
    }

def extract_quotes_from_transcript(transcript_text, num_quotes=5):
    """
    Enhanced quote extraction function with comprehensive filtering
    to ensure only high-quality, grammatically correct, standalone quotes.
    
    Args:
        transcript_text (str): The podcast transcript
        num_quotes (int): Number of quotes to extract
        
    Returns:
        list: Extracted quotes with context and timestamp
    """
    try:
        # Check if this is a speaker-annotated transcript
        is_speaker_transcript = bool(re.search(r'\[\d+\.\d+-\d+\.\d+\]\s+Speaker\s+\d+:', transcript_text))
        
        if is_speaker_transcript:
            # Parse the transcript into clean text and speaker segments
            parsed_transcript = parse_speaker_based_transcript(transcript_text)
            
            # Clean all raw text before processing to remove timestamps and speaker references
            cleaned_text = _clean_and_format_quote(parsed_transcript['text'])
            
            # Process the clean text version for quotes - get many candidates for thorough filtering
            standard_quotes = get_diverse_quotes(cleaned_text, num_quotes*5)
            
            # Also process each speaker segment separately
            speaker_quotes = []
            for segment in parsed_transcript['speakers']:
                if len(segment['text'].split()) >= MIN_MEANINGFUL_WORDS * 2:  # Only process substantial segments
                    # Clean segment text before processing
                    cleaned_segment = _clean_and_format_quote(segment['text'])
                    segment_quotes = get_diverse_quotes(cleaned_segment, 4)  # Get more quotes per substantial segment
                    
                    if isinstance(segment_quotes, str):
                        speaker_quotes.append(segment_quotes)
                    else:
                        speaker_quotes.extend(segment_quotes)
            
            # Combine and select the best quotes
            all_candidate_quotes = standard_quotes + speaker_quotes
            
            # Apply comprehensive filtering
            high_quality_quotes = []
            for quote in all_candidate_quotes:
                # Clean the quote thoroughly
                cleaned_quote = _clean_and_format_quote(quote)
                
                # Apply all filters (existing and new)
                if (not is_podcast_structural_element(cleaned_quote) and 
                    not is_low_information_content(cleaned_quote) and
                    has_standalone_value(cleaned_quote) and
                    len(cleaned_quote.split()) >= MIN_MEANINGFUL_WORDS and
                    is_well_formed_quote(cleaned_quote)):
                    
                    # Get context for the quote
                    quote_with_context = extract_quotes_with_context(transcript_text, cleaned_quote)
                    
                    if quote_with_context:
                        # Only add if not already in list and verified in the transcript
                        if not any(q['text'] == cleaned_quote for q in high_quality_quotes):
                            high_quality_quotes.append({
                                'text': cleaned_quote,
                                'context': quote_with_context['context'],
                                'position': quote_with_context['position'],
                                'timestamp': quote_with_context['timestamp'],
                                'verified': True
                            })
                
                if len(high_quality_quotes) >= num_quotes:
                    break
            
            # If we don't have enough quotes, try again with slightly relaxed criteria
            if len(high_quality_quotes) < num_quotes:
                for quote in all_candidate_quotes:
                    cleaned_quote = _clean_and_format_quote(quote)
                    
                    # Relaxed version - prioritize grammatical correctness and standalone value
                    if (not is_podcast_structural_element(cleaned_quote) and 
                        not is_low_information_content(cleaned_quote) and
                        has_standalone_value(cleaned_quote) and
                        len(cleaned_quote.split()) >= MIN_MEANINGFUL_WORDS and
                        check_grammatical_integrity(cleaned_quote) and
                        not is_question(cleaned_quote) and
                        not has_host_prompt_or_transition(cleaned_quote)):
                        
                        # Get context for the quote
                        quote_with_context = extract_quotes_with_context(transcript_text, cleaned_quote)
                        
                        if quote_with_context and not any(q['text'] == cleaned_quote for q in high_quality_quotes):
                            high_quality_quotes.append({
                                'text': cleaned_quote,
                                'context': quote_with_context['context'],
                                'position': quote_with_context['position'],
                                'timestamp': quote_with_context['timestamp'],
                                'verified': True
                            })
                    
                    if len(high_quality_quotes) >= num_quotes:
                        break
            
            return high_quality_quotes[:num_quotes] if high_quality_quotes else [{"text": "No meaningful quotes found in the transcript.", "verified": False}]

        # Handle other transcript types
        else:
            # Use existing code paths but with our enhanced filtering
            if is_unpunctuated_text(transcript_text):
                print("Detected unpunctuated transcript, applying special processing.")
                segments = segment_unpunctuated_transcript(transcript_text)
                merged_segments = merge_short_segments(segments)
                filtered_segments = filter_incomplete_thoughts(merged_segments)
                
                if len(filtered_segments) < num_quotes * 2:
                    filtered_segments = merged_segments if len(merged_segments) >= num_quotes else segments
                
                formatted_text = ' '.join(filtered_segments)
                quotes = get_diverse_quotes(formatted_text, num_quotes*5)  # Get more for filtering
            else:
                quotes = get_diverse_quotes(transcript_text, num_quotes*5)  # Get more for filtering
            
            # Apply comprehensive filtering
            high_quality_quotes = []
            for quote in quotes:
                cleaned_quote = _clean_and_format_quote(quote)
                
                if (not is_podcast_structural_element(cleaned_quote) and 
                    not is_low_information_content(cleaned_quote) and
                    has_standalone_value(cleaned_quote) and
                    len(cleaned_quote.split()) >= MIN_MEANINGFUL_WORDS and
                    is_well_formed_quote(cleaned_quote)):
                    
                    # Get context for the quote
                    quote_with_context = extract_quotes_with_context(transcript_text, cleaned_quote)
                    
                    if quote_with_context:
                        if not any(q['text'] == cleaned_quote for q in high_quality_quotes):
                            high_quality_quotes.append({
                                'text': cleaned_quote,
                                'context': quote_with_context['context'],
                                'position': quote_with_context['position'],
                                'timestamp': quote_with_context['timestamp'],
                                'verified': True
                            })
                
                if len(high_quality_quotes) >= num_quotes:
                    break
            
            # Try to get more quotes if needed
            if len(high_quality_quotes) < num_quotes:
                more_quotes = get_diverse_quotes(transcript_text, num_quotes * 5, similarity_threshold=0.4)
                
                for quote in more_quotes:
                    cleaned_quote = _clean_and_format_quote(quote)
                    
                    # Relaxed version - prioritize grammatical correctness and standalone value
                    if (not is_podcast_structural_element(cleaned_quote) and 
                        not is_low_information_content(cleaned_quote) and
                        has_standalone_value(cleaned_quote) and
                        len(cleaned_quote.split()) >= MIN_MEANINGFUL_WORDS and
                        check_grammatical_integrity(cleaned_quote) and
                        not is_question(cleaned_quote) and
                        not has_host_prompt_or_transition(cleaned_quote)):
                        
                        # Get context for the quote
                        quote_with_context = extract_quotes_with_context(transcript_text, cleaned_quote)
                        
                        if quote_with_context and not any(q['text'] == cleaned_quote for q in high_quality_quotes):
                            high_quality_quotes.append({
                                'text': cleaned_quote,
                                'context': quote_with_context['context'],
                                'position': quote_with_context['position'],
                                'timestamp': quote_with_context['timestamp'],
                                'verified': True
                            })
                        
                        if len(high_quality_quotes) >= num_quotes:
                            break
            
            return high_quality_quotes[:num_quotes] if high_quality_quotes else [{"text": "No meaningful quotes found in the transcript.", "verified": False}]
        
    except Exception as e:
        print(f"Error extracting quotes: {e}")
        import traceback
        traceback.print_exc()
        return [{"text": "Error extracting quotes. Please check your transcript format.", "verified": False}]
#-----------------------------------------------------------------------------        
# PODCAST STRUCTURAL ELEMENTS FILTERING
#-----------------------------------------------------------------------------

# Patterns to identify non-quotable structural elements
PODCAST_STRUCTURAL_PATTERNS = [
    # Intro/outro markers
    r"(?i)\[?(intro|outro|opening|closing)[\s_]?(music|theme|segment)?\]?",
    r"(?i)\[?(music|jingle|theme|sound[\s_]?effect|stinger)s?\]?",
    r"(?i)(welcome|thanks?)[\s_]?(back|again|for[\s_]?joining|for[\s_]?listening|for[\s_]?tuning[\s_]?in|for[\s_]?being[\s_]?here)",
    r"(?i)that'?s[\s_]?(all|it)[\s_]?for[\s_]?(today'?s|this|another)[\s_]?episode",
    r"(?i)see[\s_]?you[\s_]?(next[\s_]?time|next[\s_]?week|in[\s_]?the[\s_]?next[\s_]?episode|soon|later)",
    r"(?i)(this[\s_]?is|you'?re[\s_]?listening[\s_]?to)[\s_]?('|\"|the)?[\s_]?[\w\s]+[\s_]?(podcast|show|radio)",
    r"(?i)(before[\s_]?we[\s_]?start|before[\s_]?we[\s_]?jump[\s_]?in|let’s[\s_]?get[\s_]?started|first[\s_]?off)",
    r"(?i)(if you('re| are) just joining us|for those (just tuning|joining) in|to recap|to those who just joined)",

    # Production notes (non-verbal or background cues)
    r"(?i)\[?(pause|break|silence|cough|laughter|chuckle|sigh|applause|cheering|audience[\s_]?(reaction|clap))\]?",
    r"(?i)\[?(music|sound)[\s_]?(plays|fades|swells|ends|starts|continues)\]?",
    r"(?i)\[?(short|brief|quick|sponsored|paid)[\s_]?(music|ad|advertisement|commercial|promo)[\s_]?(break|segment)?\]?",
    r"(?i)(let’s[\s_]?take[\s_]?a[\s_]?quick[\s_]?break|we’ll[\s_]?be[\s_]?right[\s_]?back|stay[\s_]?tuned)",  

    # Sponsorships and call-to-actions
    r"(?i)(this[\s_]?episode[\s_]?is[\s_]?brought[\s_]?to[\s_]?you[\s_]?by|today’s[\s_]?sponsor|shoutout[\s_]?to[\s_]?our[\s_]?sponsor)",  
    r"(?i)(visit[\s_]?our[\s_]?website|check[\s_]?out[\s_]?our[\s_]?sponsors|don’t[\s_]?forget[\s_]?to[\s_]?subscribe|leave[\s_]?a[\s_]?review)",  
    r"(?i)(follow[\s_]?us[\s_]?on[\s_]?social[\s_]?media|find[\s_]?us[\s_]?on[\s_]?Twitter|support[\s_]?us[\s_]?on[\s_]?Patreon|sign[\s_]?up[\s_]?for[\s_]?our[\s_]?newsletter)",  
    r"(?i)(use[\s_]?code[\s_]?[\w\d]+[\s_]?for[\s_]?a[\s_]?discount|special[\s_]?offer[\s_]?just[\s_]?for[\s_]?listeners)",  

    # Speaker identifiers (structured speaker labels)
    r"(?i)^[\s_]?(host|guest|interviewer|speaker[\s_]?\d+|moderator|announcer)[\s_]?:",
    r"(?i)^[\s_]?([A-Z][a-zA-Z]+)[\s_]?(\([^)]+\))?[\s_]?:",

    # Technical or disclaimer-related
    r"(?i)(the[\s_]?views[\s_]?expressed[\s_]?are[\s_]?not[\s_]?necessarily[\s_]?those[\s_]?of[\s_]?the[\s_]?host|this[\s_]?is[\s_]?not[\s_]?financial[\s_]?advice|for[\s_]?informational[\s_]?purposes[\s_]?only)",
    r"(?i)(content[\s_]?may[\s_]?contain[\s_]?sensitive[\s_]?topics|listener[\s_]?discretion[\s_]?is[\s_]?advised)",  

    # Closing statements
    r"(?i)(that’s[\s_]?it[\s_]?for[\s_]?today|thanks[\s_]?for[\s_]?tuning[\s_]?in|catch[\s_]?you[\s_]?next[\s_]?time)",  
    r"(?i)(until[\s_]?next[\s_]?time|take[\s_]?care[\s_]?everyone|signing[\s_]?off)"
]

# Words that would be present in low-value quotes (e.g., simple greetings, transitions)
LOW_VALUE_INDICATORS = {
    "hello", "hi", "hi there", "welcome", "thanks", "thanks for joining",  
    "tune in", "coming up", "we'll be right back", "after the break",  
    "let's begin", "next week", "next time", "that's all",  
    "thank you for listening", "don't forget to subscribe",  
    "leave a review", "follow us", "today's sponsor",  
    "brought to you by", "our website", "social media",  
    "email us", "let me introduce", "let's welcome",  
    "before we get started", "stick around", "stay tuned",  
    "a quick message", "just a reminder", "shoutout to",  
    "if you enjoyed this", "if you liked this", "make sure to",  
    "we appreciate your support", "this episode is sponsored by",  
    "check out our merch", "support us on Patreon", "find us on",  
    "visit our website", "follow us on", "like and subscribe",  
    "join our community", "special thanks to",  
    "that’s a wrap", "we’ll catch you next time", "until next time"
}

def is_podcast_structural_element(text):
    """
    Determine if a text segment represents a podcast structural element rather than content.
    
    Args:
        text (str): The text segment to analyze
        
    Returns:
        bool: True if this is likely a structural element
    """
    # Check for structural patterns
    for pattern in PODCAST_STRUCTURAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if more than 50% of the words are low-value indicators
    words = text.lower().split()
    low_value_count = sum(1 for word in words if any(indicator in word for indicator in LOW_VALUE_INDICATORS))
    if len(words) > 0 and low_value_count / len(words) > 0.3:
        return True
        
    # Check for episode metadata
    if re.search(r"(?i)episode[\s_]?\d+|season[\s_]?\d+", text):
        # If a substantial portion of the text is about episode metadata, it's likely structural
        if len(re.findall(r"(?i)episode|season|\d+", text)) / len(text.split()) > 0.3:
            return True
    
    # Check if it's short and contains common podcast transitions
    if len(text.split()) < 10:
        transition_phrases = ["stay tuned", "up next", "after this", "we'll be back", "let's go to", "moving on"]
        for phrase in transition_phrases:
            if phrase in text.lower():
                return True
    
    return False

def is_low_information_content(text):
    """
    Determine if a text segment has low information value.
    
    Args:
        text (str): The text segment to analyze
        
    Returns:
        bool: True if the text likely has low information value
    """
    # Check if text is very short (likely not insightful)
    if len(text.split()) < MIN_MEANINGFUL_WORDS + 2:
        return True
    
    # Check if it contains very little specialized vocabulary (simple sentences)
    words = text.lower().split()
    stop_words = set(stopwords.words('english'))
    non_stopwords = [word for word in words if word not in stop_words and word not in string.punctuation]
    
    # If less than 30% of the words are non-stopwords, it's likely low information
    if len(words) > 0 and len(non_stopwords) / len(words) < 0.3:
        return True
    
    # Check if it contains specific patterns that indicate low information content
    filler_patterns = [
        r"(?i)^(so|anyway|anyhow|well|um|uh|hmm|like|you[\s_]?know|i[\s_]?mean|basically|actually|literally|honestly|to[\s_]?be[\s_]?honest|let[\s_]?me[\s_]?tell[\s_]?you)",  
        r"(?i)(you[\s_]?know[\s_]?what[\s_]?i[\s_]?mean|if[\s_]?you[\s_]?know[\s_]?what[\s_]?i[\s_]?mean|right\?|okay\?|alright\?)",  
        r"(?i)(like[\s_]?i[\s_]?said|as[\s_]?i[\s_]?mentioned|as[\s_]?i[\s_]?said[\s_]?before|like[\s_]?i[\s_]?mentioned|as[\s_]?we[\s_]?were[\s_]?saying)",  
        r"(?i)(just[\s_]?saying|i[\s_]?guess|sort[\s_]?of|kind[\s_]?of|maybe|probably|more[\s_]?or[\s_]?less|something[\s_]?like[\s_]?that)",  
        r"(?i)(to[\s_]?be[\s_]?fair|to[\s_]?be[\s_]?honest|to[\s_]?tell[\s_]?the[\s_]?truth|let[\s_]?me[\s_]?be[\s_]?clear)",  
        r"(?i)(at[\s_]?the[\s_]?end[\s_]?of[\s_]?the[\s_]?day|when[\s_]?all[\s_]?is[\s_]?said[\s_]?and[\s_]?done|to[\s_]?make[\s_]?a[\s_]?long[\s_]?story[\s_]?short)",  
        r"(?i)(let[\s_]?me[\s_]?tell[\s_]?you[\s_]?something|here’s[\s_]?the[\s_]?thing|this[\s_]?is[\s_]?interesting[\s_]?because)",  
        r"(?i)(if[\s_]?you[\s_]?think[\s_]?about[\s_]?it|when[\s_]?you[\s_]?really[\s_]?think[\s_]?about[\s_]?it)",  
        r"(?i)(that’s[\s_]?just[\s_]?how[\s_]?it[\s_]?is|that’s[\s_]?the[\s_]?way[\s_]?it[\s_]?goes|it[\s_]?is[\s_]?what[\s_]?it[\s_]?is)",  
        r"(?i)(for[\s_]?what[\s_]?it[\s_]?is[\s_]?worth|not[\s_]?to[\s_]?get[\s_]?too[\s_]?deep[\s_]?into[\s_]?it|not[\s_]?to[\s_]?go[\s_]?off[\s_]?on[\s_]?a[\s_]?tangent)",  
        r"(?i)(i[\s_]?was[\s_]?just[\s_]?thinking[\s_]?that|it[\s_]?just[\s_]?came[\s_]?to[\s_]?me[\s_]?that)",  
        r"(?i)(by[\s_]?the[\s_]?way|before[\s_]?i[\s_]?forget|oh[\s_]?yeah|come[\s_]?to[\s_]?think[\s_]?of[\s_]?it)",  
        r"(?i)(not[\s_]?sure[\s_]?if[\s_]?this[\s_]?makes[\s_]?sense|i[\s_]?don’t[\s_]?know[\s_]?if[\s_]?this[\s_]?is[\s_]?relevant)",  
        r"(?i)(you[\s_]?see|let[\s_]?me[\s_]?put[\s_]?it[\s_]?this[\s_]?way|how[\s_]?do[\s_]?i[\s_]?say[\s_]?this)",  
        r"(?i)(i[\s_]?mean[\s_]?it’s[\s_]?like|you[\s_]?know[\s_]?what[\s_]?i[\s_]?mean[\s_]?right)",  
        r"(?i)(so[\s_]?yeah|so[\s_]?basically|so[\s_]?like|so[\s_]?anyway)",  
        r"(?i)(it’s[\s_]?funny[\s_]?because|it’s[\s_]?weird[\s_]?because|it’s[\s_]?interesting[\s_]?because)",  
        r"(?i)(let[\s_]?me[\s_]?think[\s_]?for[\s_]?a[\s_]?second|hold[\s_]?on[\s_]?a[\s_]?minute|wait[\s_]?a[\s_]?second)"
    ]    
    for pattern in filler_patterns:
        if re.search(pattern, text):
            # If the filler content makes up a significant portion of the text, consider it low information
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches and sum(len(m.split()) for m in matches) / len(words) > 0.3:
                return True
    
    return False

def has_insight_markers(text):
    """
    Check if text has strong markers of insight or quotability.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        bool: True if strong insight markers are present
    """
    # Insight pattern score must be substantial
    insight_score = detect_insight_patterns(text)
    if insight_score >= 2:  # Text matches multiple insight patterns
        return True
    
    # Check for presence of quotable indicators
    quotable_count = sum(1 for indicator in QUOTABLE_INDICATORS if indicator in text.lower().split())
    if quotable_count >= 2:
        return True
    
    # Check for "profound statement" structures
    profound_patterns = [
        r"(?i)the (truth|reality|fact|key|secret) (is|was|remains)",
        r"(?i)(always|never) (forget|underestimate|ignore|assume)",
        r"(?i)the (most important|biggest|greatest|hardest|best) (lesson|insight|discovery|decision)",
        r"(?i)(changed|transformed|shaped|defined) (my|our|the) (life|perspective|understanding|journey|thinking|career)",
        r"(?i)(we|I) (realized|discovered|learned|figured out) that",
        r"(?i)this (changed|shaped|defined) my (life|career|perspective|path|mindset)",
        r"(?i)if there's one thing (I've|we've) learned, it's that",
        r"(?i)it (turns out|became clear|dawned on me) that",
        r"(?i)the (lesson|takeaway|moral) (here|to learn) is",
        r"(?i)what (really|truly|actually) matters is",
        r"(?i)it all comes down to (this|one thing)",
        r"(?i)this is the moment (I|we) (understood|realized|knew|got it)",
        r"(?i)at the end of the day, (it's|life is|what matters is)",
        r"(?i)one thing (I've|we've) (seen|noticed|found) over and over is",
        r"(?i)the mistake (I|we|people) (kept|keep) making is",
        r"(?i)the (one|only) way to (grow|succeed|improve|win) is",
        r"(?i)what nobody tells you about (success|failure|growth|happiness) is",
        r"(?i)you (can't|shouldn't|won't) (succeed|grow|win|change) unless",
        r"(?i)here’s (why|how|the thing):",
        r"(?i)I wish (I|we) had known this (earlier|before)",
        r"(?i)what (I|we) didn't realize until later was",
        r"(?i)this is (why|where|how) everything changed",
        r"(?i)the breakthrough moment was when",
        r"(?i)if (I|you|we) could go back, (I|you|we) would",
        r"(?i)it wasn’t until (X) that (I|we) understood",
        r"(?i)this one idea (changed|shaped|defined|transformed) everything",
        r"(?i)it sounds simple, but (it’s|this is) everything",
        r"(?i)the way (we|people) think about (X) is completely wrong"
    ]
    
    for pattern in profound_patterns:
        if re.search(pattern, text):
            return True
    
    return False

def enhance_quote_scoring(sentence, score):
    """
    Enhance the quote scoring with additional content-based heuristics.
    
    Args:
        sentence (str): The sentence being scored
        score (float): The current score from the basic algorithm
        
    Returns:
        float: Enhanced score
    """
    # Start with the base score
    enhanced_score = score
    
    # Heavily penalize podcast structural elements
    if is_podcast_structural_element(sentence):
        enhanced_score -= 15
    
    # Penalize low information content
    if is_low_information_content(sentence):
        enhanced_score -= 10
    
    # Bonus for strong insight markers
    if has_insight_markers(sentence):
        enhanced_score += 8
    
    conclusion_patterns = [
        r"(?i)(in[\s_]?other[\s_]?words|in[\s_]?essence|in[\s_]?conclusion|to[\s_]?summarize|to[\s_]?put[\s_]?it[\s_]?simply)",
        r"(?i)(what[\s_]?this[\s_]?means|what[\s_]?this[\s_]?suggests|what[\s_]?this[\s_]?tells[\s_]?us|what[\s_]?we[\s_]?can[\s_]?learn)",
        r"(?i)(the[\s_]?lesson|the[\s_]?moral|the[\s_]?takeaway|the[\s_]?bigger[\s_]?picture|the[\s_]?main[\s_]?point)",
        r"(?i)(ultimately|fundamentally|essentially|at[\s_]?its[\s_]?core|when[\s_]?you[\s_]?really[\s_]?think[\s_]?about[\s_]?it)",
        r"(?i)(the[\s_]?bottom[\s_]?line[\s_]?is|the[\s_]?truth[\s_]?is|the[\s_]?fact[\s_]?is|the[\s_]?point[\s_]?is)",
        r"(?i)(all[\s_]?things[\s_]?considered|taking[\s_]?everything[\s_]?into[\s_]?account)",
        r"(?i)(this[\s_]?goes[\s_]?to[\s_]?show|this[\s_]?proves|this[\s_]?demonstrates|this[\s_]?reinforces)",
        r"(?i)(if[\s_]?there’s[\s_]?one[\s_]?thing[\s_]?to[\s_]?remember|if[\s_]?there’s[\s_]?one[\s_]?lesson)",
        r"(?i)(it[\s_]?all[\s_]?comes[\s_]?down[\s_]?to|at[\s_]?the[\s_]?end[\s_]?of[\s_]?the[\s_]?day|the[\s_]?final[\s_]?thought)",
        r"(?i)(we[\s_]?can[\s_]?all[\s_]?agree[\s_]?that|one[\s_]?thing[\s_]?is[\s_]?clear|the[\s_]?evidence[\s_]?shows)",
        r"(?i)(what[\s_]?we[\s_]?now[\s_]?know|what[\s_]?we've[\s_]?learned|what[\s_]?science[\s_]?tells[\s_]?us)",
        r"(?i)(this[\s_]?is[\s_]?why|this[\s_]?explains[\s_]?why|this[\s_]?clarifies)",
        r"(?i)(this[\s_]?brings[\s_]?us[\s_]?to|this[\s_]?leads[\s_]?to|this[\s_]?connects[\s_]?to)",
        r"(?i)(we[\s_]?are[\s_]?left[\s_]?with[\s_]?one[\s_]?question|this[\s_]?raises[\s_]?an[\s_]?important[\s_]?point)",
        r"(?i)(now[\s_]?we[\s_]?understand|now[\s_]?we[\s_]?see|this[\s_]?puts[\s_]?things[\s_]?into[\s_]?perspective)",
        r"(?i)(let[\s_]?me[\s_]?leave[\s_]?you[\s_]?with[\s_]?this|final[\s_]?thought|final[\s_]?words)"
    ]
    
    for pattern in conclusion_patterns:
        if re.search(pattern, sentence):
            enhanced_score += 5
            break
    
    # Bonus for analogy or metaphor (often insightful)
    if re.search(r"(?i)(like|as if|similar to|compared to|resembles)", sentence):
        words = sentence.split()
        # Only boost if the analogy is substantial (not just a simple comparison)
        if len(words) > 12:
            enhanced_score += 3
    
    # Bonus for contrast or counterintuitive statements (often insightful)
    contrast_patterns = [
        r"(?i)(however|but|yet|although|though|whereas|while|even[\s_]?though|despite[\s_]?the[\s_]?fact[\s_]?that|in[\s_]?contrast|on[\s_]?the[\s_]?other[\s_]?hand|that[\s_]?being[\s_]?said|having[\s_]?said[\s_]?that)",  
        r"(?i)(surprisingly|unexpectedly|ironically|paradoxically|counterintuitively|against[\s_]?all[\s_]?odds|oddly[\s_]?enough|strangely[\s_]?enough|as[\s_]?it[\s_]?turns[\s_]?out)",  
        r"(?i)(one[\s_]?might[\s_]?expect|you’d[\s_]?think|it[\s_]?seems[\s_]?like|it[\s_]?may[\s_]?sound[\s_]?strange|at[\s_]?first[\s_]?glance)",  
        r"(?i)(the[\s_]?opposite[\s_]?is[\s_]?true|this[\s_]?may[\s_]?seem[\s_]?counterintuitive|this[\s_]?goes[\s_]?against[\s_]?common[\s_]?sense|this[\s_]?is[\s_]?not[\s_]?what[\s_]?you'd[\s_]?expect)",  
        r"(?i)(despite[\s_]?everything|nevertheless|nonetheless|regardless|even[\s_]?so|against[\s_]?expectations|defying[\s_]?logic)",  
        r"(?i)(this[\s_]?seems[\s_]?wrong[\s_]?but|this[\s_]?shouldn’t[\s_]?work[\s_]?but|it[\s_]?defies[\s_]?logic[\s_]?but|it’s[\s_]?not[\s_]?what[\s_]?you[\s_]?think)",  
        r"(?i)(what[\s_]?most[\s_]?people[\s_]?don’t[\s_]?realize|the[\s_]?common[\s_]?misconception[\s_]?is|we’ve[\s_]?been[\s_]?taught[\s_]?that[\s_]?but|contrary[\s_]?to[\s_]?popular[\s_]?belief)",  
        r"(?i)(it[\s_]?turns[\s_]?out[\s_]?that|we[\s_]?often[\s_]?assume[\s_]?but|the[\s_]?reality[\s_]?is[\s_]?different)",  
        r"(?i)(it[\s_]?sounds[\s_]?crazy[\s_]?but|you[\s_]?won’t[\s_]?believe[\s_]?this|it’s[\s_]?hard[\s_]?to[\s_]?believe[\s_]?but)",  
        r"(?i)(at[\s_]?first[\s_]?it[\s_]?seems[\s_]?like|initially[\s_]?we[\s_]?thought|we[\s_]?used[\s_]?to[\s_]?believe[\s_]?but)",  
        r"(?i)(you’d[\s_]?assume[\s_]?that|most[\s_]?people[\s_]?think[\s_]?but|conventional[\s_]?wisdom[\s_]?says[\s_]?but)"
    ]
    
    for pattern in contrast_patterns:
        if re.search(pattern, sentence):
            enhanced_score += 3
            break
    
    return enhanced_score


#-----------------------------------------------------------------------------
# QUOTE EXTRACTION
#-----------------------------------------------------------------------------

def _clean_and_format_quote(quote):
    """
    Clean up a quote for presentation.
    
    Args:
        quote (str): The raw quote
        
    Returns:
        str: Cleaned and formatted quote
    """
    # Remove filler words and clean up whitespace
    clean_quote = re.sub(r'\b(um|uh|like|you know|I mean)\b', '', quote)
    clean_quote = re.sub(r'\s+', ' ', clean_quote).strip()
    
    # Make sure the quote ends with proper punctuation
    if not clean_quote.endswith(('.', '!', '?')):
        clean_quote += '.'
        
    return clean_quote

def extract_quote(text, num_quotes=3, title=None, custom_keywords=None):
    """
    Extract the most important quotes from the text.
    
    Args:
        text (str): The text to analyze
        num_quotes (int, optional): Number of quotes to extract. Defaults to 3.
        title (str, optional): Title of the content for additional context
        custom_keywords (list, optional): Custom keywords to prioritize
        
    Returns:
        list or str: Top quotes from the text
    """
    # Clean and prepare text
    sentences = extract_sentences(text)
    
    # Skip processing if no valid sentences
    if not sentences:
        return "No meaningful quotes found in the text."
    
    # Extract title keywords if title is provided
    title_keywords = []
    if title:
        title_words = word_tokenize(title.lower())
        stop_words = set(stopwords.words('english'))
        title_keywords = [word for word in title_words if word not in stop_words and word not in string.punctuation]
    
    # Identify important keywords
    important_keywords = identify_important_keywords(text, custom_keywords)
    
    # Initialize sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    # Score each sentence
    sentence_scores = []
    for sentence in sentences:
        score = score_sentence_importance(sentence, important_keywords, sia, title_keywords)
        
        # Add length penalty for very short or very long quotes
        words = len(sentence.split())
        if words < MIN_MEANINGFUL_WORDS + 1:
            score -= 5  # Heavily penalize very short sentences
        elif words > 40:
            score -= (words - 40) // 5  # Gradually penalize long sentences
            
        sentence_scores.append((sentence, score))
    
    # Sort by score (highest first)
    ranked_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    
    # Take top quotes
    top_quotes = [sentence for sentence, _ in ranked_sentences[:num_quotes]]
    
    # If only one quote requested, return as string
    if num_quotes == 1:
        return top_quotes[0] if top_quotes else "No meaningful quotes found in the text."
    
    # Otherwise return list
    return top_quotes if top_quotes else ["No meaningful quotes found in the text."]


def _is_too_similar(quote, existing_quotes, threshold):
    """
    Helper function to check similarity between quotes.
    
    Args:
        quote (str): The quote to check
        existing_quotes (list): List of already selected quotes
        threshold (float): Similarity threshold (0-1)
        
    Returns:
        bool: True if the quote is too similar to any existing quote
    """
    for existing in existing_quotes:
        # Simple word overlap similarity
        quote_words = set(word_tokenize(quote.lower()))
        existing_words = set(word_tokenize(existing.lower()))
        
        # Calculate Jaccard similarity
        if len(quote_words) == 0 or len(existing_words) == 0:
            continue
            
        intersection = len(quote_words.intersection(existing_words))
        union = len(quote_words.union(existing_words))
        similarity = intersection / union
        
        if similarity > threshold:
            return True
    return False

def get_diverse_quotes(text, num_quotes=5, similarity_threshold=SIMILARITY_THRESHOLD_DEFAULT):
    """
    Extract diverse quotes to avoid repetition, using enhanced quote extraction.
    
    Args:
        text (str): The text to analyze
        num_quotes (int): Number of quotes to extract
        similarity_threshold (float): Threshold for quote similarity (0-1)
        
    Returns:
        list: Diverse quotes from the text
    """
    # Get a larger pool of potential quotes using enhanced extraction
    candidate_quotes = extract_quote(text, num_quotes * 3)
    
    # Handle case where candidate_quotes is a string (single quote)
    if isinstance(candidate_quotes, str):
        return [candidate_quotes]
        
    # Start with the highest ranked quote
    selected_quotes = [candidate_quotes[0]]
    
    # Add quotes that are not too similar to already selected ones
    for quote in candidate_quotes[1:]:
        if len(selected_quotes) >= num_quotes:
            break
            
        if not _is_too_similar(quote, selected_quotes, similarity_threshold):
            selected_quotes.append(quote)
    
    # If we don't have enough diverse quotes, add the remaining highest ranked ones
    if len(selected_quotes) < num_quotes:
        for quote in candidate_quotes:
            if len(selected_quotes) >= num_quotes:
                break
                
            if quote not in selected_quotes:
                selected_quotes.append(quote)
    
    return selected_quotes[:num_quotes]

