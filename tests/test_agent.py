"""
Test Suite for Intelligent Form Agent

Comprehensive tests for all agent components.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import IntelligentFormAgent, FormDocument, QueryResult, Summary
from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.text_extractor import TextExtractor
from src.processors.field_parser import FieldParser
from src.processors.table_parser import TableParser
from src.processors.schema_detector import SchemaDetector
from src.qa.qa_engine import QAEngine
from src.summarizer.summarizer import FormSummarizer
from src.utils.helpers import (
    detect_file_type, clean_text, mask_sensitive_data,
    format_currency, parse_date, chunk_text
)


class TestFieldParser:
    """Tests for the FieldParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = FieldParser()
    
    def test_parse_basic_fields(self):
        """Test parsing basic key-value fields."""
        text = """
        Name: John Doe
        Date: 01/15/2024
        Amount: $1,500.00
        """
        fields = self.parser.parse(text)
        
        assert 'Name' in fields
        assert fields['Name'] == 'John Doe'
        assert 'Date' in fields
        assert 'Amount' in fields
    
    def test_parse_email(self):
        """Test email extraction."""
        text = "Contact email: john.doe@example.com"
        fields = self.parser.parse(text)
        
        assert 'Email' in fields
        assert fields['Email'] == 'john.doe@example.com'
    
    def test_parse_phone(self):
        """Test phone number extraction."""
        text = "Phone: (555) 123-4567"
        fields = self.parser.parse(text)
        
        assert 'Phone' in fields
    
    def test_parse_ssn_masked(self):
        """Test SSN extraction and masking."""
        text = "SSN: 123-45-6789"
        fields = self.parser.parse(text)
        
        assert 'SSN' in fields
        assert fields['SSN'] == 'XXX-XX-6789'
    
    def test_parse_currency(self):
        """Test currency value extraction."""
        text = "Total: $1,234.56"
        fields = self.parser.parse(text)
        
        assert 'Total' in fields
        total = fields['Total']
        assert isinstance(total, dict)
        assert total['type'] == 'currency'
        assert total['value'] == 1234.56
    
    def test_parse_checkboxes(self):
        """Test checkbox extraction."""
        text = """
        [X] Option A
        [ ] Option B
        [X] Option C
        """
        fields = self.parser.parse(text)
        
        assert 'Selected Options' in fields
        assert 'Option A' in fields['Selected Options']
        assert 'Option C' in fields['Selected Options']


class TestTableParser:
    """Tests for the TableParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TableParser()
    
    def test_parse_simple_table(self):
        """Test parsing a simple table."""
        raw_table = [
            ['Name', 'Amount', 'Date'],
            ['Item 1', '$100', '01/01/2024'],
            ['Item 2', '$200', '01/02/2024']
        ]
        
        parsed = self.parser.parse([raw_table])
        
        assert len(parsed) == 1
        assert parsed[0].has_header == True
        assert parsed[0].headers == ['Name', 'Amount', 'Date']
        assert parsed[0].row_count == 2
    
    def test_normalize_table(self):
        """Test table normalization."""
        raw_table = [
            ['A', 'B', 'C'],
            ['1', '2'],  # Missing column
            ['3', '4', '5']
        ]
        
        normalized = self.parser._normalize_table(raw_table)
        
        assert all(len(row) == 3 for row in normalized)
    
    def test_to_dict_list(self):
        """Test conversion to dictionary list."""
        raw_table = [
            ['Name', 'Value'],
            ['Test', '100']
        ]
        
        parsed = self.parser.parse([raw_table])[0]
        dict_list = self.parser.to_dict_list(parsed)
        
        assert len(dict_list) == 1
        assert dict_list[0]['Name'] == 'Test'
        assert dict_list[0]['Value'] == '100'


class TestSchemaDetector:
    """Tests for the SchemaDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SchemaDetector()
    
    def test_detect_w2(self):
        """Test W-2 form detection."""
        text = """
        Wage and Tax Statement
        Form W-2
        Employee's Social Security Number
        Federal Income Tax Withheld
        Social Security Wages
        """
        
        schema = self.detector.detect(text)
        assert schema == 'w2'
    
    def test_detect_insurance_claim(self):
        """Test insurance claim detection."""
        text = """
        Insurance Claim Form
        Patient Information
        Date of Service
        Diagnosis Code ICD-10
        Procedure Code CPT
        Provider Name
        """
        
        schema = self.detector.detect(text)
        assert schema == 'insurance_claim'
    
    def test_detect_with_confidence(self):
        """Test detection with confidence scores."""
        text = "Form W-2 Wage and Tax Statement Employee SSN"
        
        match = self.detector.detect_with_confidence(text)
        
        assert match is not None
        assert match.schema_type == 'w2'
        assert match.confidence > 0.5
        assert len(match.matched_indicators) > 0
    
    def test_no_match(self):
        """Test when no schema matches."""
        text = "This is just some random text with no form indicators."
        
        schema = self.detector.detect(text)
        assert schema is None


