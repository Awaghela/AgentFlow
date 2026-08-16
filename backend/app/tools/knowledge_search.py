from __future__ import annotations

from app.rag.retriever import retrieve_context


def knowledge_search(query: str, top_k: int = 3) -> dict:
    result = retrieve_context(query, top_k=top_k)
    return {
        "query": result.query,
        "doc_ids": result.doc_ids,
        "num_results": result.num_results,
        "top_score": result.top_score,
    }
