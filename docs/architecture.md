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

The AI enrichment service processes vulnerability intelligence data and may later support advisory drafting workflows. Security controls are therefore required at several levels: API access, data validation, model usage, storage and operational monitoring.

### 9.1 API Security

Authentication and authorization should be enforced at the API boundary, before requests reach the enrichment pipeline.

The enrichment and search endpoints do not have the same security impact:

- `POST /vulnerabilities/enrich` modifies the semantic index. It should therefore be restricted to trusted services such as the Vulnerability-Lookup adapter, internal ingestion jobs or authorized analysts. Without access control, an attacker or unauthorized user could pollute the vector index with false vulnerability records, degrade retrieval quality, create duplicates, trigger excessive embedding workloads or store unwanted content.

- `POST /vulnerabilities/search` does not modify the index, but it can still reveal sensitive operational context. Even when vulnerability data is public, the queries made by analysts and the correlations returned by the system may reveal which technologies, sectors, products or threats are being monitored in the Luxembourg context.

Recommended controls:

- restrict access to trusted internal services and analysts;
- add authentication, for example API keys, OAuth2 or reverse-proxy authentication;
- apply role-based access control to separate ingestion, search and administration permissions;
- rate-limit endpoints to prevent abuse or denial-of-service scenarios;
- validate request payload size to prevent excessive memory usage.

The V1 exposes local development endpoints only. A production deployment should place the API behind an authenticated gateway or internal network boundary.

### 9.2 Input Validation

Incoming vulnerability records must be validated before enrichment.

The V1 uses Pydantic models to validate the normalized `VulnerabilityRecord` schema. This helps ensure that required fields are present and that fields such as `cvss_score` remain within expected bounds.

Additional production validation should include:

- maximum field lengths;
- accepted language codes;
- accepted source names;
- protection against malformed JSON;
- rejection of empty or low-quality descriptions;
- schema versioning for adapter compatibility.

### 9.3 Data Integrity

The service should preserve traceability between the enriched vector record and the original vulnerability source.

Recommended controls:

- keep the original `vulnerability_id`;
- keep the source name stored in the Qdrant payload;
- maintain ingestion timestamps;
- track adapter version and schema version;
- use deterministic point IDs to avoid duplicate records during re-ingestion.

This allows analysts to trace semantic search results back to their original structured vulnerability records.

### 9.4 Model and Prompt Security

If generative advisory drafting is added, prompt injection and hallucination risks must be controlled.

Potential risks include:

- malicious content in vulnerability descriptions;
- source data attempting to influence the model instructions;
- hallucinated remediation guidance;
- unsupported claims in generated advisories.

Mitigations:

- use retrieval-augmented generation with explicit source references;
- separate system instructions from retrieved vulnerability content;
- sanitize and delimit retrieved context;
- require human review before publication;
- log model inputs and outputs for auditability.

### 9.5 Sensitive Information

The system should avoid indexing sensitive information that is not required for correlation.

If internal asset data is later used for Luxembourg-specific prioritization, additional controls are required:

- access control on asset-related metadata;
- separation between public vulnerability data and internal exposure data;
- encryption at rest for sensitive metadata;
- audit logs for analyst access;
- data minimization in vector payloads.

### 9.6 Logging and Operational Data Exposure

Although many vulnerability records are public, the operational context around them may be sensitive.


For example, logs may reveal:

- analyst queries;
- local prioritization signals;
- sectors, technologies or products being monitored;
- internal asset or exposure context if added later;
- connector credentials or API tokens;
- future LLM prompts and generated drafts.

For this reason, logs should support debugging without storing unnecessary operational context. They should favor technical identifiers, timestamps, source names, status codes and error details over full request payloads or complete generated outputs.

Recommended controls:

- avoid logging full request and response bodies by default;
- redact credentials, tokens and secrets;
- avoid logging full analyst prompts unless explicitly required for audit;
- use request identifiers to correlate events without duplicating payloads;
- define log retention policies;
- restrict access to logs.

### 9.7 Vector Database Security

Qdrant should not be exposed directly to external clients. It should remain private and only be accessed by the `VectorStore` component.

In production, Qdrant could run on an internal server, in a cloud environment, in Kubernetes, in Docker Compose on a virtual machine, or inside a shared network. In these deployment contexts, the Qdrant API port should not be directly exposed to external clients.

The intended access path is:

