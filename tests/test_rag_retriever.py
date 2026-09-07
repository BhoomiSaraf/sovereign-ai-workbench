from app.rag.retriever import (
    CONFIDENCE_THRESHOLD,
    NO_RELEVANT_INFORMATION,
    KnowledgeRetriever,
    RetrievalResult,
)


class FakeEmbeddingModel:
    def embed_query(self, text):
        return [1.0, 0.0]


class ScoreStore:
    def __init__(self, scored):
        self.scored = scored

    def similarity_search_with_score(self, embedding, top_k):
        return self.scored[:top_k]


def test_search_returns_sentinel_when_top_distance_exceeds_threshold():
    store = ScoreStore(
        [
            (
                "unrelated text",
                {"source": "noise.md", "Header 1": "Other"},
                CONFIDENCE_THRESHOLD + 0.25,
            )
        ]
    )

    retriever = KnowledgeRetriever(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    results = retriever.search("quantum astrophysics recipes")

    assert len(results) == 1
    assert results[0].text == NO_RELEVANT_INFORMATION
    assert retriever.search_formatted(
        "quantum astrophysics recipes"
    ) == NO_RELEVANT_INFORMATION


def test_search_keeps_strong_matches_and_formats_citations():
    store = ScoreStore(
        [
            (
                "Inspect the coupling guard every shift.",
                {
                    "source": "MRPL_Maintenance_SOP.md",
                    "Header 1": "MRPL Mechanical Maintenance Standard Operating Procedure",
                    "section": "Pump Visual Inspection",
                },
                0.21,
            ),
            (
                "unrelated distant chunk",
                {"source": "other.md", "Header 1": "Other"},
                CONFIDENCE_THRESHOLD + 0.4,
            ),
        ]
    )

    retriever = KnowledgeRetriever(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    results = retriever.search("pump visual inspection")

    assert len(results) == 1
    assert "coupling guard" in results[0].text

    citation = retriever.format_citation(results[0])

    assert citation.startswith("Source: MRPL_Maintenance_SOP.md")
    assert "Section: MRPL Mechanical Maintenance Standard Operating Procedure" in citation
    assert "Score: 0.2100" in citation
    assert "Content: Inspect the coupling guard every shift." in citation


def test_format_citations_uses_general_when_header_missing():
    result = RetrievalResult(
        text="Approval limit is INR 5,00,000.",
        source="Delegation_of_Power_2026.md",
        score=0.4,
        metadata={"source": "Delegation_of_Power_2026.md"},
    )

    formatted = KnowledgeRetriever(
        embedding_model=FakeEmbeddingModel(),
        store=ScoreStore([]),
    ).format_citation(result)

    assert "Section: General" in formatted
