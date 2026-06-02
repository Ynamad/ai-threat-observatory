# ai-threat-observatory

## Overview

`ai-threat-observatory` is a Python/FastAPI project implementing the first version of the **Vulnerability Intelligence Correlation Service (VICS)**.

VICS is an AI-assisted vulnerability correlation service designed to integrate with Vulnerability-Lookup. It consumes vulnerability records, converts them into a normalized internal schema, generates semantic embeddings, stores vectors and metadata in Qdrant, and exposes similarity search through an API.

The current implementation focuses on semantic enrichment and vulnerability similarity search. It does not implement autonomous advisory generation, automated severity reassessment, or a complete threat observatory platform. Those capabilities are considered possible future extensions.

## Main Features

* FastAPI application exposing enrichment and similarity search endpoints.
* Internal `VulnerabilityRecord` schema for normalized vulnerability data.
* `VulnerabilityLookupAdapter` for mapping CVE-style Vulnerability-Lookup records into the internal schema.
* Semantic embedding generation using `sentence-transformers`.
* Vector storage and similarity search with Qdrant.
* Deterministic UUIDv5 point identifiers based on `vulnerability_id`, enabling idempotent re-ingestion.
* Unit tests with `pytest`.

## Architecture Summary

VICS is structured around a modular enrichment and correlation pipeline:

![AI Threat Observatory architecture](./images/ArchitectureObservatory.png)

Vulnerability-Lookup is treated as the direct vulnerability intelligence source for VICS. The adapter transforms records exposed by Vulnerability-Lookup into the internal `VulnerabilityRecord` schema. Once normalized, records can be embedded, stored in Qdrant, and retrieved through semantic similarity search.

Qdrant is used as a semantic vector index. It stores embeddings and metadata payloads required for similarity search, while Vulnerability-Lookup remains the consolidated vulnerability intelligence source.

## Repository Structure

```text
ai-threat-observatory/
├── app/
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── vulnerability_lookup_adapter.py
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   └── vulnerability.py
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── enrichment_service.py
│   │   └── vector_store.py
│   └── main.py
├── docs/
│   └── architecture.md
├── tests/
│   └── test_vulnerability_lookup_adapter.py
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

## Core Components

### FastAPI Application

The FastAPI application exposes the HTTP API. It defines the service metadata, includes the API routes, and provides a root endpoint.

Main endpoints:

* `GET /`: returns basic service status.
* `GET /health`: returns API health status.
* `POST /vulnerabilities/enrich`: enriches and stores a normalized vulnerability record.
* `POST /vulnerabilities/search`: searches for semantically similar vulnerabilities.

### VulnerabilityRecord

`VulnerabilityRecord` is the internal normalized vulnerability schema used by VICS. It contains the fields required for embedding generation and semantic search:

* `vulnerability_id`
* `title`
* `description`
* `severity`
* `cvss_score`
* `source`
* `language`

It also provides `to_embedding_text()`, which converts structured vulnerability data into text suitable for embedding generation.

### VulnerabilityLookupAdapter

`VulnerabilityLookupAdapter` maps CVE-style records exposed by Vulnerability-Lookup into the internal `VulnerabilityRecord` schema.

It extracts:

* CVE identifier;
* title;
* description;
* language;
* CVSS score;
* severity;
* source metadata.

For source traceability, the adapter can return values such as:

```text
Vulnerability-Lookup:f5
```

This indicates that the record was consumed through Vulnerability-Lookup while preserving the original provider metadata when available.

### EnrichmentService

`EnrichmentService` orchestrates the enrichment and retrieval logic.

For enrichment, it converts a `VulnerabilityRecord` into embedding-ready text, calls the embedding service, stores the vector through `VectorStore`, and returns an enrichment response.

For similarity search, it embeds the query and retrieves similar vulnerabilities from Qdrant.

### EmbeddingService

`EmbeddingService` generates semantic embeddings using a `sentence-transformers` model.

The default model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding model is encapsulated inside this service so it can be replaced later without changing the API, normalized data schema, or vector storage abstraction.

### VectorStore

`VectorStore` abstracts Qdrant operations.

It is responsible for:

* ensuring that the Qdrant collection exists;
* storing vulnerability vectors and metadata payloads;
* using deterministic UUIDv5 point IDs based on `vulnerability_id`;
* querying Qdrant for semantically similar vulnerabilities;
* converting Qdrant results into application-level response objects.

## Requirements

* Python 3.10 or later recommended.
* Docker and Docker Compose.
* Qdrant, launched through `docker-compose.yml`.
* Python dependencies listed in `requirements.txt`.

## Installation

Clone the repository:

```bash
git clone https://github.com/Ynamad/ai-threat-observatory.git
cd ai-threat-observatory
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running Qdrant

Start Qdrant with Docker Compose:

```bash
docker compose up -d
```

Qdrant will be available at:

```text
http://localhost:6333
```

The Qdrant dashboard is available at:

```text
http://localhost:6333/dashboard
```

Stop Qdrant:

```bash
docker compose down
```

## Running the API

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## API Examples

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

### Enrich a Vulnerability

`POST /vulnerabilities/enrich` expects a normalized `VulnerabilityRecord`.