class TestQAEngine:
    """Tests for the QAEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.qa = QAEngine()
        
        # Create a mock document
        self.mock_doc = FormDocument(
            file_path="test.pdf",
            file_type="pdf",
            raw_text="John Doe is the employee. The total amount is $5,000.",
            fields={
                'Employee Name': 'John Doe',
                'Total Amount': {'type': 'currency', 'value': 5000},
                'Date': '01/15/2024'
            },
            tables=[],
            metadata={}
        )
    
    def test_answer_what_question(self):
        """Test answering 'what' questions."""
        result = self.qa.answer("What is the employee name?", self.mock_doc)
        
        assert isinstance(result, QueryResult)
        assert 'John Doe' in result.answer
        assert result.confidence > 0.5
    
    def test_answer_quantity_question(self):
        """Test answering quantity questions."""
        result = self.qa.answer("How much is the total amount?", self.mock_doc)
        
        assert isinstance(result, QueryResult)
        assert '5000' in result.answer or '5,000' in result.answer
    
    def test_no_context_answer(self):
        """Test answer when no relevant context found."""
        empty_doc = FormDocument(
            file_path="empty.pdf",
            file_type="pdf",
            raw_text="",
            fields={},
            tables=[],
            metadata={}
        )
        
        result = self.qa.answer("What is the answer?", empty_doc)
        
        assert result.confidence < 0.5


class TestSummarizer:
    """Tests for the FormSummarizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.summarizer = FormSummarizer()
        
        self.mock_doc = FormDocument(
            file_path="test.pdf",
            file_type="pdf",
            raw_text="This is a W-2 form for John Doe.",
            fields={
                'Employee Name': 'John Doe',
                'Wages': {'type': 'currency', 'value': 50000},
                'Tax Withheld': {'type': 'currency', 'value': 7500}
            },
            tables=[],
            metadata={},
            schema_type='w2',
            extraction_confidence=0.85
        )
    
    def test_summarize_returns_summary(self):
        """Test that summarize returns a Summary object."""
        summary = self.summarizer.summarize(self.mock_doc)
        
        assert isinstance(summary, Summary)
        assert summary.form_type == 'w2'
        assert len(summary.key_information) > 0
    
    def test_bullet_style_summary(self):
        """Test bullet point style summary."""
        self.summarizer.style = 'bullet_points'
        summary = self.summarizer.summarize(self.mock_doc)
        
        assert 'KEY INFORMATION:' in summary.full_text
        assert '•' in summary.full_text
    
    def test_narrative_style_summary(self):
        """Test narrative style summary."""
        self.summarizer.style = 'narrative'
        summary = self.summarizer.summarize(self.mock_doc)
        
        assert isinstance(summary.full_text, str)


class TestHelpers:
    """Tests for utility helper functions."""
    
    def test_detect_file_type_by_extension(self):
        """Test file type detection by extension."""
        assert detect_file_type("test.pdf") == 'pdf'
        assert detect_file_type("image.png") == 'png'
        assert detect_file_type("data.json") == 'json'
        assert detect_file_type("doc.txt") == 'txt'
    
    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Hello   World  \n\n  Test  "
        cleaned = clean_text(dirty_text)
        
        assert '  ' not in cleaned or cleaned.count('  ') == 0
    
    def test_mask_ssn(self):
        """Test SSN masking."""
        text = "SSN: 123-45-6789"
        masked = mask_sensitive_data(text, mask_ssn=True)
        
        assert '123-45' not in masked
        assert '6789' in masked
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1234.56) == '$1,234.56'
        assert format_currency(1000000) == '$1,000,000.00'
    
    def test_parse_date(self):
        """Test date parsing."""
        assert parse_date("01/15/2024") == '2024-01-15'
        assert parse_date("2024-01-15") == '2024-01-15'
        assert parse_date("January 15, 2024") == '2024-01-15'
    
    def test_chunk_text(self):
        """Test text chunking."""
        text = "This is a test. " * 100
        chunks = chunk_text(text, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(c) <= 150 for c in chunks)  # Some overflow allowed


