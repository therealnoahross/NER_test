"""
Data models for the ingestion pipeline.

Defines Pydantic schemas for entities, triples, and extraction results.
"""

from pydantic import BaseModel


class Entity(BaseModel):
    """Represents a named entity extracted from text."""
    name: str
    type: str  # UNIT, PERSON, LOCATION, EQUIPMENT, TIME, etc.


class Triple(BaseModel):
    """Represents a relationship between two entities."""
    subject: Entity
    predicate: str  # located_at, commands, equipped_with, etc.
    object: Entity
    confidence: float = 1.0


class ExtractionResult(BaseModel):
    """Contains all extracted data from a single chunk."""
    source_file: str
    chunk_id: int
    entities: list[Entity]
    triples: list[Triple]
