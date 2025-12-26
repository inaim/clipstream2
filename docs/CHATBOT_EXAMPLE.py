"""
RAG Chatbot Example for Clipstream Documentation

This example shows how to build a chatbot using the RAG knowledge base.
Uses semantic search over documentation to answer user questions.
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional


# ============================================================================
# RAG KNOWLEDGE BASE LOADER
# ============================================================================

class ClipstreamRAG:
    """RAG system for Clipstream documentation."""

    def __init__(self, index_file: str = "RAG_INDEX.json"):
        """Load RAG index."""
        with open(index_file, 'r') as f:
            self.index = json.load(f)

        self.documents = {doc['id']: doc for doc in self.index['documents']}
        self.search_index = self.index['search_index']
        self.faq = self.index['faq']

    def search_by_keyword(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search documents by keyword matching.

        Args:
            query: User query
            top_k: Number of results

        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        results = []

        # Check FAQ first
        for faq_item in self.faq:
            if any(word in faq_item['question'].lower() for word in query_lower.split()):
                results.append({
                    'type': 'faq',
                    'question': faq_item['question'],
                    'answer': faq_item['answer'],
                    'doc_ref': faq_item['doc_ref'],
                    'score': 1.0
                })

        # Search in documents
        for doc_id, doc in self.documents.items():
            # Check keywords
            keyword_matches = sum(
                1 for keyword in doc['keywords']
                if keyword in query_lower
            )

            # Check title
            title_match = any(word in doc['title'].lower() for word in query_lower.split())

            # Check summary
            summary_match = any(word in doc['summary'].lower() for word in query_lower.split())

            # Calculate score
            score = (keyword_matches * 0.5) + (title_match * 0.3) + (summary_match * 0.2)

            if score > 0:
                results.append({
                    'type': 'document',
                    'doc_id': doc_id,
                    'title': doc['title'],
                    'file': doc['file'],
                    'summary': doc['summary'],
                    'score': score
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:top_k]

    def get_quick_answer(self, query: str) -> Optional[str]:
        """Get quick answer from FAQ."""
        query_lower = query.lower()

        for faq_item in self.faq:
            if any(word in query_lower for word in faq_item['question'].lower().split()):
                return faq_item['answer']

        return None

    def get_chatbot_response(self, query: str) -> str:
        """
        Get chatbot response for user query.

        Args:
            query: User query

        Returns:
            Chatbot response
        """
        # Try FAQ first
        quick_answer = self.get_quick_answer(query)
        if quick_answer:
            return quick_answer

        # Search documents
        results = self.search_by_keyword(query, top_k=3)

        if not results:
            return self.index['chatbot_prompts']['unknown']

        # Build response
        response = "Based on the documentation:\n\n"

        for i, result in enumerate(results, 1):
            if result['type'] == 'faq':
                response += f"**{result['question']}**\n{result['answer']}\n\n"
            else:
                response += f"{i}. **{result['title']}**\n"
                response += f"   {result['summary'][:200]}...\n"
                response += f"   📄 See: `{result['file']}`\n\n"

        return response


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize RAG system
    rag = ClipstreamRAG("RAG_INDEX.json")

    # Example queries
    queries = [
        "How do I start the platform?",
        "How fast is embedding search?",
        "What are the API endpoints?",
        "How do I test the ML algorithm?",
        "Can I use real TikTok videos?",
        "How do I fix SSE not working?",
        "What's the database schema?",
        "How do I scale to production?",
    ]

    print("🤖 Clipstream RAG Chatbot Example")
    print("=" * 60)
    print()

    for query in queries:
        print(f"❓ User: {query}")
        print()

        response = rag.get_chatbot_response(query)
        print(f"🤖 Bot: {response}")
        print("-" * 60)
        print()


# ============================================================================
# ADVANCED: EMBEDDING-BASED SEARCH
# ============================================================================

class ClipstreamRAGAdvanced(ClipstreamRAG):
    """
    Advanced RAG with embedding-based semantic search.

    Requires: sentence-transformers
    pip install sentence-transformers
    """

    def __init__(self, index_file: str = "RAG_INDEX.json"):
        super().__init__(index_file)

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

            # Pre-compute document embeddings
            self.doc_embeddings = {}
            for doc_id, doc in self.documents.items():
                # Combine title, summary, keywords for embedding
                text = f"{doc['title']} {doc['summary']} {' '.join(doc['keywords'])}"
                self.doc_embeddings[doc_id] = self.model.encode(text)

            print("✅ Advanced RAG with embeddings loaded")

        except ImportError:
            print("⚠️  sentence-transformers not installed, using keyword search")
            self.model = None

    def search_by_embedding(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search using semantic embeddings.

        Args:
            query: User query
            top_k: Number of results

        Returns:
            List of matching documents
        """
        if not self.model:
            return self.search_by_keyword(query, top_k)

        # Encode query
        query_embedding = self.model.encode(query)

        # Compute similarity with all documents
        results = []
        for doc_id, doc_embedding in self.doc_embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )

            doc = self.documents[doc_id]
            results.append({
                'type': 'document',
                'doc_id': doc_id,
                'title': doc['title'],
                'file': doc['file'],
                'summary': doc['summary'],
                'score': float(similarity)
            })

        # Sort by similarity
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:top_k]

    def get_chatbot_response(self, query: str) -> str:
        """Get response using embeddings."""
        # Try FAQ first
        quick_answer = self.get_quick_answer(query)
        if quick_answer:
            return quick_answer

        # Search with embeddings
        results = self.search_by_embedding(query, top_k=3)

        if not results or results[0]['score'] < 0.3:
            return self.index['chatbot_prompts']['unknown']

        # Build response
        response = "Based on the documentation:\n\n"

        for i, result in enumerate(results, 1):
            response += f"{i}. **{result['title']}** (relevance: {result['score']:.2f})\n"
            response += f"   {result['summary'][:200]}...\n"
            response += f"   📄 See: `{result['file']}`\n\n"

        return response


# ============================================================================
# WEB API EXAMPLE
# ============================================================================

"""
FastAPI endpoint for chatbot:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
rag = ClipstreamRAGAdvanced("docs/RAG_INDEX.json")

class Query(BaseModel):
    question: str

@app.post("/chatbot")
async def ask_chatbot(query: Query):
    response = rag.get_chatbot_response(query.question)
    return {"answer": response}
```

Usage:
```bash
curl -X POST http://localhost:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I start the platform?"}'
```
"""
