# ai-threat-observatory

http://localhost:6333/dashboard

## Rôles
routes.py = couche HTTP
enrichment_service.py = logique métier
embedding_service.py = IA
vector_store.py = stockage vectoriel

## Ordre logique :
1. API démarre
2. modèles de données
3. embeddings
4. stockage Qdrant
5. endpoint d’enrichissement
6. endpoint de similarité
7. tests
8. documentation

The AI enrichment module uses a normalized internal vulnerability schema instead of coupling the enrichment logic to a specific external feed format. Source-specific adapters can map records from the Cybersecurity Data Space, Vulnerability-Lookup, CIRCL CVE feeds or other advisory sources into this internal schema before embedding generation and vector storage.


# structure :

- project overview
- install
- run with Docker Compose
- API endpoints
- curl examples
- tests
- repository structure
- migration notes