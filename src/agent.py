"""
Intelligent Form Agent - Main Orchestrator

This module provides the main entry point for the Intelligent Form Agent,
coordinating extraction, QA, and summarization capabilities.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.image_extractor import ImageExtractor
from src.extractors.text_extractor import TextExtractor
from src.processors.field_parser import FieldParser
from src.processors.table_parser import TableParser
from src.processors.schema_detector import SchemaDetector
from src.qa.qa_engine import QAEngine
from src.summarizer.summarizer import FormSummarizer
from src.utils.helpers import detect_file_type, load_config


@dataclass
class FormDocument:
    """Represents a processed form document."""
    file_path: str
    file_type: str
    raw_text: str
    fields: Dict[str, Any] = field(default_factory=dict)
    tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_type: Optional[str] = None
    extraction_confidence: float = 0.0
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


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


@dataclass
class Summary:
    """Represents a form summary."""
    form_type: str
    key_information: Dict[str, Any]
    highlights: List[str]
    notable_items: List[str]
    full_text: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class IntelligentFormAgent:
    """
    Main agent class that orchestrates form processing, QA, and summarization.
    
    Example usage:
        agent = IntelligentFormAgent()
        form = agent.load_form("path/to/form.pdf")
        answer = agent.ask("What is the total amount?", form)
        summary = agent.summarize(form)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Intelligent Form Agent.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path) if config_path else self._default_config()
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor()
        self.image_extractor = ImageExtractor()
        self.text_extractor = TextExtractor()
        
        # Initialize processors
        self.field_parser = FieldParser()
        self.table_parser = TableParser()
        self.schema_detector = SchemaDetector()
        
        # Initialize intelligence components
        self.qa_engine = QAEngine(config=self.config.get('qa', {}))
        self.summarizer = FormSummarizer(config=self.config.get('summarization', {}))
        
        # Document store for loaded forms
        self._document_store: Dict[str, FormDocument] = {}
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            'extraction': {
                'ocr_language': 'eng',
                'confidence_threshold': 0.7,
                'extract_tables': True
            },
            'qa': {
                'model': 'sentence-transformers/all-MiniLM-L6-v2',
                'max_context_length': 512,
                'top_k_retrieval': 5
            },
            'summarization': {
                'max_length': 500,
                'min_length': 100,
                'style': 'bullet_points'
            }
        }
    
    def load_form(self, file_path: str) -> FormDocument:
        """
        Load and process a form from a file.
        
        Args:
            file_path: Path to the form file
            
        Returns:
            FormDocument object with extracted data
        """
        file_path = str(Path(file_path).resolve())
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Form file not found: {file_path}")
        
        # Detect file type
        file_type = detect_file_type(file_path)
        
        # Extract raw content based on file type
        if file_type == 'pdf':
            raw_text, tables, metadata = self.pdf_extractor.extract(file_path)
        elif file_type in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
            raw_text, tables, metadata = self.image_extractor.extract(file_path)
        else:
            raw_text, tables, metadata = self.text_extractor.extract(file_path)
        
        # Parse fields from raw text
        fields = self.field_parser.parse(raw_text)
        
        # Detect schema/form type
        schema_type = self.schema_detector.detect(raw_text, fields)
        
        # Calculate extraction confidence
        confidence = self._calculate_confidence(fields, raw_text)
        
        # Create document
        document = FormDocument(
            file_path=file_path,
            file_type=file_type,
            raw_text=raw_text,
            fields=fields,
            tables=tables,
            metadata=metadata,
            schema_type=schema_type,
            extraction_confidence=confidence
        )
        
        # Store in document cache
        self._document_store[file_path] = document
        
        return document
    
    def load_forms(self, file_paths: List[str]) -> List[FormDocument]:
        """
        Load multiple forms.
        
        Args:
            file_paths: List of paths to form files
            
        Returns:
            List of FormDocument objects
        """
        return [self.load_form(path) for path in file_paths]
    
    def extract_fields(self, document: FormDocument) -> Dict[str, Any]:
        """
        Extract all fields from a form document.
        
        Args:
            document: FormDocument to extract from
            
        Returns:
            Dictionary of field names to values
        """
        return document.fields
    
    def ask(self, question: str, document: Union[FormDocument, str]) -> QueryResult:
        """
        Ask a question about a form.
        
        Args:
            question: Natural language question
            document: FormDocument or path to form
            
        Returns:
            QueryResult with answer and metadata
        """
        if isinstance(document, str):
            if document in self._document_store:
                document = self._document_store[document]
            else:
                document = self.load_form(document)
        
        return self.qa_engine.answer(question, document)
    
    def ask_multiple(self, question: str, documents: List[FormDocument]) -> QueryResult:
        """
        Ask a question across multiple forms for holistic analysis.
        
        Args:
            question: Natural language question
            documents: List of FormDocument objects
            
        Returns:
            QueryResult with aggregated answer
        """
        return self.qa_engine.answer_multiple(question, documents)
    
    def summarize(self, document: Union[FormDocument, str]) -> Summary:
        """
        Generate a summary of a form.
        
        Args:
            document: FormDocument or path to form
            
        Returns:
            Summary object
        """
        if isinstance(document, str):
            if document in self._document_store:
                document = self._document_store[document]
            else:
                document = self.load_form(document)
        
        return self.summarizer.summarize(document)
    
    def analyze(self, documents: List[FormDocument], question: str) -> Dict[str, Any]:
        """
        Perform cross-form analysis.
        
        Args:
            documents: List of forms to analyze
            question: Analysis question
            
        Returns:
            Dictionary with analysis results
        """
        return self.qa_engine.cross_form_analysis(question, documents)
    
    def compare(self, doc1: FormDocument, doc2: FormDocument) -> Dict[str, Any]:
        """
        Compare two forms.
        
        Args:
            doc1: First form
            doc2: Second form
            
        Returns:
            Comparison results
        """
        common_fields = set(doc1.fields.keys()) & set(doc2.fields.keys())
        only_in_doc1 = set(doc1.fields.keys()) - set(doc2.fields.keys())
        only_in_doc2 = set(doc2.fields.keys()) - set(doc1.fields.keys())
        
        differences = {}
        for field in common_fields:
            if doc1.fields[field] != doc2.fields[field]:
                differences[field] = {
                    'doc1': doc1.fields[field],
                    'doc2': doc2.fields[field]
                }
        
        return {
            'common_fields': list(common_fields),
            'only_in_first': list(only_in_doc1),
            'only_in_second': list(only_in_doc2),
            'differences': differences,
            'same_schema': doc1.schema_type == doc2.schema_type
        }
    
    def export(self, document: FormDocument, format: str = 'json', 
               output_path: Optional[str] = None) -> str:
        """
        Export extracted data.
        
        Args:
            document: Form to export
            format: Output format ('json', 'csv', 'markdown')
            output_path: Optional output file path
            
        Returns:
            Exported data as string
        """
        if format == 'json':
            output = document.to_json()
        elif format == 'csv':
            import csv
            from io import StringIO
            buffer = StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['Field', 'Value'])
            for k, v in document.fields.items():
                writer.writerow([k, str(v)])
            output = buffer.getvalue()
        elif format == 'markdown':
            output = self._to_markdown(document)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(output)
        
        return output
    
    def _to_markdown(self, document: FormDocument) -> str:
        """Convert document to markdown format."""
        lines = [
            f"# Form Extraction Report",
            f"",
            f"**File**: {document.file_path}",
            f"**Type**: {document.file_type}",
            f"**Schema**: {document.schema_type or 'Unknown'}",
            f"**Confidence**: {document.extraction_confidence:.2%}",
            f"**Processed**: {document.processed_at}",
            f"",
            f"## Extracted Fields",
            f""
        ]
        
        for field, value in document.fields.items():
            lines.append(f"- **{field}**: {value}")
        
        if document.tables:
            lines.extend([f"", f"## Tables", f""])
            for i, table in enumerate(document.tables):
                lines.append(f"### Table {i+1}")
                if table:
                    # Header row
                    lines.append("| " + " | ".join(str(c) for c in table[0]) + " |")
                    lines.append("| " + " | ".join("---" for _ in table[0]) + " |")
                    # Data rows
                    for row in table[1:]:
                        lines.append("| " + " | ".join(str(c) for c in row) + " |")
                lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_confidence(self, fields: Dict, raw_text: str) -> float:
        """Calculate extraction confidence score."""
        if not raw_text:
            return 0.0
        
        # Base confidence from text quality
        text_quality = min(1.0, len(raw_text) / 500)
        
        # Boost for extracted fields
        field_boost = min(0.3, len(fields) * 0.03)
        
        # Penalize if mostly numbers/special chars (likely OCR noise)
        alpha_ratio = sum(c.isalpha() for c in raw_text) / max(1, len(raw_text))
        quality_factor = min(1.0, alpha_ratio * 2)
        
        confidence = (text_quality * 0.4 + field_boost + quality_factor * 0.3)
        return min(1.0, confidence)


