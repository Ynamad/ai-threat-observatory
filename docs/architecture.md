# Architecture and Design

## 1. Objective

The objective of this proposal is to extend the existing NC3 Cybersecurity Observatory with an AI-assisted vulnerability enrichment and correlation layer. The implemented V1, focused on multilingual semantic embeddings, vector storage, and similarity search, is designed to integrate with Vulnerability-Lookup. In the target architecture, this layer can contribute to multilingual advisory drafting using open-source generative models such as Qwen, and to Luxembourg-specific threat prioritization by combining semantic retrieval with structured risk signals such as CVSS, exploitability, affected products, sector relevance and local context.

## 2. Proposed AI Extension

The proposed extension is an AI-assisted vulnerability enrichment and correlation service designed to integrate with Vulnerability-Lookup and the broader cybersecurity observatory ecosystem.

The implemented V1 provides a focused and maintainable foundation:

- normalized vulnerability records;
- multilingual semantic embedding generation;
- vector storage in Qdrant;
- similarity search through a FastAPI API;
- deterministic upsert logic to avoid duplicate records during re-ingestion.

The enrichment pipeline is model-agnostic. The embedding model can be configured without changing the API, the business logic or the vector storage layer. For multilingual vulnerability records, the V1 can use a multilingual sentence-transformers model such as `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` or `BAAI/bge-m3`, allowing cross-language semantic correlation between vulnerability descriptions written in different languages.

The service is source-agnostic by design. It relies on an internal normalized `VulnerabilityRecord` schema, which acts as a stable boundary between external vulnerability sources and the AI enrichment pipeline. Vulnerability records coming from Vulnerability-Lookup can therefore be mapped into this schema before being embedded, indexed and correlated semantically.

In this design, Vulnerability-Lookup remains the primary vulnerability intelligence and correlation source, while the AI enrichment module adds a semantic correlation layer on top of structured vulnerability data. This avoids tightly coupling the AI pipeline to a single external JSON format while still allowing direct integration with Vulnerability-Lookup workflows.

This V1 is intentionally limited to semantic enrichment and correlation. It does not directly generate advisories or replace existing severity scoring systems.

Further production extensions can include:

- a dedicated Vulnerability-Lookup API client for automated synchronization;
- additional source-specific adapters for Cybersecurity Data Space datasets, CIRCL feeds, NVD or vendor advisories;
- retrieval-augmented advisory drafting using open-source generative models such as Qwen2.5, Mistral, or Llama 3;
- prioritization logic combining semantic similarity with structured cyber risk signals;
- observability and evaluation pipelines to monitor embedding quality, retrieval relevance and model behavior over time.

## 3. High-Level Architecture

The proposed architecture introduces an AI enrichment service between vulnerability intelligence sources and the Cybersecurity Observatory user-facing layer.

The service is designed as a modular component that can consume normalized vulnerability records, generate semantic embeddings, store them in a vector database and expose similarity search capabilities through an API.

![AI Threat Observatory architecture](../images/ArchitectureObservatory.png)

## 4. Service Decomposition

The system is decomposed into small components with clear responsibilities. The goal is to keep the AI enrichment module maintainable, testable and easy to evolve.

### 4.1 FastAPI Application

The FastAPI application exposes the HTTP interface of the enrichment service.

Main responsibilities:

- expose health and enrichment endpoints;
- receive normalized vulnerability records;
- receive semantic search queries;
- validate incoming JSON payloads;
- call the enrichment pipeline;
- return JSON responses to the client.

Implemented endpoints:

- `GET /health`: verifies that the API is running;
- `POST /vulnerabilities/enrich`: enriches and stores a vulnerability record;
- `POST /vulnerabilities/search`: searches for semantically similar vulnerabilities.

The API layer does not directly generate embeddings or communicate with Qdrant. It delegates this logic to the service layer.

### 4.2 VulnerabilityRecord Model

`VulnerabilityRecord` is the internal normalized schema used by the enrichment module.

It contains the core fields required for semantic enrichment:

- `vulnerability_id` : Unique vulnerability identifier, for example CVE-2024-12345;
- `title` : Short human-readable vulnerability title;
- `description` : Detailed vulnerability description;
- `severity` : Severity label such as low, medium, high or critical;
- `cvss_score` : CVSS score between 0.0 and 10.0;
- `source` : Source feed or provider, for example NVD, CIRCL or vendor advisory;
- `language` : Language of the original vulnerability record.

This schema acts as a stable boundary between external data sources and the internal AI pipeline. External formats coming from Vulnerability-Lookup, Cybersecurity Data Space datasets, CIRCL feeds, NVD or vendor advisories can be mapped with Source-specific adapters into this schema before enrichment.

