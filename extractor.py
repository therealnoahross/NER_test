"""
Entity and relationship extraction using DSPy.

Uses an LLM to extract entities and triples from text chunks.
"""

import json
import dspy

from models import Entity, Triple, ExtractionResult


class ExtractTriples(dspy.Signature):
    """Extract entities and relationships from military text."""
    
    text: str = dspy.InputField(desc="Military document text")
    entities: str = dspy.OutputField(desc="JSON list of {name, type} objects. Types: UNIT, PERSON, LOCATION, EQUIPMENT, TIME, ORGANIZATION")
    triples: str = dspy.OutputField(desc="JSON list of {subject: {name, type}, predicate, object: {name, type}} objects")


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
    extractor = dspy.ChainOfThought(ExtractTriples)
    
    try:
        result = extractor(text=text)
        
        # Parse entities
        entities_raw = json.loads(result.entities)
        entities = [Entity(**e) for e in entities_raw]
        
        # Parse triples
        triples_raw = json.loads(result.triples)
        triples = []
        for t in triples_raw:
            triple = Triple(
                subject=Entity(**t["subject"]),
                predicate=t["predicate"],
                object=Entity(**t["object"]),
                confidence=t.get("confidence", 1.0)
            )
            triples.append(triple)
        
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=entities,
            triples=triples
        )
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"  ⚠ Failed to parse LLM response for chunk {chunk_id}: {e}")
        # Return empty result on parse failure
        return ExtractionResult(
            source_file=source,
            chunk_id=chunk_id,
            entities=[],
            triples=[]
        )
