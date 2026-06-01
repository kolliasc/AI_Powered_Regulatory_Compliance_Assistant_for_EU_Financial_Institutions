# Contract 1: RegulatoryChunkModel
# Ένα Pydantic μοντέλο που περιγράφει τη δομή των chunks κανονιστικών κειμένων που θα αποθηκεύονται στο Databricks.
from datetime import date
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl

class RegulatoryChunkModel(BaseModel):
    chunk_id: UUID = Field(default_factory=uuid4, description="Μοναδικό ID κάθε chunk")
    document_id: UUID = Field(description="ID του parent document")
    regulation_title: str = Field(..., description="Τίτλος κανονισμού")
    issuing_authority: str = Field(..., description="Αρχή έκδοσης (π.χ. ESMA, EBA)")
    publication_date: date = Field(..., description="Ημερομηνία δημοσίευσης")
    regulation_category: str = Field(..., description="Κατηγορία (AML, GDPR, DORA, κτλ.)")
    article_reference: str = Field(..., description="Αναφορά άρθρου")
    compliance_domain: str = Field(..., description="Τομέας συμμόρφωσης")
    chunk_text: str = Field(..., description="Το κείμενο του chunk")
    chunk_index: int = Field(..., description="Σειρά chunk μέσα στο document")
    embedding_model: str = Field(default="text-embedding-3-large-v1", description="Έκδοση embedding model")
    
    # Το vector θα παραχθεί αργότερα (3072 dims), αρχικά μπορεί να είναι None ή Empty List
    embedding_vector: Optional[List[float]] = Field(default=None, description="Το vector (3072 dims)")
    source_url: Optional[str] = Field(default=None, description="URL πηγής")
    
    # Extra metadata που μπορεί να χρειαστούν
    pii_redacted: bool = Field(default=False, description="Αν έχουν αφαιρεθεί προσωπικά δεδομένα")

    class Config:
        # Επιτρέπει τη μετατροπή από/προς ORM αν χρειαστεί στο Databricks
        from_attributes = True