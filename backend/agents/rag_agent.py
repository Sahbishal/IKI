"""
RAG Search Agent
Retrieves relevant document chunks + Knowledge Graph context,
then uses Gemini to generate grounded, cited answers
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from core.vectorstore import search_similar
from core.knowledge_graph import knowledge_graph
from core.llm import ainvoke_llm

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are an expert Industrial AI Assistant for an industrial operations platform.

You answer questions about equipment, maintenance, failures, compliance, and safety 
based ONLY on the provided document excerpts and knowledge graph context.

Rules:
1. Always cite your sources: mention the document name and page number
2. If the information is not in the provided context, say so clearly
3. Be precise about equipment IDs (e.g., P-101, not just "the pump")
4. Highlight safety concerns or compliance violations prominently
5. For predictive questions, explain your reasoning based on historical data
6. Structure long answers with clear sections
7. Use the knowledge graph relationships to provide richer context

Format citations as: [Source: DocumentName, Page X]"""


async def rag_query(
    question: str,
    n_chunks: int = 5,
    session_history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline:
    1. Embed question
    2. Retrieve similar chunks from ChromaDB
    3. Search Knowledge Graph for entity context
    4. Build prompt with context
    5. Generate answer with Gemini
    6. Return answer + citations
    """
    # Step 1: Vector search
    logger.info(f"RAG query: {question[:80]}")
    chunks = search_similar(question, n_results=n_chunks)

    # Step 2: Knowledge Graph search
    kg_context = _search_knowledge_graph(question)

    # Step 3: Build context
    context_parts = []
    citations = []

    for i, chunk in enumerate(chunks):
        doc_name = chunk["metadata"].get("document_name", "Unknown Document")
        page = chunk["metadata"].get("page", "?")
        score = chunk.get("score", 0)

        context_parts.append(
            f"[Document {i+1}: {doc_name}, Page {page} (relevance: {score:.2f})]\n{chunk['text']}"
        )
        citations.append({
            "document": doc_name,
            "page": str(page),
            "relevance_score": round(score, 3),
            "excerpt": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
        })

    # Build conversation history context
    history_context = ""
    if session_history:
        recent = session_history[-4:]  # Last 4 turns
        history_context = "\n".join([
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:300]}"
            for m in recent
        ])

    # Step 4: Assemble prompt
    prompt = f"""QUESTION: {question}

KNOWLEDGE GRAPH CONTEXT:
{kg_context if kg_context else "No direct entity matches found in knowledge graph."}

DOCUMENT CONTEXT:
{chr(10).join(context_parts) if context_parts else "No relevant documents found. The knowledge base may be empty — please upload documents first."}

{"CONVERSATION HISTORY:" + chr(10) + history_context if history_context else ""}

Please answer the question based on the above context. Include citations."""

    # Step 5: Generate answer
    answer = await ainvoke_llm(prompt, system_prompt=RAG_SYSTEM_PROMPT, temperature=0.2)

    # Step 6: Determine agent steps for UI display
    agent_steps = [
        {"step": "Vector Search", "status": "done", "detail": f"Retrieved {len(chunks)} relevant chunks"},
        {"step": "Knowledge Graph Lookup", "status": "done", "detail": kg_context[:100] if kg_context else "No KG matches"},
        {"step": "LLM Generation", "status": "done", "detail": "Gemini 2.0 Flash"},
    ]

    return {
        "answer": answer,
        "citations": citations,
        "agent_steps": agent_steps,
        "chunks_retrieved": len(chunks),
        "kg_context_found": bool(kg_context),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _search_knowledge_graph(question: str) -> str:
    """Extract entity context from knowledge graph based on question"""
    # Extract potential entity names from question
    import re

    # Look for equipment IDs (P-101, C-22, B-5 etc.)
    equipment_pattern = re.findall(r"[A-Z]-?\d+", question)
    # Look for named entities
    words = question.split()

    kg_results = []

    # Search by equipment ID patterns
    for eq_id in equipment_pattern:
        results = knowledge_graph.search_entity(eq_id)
        for r in results[:2]:
            entity_info = knowledge_graph.get_entity_neighbors(r["id"])
            if entity_info["connections"]:
                relations = ", ".join([
                    f"{c['relation']} → {c['label']}"
                    for c in entity_info["connections"][:5]
                ])
                kg_results.append(f"• {r.get('label', r['id'])}: {relations}")

    # Keyword search
    for word in words:
        if len(word) > 4 and word.isalpha():
            results = knowledge_graph.search_entity(word)
            for r in results[:1]:
                kg_results.append(f"• {r.get('label', r['id'])} (type: {r.get('type', 'unknown')})")

    return "\n".join(kg_results[:8]) if kg_results else ""
