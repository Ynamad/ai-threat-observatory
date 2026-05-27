from app.models.vulnerability import (
    EnrichmentResponse,
    SimilaritySearchResponse,
    VulnerabilityRecord,
)
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


class EnrichmentService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def enrich_vulnerability(
        self,
        vulnerability: VulnerabilityRecord,
    ) -> EnrichmentResponse:
        embedding_text = vulnerability.to_embedding_text()
        embedding = self.embedding_service.embed_text(embedding_text)

        point_id = self.vector_store.upsert_vulnerability(
            vulnerability=vulnerability,
            embedding=embedding,
        )

        return EnrichmentResponse(
            vulnerability_id=vulnerability.vulnerability_id,
            status="enriched",
            message=f"Vulnerability stored successfully with point ID {point_id}.",
        )

    def search_similar_vulnerabilities(
        self,
        query: str,
        limit: int = 5,
    ) -> SimilaritySearchResponse:
        query_embedding = self.embedding_service.embed_text(query)

        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            limit=limit,
        )

        return SimilaritySearchResponse(
            query=query,
            results=results,
        )