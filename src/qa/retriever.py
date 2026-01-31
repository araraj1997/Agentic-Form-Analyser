"""
Context Retriever Module

Provides intelligent context retrieval for QA operations.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Represents a retrieval result."""
    text: str
    score: float
    source: str
    chunk_type: str  # 'field', 'table', 'text'


class ContextRetriever:
    """
    Retrieves relevant context from documents for QA.
    
    Features:
    - Keyword-based retrieval
    - Semantic similarity (with embeddings)
    - Field-aware retrieval
    - Table-aware retrieval
    """
    
    def __init__(self, use_embeddings: bool = True):
        """
        Initialize retriever.
        
        Args:
            use_embeddings: Whether to use semantic embeddings
        """
        self.use_embeddings = use_embeddings
        self._embedder = None
    
    def retrieve(self, query: str, document, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant context from a document.
        
        Args:
            query: Search query
            document: FormDocument object
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        results = []
        
        # Retrieve from fields
        field_results = self._retrieve_from_fields(query, document.fields)
        results.extend(field_results)
        
        # Retrieve from tables
        if document.tables:
            table_results = self._retrieve_from_tables(query, document.tables)
            results.extend(table_results)
        
        # Retrieve from raw text
        text_results = self._retrieve_from_text(query, document.raw_text)
        results.extend(text_results)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def retrieve_multi(self, query: str, documents: List, 
                       top_k: int = 10) -> List[RetrievalResult]:
        """
        Retrieve from multiple documents.
        
        Args:
            query: Search query
            documents: List of FormDocument objects
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        all_results = []
        
        for doc in documents:
            results = self.retrieve(query, doc, top_k=top_k // len(documents) + 1)
            # Add document source to results
            for r in results:
                r.source = f"{doc.file_path}: {r.source}"
            all_results.extend(results)
        
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
    
    def _retrieve_from_fields(self, query: str, fields: Dict) -> List[RetrievalResult]:
        """Retrieve from document fields."""
        results = []
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w{3,}\b', query_lower))
        
        for field, value in fields.items():
            field_lower = field.lower()
            value_str = str(value).lower()
            
            # Calculate match score
            field_terms = set(re.findall(r'\b\w{3,}\b', field_lower))
            value_terms = set(re.findall(r'\b\w{3,}\b', value_str))
            
            field_overlap = len(query_terms & field_terms)
            value_overlap = len(query_terms & value_terms)
            
            score = (field_overlap * 2 + value_overlap) / max(1, len(query_terms))
            
            if score > 0:
                results.append(RetrievalResult(
                    text=f"{field}: {value}",
                    score=min(1.0, score),
                    source=field,
                    chunk_type='field'
                ))
        
        return results
    
    def _retrieve_from_tables(self, query: str, tables: List) -> List[RetrievalResult]:
        """Retrieve from document tables."""
        results = []
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w{3,}\b', query_lower))
        
        for i, table in enumerate(tables):
            if not table:
                continue
            
            # Convert table to searchable text
            table_text = ""
            for row in table:
                row_text = " | ".join(str(cell) for cell in row)
                table_text += row_text + "\n"
            
            # Calculate match score
            table_terms = set(re.findall(r'\b\w{3,}\b', table_text.lower()))
            overlap = len(query_terms & table_terms)
            score = overlap / max(1, len(query_terms))
            
            if score > 0.1:
                results.append(RetrievalResult(
                    text=table_text[:500],
                    score=min(1.0, score),
                    source=f"Table {i+1}",
                    chunk_type='table'
                ))
        
        return results
    
    def _retrieve_from_text(self, query: str, text: str) -> List[RetrievalResult]:
        """Retrieve from raw text."""
        results = []
        
        if not text:
            return results
        
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w{3,}\b', query_lower))
        
        # Split into paragraphs/chunks
        chunks = self._split_into_chunks(text)
        
        for chunk in chunks:
            chunk_lower = chunk.lower()
            chunk_terms = set(re.findall(r'\b\w{3,}\b', chunk_lower))
            
            overlap = len(query_terms & chunk_terms)
            score = overlap / max(1, len(query_terms))
            
            if score > 0.2:
                results.append(RetrievalResult(
                    text=chunk,
                    score=min(1.0, score * 0.8),  # Slightly lower weight for raw text
                    source="document text",
                    chunk_type='text'
                ))
        
        return results
    
    def _split_into_chunks(self, text: str, chunk_size: int = 300) -> List[str]:
        """Split text into manageable chunks."""
        chunks = []
        
        # First split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        for para in paragraphs:
            para = para.strip()
            
            if not para:
                continue
            
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                # Split long paragraphs by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= chunk_size:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk)
        
        return chunks
    
    def semantic_retrieve(self, query: str, document, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve using semantic similarity.
        
        Args:
            query: Search query
            document: FormDocument object
            top_k: Number of results
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.use_embeddings:
            return self.retrieve(query, document, top_k)
        
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                return self.retrieve(query, document, top_k)
        
        try:
            import numpy as np
            
            # Collect all text chunks
            chunks_with_meta = []
            
            # Add fields
            for field, value in document.fields.items():
                chunks_with_meta.append({
                    'text': f"{field}: {value}",
                    'source': field,
                    'type': 'field'
                })
            
            # Add text chunks
            text_chunks = self._split_into_chunks(document.raw_text)
            for chunk in text_chunks:
                chunks_with_meta.append({
                    'text': chunk,
                    'source': 'document text',
                    'type': 'text'
                })
            
            if not chunks_with_meta:
                return []
            
            # Embed query and chunks
            query_emb = self._embedder.encode([query])[0]
            chunk_texts = [c['text'] for c in chunks_with_meta]
            chunk_embs = self._embedder.encode(chunk_texts)
            
            # Calculate cosine similarities
            similarities = np.dot(chunk_embs, query_emb) / (
                np.linalg.norm(chunk_embs, axis=1) * np.linalg.norm(query_emb)
            )
            
            # Get top results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.2:
                    meta = chunks_with_meta[idx]
                    results.append(RetrievalResult(
                        text=meta['text'],
                        score=float(similarities[idx]),
                        source=meta['source'],
                        chunk_type=meta['type']
                    ))
            
            return results
            
        except Exception:
            return self.retrieve(query, document, top_k)
