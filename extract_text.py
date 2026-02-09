"""
Document text extraction.

Right now this does not use docling, and it only takes in pdf or txt files.

I plan on changing this to docling soon, but a working product was needed first.
"""

from pathlib import Path


def extract_text(file_path: str | Path) -> str:
    """
    Extract text from a document.
   
    Args:
        file_path: Path to the document.
        
    Returns:
        str: Extracted text content.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix == ".txt":
        return _extract_from_txt(file_path)
    elif suffix == ".pdf":
        return _extract_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_from_txt(file_path: Path) -> str:
    """Extract text from a .txt file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz
    
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    
    return text