```text
Client
    → FastAPI API
    → EnrichmentService
    → VectorStore
    → Qdrant
```
Direct access should be avoided:
```text
External client
    → Qdrant
```
Exposing Qdrant directly would allow clients to bypass the API validation, authorization and business logic layers. Depending on permissions, this could lead to unauthorized reads, vector index pollution, deletion or modification of stored points, excessive query load or leakage of payload metadata.

Recommended controls:

- do not expose Qdrant directly to the public internet;
- restrict Qdrant access to the enrichment service;
- enable authentication where available;
- isolate the vector database in a private network;
- back up collections regularly;
- monitor collection size, query volume and failure rates.

### 9.8 Supply Chain Security

The system depends on open-source components such as FastAPI, sentence-transformers, Qdrant client and embedding models.

Recommended controls:

- pin dependency versions;
- scan dependencies for vulnerabilities;
- document model sources and licenses;
- verify model provenance;
- avoid untrusted model weights;
- review Docker images before deployment.

## 10. Scaling Assumptions

The proposed architecture is designed to start as a lightweight enrichment service and evolve toward a scalable production component.

### 10.1 Expected Workload

The system has two main workload types:

- ingestion workload: vulnerability records are normalized, embedded and stored in Qdrant;
- search workload: analyst queries or downstream services request semantically similar vulnerabilities.

These workloads have different scaling characteristics.

Ingestion can usually be processed asynchronously or in batches. Search is more latency-sensitive because it is part of an analyst-facing workflow.

### 10.2 API Scaling

The FastAPI layer can be scaled horizontally by running multiple API workers behind a load balancer.

This is possible because the API layer should remain stateless. The persistent state is stored outside the API process:

- semantic vectors and payloads are stored in Qdrant;
- original vulnerability intelligence remains in Vulnerability-Lookup or another primary source;
- configuration should be provided through environment variables or deployment configuration.

### 10.3 Embedding Scaling

Embedding generation is one of the main compute bottlenecks.

For small to medium workloads, CPU inference with a lightweight sentence-transformers model may be sufficient. For larger volumes, the system can evolve toward:

- batch embedding during ingestion;
- asynchronous enrichment jobs;
- dedicated embedding workers;
- GPU-backed inference for larger models;
- model caching at service startup;
- queue-based processing for high-volume feeds.

Embedding results should be reused when the vulnerability content has not changed.

For large-scale batch workloads, the enrichment pipeline could also be executed through HPC or job-scheduler based infrastructure. This would be relevant for historical backfills, large embedding regeneration campaigns after a model migration, large-scale evaluation runs, or enrichment of high-volume vulnerability datasets. In that case, FastAPI would remain the interactive API layer, while scheduled batch jobs would run the embedding pipeline offline and write enriched vectors into Qdrant.

### 10.4 Qdrant Scaling

Qdrant is used as the vector index for semantic retrieval.

Scaling considerations include:

- collection size;
- vector dimension and embedding model version;
- indexing configuration;
- query latency and concurrent search requests;
- backup and recovery requirements.

For a production deployment, Qdrant should be monitored and sized according to the expected number of vulnerability records and query volume.

For large-scale deployments, separate Qdrant collections can be used when there is a clear operational boundary, such as severity, data sensitivity, or environment. For example, critical and high-severity vulnerabilities could be stored in a dedicated collection to support faster analyst workflows focused on urgent threats, while medium and low-severity vulnerabilities could remain in a broader collection for general investigation.

A collection selection layer could route ingestion and search requests to the appropriate collection. However, collections should not be split prematurely based only on semantic proximity, as this can reduce recall and add routing complexity. 

Using smaller, well-scoped collections can improve semantic search latency by reducing the number of vectors searched and simplifying index management. This is useful when collections are separated by stable and relevant operational boundaries. However, collections should not be split prematurely based only on semantic proximity, as this may reduce recall and add routing complexity.

If multiple embedding models or model versions are used, separate collections should be created to avoid mixing incompatible vector spaces.


### 10.5 Ingestion Scaling

The ingestion pipeline should support both incremental updates and historical backfills.

Recommended ingestion modes:

- incremental ingestion for new or updated vulnerabilities;
- scheduled synchronization from Vulnerability-Lookup;
- batch ingestion for historical datasets;
- dead-letter handling for invalid or malformed records;
- idempotent upserts to avoid duplicate vectors.

