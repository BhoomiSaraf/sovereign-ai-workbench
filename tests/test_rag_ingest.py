from app.rag.ingest import KnowledgeIngester


class FakeEmbeddingModel:
    def embed_documents(self, texts):
        return [
            [float(len(text)), 1.0]
            for text in texts
        ]

    def embed_query(self, text):
        return [float(len(text)), 1.0]


class FakeStore:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.metadatas = []
        self.ids = []

    def add_documents(
        self,
        documents,
        embeddings,
        metadatas,
        ids,
    ):
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)


MARKDOWN = """# MRPL Maintenance SOP

## Pump Visual Inspection

Inspect the coupling guard, seal pot, and bearing housing on every shift.
Record only what is visible. Do not infer internal wear from paint condition.

### Inspection Sequence

Walk suction, casing, then discharge. Photograph the skid.

## Criteria for Failure

Declare the pump unfit when seal spray is visible or vibration exceeds 7.1 mm/s RMS.
"""


def test_ingest_splits_on_markdown_headers():
    store = FakeStore()

    ingester = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    count = ingester.ingest_text(
        text=MARKDOWN,
        source="MRPL_Maintenance_SOP.md",
        document_type="md",
        date_ingested="2026-09-07",
    )

    assert count >= 2
    assert len(store.documents) == count

    sections = {
        metadata["section"]
        for metadata in store.metadatas
    }

    assert "Pump Visual Inspection" in sections
    assert "Criteria for Failure" in sections or "Inspection Sequence" in sections

    for metadata in store.metadatas:
        assert metadata["source"] == "MRPL_Maintenance_SOP.md"
        assert metadata["document_type"] == "md"
        assert metadata["date_ingested"] == "2026-09-07"
        assert "section" in metadata


def test_ingest_file_supports_markdown(tmp_path):
    path = tmp_path / "Delegation_of_Power_2026.md"
    path.write_text(
        "# Delegation of Power 2026\n\n"
        "## Maintenance Department Limits\n\n"
        "Mechanical Maintenance Manager may approve up to INR 5,00,000.\n",
        encoding="utf-8",
    )

    store = FakeStore()

    result = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    ).ingest_file(str(path))

    assert result["status"] == "ingested"
    assert result["document_type"] == "md"
    assert result["chunks"] > 0
    assert store.metadatas[0]["source"] == path.name


def test_ingest_file_rejects_unsupported_type(tmp_path):
    path = tmp_path / "notes.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")

    result = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=FakeStore(),
    ).ingest_file(str(path))

    assert result["status"] == "error"
    assert "Unsupported" in result["error"]


def test_oversized_section_uses_recursive_fallback():
    huge_section = "Pump inspection notes. " * 80

    text = (
        "# Maintenance SOP\n\n"
        f"## Pump Visual Inspection\n\n{huge_section}\n"
    )

    store = FakeStore()

    count = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    ).ingest_text(
        text=text,
        source="long_sop.md",
        document_type="md",
    )

    assert count > 1
    assert all(
        metadata["section"] == "Pump Visual Inspection"
        for metadata in store.metadatas
    )
