from app.services.embedding_service import EmbeddingService

def test_embedding_service_generates_vector():
    service = EmbeddingService()

    embedding = service.embed_text("Remote code execution vulnerability")

    assert isinstance(embedding, list)
    assert len(embedding) == service.get_embedding_dimension()
    assert all(isinstance(value, float) for value in embedding)
