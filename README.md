# ai-threat-observatory


http://localhost:6333

# Rôles
routes.py = couche HTTP
enrichment_service.py = logique métier
embedding_service.py = IA
vector_store.py = stockage vectoriel

# Ordre logique :
1. API démarre
2. modèles de données
3. embeddings
4. stockage Qdrant
5. endpoint d’enrichissement
6. endpoint de similarité
7. tests
8. documentation