The current deterministic upsert strategy supports re-ingestion without creating duplicate Qdrant points.

### 10.6 Search Scaling

Similarity search should remain responsive for analyst workflows.

Recommended search controls:

- use a lightweight embedding model that provides an acceptable trade-off between semantic retrieval quality and query latency.
- limit the number of returned results;
- apply rate limits on public or shared endpoints;
- use appropriate Qdrant indexing parameters;
- avoid storing user queries;
- monitor latency percentiles, not only average latency.

Use smaller, well-scoped Qdrant collections is relevant to reduce the searched vector space and improve query latency.

### 10.7 Deployment Assumptions

For a first production iteration, the system can remain relatively simple:

* one FastAPI service;
* one Qdrant instance;
* scheduled ingestion;
* lightweight multilingual embedding model;
* internal network deployment.

The architecture can then evolve progressively as ingestion volume, query volume and model complexity increase.

## 11. Observability

Observability is required to ensure that the enrichment service remains reliable, explainable and useful over time. The goal is not only to monitor whether the API is running, but also whether the AI-assisted retrieval pipeline continues to return relevant results.

### 11.1 Application Metrics

The service should expose standard application metrics, such as:

- request count by endpoint;
- request latency by endpoint;
- error rate;
- number of enriched vulnerabilities;
- number of similarity search requests;
- embedding generation latency;
- Qdrant query latency.

These metrics help detect performance regressions, service overload or abnormal usage patterns.

### 11.2 Ingestion Monitoring

The ingestion pipeline should track whether records are processed correctly.

Useful metrics include:

- number of records ingested;
- number of records rejected during validation;
- number of failed enrichment operations;
- number of updated records versus newly inserted records;
- ingestion latency;
- source distribution of ingested records.

This helps identify broken adapters, malformed source data or unexpected feed changes.

### 11.3 Retrieval Quality Monitoring

Because the system relies on semantic search, functional correctness cannot be measured only through uptime.

The following signals should be monitored:

- average similarity scores;
- distribution of similarity scores over time;
- number of empty or low-confidence result sets;
- analyst feedback on returned results;
- changes in top-k retrieval quality after adding a new source or changing the embedding model.

A sudden drop in similarity scores or analyst feedback quality may indicate a feed quality issue, a model mismatch or a problem in the normalization layer.

### 11.4 Logging

Logs should support debugging without exposing unnecessary sensitive information.

logs:

- request identifier;
- endpoint called;
- model name and collection name used for enrichment.
- source of ingested records;
- vulnerability identifier;
- validation failures;
- enrichment failures;
- Qdrant operation failures;

Logs should avoid storing full sensitive payloads unless there is a clear operational need.

### 11.5 Tracing

For production deployment, distributed tracing can help understand where latency or failures occur.

A trace should make it possible to follow a request across the full enrichment pipeline and identify whether latency or failures come from API handling, embedding inference, vector storage or Qdrant search operations.

This is useful when diagnosing whether a slowdown comes from API handling, embedding inference, vector search or database operations.

### 11.6 Alerting

Alerts should focus on operational reliability and AI quality signals.

Examples:

* API error rate above threshold;
* Qdrant unavailable;
* embedding model loading failure;
* search latency above threshold;
* ingestion failure spike;
* unexpected drop in average similarity scores.

This ensures that both infrastructure issues and AI retrieval quality issues are detected early.

## 12. Evaluation Metrics

Evaluation should verify that the AI enrichment module is useful for analysts, not only that it runs correctly. The V1 should mainly be evaluated on semantic retrieval quality, data quality and operational performance.

### 12.1 Retrieval Quality

The core AI capability of the V1 is similarity search. It should be evaluated with a small benchmark made of vulnerability queries and expected related records.

Relevant metrics include:

- **Precision@k**: how many of the top-k returned vulnerabilities are relevant;
- **Recall@k**: measures whether the system is able to retrieve known related vulnerabilities within the top-k results.
- **Mean Reciprocal Rank (MRR)**: whether the first relevant result appears high in the ranking;
- **low-confidence result rate**: how often the system returns weak or irrelevant matches.

These metrics help determine whether the embedding model and normalization strategy produce meaningful semantic correlations.

### 12.2 Analyst Feedback

Quantitative retrieval metrics should be complemented with analyst feedback.

Analysts should be able to indicate whether returned vulnerabilities are useful, too broad, too narrow or missing important related records. This feedback can later be used to improve normalization rules, model selection, search thresholds and ranking logic.

