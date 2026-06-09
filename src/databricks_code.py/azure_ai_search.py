from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchField, SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile
)
import json
from pathlib import Path
from src.data_ingestion.pdf_ingestion import extract_pdf_pages
from src.data_ingestion.chunking import create_chunks
from src.data_ingestion.embeddings import LocalEmbeddingModel

AZURE_SEARCH_ENDPOINT = "https://accenture2026search.search.windows.net"
AZURE_SEARCH_KEY = "Gl8CoPovFit1MbFKrezT79VlTrImn7uCNN8eiQ0hTVAzSeDmQMnV"
INDEX_NAME = "index10"

credential = AzureKeyCredential(AZURE_SEARCH_KEY)
search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)
index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=credential)

def create_azure_search_index_if_not_exists(vector_dimensions: int = 1536):
    try:
        index_client.get_index(INDEX_NAME)
        print(f"Azure Search Index '{INDEX_NAME}' already exists.")
    except Exception:
        print(f"Index not found. Creating brand new index: '{INDEX_NAME}'...")
        fields = [
            SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="celex_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="text_content", type=SearchFieldDataType.String, searchable=True),
            SearchField(
                name="embeddings", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True, vector_search_dimensions=vector_dimensions, vector_search_profile_name="rag-vector-profile"
            )
        ]
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="rag-hnsw-config")],
            profiles=[VectorSearchProfile(name="rag-vector-profile", algorithm_configuration_name="rag-hnsw-config")]
        )
        index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
        index_client.create_index(index)
        print("Azure AI Search index established successfully!")

def ingest_all_pdfs_to_azure(embedder: LocalEmbeddingModel):
    pdf_files = list(settings.DOCUMENTS_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs in target directory: {settings.DOCUMENTS_DIR}")
    
    silver_records, gold_records, azure_push_batch = [], [], []
    total_chunks = 0

    for pdf_path in pdf_files:
        print(f"Processing File: {pdf_path.name}")
        celex_id_val = pdf_path.stem.split('_')[0]

        pages = extract_pdf_pages(str(pdf_path))
        chunks = create_chunks(pages)
        embedded_chunks = embedder.embed_chunks(chunks)

        for idx, embedded_chunk in enumerate(embedded_chunks):
            vector = embedded_chunk.embedding if hasattr(embedded_chunk, 'embedding') else embedded_chunk.get('embedding')
            chunk_text = embedded_chunk.text if hasattr(embedded_chunk, 'text') else str(embedded_chunk)
            
            sanitized_chunk_id = f"{pdf_path.stem}_{idx}".replace("-", "_").replace(".", "_")
            vector_floats = [float(v) for v in vector]

            document_record = {
                "chunk_id": sanitized_chunk_id,
                "celex_id": celex_id_val,
                "text_content": chunk_text,
                "embeddings": vector_floats
            }
            azure_push_batch.append(document_record)
            gold_records.append(document_record)
            silver_records.append({"chunk_id": sanitized_chunk_id, "celex_id": celex_id_val, "text_content": chunk_text})

        total_chunks += len(chunks)

    if azure_push_batch:
        create_azure_search_index_if_not_exists(vector_dimensions=len(azure_push_batch[0]["embeddings"]))
        print(f"📡 Transmitting {len(azure_push_batch)} records to Azure Vector Space...")
        search_client.upload_documents(documents=azure_push_batch)
        print("Azure Cloud upload finished!")

    # Export staging JSON logs to your project's local data folder layout
    target_data_dir = os.path.join(project_root, "data")
    os.makedirs(target_data_dir, exist_ok=True)
    with open(os.path.join(target_data_dir, "silver_staging.json"), "w", encoding="utf-8") as f:
        json.dump(silver_records, f, ensure_ascii=False, indent=4)
    with open(os.path.join(target_data_dir, "gold_staging.json"), "w", encoding="utf-8") as f:
        json.dump(gold_records, f, ensure_ascii=False, indent=4)
    print(f"Local logs saved to: {target_data_dir}")

# Execute Ingestion Run
local_embedder = LocalEmbeddingModel()
ingest_all_pdfs_to_azure(local_embedder)