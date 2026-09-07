from langchain_core.tools import BaseTool

from app.rag.retriever import NO_RELEVANT_INFORMATION
from app.tools.rag_tool import search_organizational_knowledge


def test_search_organizational_knowledge_is_a_langchain_tool():
    assert isinstance(search_organizational_knowledge, BaseTool)
    assert search_organizational_knowledge.name == (
        "search_organizational_knowledge"
    )
    assert "SOP" in search_organizational_knowledge.description
    assert callable(search_organizational_knowledge.invoke)


def test_search_organizational_knowledge_uses_retriever(monkeypatch):
    calls = []

    class FakeRetriever:
        def search_formatted(self, query):
            calls.append(query)
            return (
                "Source: MRPL_Maintenance_SOP.md | "
                "Section: Pump Visual Inspection | Score: 0.1800\n"
                "Content: Inspect the coupling guard every shift."
            )

    monkeypatch.setattr(
        "app.tools.rag_tool.KnowledgeRetriever",
        FakeRetriever,
    )

    output = search_organizational_knowledge.invoke(
        {"query": "pump visual inspection"}
    )

    assert calls == ["pump visual inspection"]
    assert "Source: MRPL_Maintenance_SOP.md" in output
    assert "Section: Pump Visual Inspection" in output


def test_search_organizational_knowledge_returns_sentinel(monkeypatch):
    class FakeRetriever:
        def search_formatted(self, query):
            return NO_RELEVANT_INFORMATION

    monkeypatch.setattr(
        "app.tools.rag_tool.KnowledgeRetriever",
        FakeRetriever,
    )

    output = search_organizational_knowledge.invoke(
        {"query": "unrelated topic"}
    )

    assert output == NO_RELEVANT_INFORMATION