The model also exposes `to_embedding_text()`, which converts the structured vulnerability data into embedding-ready text.

### 4.3 EnrichmentService

`EnrichmentService` is the central orchestration component of the AI pipeline.

For vulnerability enrichment, it:

1. receives a validated `VulnerabilityRecord`;
2. converts it into embedding-ready text;
3. calls `EmbeddingService` to generate a semantic vector;
4. sends the record and its embedding to `VectorStore`;
5. returns an enrichment response.

For similarity search, it:

1. receives a natural language query;
2. asks `EmbeddingService` to generate a query embedding;
3. calls `VectorStore.search_similar()`;
4. returns similar vulnerabilities with similarity scores.

`EnrichmentService` does not expose HTTP routes and does not depend directly on Qdrant-specific implementation details.

### 4.4 EmbeddingService

`EmbeddingService` is responsible for semantic embedding generation.

It converts vulnerability descriptions or search queries into numerical vectors using a `sentence-transformers` model.

The service is model-agnostic. The embedding model can be replaced without changing the API, the business logic or the vector storage logic. For multilingual vulnerability data, the service can use a multilingual model such as:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- `BAAI/bge-m3`.

This design allows the system to support cross-language semantic correlation while remaining easy to maintain.

### 4.5 VectorStore

`VectorStore` is the abstraction layer between the enrichment logic and Qdrant.

It is responsible for:

- creating or checking the Qdrant collection;
- storing vulnerability embeddings and payloads;
- querying the vector database for similar vulnerabilities;
- converting Qdrant search results into application-level response objects.

It exposes two main operations:

- `upsert_vulnerability()`: stores or updates a vulnerability vector and its metadata payload;
- `search_similar()`: performs semantic similarity search in Qdrant.

The upsert logic uses deterministic identifiers based on the vulnerability ID, which avoids duplicate records when the same vulnerability is re-ingested.

### 4.6 Qdrant Vector Database

Qdrant is used as the vector database for semantic retrieval.

It stores:

- vulnerability embeddings;
- metadata payloads such as title, description, severity, CVSS score, source and language.

Qdrant is not intended to replace the main vulnerability intelligence database. It is used as a semantic index that enables similarity search and correlation on top of structured vulnerability data.

### 4.7 Adapter and Normalization Layer

The adapter layer maps source-specific vulnerability formats into the internal `VulnerabilityRecord` schema.

The design includes:

- `VulnerabilityLookupAdapter` for records coming from Vulnerability-Lookup;
- `SourceSpecificAdapters` for other feeds such as Cybersecurity Data Space datasets, CIRCL, NVD or vendor advisories.

This layer keeps the AI enrichment module decoupled from external JSON formats. If a source changes its schema, only the corresponding adapter needs to be updated.

## 5. Data Ingestion Pipeline

The ingestion pipeline is responsible for transforming vulnerability intelligence records into searchable semantic vectors.

The pipeline follows these steps:

1. **Source collection**  
   Vulnerability records are retrieved from external sources such as Vulnerability-Lookup, Cybersecurity Data Space datasets, CIRCL feeds, NVD or vendor advisories.

2. **Normalization**  
   Source-specific adapters convert heterogeneous input formats into the internal `VulnerabilityRecord` schema.

3. **Validation**  
   The FastAPI application validates incoming records using the Pydantic `VulnerabilityRecord` model.

4. **Text preparation**  
   The validated record is converted into embedding-ready text through `VulnerabilityRecord.to_embedding_text()`.

5. **Embedding generation**  
   `EmbeddingService` generates a semantic vector from the prepared vulnerability text.

6. **Vector storage**  
   `VectorStore.upsert_vulnerability()` stores the embedding and metadata payload in Qdrant.

7. **Idempotent re-ingestion**  
   Re-ingesting the same vulnerability updates the existing vector and payload instead of creating duplicates. This is achieved by using deterministic point identifiers derived from the vulnerability identifier.

### Ingestion Flow

```text
External vulnerability source
    → Adapter / Normalization layer
    → VulnerabilityRecord
    → FastAPI / POST /vulnerabilities/enrich
    → EnrichmentService
    → EmbeddingService
    → VectorStore.upsert_vulnerability()
    → Qdrant
```
### Current V1 Scope

The implemented V1 focuses on the core enrichment path:

```text
VulnerabilityRecord JSON
    → FastAPI
    → EnrichmentService
    → EmbeddingService
    → Qdrant
```
The API currently accepts already normalized vulnerability records. This allows the enrichment module to remain independent from external feed formats while still being ready to integrate with Vulnerability-Lookup through a dedicated adapter.

