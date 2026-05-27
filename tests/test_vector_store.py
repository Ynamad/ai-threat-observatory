from app.models.vulnerability import VulnerabilityRecord
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


def test_vector_store_upsert_and_search():
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        collection_name="test_vulnerabilities", 
        vector_size=embedding_service.get_embedding_dimension()
    )

    vulnerability = VulnerabilityRecord(
        vulnerability_id="CVE-2024-0001",
        title="Remote code execution in web application",
        description="An attacker can remotely execute arbitrary code through a vulnerable endpoint.",
        severity="critical",
        cvss_score=9.8,
        source="test",
        language="en",
    )

    embedding = embedding_service.embed_text(vulnerability.to_embedding_text())

    point_id = vector_store.upsert_vulnerability(vulnerability, embedding)

    query_embedding = embedding_service.embed_text("remote code execution vulnerability")

    results = vector_store.search_similar(query_embedding, limit=3)

    assert point_id is not None
    assert len(results) >= 1
    assert results[0].vulnerability_id == "CVE-2024-0001"