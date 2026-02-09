"""
Text chunking utilities.

Splits large documents into smaller chunks for LLM processing.
"""

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into overlapping chunks by words.
    
    Args:
        text: The full text to chunk.
        chunk_size: Maximum words per chunk.
        overlap: Number of overlapping words between chunks.
        
    Returns:
        list[str]: List of text chunks.
    """
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [text]
    
    step = chunk_size - overlap
    
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
        
        # Stop if we've captured all words
        if i + chunk_size >= len(words):
            break
    
    return chunks
