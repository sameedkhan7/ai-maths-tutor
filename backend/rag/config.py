import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
CHROMA_PERSIST_DIR = BASE_DIR / "backend" / "chroma_db"

# RAG Splitter Configuration
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

# Multilingual Embedding Model (English + Hindi + 50+ languages)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_RESULTS = 2
MIN_RELEVANCE_SCORE = 0.35
