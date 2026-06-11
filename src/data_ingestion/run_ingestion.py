"""
run_ingestion.py
Κεντρικό script για το διάβασμα των PDF κανονισμών, 
το chunking, την παραγωγή Azure Embeddings και την αποθήκευση στη ChromaDB.
"""

import os
from pathlib import Path
from dotenv import load_dotenv  

from src.config.settings import settings
from src.data_ingestion.pdf_ingestion import extract_pdf_pages
from src.data_ingestion.chunking import create_chunks
from src.data_ingestion.embeddings import LocalEmbeddingModel
from src.data_ingestion.vector_store import ChromaVectorStore

def main():

    load_dotenv() 

    
    pdf_dir = Path("data/raw_documents")
    
    if not pdf_dir.exists():
        print(f" Δημιουργία φακέλου εγγράφων στο: {pdf_dir}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        print(" Παρακαλώ βάλε τα PDF των κανονισμών (DORA, GDPR κλπ.) μέσα σε αυτόν τον φάκελο και ξανατρέξε το script!")
        return

    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f" Δεν βρέθηκαν PDF αρχεία στον φάκελο {pdf_dir}")
        return

    print(f" Βρέθηκαν {len(pdf_files)} αρχεία προς επεξεργασία.")

    
    print(" Αρχικοποίηση Azure OpenAI Embedding Model...")
    embedder = LocalEmbeddingModel()
    
    
    chroma_path = Path(getattr(settings, "VECTOR_DB_DIR", "data/chroma_db"))
    print(f" Σύνδεση με ChromaDB στο path: {chroma_path}")
    vector_store = ChromaVectorStore(
        persist_path=chroma_path,
        collection_name=settings.COLLECTION_NAME,
    )

    
    print(" Καθαρισμός προηγούμενων δεδομένων της collection...")
    vector_store.reset()

    total_chunks_added = 0

    
    for pdf_file in pdf_files:
        print(f"\n Επεξεργασία αρχείου: {pdf_file.name}")
        
        try:
            
            pages = extract_pdf_pages(str(pdf_file))
            if not pages:
                print(f" Το αρχείο {pdf_file.name} είναι άδειο ή δεν διαβάστηκε σωστά.")
                continue
                
           
            chunks = create_chunks(pages)
            print(f" Δημιουργήθηκαν {len(chunks)} chunks για το αρχείο {pdf_file.name}")
            
            
            print(" Παραγωγή Azure Embeddings (1536 dimensions)...")
            embedded_chunks = embedder.embed_chunks(chunks)
            
            
            print(" Αποθήκευση vectors στη ChromaDB...")
            vector_store.add_chunks(embedded_chunks)
            
            total_chunks_added += len(embedded_chunks)
            print(f" Επιτυχής εισαγωγή του αρχείου {pdf_file.name}")
            
        except Exception as e:
            print(f" Σφάλμα κατά την επεξεργασία του {pdf_file.name}: {str(e)}")

    print("\n==================================================")
    print(f" Η διαδικασία ολοκληρώθηκε! Συνολικά chunks στη βάση: {vector_store.count()}")
    print("==================================================")

if __name__ == "__main__":
    main()
