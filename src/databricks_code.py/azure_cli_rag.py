import os
import ipywidgets as widgets
from IPython.display import display, clear_output
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from src.data_ingestion.retriever import AzureOpenAIChatLLM
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