```bash
curl -X POST "http://localhost:8000/vulnerabilities/enrich" \
  -H "Content-Type: application/json" \
  -d '{
    "vulnerability_id": "CVE-2026-42945",
    "title": "NGINX ngx_http_rewrite_module vulnerability",
    "description": "NGINX Plus and NGINX Open Source have a vulnerability in the ngx_http_rewrite_module module. An unauthenticated attacker can exploit this vulnerability by sending crafted HTTP requests.",
    "severity": "high",
    "cvss_score": 8.1,
    "source": "Vulnerability-Lookup:f5",
    "language": "en"
  }'
```

Example response:

```json
{
  "vulnerability_id": "CVE-2026-42945",
  "status": "enriched",
  "message": "Vulnerability stored successfully with point ID ..."
}
```

### Search Similar Vulnerabilities

```bash
curl -X POST "http://localhost:8000/vulnerabilities/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "remote code execution in a web server module using crafted HTTP requests",
    "limit": 5
  }'
```

Example response:

```json
{
  "query": "remote code execution in a web server module using crafted HTTP requests",
  "results": [
    {
      "vulnerability_id": "CVE-2026-42945",
      "score": 0.82,
      "title": "NGINX ngx_http_rewrite_module vulnerability",
      "description": "NGINX Plus and NGINX Open Source have a vulnerability in the ngx_http_rewrite_module module...",
      "severity": "high",
      "cvss_score": 8.1,
      "source": "Vulnerability-Lookup:f5"
    }
  ]
}
```

The exact similarity score depends on the embedding model and the indexed records.

## Vulnerability-Lookup Adapter Example

The adapter can be used to transform a Vulnerability-Lookup CVE-style record into a normalized `VulnerabilityRecord`.

```python
from app.adapters.vulnerability_lookup_adapter import VulnerabilityLookupAdapter

raw_record = {
    "containers": {
        "cna": {
            "title": "NGINX ngx_http_rewrite_module vulnerability",
            "descriptions": [
                {
                    "lang": "en",
                    "value": "NGINX Plus and NGINX Open Source have a vulnerability in the ngx_http_rewrite_module module.",
                }
            ],
            "metrics": [
                {
                    "format": "CVSS",
                    "cvssV3_1": {
                        "baseScore": 8.1,
                        "baseSeverity": "HIGH",
                    },
                }
            ],
            "providerMetadata": {
                "shortName": "f5",
            },
        }
    },
    "cveMetadata": {
        "cveId": "CVE-2026-42945",
        "assignerShortName": "f5",
    },
}

adapter = VulnerabilityLookupAdapter()
vulnerability = adapter.to_vulnerability_record(raw_record)

print(vulnerability.model_dump())
```

The adapter currently focuses on transforming Vulnerability-Lookup records into the internal schema. A complete HTTP client for automated synchronization with the Vulnerability-Lookup API can be added as a future extension.

## Testing

Run all tests:

```bash
python -m pytest
```

Run only the adapter tests:

```bash
python -m pytest tests/test_vulnerability_lookup_adapter.py
```

The current adapter tests verify that:

* CVE-style Vulnerability-Lookup records are correctly mapped to `VulnerabilityRecord`;
* CVSS score and severity are extracted correctly;
* source metadata falls back to `Vulnerability-Lookup` when provider metadata is not available.

## Migration Notes

The current implementation uses deterministic UUIDv5 identifiers derived from `vulnerability_id` when storing vectors in Qdrant. This makes ingestion idempotent: re-ingesting the same vulnerability updates the existing vector point instead of creating duplicates.

If the embedding model changes, existing vectors should not be mixed with vectors generated by the new model. A safe migration path is:

1. create a new Qdrant collection with a versioned name, for example `vulnerabilities_v2`;
2. re-embed existing vulnerability records with the new model;
3. store the new vectors in the new collection;
4. evaluate retrieval quality;
5. update the API configuration to use the new collection;
6. keep the previous collection temporarily for rollback.

## Current Limitations

* The current API accepts normalized `VulnerabilityRecord` payloads for enrichment.
* The `VulnerabilityLookupAdapter` maps Vulnerability-Lookup records programmatically, but automated synchronization with the live Vulnerability-Lookup API is not implemented yet.
* The current V1 focuses on semantic embeddings and similarity search.
* Generative advisory drafting is not implemented.
* Authentication, authorization, rate limiting and production-grade logging are not implemented in this development version.
* The default embedding model is general-purpose and should be evaluated against vulnerability-specific retrieval benchmarks before production use.

## Future Work

Potential extensions include:

* adding a Vulnerability-Lookup API client for scheduled synchronization;
* adding asynchronous ingestion workers for large feeds and historical backfills;
* supporting versioned Qdrant collections for embedding model migration;
* evaluating multilingual or cybersecurity-specific embedding models;
* adding retrieval quality metrics such as Precision@k, Recall@k and Mean Reciprocal Rank;
* adding authentication, role-based access control and rate limiting;
* adding observability for API latency, embedding latency, Qdrant latency and low-confidence search results;
* adding downstream generative advisory drafting with human validation.

## Project Status

This repository implements a functional V1 of VICS focused on semantic vulnerability enrichment, vector storage and similarity search. It is intended as a maintainable foundation for an AI-assisted vulnerability correlation service integrated with Vulnerability-Lookup.
