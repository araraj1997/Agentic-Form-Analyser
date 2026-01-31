"""
Question Answering Engine Module

Provides intelligent question answering capabilities for forms.
"""

import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class QueryResult:
    """Represents a QA query result."""
    question: str
    answer: str
    confidence: float
    source_fields: List[str]
    context: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class QAEngine:
    """
    Question Answering Engine for form documents.
    
    Features:
    - Semantic similarity matching
    - Field-based retrieval
    - Cross-document analysis
    - Natural language answer generation
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize QA engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.model_name = self.config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
        self.max_context = self.config.get('max_context_length', 512)
        self.top_k = self.config.get('top_k_retrieval', 5)
        
        self._embedder = None
        self._use_embeddings = True
    
    def _lazy_load_embedder(self):
        """Lazy load the sentence transformer model."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.model_name)
            except ImportError:
                self._use_embeddings = False
                print("Warning: sentence-transformers not available. Using keyword matching.")
        return self._embedder
    
    def answer(self, question: str, document) -> QueryResult:
        """
        Answer a question about a single form document.
        
        Args:
            question: Natural language question
            document: FormDocument object
            
        Returns:
            QueryResult with answer and metadata
        """
        # Extract relevant context
        context, source_fields = self._retrieve_context(question, document)
        
        # Generate answer
        answer, confidence = self._generate_answer(question, context, document)
        
        return QueryResult(
            question=question,
            answer=answer,
            confidence=confidence,
            source_fields=source_fields,
            context=context[:500] if context else ""
        )
    
    def answer_multiple(self, question: str, documents: List) -> QueryResult:
        """
        Answer a question across multiple documents.
        
        Args:
            question: Natural language question
            documents: List of FormDocument objects
            
        Returns:
            QueryResult with aggregated answer
        """
        all_contexts = []
        all_source_fields = []
        
        for doc in documents:
            context, fields = self._retrieve_context(question, doc)
            if context:
                all_contexts.append(f"[{doc.file_path}]: {context}")
                all_source_fields.extend(fields)
        
        combined_context = "\n\n".join(all_contexts)
        answer, confidence = self._generate_answer(question, combined_context, documents)
        
        return QueryResult(
            question=question,
            answer=answer,
            confidence=confidence,
            source_fields=list(set(all_source_fields)),
            context=combined_context[:1000] if combined_context else ""
        )
    
    def cross_form_analysis(self, question: str, documents: List) -> Dict[str, Any]:
        """
        Perform cross-form analysis.
        
        Args:
            question: Analysis question
            documents: List of FormDocument objects
            
        Returns:
            Analysis results dictionary
        """
        # Collect all fields across documents
        all_fields = {}
        for doc in documents:
            for field, value in doc.fields.items():
                if field not in all_fields:
                    all_fields[field] = []
                all_fields[field].append({
                    'value': value,
                    'source': doc.file_path
                })
        
        # Find common fields
        common_fields = [f for f, v in all_fields.items() if len(v) == len(documents)]
        
        # Perform analysis based on question type
        analysis = {
            'total_documents': len(documents),
            'common_fields': common_fields,
            'schema_types': [doc.schema_type for doc in documents],
            'field_summary': {}
        }
        
        # Analyze numeric fields
        for field, values in all_fields.items():
            numeric_values = []
            for v in values:
                val = v['value']
                if isinstance(val, (int, float)):
                    numeric_values.append(val)
                elif isinstance(val, dict) and 'value' in val:
                    try:
                        numeric_values.append(float(val['value']))
                    except (ValueError, TypeError):
                        pass
            
            if numeric_values:
                analysis['field_summary'][field] = {
                    'count': len(numeric_values),
                    'sum': sum(numeric_values),
                    'average': sum(numeric_values) / len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values)
                }
        
        # Generate insights based on question
        insights = self._generate_insights(question, documents, analysis)
        analysis['insights'] = insights
        
        # Direct answer to the question
        answer_result = self.answer_multiple(question, documents)
        analysis['answer'] = answer_result.answer
        
        return analysis
    
    def _retrieve_context(self, question: str, document) -> tuple:
        """
        Retrieve relevant context for answering.
        
        Args:
            question: The question to answer
            document: FormDocument object
            
        Returns:
            Tuple of (context string, list of source fields)
        """
        question_lower = question.lower()
        source_fields = []
        context_parts = []
        
        # Check fields for relevant information
        for field, value in document.fields.items():
            field_lower = field.lower()
            
            # Check if field name is relevant to question
            relevance = self._calculate_relevance(question_lower, field_lower, str(value).lower())
            
            if relevance > 0.3:
                source_fields.append(field)
                context_parts.append(f"{field}: {value}")
        
        # If using embeddings and available, do semantic search
        if self._use_embeddings and len(context_parts) < 3:
            additional = self._semantic_search(question, document)
            context_parts.extend(additional)
        
        # Also include relevant parts of raw text
        text_snippets = self._extract_relevant_snippets(question, document.raw_text)
        context_parts.extend(text_snippets)
        
        return "\n".join(context_parts[:self.top_k]), source_fields
    
    def _calculate_relevance(self, question: str, field: str, value: str) -> float:
        """Calculate relevance score between question and field."""
        # Extract key terms from question
        question_terms = set(re.findall(r'\b\w+\b', question))
        field_terms = set(re.findall(r'\b\w+\b', field))
        value_terms = set(re.findall(r'\b\w+\b', value))
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 
                      'where', 'when', 'how', 'which', 'this', 'that', 'of', 'in', 
                      'on', 'for', 'to', 'from', 'with', 'by'}
        
        question_terms -= stop_words
        
        # Calculate overlap
        field_overlap = len(question_terms & field_terms) / max(1, len(question_terms))
        value_overlap = len(question_terms & value_terms) / max(1, len(question_terms))
        
        return max(field_overlap, value_overlap * 0.5)
    
    def _semantic_search(self, question: str, document) -> List[str]:
        """Perform semantic search using embeddings."""
        embedder = self._lazy_load_embedder()
        
        if embedder is None:
            return []
        
        try:
            import numpy as np
            
            # Create text chunks from document
            chunks = []
            
            # Add fields as chunks
            for field, value in document.fields.items():
                chunks.append(f"{field}: {value}")
            
            # Add text paragraphs
            paragraphs = document.raw_text.split('\n\n')
            chunks.extend([p.strip() for p in paragraphs if p.strip()])
            
            if not chunks:
                return []
            
            # Embed question and chunks
            question_embedding = embedder.encode([question])[0]
            chunk_embeddings = embedder.encode(chunks)
            
            # Calculate similarities
            similarities = np.dot(chunk_embeddings, question_embedding) / (
                np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(question_embedding)
            )
            
            # Get top matches
            top_indices = np.argsort(similarities)[-self.top_k:][::-1]
            
            return [chunks[i] for i in top_indices if similarities[i] > 0.3]
            
        except Exception:
            return []
    
    def _extract_relevant_snippets(self, question: str, text: str) -> List[str]:
        """Extract relevant text snippets."""
        if not text:
            return []
        
        snippets = []
        question_terms = set(re.findall(r'\b\w{3,}\b', question.lower()))
        
        # Split into sentences
        sentences = re.split(r'[.!?\n]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 500:
                continue
            
            sentence_terms = set(re.findall(r'\b\w{3,}\b', sentence.lower()))
            overlap = len(question_terms & sentence_terms)
            
            if overlap >= 2:
                snippets.append(sentence)
        
        return snippets[:3]
    
    def _generate_answer(self, question: str, context: str, document) -> tuple:
        """
        Generate an answer based on context.
        
        Args:
            question: The question
            context: Retrieved context
            document: Source document(s)
            
        Returns:
            Tuple of (answer, confidence)
        """
        if not context:
            return "I couldn't find relevant information to answer this question.", 0.0
        
        question_lower = question.lower()
        
        # Handle specific question types
        if any(w in question_lower for w in ['what is', 'what\'s', "what are"]):
            return self._answer_what_question(question_lower, context, document)
        
        if any(w in question_lower for w in ['how much', 'how many', 'total', 'sum', 'amount']):
            return self._answer_quantity_question(question_lower, context, document)
        
        if any(w in question_lower for w in ['who', 'whose']):
            return self._answer_who_question(question_lower, context, document)
        
        if any(w in question_lower for w in ['when', 'date']):
            return self._answer_when_question(question_lower, context, document)
        
        if any(w in question_lower for w in ['where', 'address', 'location']):
            return self._answer_where_question(question_lower, context, document)
        
        # Default: return most relevant context
        return f"Based on the form: {context[:300]}...", 0.6
    
    def _answer_what_question(self, question: str, context: str, document) -> tuple:
        """Answer 'what' questions."""
        # Extract the subject from the question
        patterns = [
            r"what is (?:the )?(.+?)(?:\?|$)",
            r"what's (?:the )?(.+?)(?:\?|$)",
            r"what are (?:the )?(.+?)(?:\?|$)"
        ]
        
        subject = None
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                subject = match.group(1).strip()
                break
        
        if subject and hasattr(document, 'fields'):
            # Look for matching field
            for field, value in document.fields.items():
                if subject in field.lower() or field.lower() in subject:
                    return f"The {field} is: {value}", 0.9
        
        # Return from context
        lines = context.split('\n')
        for line in lines:
            if ':' in line:
                return line.strip(), 0.7
        
        return context[:200], 0.5
    
    def _answer_quantity_question(self, question: str, context: str, document) -> tuple:
        """Answer quantity questions."""
        # Look for numeric values in context
        numbers = re.findall(r'\$?[\d,]+(?:\.\d{2})?', context)
        
        if numbers:
            # If asking for total, try to find total field
            if 'total' in question:
                for line in context.split('\n'):
                    if 'total' in line.lower():
                        return line.strip(), 0.85
            
            # Return the largest number found (often the relevant one)
            parsed_numbers = []
            for n in numbers:
                try:
                    parsed_numbers.append(float(n.replace('$', '').replace(',', '')))
                except ValueError:
                    pass
            
            if parsed_numbers:
                return f"The amount is: ${max(parsed_numbers):,.2f}", 0.7
        
        return f"Based on the form: {context[:200]}", 0.5
    
    def _answer_who_question(self, question: str, context: str, document) -> tuple:
        """Answer 'who' questions."""
        # Look for name fields
        name_patterns = ['name', 'applicant', 'employee', 'patient', 'customer', 'client']
        
        if hasattr(document, 'fields'):
            for field, value in document.fields.items():
                if any(p in field.lower() for p in name_patterns):
                    return f"The {field} is: {value}", 0.9
        
        # Look in context
        for line in context.split('\n'):
            if any(p in line.lower() for p in name_patterns):
                return line.strip(), 0.7
        
        return f"Based on the form: {context[:200]}", 0.5
    
    def _answer_when_question(self, question: str, context: str, document) -> tuple:
        """Answer 'when' questions."""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return f"The date is: {match.group()}", 0.8
        
        if hasattr(document, 'fields'):
            for field, value in document.fields.items():
                if 'date' in field.lower():
                    return f"The {field} is: {value}", 0.9
        
        return f"Based on the form: {context[:200]}", 0.5
    
    def _answer_where_question(self, question: str, context: str, document) -> tuple:
        """Answer 'where' questions."""
        location_patterns = ['address', 'location', 'city', 'state', 'zip', 'street']
        
        if hasattr(document, 'fields'):
            for field, value in document.fields.items():
                if any(p in field.lower() for p in location_patterns):
                    return f"The {field} is: {value}", 0.9
        
        for line in context.split('\n'):
            if any(p in line.lower() for p in location_patterns):
                return line.strip(), 0.7
        
        return f"Based on the form: {context[:200]}", 0.5
    
    def _generate_insights(self, question: str, documents: List, analysis: Dict) -> List[str]:
        """Generate insights from analysis."""
        insights = []
        
        # Schema diversity
        unique_schemas = set(s for s in analysis['schema_types'] if s)
        if len(unique_schemas) > 1:
            insights.append(f"Forms include {len(unique_schemas)} different types: {', '.join(unique_schemas)}")
        elif len(unique_schemas) == 1:
            insights.append(f"All forms are of type: {list(unique_schemas)[0]}")
        
        # Common fields
        if analysis['common_fields']:
            insights.append(f"All forms share these fields: {', '.join(analysis['common_fields'][:5])}")
        
        # Numeric field insights
        for field, stats in analysis.get('field_summary', {}).items():
            if stats['count'] > 1:
                if 'salary' in field.lower() or 'income' in field.lower() or 'amount' in field.lower():
                    insights.append(
                        f"Average {field}: ${stats['average']:,.2f} "
                        f"(range: ${stats['min']:,.2f} - ${stats['max']:,.2f})"
                    )
        
        return insights
