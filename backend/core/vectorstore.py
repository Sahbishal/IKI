"""
Vector Store — ChromaDB wrapper
Stores document chunks with embeddings for semantic search
"""
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Global client
_chroma_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None

COLLECTION_NAME = "iki_documents"


def init_vectorstore():
    """Initialize ChromaDB"""
    global _chroma_client, _collection
    _chroma_client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"✅ ChromaDB initialized. Collection: {COLLECTION_NAME}, Items: {_collection.count()}")


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        init_vectorstore()
    return _collection


def add_documents(
    texts: List[str],
    ids: List[str],
    metadatas: List[Dict[str, Any]],
    embeddings: Optional[List[List[float]]] = None,
):
    """Add document chunks to ChromaDB"""
    collection = get_collection()

    # Use Gemini embeddings if not provided
    if embeddings is None:
        from core.llm import get_embeddings
        embed_model = get_embeddings()
        embeddings = embed_model.embed_documents(texts)

    collection.add(
        documents=texts,
        ids=ids,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    logger.info(f"Added {len(texts)} chunks to ChromaDB")


def search_similar(
    query: str,
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Search for similar documents"""
    from core.llm import get_embeddings

    collection = get_collection()
    embed_model = get_embeddings()
    query_embedding = embed_model.embed_query(query)

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "score": 1 - results["distances"][0][i],  # cosine similarity
        })
    return output


def delete_document_chunks(document_id: str):
    """Remove all chunks for a document"""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})


def get_chunk_count() -> int:
    """Total number of stored chunks"""
    return get_collection().count()
