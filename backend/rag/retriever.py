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

try:
    from backend.rag.curriculum import classify_question_curriculum, normalize_class_name
except ImportError:
    from rag.curriculum import classify_question_curriculum, normalize_class_name

_cached_chunks = None

def get_all_chunks():
    global _cached_chunks
    if _cached_chunks is None:
        docs = load_documents(include_pdfs=False)
        _cached_chunks = split_text_into_chunks(docs)
    return _cached_chunks


def retrieve_math_context(query: str, student_class: str = "Class 10", top_k: int = TOP_K_RESULTS) -> dict:
    """
    Retrieves NCERT math curriculum context for a student query with:
    1. Priority Search on student's selected class (e.g. Class 12 first).
    2. Fallback to other classes if topic belongs to Class 9/10/11.
    3. Cross-class detection and automatic citation badge generation.
    """
    if not query or not query.strip():
        return {
            "has_context": False,
            "chunks": [],
            "formatted_context": "",
            "reference_badge": "📚 NCERT Mathematics",
            "matched_class": student_class,
            "target_class": student_class,
            "is_cross_class": False,
            "note_text": None
        }

    # 1. ⚡ Fast NCERT Curriculum Search (Class-Priority First)
    curriculum_meta = classify_question_curriculum(query, student_class=student_class)
    matched_class = curriculum_meta.get("matched_class", student_class)
    target_class = curriculum_meta.get("target_class", student_class)
    is_cross_class = curriculum_meta.get("is_cross_class", False)
    chapter_title = curriculum_meta.get("chapter_title", "")
    chapter_summary = curriculum_meta.get("chapter_summary", "")
    reference_badge = curriculum_meta.get("reference_badge", f"📚 NCERT Reference: {target_class}")
    note_text = curriculum_meta.get("note_text")

    chunks = get_all_chunks()
    scored_chunks = []

    # 2. Try LangChain Chroma Retriever if available
    embeddings = get_embeddings()
    if embeddings and CHROMA_PERSIST_DIR.exists():
        try:
            from langchain_chroma import Chroma
            db = Chroma(
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=embeddings
            )
            results = db.similarity_search_with_relevance_scores(query, k=top_k)
            for doc, score in results:
                scored_chunks.append({
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", f"NCERT {matched_class}"),
                    "page": doc.metadata.get("page", 1),
                    "score": float(score)
                })
        except Exception:
            pass

    # 3. Fast Keyword Matching with Priority Boost on Matched Class
    if not scored_chunks and chunks:
        query_words = set(re.findall(r'\w+', query.lower()))
        matched_class_norm = matched_class.lower().replace(" ", "")

        for chunk in chunks:
            text_lower = chunk["text"].lower()
            source_lower = str(chunk["metadata"].get("source", "")).lower()

            matches = sum(1 for w in query_words if w in text_lower and len(w) > 2)
            if matches > 0:
                base_score = 0.4 + (matches * 0.15)
                # Class Priority Boost: if document matches the identified class, boost relevance
                if matched_class_norm in source_lower or matched_class_norm in text_lower:
                    base_score += 0.3
                scored_chunks.append({
                    "text": chunk["text"],
                    "source": chunk["metadata"].get("source", f"NCERT {matched_class}"),
                    "page": chunk["metadata"].get("page", 1),
                    "score": min(0.98, base_score)
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        scored_chunks = scored_chunks[:top_k]

    # 4. Assemble Final Context with Curriculum Grounding
    curriculum_header = f"[Official NCERT Grounding: {reference_badge}]\nChapter Scope: {chapter_title} — {chapter_summary}"
    
    if scored_chunks:
        chunks_text = "\n\n---\n\n".join([
            f"[Source: {c['source']} (Page {c['page']})]\n{c['text']}"
            for c in scored_chunks
        ])
        formatted_context = f"{curriculum_header}\n\nExcerpts:\n{chunks_text}"
    else:
        formatted_context = curriculum_header

    return {
        "has_context": True,
        "chunks": scored_chunks,
        "formatted_context": formatted_context,
        "reference_badge": reference_badge,
        "matched_class": matched_class,
        "target_class": target_class,
        "is_cross_class": is_cross_class,
        "chapter_no": curriculum_meta.get("chapter_no"),
        "chapter_title": chapter_title,
        "note_text": note_text
    }


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
