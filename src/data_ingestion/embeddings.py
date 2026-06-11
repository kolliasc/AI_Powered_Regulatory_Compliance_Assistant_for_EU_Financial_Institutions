"""
embeddings.py

Embedding generation layer.

Current implementation:
- SentenceTransformers

Future replacements:
- Azure OpenAI
- Databricks Foundation Models
- Databricks Vector Search
"""

from sentence_transformers import SentenceTransformer

from src.config.settings import settings


class LocalEmbeddingModel:

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
    ):
        self.model = SentenceTransformer(model_name)

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_chunks(
        self,
        chunks: list[dict],
    ) -> list[dict]:
        """
        Adds embeddings to chunk records.
        """

        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = self.embed_documents(texts)

        enriched_chunks = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
            strict=False,
        ):

            enriched_chunk = {
                **chunk,
                "embedding": embedding,
                "embedding_model":
                    settings.EMBEDDING_MODEL_NAME,
            }

            enriched_chunks.append(
                enriched_chunk
            )

        return enriched_chunks

"""
embeddings.py

Embedding generation layer.

Current implementation:
- Azure OpenAI (text-embedding-3-small)
"""

# import os
# from openai import AzureOpenAI
# from src.config.settings import settings


# class LocalEmbeddingModel:  
#     # Κρατάμε το όνομα "LocalEmbeddingModel" για να μην σπάσει ΚΑΝΕΝΑ import στο project σου

#     def __init__(
#         self,
#         model_name: str = settings.EMBEDDING_MODEL_NAME,
#     ):
#         self.model_name = model_name
#         # Αρχικοποίηση του επίσημου Azure OpenAI Client
#         self.client = AzureOpenAI(
#             azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#             api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#             api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
#         )

#     def embed_documents(
#         self,
#         texts: list[str],
#     ) -> list[list[float]]:
#         # Η Azure δέχεται απευθείας λίστα από κείμενα
#         response = self.client.embeddings.create(
#             input=texts,
#             model=self.model_name
#         )
#         return [data.embedding for data in response.data]

#     def embed_query(
#         self,
#         text: str,
#     ) -> list[float]:
#         response = self.client.embeddings.create(
#             input=[text],
#             model=self.model_name
#         )
#         return response.data[0].embedding

#     def embed_chunks(
#         self,
#         chunks: list[dict],
#     ) -> list[dict]:
#         """
#         Adds embeddings to chunk records.
#         """
#         texts = [chunk["content"] for chunk in chunks]
#         embeddings = self.embed_documents(texts)

#         enriched_chunks = []
#         for chunk, embedding in zip(chunks, embeddings, strict=False):
#             enriched_chunk = {
#                 **chunk,
#                 "embedding": embedding,
#                 "embedding_model": self.model_name,
#             }
#             enriched_chunks.append(enriched_chunk)

#         return enriched_chunks