### Production Evolution

In a production deployment, ingestion can be automated with:

- scheduled synchronization from Vulnerability-Lookup;
- event-driven ingestion when new vulnerability records are added;
- batch ingestion for historical datasets;
- retry and dead-letter mechanisms for failed records;
- schema versioning for adapter compatibility;
- ingestion metrics such as number of records processed, failed records and embedding latency.

## 6. Storage and Retrieval Strategy

The storage and retrieval strategy separates semantic search from the main vulnerability intelligence storage.

The AI enrichment module uses Qdrant as a vector database. Qdrant stores vulnerability embeddings and their associated metadata payloads, but it is not intended to replace Vulnerability-Lookup or any primary vulnerability database.

### 6.1 Vector Storage

Each enriched vulnerability is stored in Qdrant as a vector point.

A vector point contains:

- a deterministic point ID derived from the vulnerability identifier;
- the semantic embedding generated from the vulnerability text;
- a metadata payload containing the normalized vulnerability fields.

Payload example:

```json
{
  "vulnerability_id": "CVE-2024-0001",
  "title": "Remote code execution in web application",
  "description": "An attacker can remotely execute arbitrary code through a vulnerable endpoint.",
  "severity": "critical",
  "cvss_score": 9.8,
  "source": "Vulnerability-Lookup",
  "language": "en"
}
````

The deterministic point ID makes the ingestion process idempotent. If the same vulnerability is ingested again, the existing vector and payload are updated instead of creating a duplicate record.

### 6.2 Semantic Retrieval

Similarity search is performed by embedding the user query and comparing it against the stored vulnerability embeddings.

The retrieval flow is:

```text
User query
    → FastAPI / POST /vulnerabilities/search
    → EnrichmentService
    → EmbeddingService
    → query embedding
    → VectorStore.search_similar()
    → Qdrant similarity search
    → SimilaritySearchResponse
```

The query itself is not stored in Qdrant. It is only transformed into an embedding at runtime in order to retrieve semantically similar vulnerabilities.

### 6.3 Metadata Retrieval

Qdrant returns both similarity scores and payload metadata. This allows the API to return useful results directly, such as:

* vulnerability identifier;
* title;
* description;
* severity;
* CVSS score;
* source;
* similarity score.

This enables analysts or downstream services to quickly inspect why a vulnerability was returned as semantically related.

### 6.4 Separation of Responsibilities

The design deliberately separates storage responsibilities:

* Vulnerability-Lookup or another primary database remains responsible for structured vulnerability intelligence.
* Qdrant is responsible for semantic indexing and similarity retrieval.
* FastAPI exposes the enrichment and search capabilities.
* VectorStore hides Qdrant-specific operations from the rest of the application.

This avoids coupling the AI module too tightly to a single storage technology and makes future migration easier.

## 7. Inference Strategy

The inference strategy separates two different AI capabilities:

1. **embedding inference**, implemented in the V1;
2. **generative inference**, proposed for advisory drafting in the target architecture.

This separation keeps the current module lightweight and maintainable while leaving a clear path for future AI-assisted drafting capabilities.

### 7.1 Embedding Inference

The implemented V1 uses embedding inference to transform vulnerability records and search queries into semantic vectors.

Embedding inference is used in two situations:

- during ingestion, to generate a vector representation of a vulnerability record;
- during similarity search, to generate a vector representation of the user query.

The embedding model is encapsulated inside `EmbeddingService`. This means the rest of the application does not depend directly on a specific model implementation.

Current flow for vulnerability enrichment:

```text
VulnerabilityRecord
    → VulnerabilityRecord.to_embedding_text()
    → EmbeddingService
    → semantic embedding
    → VectorStore
    → Qdrant
````

Current flow for similarity search:

```text
Search query
    → EmbeddingService
    → query embedding
    → VectorStore.search_similar()
    → Qdrant
    → SimilaritySearchResponse
```

### 7.2 Model-Agnostic Design

The enrichment module is designed to be model-agnostic.

The embedding dimension is retrieved dynamically from the selected embedding model and passed to the vector store when the Qdrant collection is initialized. This avoids hardcoding the vector size in the storage layer.

This design makes it possible to replace the embedding model later, for example when:

* better multilingual retrieval performance is needed;
* a domain-specific cybersecurity embedding model becomes available;
* latency or infrastructure constraints require a smaller model;
* evaluation shows that retrieval quality has degraded.

If the embedding model changes, existing vectors may need to be regenerated because embeddings from different models are not directly comparable.