class TestIntelligentFormAgent:
    """Integration tests for the full agent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = IntelligentFormAgent()
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        assert self.agent is not None
        assert self.agent.pdf_extractor is not None
        assert self.agent.qa_engine is not None
        assert self.agent.summarizer is not None
    
    def test_load_text_form(self):
        """Test loading a text-based form."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("""
            Employee Information Form
            Name: Jane Smith
            Date of Birth: 03/20/1990
            Department: Engineering
            Salary: $75,000
            Start Date: 01/01/2024
            """)
            temp_path = f.name
        
        try:
            doc = self.agent.load_form(temp_path)
            
            assert isinstance(doc, FormDocument)
            assert doc.file_type == 'txt'
            assert len(doc.fields) > 0
            assert 'Name' in doc.fields
        finally:
            os.unlink(temp_path)
    
    def test_ask_question(self):
        """Test asking a question about a form."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("Name: John Doe\nAmount: $1,000")
            temp_path = f.name
        
        try:
            doc = self.agent.load_form(temp_path)
            result = self.agent.ask("What is the name?", doc)
            
            assert isinstance(result, QueryResult)
            assert 'John' in result.answer or result.answer != ""
        finally:
            os.unlink(temp_path)
    
    def test_summarize_form(self):
        """Test summarizing a form."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("""
            W-2 Wage and Tax Statement
            Employee Name: Alice Johnson
            Wages: $80,000
            Federal Tax Withheld: $12,000
            """)
            temp_path = f.name
        
        try:
            doc = self.agent.load_form(temp_path)
            summary = self.agent.summarize(doc)
            
            assert isinstance(summary, Summary)
            assert len(summary.full_text) > 0
        finally:
            os.unlink(temp_path)
    
    def test_export_json(self):
        """Test exporting form data to JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("Name: Test\nValue: 100")
            temp_path = f.name
        
        try:
            doc = self.agent.load_form(temp_path)
            json_output = self.agent.export(doc, 'json')
            
            # Should be valid JSON
            parsed = json.loads(json_output)
            assert 'fields' in parsed
            assert 'file_path' in parsed
        finally:
            os.unlink(temp_path)
    
    def test_compare_forms(self):
        """Test comparing two forms."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f1:
            f1.write("Name: John\nAmount: 100")
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f2:
            f2.write("Name: Jane\nAmount: 200\nDate: 2024-01-01")
            path2 = f2.name
        
        try:
            doc1 = self.agent.load_form(path1)
            doc2 = self.agent.load_form(path2)
            
            comparison = self.agent.compare(doc1, doc2)
            
            assert 'common_fields' in comparison
            assert 'differences' in comparison
        finally:
            os.unlink(path1)
            os.unlink(path2)


class TestExampleRuns:
    """
    Demonstration tests showing example usage scenarios.
    These serve as both tests and documentation.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = IntelligentFormAgent()
    
    def test_example_single_form_qa(self):
        """
        Example 1: Answering a question from a single form.
        
        Scenario: Process a W-2 tax form and ask about the employee's wages.
        """
        # Create a sample W-2 form
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("""
            Form W-2 Wage and Tax Statement
            Employee Name: John Smith
            Employee SSN: 123-45-6789
            Employer Name: Acme Corporation
            Wages: $75,000.00
            Federal Tax Withheld: $11,250.00
            """)
            temp_path = f.name
        
        try:
            # Load the form
            doc = self.agent.load_form(temp_path)
            
            # Ask a question
            result = self.agent.ask("What is the employee's name?", doc)
            
            # Verify we got a reasonable answer
            assert 'John' in result.answer or 'Smith' in result.answer
            assert result.confidence > 0.3
            
            print(f"Question: What is the employee's name?")
            print(f"Answer: {result.answer}")
            print(f"Confidence: {result.confidence:.1%}")
            
        finally:
            os.unlink(temp_path)
    
    def test_example_form_summary(self):
        """
        Example 2: Generating a summary of one form.
        
        Scenario: Summarize an insurance claim form.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                          delete=False) as f:
            f.write("""
            Health Insurance Claim Form
            Patient Name: Jane Doe
            Date of Birth: 05/15/1985
            Policy Number: BCBS-2024-789012
            Provider: City General Hospital
            Date of Service: 01/15/2024
            Diagnosis Code: Z00.00
            Total Charges: $450.00
            Claim Status: Pending
            """)
            temp_path = f.name
        
        try:
            doc = self.agent.load_form(temp_path)
            summary = self.agent.summarize(doc)
            
            # Verify summary contains key information
            assert len(summary.full_text) > 50
            assert len(summary.key_information) > 0
            
            print(f"Summary:\n{summary.full_text}")
            
        finally:
            os.unlink(temp_path)
    
    def test_example_cross_form_analysis(self):
        """
        Example 3: Cross-form holistic analysis.
        
        Scenario: Analyze multiple employee forms to find patterns.
        """
        temp_files = []
        
        try:
            # Create multiple forms
            employees = [
                ("Alice", "Engineering", "110000"),
                ("Bob", "Marketing", "80000"),
                ("Carol", "Sales", "65000")
            ]
            
            for name, dept, salary in employees:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                                  delete=False) as f:
                    f.write(f"""
                    Employee Onboarding Form
                    Full Name: {name}
                    Department: {dept}
                    Annual Salary: ${salary}
                    Start Date: 02/01/2024
                    """)
                    temp_files.append(f.name)
            
            # Load all forms
            docs = self.agent.load_forms(temp_files)
            
            # Cross-form analysis
            analysis = self.agent.analyze(
                docs, 
                "What is the average salary across departments?"
            )
            
            # Verify analysis results
            assert analysis['total_documents'] == 3
            assert len(analysis.get('insights', [])) > 0
            
            print(f"Analysis of {analysis['total_documents']} forms:")
            print(f"Insights: {analysis.get('insights', [])}")
            
        finally:
            for path in temp_files:
                if os.path.exists(path):
                    os.unlink(path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
