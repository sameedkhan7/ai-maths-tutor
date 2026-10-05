import re
from pathlib import Path
from backend.rag.config import (
    TOP_K_RESULTS,
    MIN_RELEVANCE_SCORE,
    CHROMA_PERSIST_DIR,
    SAMPLE_DOCS_DIR
)
from backend.rag.embeddings import get_embeddings
from backend.rag.ingest import load_documents, split_text_into_chunks

_cached_chunks = None

def get_all_chunks():
    global _cached_chunks
    if _cached_chunks is None:
        docs = load_documents()
        _cached_chunks = split_text_into_chunks(docs)
    return _cached_chunks


def retrieve_math_context(query: str, top_k: int = TOP_K_RESULTS) -> dict:
    """
    Retrieves the most relevant NCERT math textbook chunks for a student query.
    Returns:
        {
            "has_context": bool,
            "chunks": list[dict],
            "formatted_context": str
        }
    """
    if not query or not query.strip():
        return {"has_context": False, "chunks": [], "formatted_context": ""}

    chunks = get_all_chunks()
    if not chunks:
        return {"has_context": False, "chunks": [], "formatted_context": ""}

    # 1. Try LangChain Chroma Retriever if available
    embeddings = get_embeddings()
    if embeddings and CHROMA_PERSIST_DIR.exists():
        try:
            from langchain_chroma import Chroma
            db = Chroma(
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=embeddings
            )
            results = db.similarity_search_with_relevance_scores(query, k=top_k)
            retrieved = []
            for doc, score in results:
                retrieved.append({
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "NCERT Textbook"),
                    "page": doc.metadata.get("page", 1),
                    "score": float(score)
                })

            if retrieved:
                formatted = "\n\n---\n\n".join([
                    f"[NCERT Source: {c['source']} (Page {c['page']})]\n{c['text']}"
                    for c in retrieved
                ])
                return {
                    "has_context": True,
                    "chunks": retrieved,
                    "formatted_context": formatted
                }
        except Exception as e:
            # Fallback to local matching
            pass

    # 2. Fast Keyword + Relevance Scoring Fallback
    query_words = set(re.findall(r'\w+', query.lower()))
    scored_chunks = []

    for chunk in chunks:
        text_lower = chunk["text"].lower()
        # Count matched keywords
        matches = sum(1 for w in query_words if w in text_lower and len(w) > 2)
        if matches > 0:
            score = min(0.95, 0.4 + (matches * 0.15))
            scored_chunks.append({
                "text": chunk["text"],
                "source": chunk["metadata"].get("source", "NCERT Mathematics"),
                "page": chunk["metadata"].get("page", 1),
                "score": score
            })

    # Sort by score descending
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:top_k]

    if top_chunks:
        formatted = "\n\n---\n\n".join([
            f"[NCERT Source: {c['source']} (Page {c['page']})]\n{c['text']}"
            for c in top_chunks
        ])
        return {
            "has_context": True,
            "chunks": top_chunks,
            "formatted_context": formatted
        }

    return {"has_context": False, "chunks": [], "formatted_context": ""}


def get_langchain_retriever(k: int = TOP_K_RESULTS):
    """
    Returns standard LangChain retriever instance for LCEL chains.
    """
    embeddings = get_embeddings()
    if embeddings and CHROMA_PERSIST_DIR.exists():
        from langchain_chroma import Chroma
        db = Chroma(
            persist_directory=str(CHROMA_PERSIST_DIR),
            embedding_function=embeddings
        )
        return db.as_retriever(search_kwargs={"k": k})
    return None


if __name__ == "__main__":
    res = retrieve_math_context("What is the derivative of x^n?")
    print("Has context:", res["has_context"])
    print("Chunks count:", len(res["chunks"]))
    if res["chunks"]:
        print("Sample context:\n", res["formatted_context"][:200])
