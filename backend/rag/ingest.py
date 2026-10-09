import os
import sys
import glob
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from backend.rag.config import (
    RAW_PDFS_DIR,
    SAMPLE_DOCS_DIR,
    CHROMA_PERSIST_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from backend.rag.embeddings import get_embeddings

def load_documents(include_pdfs: bool = False):
    """
    Loads documents from data/sample_docs/ (Text files) and optionally data/raw_pdfs/ (PDFs).
    """
    documents = []
    
    # 1. Load Text files from sample_docs
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PDFS_DIR.mkdir(parents=True, exist_ok=True)

    text_files = list(SAMPLE_DOCS_DIR.glob("*.txt"))
    for file_path in text_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                # Create a lightweight doc structure
                documents.append({
                    "text": text,
                    "metadata": {
                        "source": file_path.name,
                        "page": 1,
                        "type": "text"
                    }
                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # 2. Load PDF files from raw_pdfs (only when include_pdfs is requested)
    if include_pdfs:
        pdf_files = list(RAW_PDFS_DIR.glob("*.pdf"))
        if pdf_files:
            try:
                from pypdf import PdfReader
                for pdf_path in pdf_files:
                    reader = PdfReader(str(pdf_path))
                    for page_num, page in enumerate(reader.pages):
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            documents.append({
                                "text": page_text,
                                "metadata": {
                                    "source": pdf_path.name,
                                    "page": page_num + 1,
                                    "type": "pdf"
                                }
                            })
            except Exception as e:
                print(f"PDF reading error: {e}")

    return documents


def split_text_into_chunks(documents: list[dict]) -> list[dict]:
    """
    Splits documents into overlapping chunks (700 chars with 100 overlap).
    """
    chunks = []
    
    for doc in documents:
        full_text = doc["text"]
        meta = doc["metadata"]
        
        start = 0
        while start < len(full_text):
            end = start + CHUNK_SIZE
            chunk_str = full_text[start:end].strip()
            if chunk_str:
                chunks.append({
                    "text": chunk_str,
                    "metadata": meta
                })
            start += (CHUNK_SIZE - CHUNK_OVERLAP)
            
    return chunks


def ingest_all():
    """
    Ingests all NCERT math documents into Chroma vector store.
    """
    print("Loading NCERT curriculum documents...")
    docs = load_documents(include_pdfs=True)
    print(f"Loaded {len(docs)} documents.")

    chunks = split_text_into_chunks(docs)
    print(f"Split into {len(chunks)} chunks.")

    embeddings = get_embeddings()
    if embeddings:
        try:
            from langchain_chroma import Chroma
            from langchain_core.documents import Document

            langchain_docs = [
                Document(page_content=c["text"], metadata=c["metadata"])
                for c in chunks
            ]

            CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            db = Chroma.from_documents(
                documents=langchain_docs,
                embedding=embeddings,
                persist_directory=str(CHROMA_PERSIST_DIR)
            )
            print(f"[OK] Ingested {len(chunks)} chunks into ChromaDB at {CHROMA_PERSIST_DIR}!")
            return db
        except Exception as e:
            print(f"Chroma ingest warning: {e}")

    print("[OK] Fallback chunk store ready.")
    return chunks

import re
import urllib.request
from bs4 import BeautifulSoup

def ingest_pdf_bytes(file_bytes: bytes, filename: str):
    """Saves PDF file bytes and updates RAG vector database"""
    RAW_PDFS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = RAW_PDFS_DIR / filename
    with open(pdf_path, "wb") as f:
        f.write(file_bytes)
    
    ingest_all()
    return {"filename": filename, "size_bytes": len(file_bytes)}

def ingest_text_content(title: str, content: str):
    """Saves text content and updates RAG vector database"""
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^a-zA-Z0-9]', '_', title)[:30]
    filename = f"note_{slug}.txt"
    file_path = SAMPLE_DOCS_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n\n{content}")
    
    ingest_all()
    return {"filename": filename, "char_count": len(content)}

def scrape_and_ingest_url(url: str):
    """Scrapes text content from web URL and ingests into RAG vector database"""
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        html = response.read().decode('utf-8', errors='ignore')
        
    soup = BeautifulSoup(html, 'html.parser')
    for elem in soup(["script", "style", "nav", "footer", "header", "svg"]):
        elem.extract()
        
    text = soup.get_text(separator=' ')
    clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(clean_lines)
    
    slug = re.sub(r'[^a-zA-Z0-9]', '_', url.replace('https://', '').replace('http://', ''))[:35]
    filename = f"scraped_{slug}.txt"
    file_path = SAMPLE_DOCS_DIR / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Source URL: {url}\n\n{clean_text}")
        
    ingest_all()
    return {"filename": filename, "source": url, "char_count": len(clean_text)}

import json

def get_rag_stats(force_refresh: bool = False):
    """Returns real-time statistics of RAG knowledge base (instant via metadata cache)"""
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PDFS_DIR.mkdir(parents=True, exist_ok=True)
    text_files = list(SAMPLE_DOCS_DIR.glob("*.txt"))
    pdf_files = list(RAW_PDFS_DIR.glob("*.pdf"))
    
    cache_file = RAW_PDFS_DIR.parent / "rag_stats_cache.json"
    if not force_refresh and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("pdf_count") == len(pdf_files) and cached.get("text_count") == len(text_files):
                cached["pdfs"] = [p.name for p in pdf_files]
                cached["texts"] = [t.name for t in text_files]
                return cached
        except Exception:
            pass

    docs = load_documents()
    chunks = split_text_into_chunks(docs)
    stats = {
        "pdf_count": len(pdf_files),
        "text_count": len(text_files),
        "total_documents": len(docs),
        "total_chunks": len(chunks),
        "pdfs": [p.name for p in pdf_files],
        "texts": [t.name for t in text_files]
    }
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass
    return stats

if __name__ == "__main__":
    ingest_all()
