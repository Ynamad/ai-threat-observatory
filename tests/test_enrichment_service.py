from app.models.vulnerability import VulnerabilityRecord
from app.services.embedding_service import EmbeddingService
from app.services.enrichment_service import EnrichmentService
from app.services.vector_store import VectorStore


def test_enrichment_service_enrich_and_search():
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        collection_name="test_enrichment_vulnerabilities",
        vector_size=embedding_service.get_embedding_dimension(),
    )

    service = EnrichmentService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    vulnerability = VulnerabilityRecord(
        vulnerability_id="CVE-2024-9999",
        title="SQL injection in login form",
        description="An attacker can bypass authentication using crafted SQL payloads.",
        severity="high",
        cvss_score=8.1,
        source="test",
        language="en",
    )

    enrichment_response = service.enrich_vulnerability(vulnerability)

    assert enrichment_response.status == "enriched"
    assert enrichment_response.vulnerability_id == "CVE-2024-9999"

    search_response = service.search_similar_vulnerabilities(
        query="authentication bypass through SQL injection",
        limit=3,
    )

    assert search_response.query == "authentication bypass through SQL injection"
    assert len(search_response.results) >= 1
    assert search_response.results[0].vulnerability_id == "CVE-2024-9999"