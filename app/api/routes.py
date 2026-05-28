from fastapi import APIRouter

from app.models.vulnerability import (
    EnrichmentResponse,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    VulnerabilityRecord,
)
from app.services.embedding_service import EmbeddingService
from app.services.enrichment_service import EnrichmentService
from app.services.vector_store import VectorStore


router = APIRouter()

embedding_service = EmbeddingService()

vector_store = VectorStore(
    collection_name="vulnerabilities",
    vector_size=embedding_service.get_embedding_dimension(),
)

enrichment_service = EnrichmentService(
    embedding_service=embedding_service,
    vector_store=vector_store,
)


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@router.post(
    "/vulnerabilities/enrich",
    response_model=EnrichmentResponse,
)
def enrich_vulnerability(
    vulnerability: VulnerabilityRecord,
) -> EnrichmentResponse:
    return enrichment_service.enrich_vulnerability(vulnerability)


@router.post(
    "/vulnerabilities/search",
    response_model=SimilaritySearchResponse,
)
def search_similar_vulnerabilities(
    request: SimilaritySearchRequest,
) -> SimilaritySearchResponse:
    return enrichment_service.search_similar_vulnerabilities(
        query=request.query,
        limit=request.limit,
    )