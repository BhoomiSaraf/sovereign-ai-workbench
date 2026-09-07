from langchain_core.tools import tool

from app.rag.retriever import KnowledgeRetriever


@tool
def search_organizational_knowledge(query: str) -> str:
    """Look up private organizational knowledge to ground reasoning.

    Use this tool when the task depends on internal SOPs, past
    inspection reports, maintenance procedures, safety protocols,
    delegation-of-power rules, or financial approval limits.

    The knowledge base is local and air-gapped. Combine the
    returned citations with OCR/vision observations. Do not treat
    retrieved policy text as a live observation of current
    equipment condition.

    Args:
        query: Natural-language search query, for example
            "pump visual inspection failure criteria" or
            "maintenance department approval limit".

    Returns:
        Citation-formatted passages, or a message that no
        sufficiently relevant organizational information was found.
    """

    try:
        retriever = KnowledgeRetriever()
        return retriever.search_formatted(query)
    except Exception as exc:
        return (
            "Organizational knowledge search failed: "
            f"{exc}"
        )
