"""
Redis storage for extracted triples.

Stores triples as Redis Hashes for easy querying.
"""

import redis

from models import ExtractionResult
from config import REDIS_HOST, REDIS_PORT


def get_redis_client() -> redis.Redis:
    """
    Create and return a Redis client connection.
    
    Returns:
        redis.Redis: Connected Redis client.
    """
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    
    try:
        client.ping()
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        raise
    
    return client


def store_extraction(r: redis.Redis, extraction: ExtractionResult) -> int:
    """
    Store extracted triples in Redis.
    
    Each triple is stored as a Redis Hash with key: triple:{source}:{chunk_id}:{index}
    
    Args:
        r: Redis client connection.
        extraction: The extraction result to store.
        
    Returns:
        int: Number of triples stored.
    """
    stored_count = 0
    
    for i, triple in enumerate(extraction.triples):
        # Create unique ID: source:chunk:index
        triple_id = f"{extraction.source_file}:{extraction.chunk_id}:{i}"
        
        # Store as hash
        r.hset(f"triple:{triple_id}", mapping={
            "subject": triple.subject.name,
            "subject_type": triple.subject.type,
            "predicate": triple.predicate,
            "object": triple.object.name,
            "object_type": triple.object.type,
            "confidence": str(triple.confidence),
            "source": extraction.source_file,
            "chunk_id": str(extraction.chunk_id),
        })
        stored_count += 1
    
    # Also store entities (optional, for entity lookup)
    for entity in extraction.entities:
        entity_key = f"entity:{entity.name}"
        r.hset(entity_key, mapping={
            "name": entity.name,
            "type": entity.type,
            "source": extraction.source_file,
        })
    
    return stored_count


def get_all_triples(r: redis.Redis) -> list[dict]:
    """
    Retrieve all stored triples from Redis.
    
    Returns:
        list[dict]: All triples as dictionaries.
    """
    triples = []
    
    for key in r.scan_iter("triple:*"):
        triple = r.hgetall(key)
        triple["id"] = key
        triples.append(triple)
    
    return triples


def get_triples_by_subject(r: redis.Redis, subject_name: str) -> list[dict]:
    """
    Find all triples where the subject matches.
    
    Note: This scans all triples. For production, use RediSearch.
    """
    triples = []
    
    for key in r.scan_iter("triple:*"):
        triple = r.hgetall(key)
        if triple.get("subject") == subject_name:
            triple["id"] = key
            triples.append(triple)
    
    return triples


def flush_triples(r: redis.Redis, confirm: bool = True) -> bool:
    """
    Delete all triples and entities from Redis.
    
    Args:
        r: Redis client.
        confirm: If True, prompt for confirmation.
        
    Returns:
        bool: True if flushed, False if cancelled.
    """
    if confirm:
        response = input("Delete all triples and entities? (y/N): ")
        if response.lower() != 'y':
            print("  Cancelled.")
            return False
    
    # Delete all triple keys
    for key in r.scan_iter("triple:*"):
        r.delete(key)
    
    # Delete all entity keys
    for key in r.scan_iter("entity:*"):
        r.delete(key)
    
    print("All triples and entities deleted.")
    return True
