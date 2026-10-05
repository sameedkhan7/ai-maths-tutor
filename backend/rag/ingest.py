import os
import glob
from pathlib import Path
from backend.rag.config import (
    RAW_PDFS_DIR,
    SAMPLE_DOCS_DIR,
    CHROMA_PERSIST_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from backend.rag.embeddings import get_embeddings

def load_documents():
    """
    Loads documents from data/raw_pdfs/ (PDFs) and data/sample_docs/ (Text files).
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

    # 2. Load PDF files from raw_pdfs
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
    docs = load_documents()
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

if __name__ == "__main__":
    ingest_all()
