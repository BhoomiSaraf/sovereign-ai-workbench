from fastapi import APIRouter, Query

from app.rag.retriever import KnowledgeRetriever


router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


@router.get("/search")
def search_knowledge(
    query: str = Query(
        ...,
        min_length=1,
    ),
    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),
):
    """
    Search the local organizational knowledge base.
    """

    retriever = KnowledgeRetriever()

    results = retriever.search(
        query=query,
        top_k=top_k,
    )

    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "text": result.text,
                "source": result.source,
                "score": result.score,
                "metadata": result.metadata,
            }
            for result in results
        ],
    }