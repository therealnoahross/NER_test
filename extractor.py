"""
Entity and relationship extraction using DSPy.

Uses an LLM to extract entities and triples from text chunks.
"""

import json
import re
import dspy

from models import Entity, Triple, ExtractionResult


class ExtractTriples(dspy.Signature):
    """Extract entities and relationships from military text."""
    
    text: str = dspy.InputField(desc="Military document text")
    entities: str = dspy.OutputField(desc="JSON list of {name, type} objects. Types: UNIT, PERSON, LOCATION, EQUIPMENT, TIME, ORGANIZATION")
    triples: str = dspy.OutputField(desc="JSON list of {subject: {name, type}, predicate, object: {name, type}} objects")


def clean_json_response(text: str) -> str:
    """
    Remove markdown code blocks and other formatting from LLM JSON responses.
    
    Args:
        text: Raw LLM output that may contain ```json blocks.
        
    Returns:
        str: Clean JSON string.
    """
    if not text:
        return "[]"
    
    cleaned = text.strip()
    
    # Remove ```json at start (with optional whitespace/newlines)
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    
    # Remove ``` at end
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    # Try to fix truncated JSON by closing brackets
    if cleaned and not cleaned.endswith(']'):
        # Count open brackets
        open_brackets = cleaned.count('[') - cleaned.count(']')
        open_braces = cleaned.count('{') - cleaned.count('}')
        
        # Try to close them (rough fix for truncation)
        cleaned += '}' * open_braces
        cleaned += ']' * open_brackets
    
    return cleaned


def extract_from_chunk(text: str, chunk_id: int, source: str) -> ExtractionResult:
    """
    Extract entities and triples from a text chunk using LLM.
    
    Args:
        text: The text chunk to process.
        chunk_id: Index of this chunk in the document.
        source: Source filename for provenance.
        
    Returns:
        ExtractionResult: Validated extraction containing entities and triples.
    """
    # Skip empty or very short chunks
    if not text or len(text.strip()) < 20:
        print(f"  Chunk {chunk_id} is too short, skipping")
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=[],
            triples=[]
        )
    
    extractor = dspy.ChainOfThought(ExtractTriples)
    
    try:
        result = extractor(text=text)
        
        # Clean markdown formatting from responses
        entities_json = clean_json_response(result.entities)
        triples_json = clean_json_response(result.triples)
        
        # Debug: show if cleaning was needed
        if '```' in result.entities or '```' in result.triples:
            print(f"  (cleaned markdown from response)")
        
        # Parse entities
        entities_raw = json.loads(entities_json)
        print(f"    DEBUG entities_raw: {entities_raw}")
        entities = [Entity(**e) for e in entities_raw]
        
        # Parse triples
        triples_raw = json.loads(triples_json)
        print(f"    DEBUG triples_raw: {triples_raw}")
        triples = []
        for t in triples_raw:
            try:
                # Handle subject - could be dict or string
                if isinstance(t["subject"], dict):
                    subject = Entity(**t["subject"])
                else:
                    subject = Entity(name=str(t["subject"]), type="UNKNOWN")
                
                # Handle object - could be dict or string
                if isinstance(t["object"], dict):
                    obj = Entity(**t["object"])
                else:
                    obj = Entity(name=str(t["object"]), type="UNKNOWN")
                
                triple = Triple(
                    subject=subject,
                    predicate=t["predicate"],
                    object=obj,
                    confidence=t.get("confidence", 1.0)
                )
                triples.append(triple)
            except (KeyError, TypeError) as e:
                print(f"    Skipping malformed triple: {t} - {e}")
                continue
        
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=entities,
            triples=triples
        )
        
    except json.JSONDecodeError as e:
        print(f"    JSON parse error for chunk {chunk_id}: {e}")
        print(f"    Cleaned entities: {entities_json[:200] if 'entities_json' in dir() else 'N/A'}...")
        print(f"    Cleaned triples: {triples_json[:200] if 'triples_json' in dir() else 'N/A'}...")
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=[],
            triples=[]
        )
    except (KeyError, TypeError) as e:
        print(f"    Data structure error for chunk {chunk_id}: {e}")
        print(f"    Parsed entities structure: {entities_raw[:3] if 'entities_raw' in dir() else 'N/A'}")
        print(f"    Parsed triples structure: {triples_raw[:1] if 'triples_raw' in dir() else 'N/A'}")
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=[],
            triples=[]
        )