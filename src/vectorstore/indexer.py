"""Builds a Chroma collection from a chunk-shaped DataFrame.

Used for both the clean KB and every poisoned KB variant — the same
function, so indexing logic can never differ between clean and poisoned
data (mirrors the "no special path for poisoned data" rule in
src/preprocessing/text_cleaning.py).
"""
from __future__ import annotations

import pandas as pd

from src.embeddings.embedding_service import EmbeddingService
from src.preprocessing.text_cleaning import clean_text
from src.vectorstore.chroma_store import ChromaVectorStore
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Columns expected on the chunk-shaped DataFrame passed to index_chunks().
# (Both real chunks.csv rows and the poison-as-chunk rows produced by
# src.attacks.poison_generator.as_chunk_rows() carry all of these.)
REQUIRED_COLUMNS = [
    "chunk_id", "document_id", "title", "category", "text",
    "source", "source_url", "trust_level", "verification_status",
]


def index_chunks(
    chunks_df: pd.DataFrame,
    embedder: EmbeddingService,
    store: ChromaVectorStore,
    collection_name: str,
    reset: bool = True,
) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in chunks_df.columns]
    if missing:
        raise ValueError(f"index_chunks: chunk dataframe missing columns {missing}")

    if reset:
        store.reset_collection(collection_name)

    cleaned_texts = [clean_text(t) for t in chunks_df["text"].tolist()]
    embeddings = embedder.encode(cleaned_texts)

    metadatas = [
        {
            "document_id": row.document_id,
            "title": row.title,
            "category": row.category,
            "source": row.source,
            "source_url": row.source_url,
            "trust_level": row.trust_level,
            "verification_status": row.verification_status,
        }
        for row in chunks_df.itertuples(index=False)
    ]

    store.add_documents(
        collection_name=collection_name,
        ids=chunks_df["chunk_id"].tolist(),
        embeddings=embeddings,
        documents=cleaned_texts,
        metadatas=metadatas,
    )
    logger.info(
        "Indexed %d chunks into '%s' using embedding backend %s",
        len(chunks_df), collection_name, embedder.backend_name,
    )