### 12.3 Data Quality

Poor input data directly degrades embedding quality. The system should therefore monitor whether ingested records contain enough usable information for semantic search.

Important indicators include:

- missing or very short descriptions;
- malformed records;
- inconsistent severity values;
- duplicate vulnerability identifiers;
- language distribution;
- source distribution;
- validation rejection rate.

These signals help detect feed or adapter issues before they degrade retrieval quality.

### 12.4 Operational Performance

The service should also be evaluated as a production component.

The most relevant operational metrics are:

- API latency;
- embedding generation latency;
- Qdrant query latency;
- ingestion throughput;
- search throughput;
- API error rate;
- Qdrant availability.

These metrics help determine whether the architecture can support larger ingestion volumes and analyst-facing search workflows.

### 12.5 Generative Drafting Evaluation

If advisory drafting is added later, the evaluation must focus on factual correctness rather than writing fluency.

Generated drafts should be reviewed for consistency with source vulnerability data, correct severity wording, absence of unsupported claims, clarity of remediation guidance, multilingual quality and analyst editing effort.

The generative model should remain human-in-the-loop, especially for public advisories or Luxembourg-specific prioritization.

### 12.6 Regression Checks

Evaluation should be repeated before major changes, especially when changing the embedding model, adding a new feed, modifying normalization logic or updating drafting prompts.

This prevents silent regressions in retrieval quality or advisory drafting behavior.

## 13. Maintainability and Two-Year Relevance

The proposed architecture is designed to remain maintainable and relevant over the next two years by avoiding tight coupling between external feeds, AI models, storage technology and API logic.

### 13.1 Modular Design

The system separates responsibilities into dedicated components:

- the API layer handles HTTP requests and responses;
- the adapter layer handles source-specific normalization;
- the enrichment service orchestrates the pipeline;
- the embedding service handles model inference;
- the vector store abstracts Qdrant operations.

This makes the system easier to test, debug and evolve. A change in one layer should not require rewriting the entire service.

### 13.2 Source-Agnostic Ingestion

The enrichment module relies on the normalized `VulnerabilityRecord` schema rather than raw external formats.

This is important because external vulnerability sources may evolve over time. If the Vulnerability-Lookup API, Cybersecurity Data Space datasets or another feed changes format, only the corresponding adapter should need to be updated.

### 13.3 Model-Agnostic AI Layer

The embedding model is encapsulated inside `EmbeddingService`.

This allows the system to switch from one sentence-transformers model to another without changing the API or business logic. This is important because embedding models are likely to improve significantly over the next two years, especially for multilingual and cybersecurity-specific retrieval.

If the embedding model changes, vectors should be regenerated into a new versioned Qdrant collection to avoid mixing incompatible vector spaces.

### 13.4 Separation Between Retrieval and Generation

The V1 focuses on semantic enrichment and similarity search. Generative advisory drafting is treated as a downstream capability.

This separation is important because retrieval and generation have different risks, costs and evaluation methods. The retrieval layer can remain stable while generative models evolve.

### 13.5 Human-in-the-Loop by Design

The system is designed to assist analysts, not replace them.

For cybersecurity use cases, human review remains necessary for severity interpretation, remediation guidance, public advisory publication and Luxembourg-specific prioritization.

This makes the system more realistic and safer to operate in a professional environment.

### 13.6 Future-Proofing

The architecture can evolve progressively with:

- a dedicated Vulnerability-Lookup API client for automated synchronization;
- additional source adapters for new vulnerability feeds;
- production security controls such as authentication, authorization, rate limiting and network isolation;
- observability metrics for API latency, embedding latency, Qdrant query latency, ingestion failures and retrieval confidence;
- evaluation pipelines for retrieval quality, analyst feedback and regression testing before model or feed changes;
- generative advisory drafting with human review;
- analyst feedback loops to continuously improve retrieval relevance;
- asynchronous ingestion workers for large feeds and historical backfills;
- larger-scale deployment using job schedulers, containers, Kubernetes or HPC infrastructure;
- versioned Qdrant collections for embedding model migrations;
- CI/CD pipelines with automated tests, dependency scanning and deployment checks.

The key design principle is to keep each part replaceable. This allows the system to adapt to new feeds, new models, new deployment constraints, new security requirements and new observatory needs without requiring a full rewrite.