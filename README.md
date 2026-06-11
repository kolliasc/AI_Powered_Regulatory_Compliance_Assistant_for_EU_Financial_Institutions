# AI-Powered Regulatory Compliance Assistant for EU Financial Institutions

## Project Goal

The objective of this project is to demonstrate how modern AI Knowledge Engineering practices can be applied to regulatory compliance challenges, enabling organizations to transform large volumes of complex regulatory information into accessible, searchable, and actionable knowledge.

## Overview

The AI-Powered Regulatory Compliance Assistant is an enterprise knowledge platform designed to help financial institutions navigate and understand complex European regulatory frameworks through natural language interactions.

The solution combines modern data engineering, document processing, Retrieval-Augmented Generation (RAG), semantic search, and Generative AI to transform large collections of regulatory documents into an intelligent and searchable knowledge ecosystem.

Rather than relying on traditional keyword-based document repositories, the platform enables users to ask compliance-related questions in natural language and receive grounded, traceable answers supported by source references.

---

## Business Challenge

Financial institutions operating within the European Union must comply with an increasingly complex regulatory environment that includes frameworks such as:

* MiFID II
* PSD2
* DORA
* GDPR
* AML Directives
* EBA and ECB Guidelines

Compliance teams often spend significant time searching through regulations, technical standards, supervisory guidelines, and internal documentation to identify obligations and validate controls.

Traditional document management systems struggle to provide contextual understanding and cross-document intelligence, creating operational inefficiencies and increasing regulatory risk.

This project addresses that challenge by building an AI-powered knowledge platform capable of understanding, retrieving, and explaining regulatory information at scale.

---

## Solution

The platform ingests regulatory content from trusted European regulatory sources, processes documents into AI-ready formats, enriches them with metadata, generates semantic embeddings, and indexes them for intelligent retrieval.

Users interact with the system through a REST API and can ask questions in natural language.

The platform retrieves relevant regulatory content, constructs contextual evidence, and generates responses grounded in the original source material.



## End-to-End Workflow

### 1. Regulatory Acquisition

Documents are collected from trusted regulatory repositories.

### 2. Processing & Enrichment

Content is extracted, structured, enriched with metadata, and prepared for AI consumption.

### 3. Embedding Generation

Semantic vector representations are created for each document segment.

### 4. Indexing

Embeddings and metadata are indexed to support efficient retrieval.

### 5. Query Processing

Users submit natural language questions through the API.

### 6. Context Retrieval

Relevant regulatory content is identified using semantic and hybrid search techniques.

### 7. Response Generation

The AI model generates grounded answers using retrieved evidence.

### 8. Traceability

Responses include references to source material, enabling users to verify findings and maintain compliance confidence.

---
## Key Features

* Intelligent regulatory document ingestion
* AI-ready document processing
* Semantic and hybrid search
* Retrieval-Augmented Generation (RAG)
* Source-backed responses
* Metadata enrichment and lineage tracking
* Scalable API architecture
* Enterprise-ready deployment model

---
<div align="center">
  
### Regulatory Compliance Assistant Home Screen

The initial interface where users can submit regulatory compliance questions and explore the platform's capabilities

<img width="69%" height="466" alt="Screenshot (512)" src="https://github.com/user-attachments/assets/2786d0c2-2855-4837-a76e-c287fc30fe4d" />
  <br><br>

### RAG-Powered Question Answering

The platform retrieves relevant regulatory documents and generates source-backed responses using Retrieval-Augmented Generation (RAG).

<img width="69%" height="793" alt="Screenshot (529)" src="https://github.com/user-attachments/assets/240a2b8f-e394-4400-87fd-5922db9faa05" />

<h3>RAG Evaluation Results</h3>

<p>
The platform was evaluated using retrieval and generation quality metrics including MMR-based retrieval relevance, Answer Relevance, and Faithfulness. These metrics assess the system's ability to retrieve contextually appropriate regulatory content and generate responses that remain grounded in source documentation.
<p>

<img width="69%" height="793" alt="Screenshot (533)" src="https://github.com/user-attachments/assets/38347452-b52f-4e2f-81d7-a3ed5bb4269e" />

</div>

## Technology Stack

### Data Engineering

* Python
* PySpark
* Databricks
* Delta Lake

### AI & Machine Learning

* Azure OpenAI
* Embedding Models
* Retrieval-Augmented Generation (RAG)

### Search & Retrieval

* Vector Search
* Hybrid Search
* Semantic Retrieval

### API & Services

* FastAPI
* REST APIs
* OpenAPI / Swagger

### DevOps

* Docker
* GitHub Actions
* CI/CD Pipelines


---

# Running the Application

## Prerequisites

Before running the project, ensure the following are installed:

* Python 3.11+
* uv
* Git
* Azure OpenAI deployment
* Azure OpenAI API credentials

---

## Clone the Repository

```bash
git clone https://github.com/<username>/AI-Powered-Regulatory-Compliance-Assistant.git

cd AI-Powered-Regulatory-Compliance-Assistant
```

---

## Create and Synchronize the Environment

```bash
uv sync
```

This command installs all project dependencies defined in the project configuration.

---

## Configure Environment Variables

Create a `.env` file in the project root and configure the required settings:

```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

CHROMA_DB_PATH=./chroma_db
```

---

## Ingest Regulatory Documents

Populate the vector database by processing regulatory documents:

```bash
uv run python src/data_ingestion/run_ingestion.py
```

This step:

* Extracts document content
* Applies chunking strategies
* Generates embeddings
* Stores vectors in ChromaDB

---

## Start the API

```bash
uv run uvicorn src.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

---

## API Interface

Open index.html

The web interface will connect to the FastAPI backend and provide an interactive RAG-powered compliance assistant experience.


## Example Query

  "question": "How an investment firm operates?"

## Expected Workflow

```text
Regulatory Documents
        │
        ▼
Document Processing
        │
        ▼
Chunk Generation
        │
        ▼
Embedding Creation
        │
        ▼
Vector Indexing
        │
        ▼
Question Submission
        │
        ▼
Semantic Retrieval
        │
        ▼
RAG Response Generation
```



