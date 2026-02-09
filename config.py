"""
Configuration settings for the ingestion pipeline.
"""

# Toggle between local and Ares server
USE_LOCAL_REDIS = True

# Local Redis (Docker)
LOCAL_REDIS_HOST = "localhost"
LOCAL_REDIS_PORT = 6379

# Ares Redis (shared server)
ARES_REDIS_HOST = "ares.westpoint.edu"
ARES_REDIS_PORT = 6379

# Active connection (based on toggle)
REDIS_HOST = LOCAL_REDIS_HOST if USE_LOCAL_REDIS else ARES_REDIS_HOST
REDIS_PORT = LOCAL_REDIS_PORT if USE_LOCAL_REDIS else ARES_REDIS_PORT

# LLM Settings

LLM_ENDPOINT = "http://ares.westpoint.edu:11435/v1"
LLM_MODEL = "openai/gemma3"


# Chunking Settings

CHUNK_SIZE = 200  # words per chunk (reduced to avoid LLM response truncation)
CHUNK_OVERLAP = 30  # overlapping words between chunks