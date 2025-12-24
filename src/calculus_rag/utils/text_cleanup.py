"""
Text cleanup utilities for fixing corrupted PDF extraction.

Fixes common issues with mathematical notation from PDF-to-text conversion.
"""

import re


def cleanup_math_text(text: str) -> str:
    """
    Clean up corrupted mathematical notation from PDF extraction.

    Fixes common issues:
    - Fragmented subscripts/superscripts (_x_, ^n^)
    - Unicode bracket artifacts (⎡ ⎤ ⎣ ⎦)
    - Strikethrough noise (~~text~~)
    - Scattered integral bounds
    - Excessive whitespace and newlines

    Args:
        text: Raw text from PDF extraction.

    Returns:
        Cleaned text with better math formatting.
    """
    if not text:
        return text

    # Remove Unicode bracket artifacts
    text = re.sub(r'[⎡⎤⎣⎦⎧⎨⎩⎫⎬⎭]', '', text)

    # Remove strikethrough notation (various malformed patterns)
    text = re.sub(r'~~([^~]*)~~', r'\1', text)  # Standard with optional content
    text = re.sub(r'~~~~+', '', text)  # Empty strikethrough (4+ tildes)
    text = re.sub(r'~([⎡⎤⎣⎦⎧⎨⎩⎫⎬⎭⎝⎠])~~', r'\1', text)  # Malformed with brackets
    text = re.sub(r'~~\s*\n\s*~~', '', text)  # Strikethrough with newlines
    text = re.sub(r'(?<!\~)~~(?!\~)', '', text)  # Standalone ~~ (not part of ~~~~)

    # Fix scattered integral bounds: lines with just "a" or "b" near integrals
    # Pattern: newline, optional space, single letter, newline -> remove the line
    text = re.sub(r'\n\s*([a-z])\s*\n\s*([a-z])\s*\n', r' from \1 to \2 ', text)
    text = re.sub(r'\n\s*([a-z])\s*\n(?=\s*\n)', r'', text)

    # Fix integral with bounds on separate lines
    text = re.sub(r'∫\s*\n+\s*([a-z0-9])\s*\n+\s*([a-z0-9])\s*\n', r'∫ from \1 to \2 ', text)
    text = re.sub(r'∫\s*\n+', r'∫ ', text)

    # Fix italic markers used for variables: _x_ -> x
    text = re.sub(r'(?<!\w)_([a-zA-Z])_(?!\w)', r'\1', text)

    # Fix _dx_ patterns (differential)
    text = re.sub(r'_d([a-z])_', r'd\1', text)

    # Fix spaced out function notation: f ( x ) -> f(x)
    text = re.sub(r'([a-zA-Z])\s*\(\s*([a-zA-Z])\s*\)', r'\1(\2)', text)
    text = re.sub(r'([a-zA-Z])\s*\(\s*([a-zA-Z])\s*,\s*([a-zA-Z])\s*\)', r'\1(\2, \3)', text)

    # Fix F ' ( x ) -> F'(x)
    text = re.sub(r"([A-Z])\s*'\s*\(\s*([a-zA-Z])\s*\)", r"\1'(\2)", text)

    # Fix interval notation [a, b]
    text = re.sub(r'\[\s*([a-z])\s*,\s*([a-z])\s*\]', r'[\1, \2]', text)

    # Fix common operators with extra spaces
    text = re.sub(r'\s*−\s*', ' - ', text)  # minus sign (unicode)
    text = re.sub(r'\s*-\s*', ' - ', text)  # regular minus
    text = re.sub(r'\s*\+\s*', ' + ', text)
    text = re.sub(r'\s*=\s*', ' = ', text)

    # Remove excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove lines that are just whitespace or single characters
    text = re.sub(r'\n\s+\n', '\n\n', text)
    text = re.sub(r'\n\s*[a-z]\s*\n', '\n', text)

    # Fix "This OpenStax book..." footer noise
    text = re.sub(r'This OpenStax book is available.*?\.12', '', text, flags=re.DOTALL)

    # Remove empty bullet points
    text = re.sub(r'\n\s*-\s*\n', '\n', text)

    # Consolidate multiple spaces
    text = re.sub(r'  +', ' ', text)

    # Fix leftover patterns like ", b" at start of lines
    text = re.sub(r'\n\s*,\s*([a-z])\s*', r', \1', text)

    # Clean up start and end
    text = text.strip()

    return text


def is_chunk_corrupted(text: str, threshold: float = 0.3) -> bool:
    """
    Check if a chunk appears to be heavily corrupted.

    Args:
        text: Text to check.
        threshold: Ratio of suspicious characters to total (0-1).

    Returns:
        True if chunk appears corrupted.
    """
    if not text or len(text) < 20:
        return True

    # Count suspicious patterns
    suspicious_patterns = [
        r'[⎡⎤⎣⎦⎧⎨⎩⎫⎬⎭]',  # Unicode brackets
        r'~~[^~]+~~',  # Strikethrough
        r'_[a-z]_\s*\n\s*_[a-z]_',  # Fragmented bounds
        r'\n\s*\n\s*\n',  # Excessive newlines
    ]

    suspicious_count = 0
    for pattern in suspicious_patterns:
        suspicious_count += len(re.findall(pattern, text))

    # Check ratio of weird characters
    weird_chars = len(re.findall(r'[⎡⎤⎣⎦⎧⎨⎩⎫⎬⎭∫∑∏√∞≤≥≠≈]', text))

    # If too many suspicious patterns relative to text length
    ratio = suspicious_count / max(len(text) / 100, 1)

    return ratio > threshold


def extract_clean_sentences(text: str) -> list[str]:
    """
    Extract clean, complete sentences from text.

    Useful for creating better chunks from corrupted text.

    Args:
        text: Input text.

    Returns:
        List of clean sentences.
    """
    # First cleanup
    text = cleanup_math_text(text)

    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter out very short or corrupted sentences
    clean_sentences = []
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and not is_chunk_corrupted(s, threshold=0.5):
            clean_sentences.append(s)

    return clean_sentences


# Test the cleanup
if __name__ == "__main__":
    # Example corrupted text from the PDF
    corrupted = """by _F_ ( _x_ ) = ∫



_f_ ( _t_ ) _dt_, then




- **Fundamental Theorem of Calculus Part 2**



_b_

_a_



If _f_ is continuous over the interval



⎡ ⎤
⎣ _a_, _b_ ⎦ and _F_ ( _x_ ) is any antiderivative of _f_ ( _x_ ), then ∫



_f_ ( _x_ ) _dx_ = _F_ ( _b_ ) − _F_ ( _a_ ).




- **Net Change Theorem**



_b_

_a_



_b_

_a_



_F_ ( _b_ ) = _F_ ( _a_ ) + ∫



_F_ '( _x_ ) _dx_ or ∫



_F_ '( _x_ ) _dx_ = _F_ ( _b_ ) − _F_ ( _a_ )


This OpenStax book is available for free at http://cnx.org/content/col11964/1.12"""

    print("BEFORE CLEANUP:")
    print("-" * 40)
    print(corrupted)
    print("\n" + "=" * 40 + "\n")
    print("AFTER CLEANUP:")
    print("-" * 40)
    print(cleanup_math_text(corrupted))
