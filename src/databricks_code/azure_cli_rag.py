# ----------------------------------- azure enviroment
import sys
import os

project_root = "/Workspace/Users/christoforosmav20@gmail.com/bundle/ai-regulatory-assistant/files"

if os.path.exists(project_root):
    if project_root not in sys.path:
        sys.path.append(project_root)
    print(f" Path successfully matched! Linked to: {project_root}")
else:
    print(f" Path check failed. Could not find: {project_root}")

# Azure OpenAI environment variables so Pydantic can validate them
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://accenture2026ab.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "4dn2Hd4qnFDuPpLTQX17BSXQc8EZ92j2IQUSmmFEv4fejDIW9VypJQQJ99CFAC5T7U2XJ3w3AAABACOGwAeF"
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-12-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4.1"

from src.config.settings import settings
print("Settings loaded perfectly!")

#--------------------------------------------- azure ai search

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

#--------------------------------------------- azure rag 
import os
import ipywidgets as widgets
from IPython.display import display, clear_output
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from src.RAG_layer.retriever import AzureOpenAIChatLLM
from src.data_ingestion.embeddings import LocalEmbeddingModel



#  NATIVE ENDPOINT RE-INITIALIZATION FOR STANDALONE EXECUTION
AZURE_SEARCH_ENDPOINT = "https://accenture2026search.search.windows.net"
AZURE_SEARCH_KEY = "Gl8CoPovFit1MbFKrezT79VlTrImn7uCNN8eiQ0hTVAzSeDmQMnV"
INDEX_NAME = "index10" 

credential = AzureKeyCredential(AZURE_SEARCH_KEY)
search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

# Create native UI components that render directly inside this cell
text_input = widgets.Text(
    value='',
    placeholder='Type your question here...',
    description='Question:',
    disabled=False,
    layout=widgets.Layout(width='70%')
)
submit_button = widgets.Button(
    description='Submit Query',
    button_style='success',
    tooltip='Click to run RAG pipeline'
)
output_area = widgets.Output()

display(widgets.HBox([text_input, submit_button]), output_area)

# Define the core processing pipeline execution
def run_rag_pipeline(b):
    question = text_input.value.strip()
    
    with output_area:
        clear_output() # Clears previous response so you can run queries repeatedly
        if not question:
            print("Please enter a question in the text box above first!")
            return
            
        print(f"Question submitted: '{question}'\n")
        print("Processing vectors and generating cloud response...")
        
        try:
            embedder = LocalEmbeddingModel()
            mock_chunk = {"content": question}
            embedded_outputs = embedder.embed_chunks([mock_chunk])
            
            query_vector_floats = embedded_outputs[0]["embedding"]

            # Query Azure Vector Database
            vector_query = VectorizedQuery(vector=query_vector_floats, k_nearest_neighbors=3, fields="embeddings")
            azure_results = search_client.search(  
                search_text=question,
                vector_queries=[vector_query],
                select=["chunk_id", "celex_id", "text_content"],
                top=3
            )  

            retrieved_contexts = []
            sources_metadata = []
            
            # Parse Azure records natively
            for result in azure_results:
                retrieved_contexts.append(result.get('text_content', ''))
                sources_metadata.append({
                    "celex_id": result.get('celex_id', 'N/A'), 
                    "score": result.get('@search.score', 0.0)
                })

            if not retrieved_contexts:
                print("No matching vector context could be retrieved from Azure index!")
                return

            # Fetch LLM Answer
            llm = AzureOpenAIChatLLM()
            unified_context = "\n\n".join(retrieved_contexts)
            
            # Dynamic fallback depending on how your ChatLLM class accepts arguments
            if hasattr(llm, 'ask'):
                try:
                    answer = llm.ask(question, unified_context)
                except Exception:
                    answer = llm.ask(unified_context, question)
            elif hasattr(llm, 'generate'):
                answer = llm.generate(question, unified_context)
            else:
                answer = "Error: Found your LLM wrapper class but couldn't verify its execution method name."

            print("\n" + "="*60)
            print("LLM ANSWER:")
            print("="*60)
            print(answer)
            print("\n" + "="*60)
            print("ATTRIBUTION SOURCES:")
            print("="*60)
            for idx, src in enumerate(sources_metadata, 1):
                print(f"[Source {idx}] CELEX ID: {src['celex_id']} | Search Score: {src['score']:.4f}")
                
        except Exception as e:
            print(f"Execution error: {e}")

submit_button.on_click(run_rag_pipeline)