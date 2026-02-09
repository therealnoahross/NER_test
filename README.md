# Ingestion Pipeline

Extracts entities and relationships from documents using LLMs, stores them as triples in Redis.

## Quick Start

### 1. Start Local Redis

```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Process a Document

```bash
uv run python agent.py sample_opord.txt
```

### 4. View Results

Open http://localhost:8001 (RedisInsight) or:

```bash
uv run python agent.py --stats
```

## Usage

```bash
# Process a single file
uv run python agent.py document.txt

# Process multiple files
uv run python agent.py doc1.txt doc2.pdf

# Clear database and process
uv run python agent.py document.txt --flush

# Show database statistics
uv run python agent.py --stats

# Run in listener mode (pub/sub)
uv run python agent.py --listen
```

## Switching to Ares Redis

Edit `config.py`:

```python
USE_LOCAL_REDIS = False  # Change from True to False
```

## Project Structure

```
ingestion_pipeline/
├── config.py           # Redis and LLM settings
├── models.py           # Pydantic schemas (Entity, Triple)
├── extract_text.py     # Document text extraction
├── chunker.py          # Text chunking
├── extractor.py        # DSPy-based extraction
├── storage.py          # Redis storage
├── agent.py            # Main entry point
├── docker-compose.yaml # Local Redis
└── pyproject.toml      # Dependencies
```

## Data Flow

```
Document (txt/pdf)
       ↓
   extract_text.py     → Raw text
       ↓
   chunker.py          → Text chunks
       ↓
   extractor.py        → Entities + Triples (via LLM)
       ↓
   storage.py          → Redis Hashes
```

## Redis Data Structure

Each triple is stored as a hash:

```
KEY: triple:sample_opord.txt:0:0

subject:      1st Battalion
subject_type: UNIT
predicate:    located_at
object:       FOB Thunder
object_type:  LOCATION
confidence:   1.0
source:       sample_opord.txt
chunk_id:     0
```