A safe migration strategy would be:

1. create a new Qdrant collection with a versioned name, for example `vulnerabilities_v2`;
2. re-embed all vulnerability records with the new model;
3. index the new vectors in the new collection;
4. evaluate retrieval quality before switching traffic;
5. update the API configuration to point to the new collection;
6. keep the old collection temporarily for rollback.

This approach avoids corrupting the existing semantic index during model migration.

### 7.3 Generative Inference for Advisory Drafting

In the target architecture, generative inference can be added as a downstream capability. A generative model such as Qwen can use retrieved vulnerability context to assist analysts in drafting multilingual security advisories.

A possible retrieval-augmented drafting flow is:

```text
Vulnerability record or analyst prompt
    → Similarity search in Qdrant
    → Related vulnerabilities and context
    → Generative model
    → Draft advisory
    → Human analyst review
```

The generative model should not be allowed to produce final advisories without human validation. Its role should be to assist analysts by preparing draft text, summaries, translations or suggested remediation sections.

### 7.4 Human-in-the-Loop Validation

For cybersecurity use cases, AI-generated outputs must remain under analyst supervision.

Human validation is especially important for:

* CVSS interpretation;
* severity wording;
* remediation guidance;
* affected product interpretation;
* national or sector-specific prioritization;
* public advisory publication.

The system should therefore be designed as an AI-assisted workflow rather than a fully autonomous advisory generation system.

### 7.5 Cost and Latency Considerations

Embedding inference is relatively lightweight compared to generative inference. It can be executed during ingestion and cached through the vector database.

Generative inference is more expensive and should be used only when needed, for example when an analyst requests an advisory draft or summary.

To control cost and latency, the system can use:

* batch embedding during ingestion;
* cached embeddings for already-ingested vulnerabilities;
* smaller embedding models for high-volume indexing;
* larger generative models only for drafting tasks;
* asynchronous processing for long-running enrichment jobs;
* rate limits and quotas on generative endpoints.

## 8. Integration with Vulnerability-Lookup

The AI enrichment service is designed to integrate with Vulnerability-Lookup as a semantic enrichment and correlation layer.

### 8.1 Integration Role

The integration relies on a normalization boundary between Vulnerability-Lookup and the AI enrichment module.

The expected flow is:

```text
Vulnerability-Lookup
    → VulnerabilityLookupAdapter
    → Normalized VulnerabilityRecord
    → AI Enrichment API
    → EmbeddingService
    → VectorStore
    → Qdrant
```

The `VulnerabilityLookupAdapter` is responsible for mapping records retrieved from Vulnerability-Lookup into the internal `VulnerabilityRecord` schema expected by the enrichment API.

This approach avoids coupling the AI pipeline directly to the raw Vulnerability-Lookup JSON structure.

### 8.2 Why Use an Adapter

The adapter pattern makes the integration more maintainable.

If the Vulnerability-Lookup API response format changes, only the adapter needs to be updated. The rest of the pipeline can remain stable:

This also makes it easier to add other sources later, such as Cybersecurity Data Space datasets, CIRCL feeds, NVD or vendor advisories.

### 8.3 Possible Integration Modes

The integration can support several modes.

#### Pull-based synchronization

The AI enrichment service periodically retrieves new or updated vulnerability records from Vulnerability-Lookup.

Example:

```text
scheduled job
    → call Vulnerability-Lookup API
    → normalize records
    → POST /vulnerabilities/enrich
    → update Qdrant index
```

This is useful for batch updates and historical indexing.

#### Event-driven synchronization

When Vulnerability-Lookup receives or updates a vulnerability, an event or webhook can trigger enrichment.

Example:

```text
new vulnerability in Vulnerability-Lookup
    → event / webhook
    → VulnerabilityLookupAdapter
    → AI enrichment pipeline
```

This is useful when low-latency updates are required.

#### API-based enrichment

External services or analysts can directly send normalized vulnerability records to the AI enrichment API.

Example:

```text
client
    → POST /vulnerabilities/enrich
    → semantic enrichment
    → Qdrant update
```

This is the mode implemented in the V1.

### 8.4 Returned Results

The semantic search API returns vulnerability metadata and similarity scores.

Example result fields:

* vulnerability identifier;
* title;
* description;
* severity;
* CVSS score;
* source;
* similarity score.

These results can then be displayed in the Cybersecurity Observatory or used by analyst workflows.

## 9. Security Concerns

## 10. Scaling Assumptions

## 11. Observability

## 12. Evaluation Metrics

## 13. Maintainability and Two-Year Relevance