def main():
    """Command-line interface for the Intelligent Form Agent."""
    parser = argparse.ArgumentParser(
        description="Intelligent Form Agent - Process, query, and analyze forms"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a form')
    process_parser.add_argument('--file', '-f', required=True, help='Path to form file')
    process_parser.add_argument('--output', '-o', help='Output file path')
    process_parser.add_argument('--format', default='json', 
                               choices=['json', 'csv', 'markdown'],
                               help='Output format')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Ask a question about a form')
    query_parser.add_argument('--file', '-f', required=True, help='Path to form file')
    query_parser.add_argument('--question', '-q', required=True, help='Question to ask')
    
    # Summarize command
    summary_parser = subparsers.add_parser('summarize', help='Summarize a form')
    summary_parser.add_argument('--file', '-f', required=True, help='Path to form file')
    summary_parser.add_argument('--style', default='bullet_points',
                               choices=['bullet_points', 'narrative'],
                               help='Summary style')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze multiple forms')
    analyze_parser.add_argument('--files', '-f', nargs='+', required=True,
                               help='Paths to form files')
    analyze_parser.add_argument('--question', '-q', required=True,
                               help='Analysis question')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    agent = IntelligentFormAgent()
    
    if args.command == 'process':
        document = agent.load_form(args.file)
        output = agent.export(document, args.format, args.output)
        print(output)
        
    elif args.command == 'query':
        document = agent.load_form(args.file)
        result = agent.ask(args.question, document)
        print(json.dumps(result.to_dict(), indent=2))
        
    elif args.command == 'summarize':
        document = agent.load_form(args.file)
        summary = agent.summarize(document)
        print(json.dumps(summary.to_dict(), indent=2))
        
    elif args.command == 'analyze':
        documents = agent.load_forms(args.files)
        result = agent.analyze(documents, args.question)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
