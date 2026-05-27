from uuid import NAMESPACE_DNS, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.models.vulnerability import SimilaritySearchResult, VulnerabilityRecord

class VectorStore:
    def __init__(
            self,
            host: str = "localhost",
            port: int = 6333,
            collection_name: str = "vulnerabilities",
            vector_size: int | None = None,
    ):
        if vector_size is None:
            raise ValueError("vector_size must be provided by the embedding service.")
        
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(host=host, port=port)

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_vulnerability(
        self,
        vulnerability: VulnerabilityRecord,
        embedding: list[float],
    ) -> str:
        point_id = str(uuid5(NAMESPACE_DNS, vulnerability.vulnerability_id))

        payload = vulnerability.model_dump()

        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload,
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        return point_id

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[SimilaritySearchResult]:
        search_response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
        )

        results = []

        for result in search_response.points:
            payload = result.payload or {}

            results.append(
                SimilaritySearchResult(
                    vulnerability_id=payload.get("vulnerability_id", ""),
                    score=result.score,
                    title=payload.get("title", ""),
                    description=payload.get("description", ""),
                    severity=payload.get("severity"),
                    cvss_score=payload.get("cvss_score"),
                    source=payload.get("source"),
                )
            )

        return results
        