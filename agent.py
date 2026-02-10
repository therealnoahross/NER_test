#!/usr/bin/env python3
"""
Ingestion Pipeline Agent

Processes documents to extract entities and relationships,
then stores them in Redis.

Usage:
    # Process a single file
    python agent.py document.txt
    python agent.py document.pdf
    
    # Process with flush (clear existing data first)
    python agent.py document.txt --flush
    
    # Run in pub/sub listener mode (for continuous processing)
    python agent.py --listen
"""

import sys
from pathlib import Path

import dspy

from config import LLM_ENDPOINT, LLM_MODEL, REDIS_HOST
from extract_text import extract_text
from chunker import chunk_text
from extractor import extract_from_chunk
from storage import get_redis_client, store_extraction, flush_triples, get_all_triples


def setup_llm():
    """Configure DSPy with the LLM endpoint."""
    print(f"Configuring LLM: {LLM_MODEL}")
    print(f"Endpoint: {LLM_ENDPOINT}")
    
    lm = dspy.LM(
        LLM_MODEL,
        api_base=LLM_ENDPOINT,
        api_key="local",
        model_type="chat"
    )
    dspy.configure(lm=lm)
    print("✓ LLM configured\n")


def process_document(file_path: str, r) -> dict:
    """
    Full pipeline for processing one document.
    
    Args:
        file_path: Path to the document.
        r: Redis client.
        
    Returns:
        dict: Statistics about the processing.
    """
    file_path = Path(file_path)
    print(f"\n{'='*60}")
    print(f"Processing: {file_path.name}")
    print('='*60)
    
    # 1. Extract text
    print("\n[1/4] Extracting text...")
    text = extract_text(file_path)
    print(f"Extracted {len(text):,} characters")
    
    # 2. Chunk
    print("\n[2/4] Chunking...")
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # 3. Extract entities and triples
    print("\n[3/4] Extracting entities and triples...")
    total_entities = 0
    total_triples = 0
    
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)}...", end=" ")
        
        extraction = extract_from_chunk(
            text=chunk,
            chunk_id=i,
            source=file_path.name
        )
        
        # 4. Store
        stored = store_extraction(r, extraction)
        
        total_entities += len(extraction.entities)
        total_triples += len(extraction.triples)
        
        print(f"entities: {len(extraction.entities)}, triples: {len(extraction.triples)}")
    
    print(f"\n[4/4] Storage complete")
    
    stats = {
        "file": file_path.name,
        "chunks": len(chunks),
        "entities": total_entities,
        "triples": total_triples,
    }
    
    return stats


def listen_mode(r):
    """
    Run in pub/sub listener mode for continuous document processing.
    
    Listens on channel: documents_to_process
    Publishes completion to: processing_complete
    """
    print("\n" + "="*60)
    print("LISTENER MODE")
    print("="*60)
    print(f"Redis: {REDIS_HOST}")
    print("Subscribing to channel: documents_to_process")
    print("Press Ctrl+C to stop\n")
    
    pubsub = r.pubsub()
    pubsub.subscribe("documents_to_process")
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            file_path = message['data']
            print(f"\nReceived: {file_path}")
            
            try:
                stats = process_document(file_path, r)
                r.publish("processing_complete", f"{file_path}|success|{stats['triples']} triples")
                print(f"✓ Published completion for {file_path}")
            except Exception as e:
                r.publish("processing_complete", f"{file_path}|error|{str(e)}")
                print(f"✗ Error processing {file_path}: {e}")


def show_stats(r):
    """Display current database statistics."""
    triples = get_all_triples(r)
    
    print(f"\n{'='*60}")
    print("DATABASE STATISTICS")
    print('='*60)
    print(f"Total triples: {len(triples)}")
    
    if triples:
        # Count by predicate
        predicates = {}
        for t in triples:
            pred = t.get("predicate", "unknown")
            predicates[pred] = predicates.get(pred, 0) + 1
        
        print("\nTriples by predicate:")
        for pred, count in sorted(predicates.items(), key=lambda x: -x[1]):
            print(f"  {pred}: {count}")
        
        # Show sample
        print("\nSample triples (first 5):")
        for t in triples[:5]:
            print(f"  ({t['subject']}) --[{t['predicate']}]--> ({t['object']})")


def main():
    """Main entry point."""
    args = sys.argv[1:]
    
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        sys.exit(0)
    
    # Parse flags
    flush = "--flush" in args
    listen = "--listen" in args
    stats = "--stats" in args
    
    # Get file path (if provided)
    file_paths = [a for a in args if not a.startswith("--")]
    
    # Setup
    setup_llm()
    r = get_redis_client()
    
    # Handle flush
    if flush:
        flush_triples(r, confirm=True)
    
    # Handle stats
    if stats:
        show_stats(r)
        return
    
    # Handle listen mode
    if listen:
        listen_mode(r)
        return
    
    # Process files
    if not file_paths:
        print("No files specified. Use --listen for pub/sub mode or provide file paths.")
        sys.exit(1)
    
    all_stats = []
    for file_path in file_paths:
        if not Path(file_path).exists():
            print(f"✗ File not found: {file_path}")
            continue
        
        stats = process_document(file_path, r)
        all_stats.append(stats)
    
    # Summary
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print('='*60)
    for s in all_stats:
        print(f"  {s['file']}: {s['chunks']} chunks, {s['entities']} entities, {s['triples']} triples")
    
    total_triples = sum(s['triples'] for s in all_stats)
    print(f"\nTotal triples stored: {total_triples}")


if __name__ == "__main__":
    main()
