"""
PDF Extractor Module

Handles extraction of text, tables, and metadata from PDF documents.
"""

import os
from typing import Tuple, List, Dict, Any
from pathlib import Path


class PDFExtractor:
    """
    Extracts content from PDF files using pdfplumber.
    
    Supports:
    - Text extraction with layout preservation
    - Table extraction
    - Metadata extraction
    - Multi-page handling
    """
    
    def __init__(self, ocr_fallback: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            ocr_fallback: Whether to use OCR for scanned PDFs
        """
        self.ocr_fallback = ocr_fallback
        self._pdfplumber = None
        self._pytesseract = None
        self._pdf2image = None
    
    def _lazy_import_pdfplumber(self):
        """Lazy import pdfplumber."""
        if self._pdfplumber is None:
            try:
                import pdfplumber
                self._pdfplumber = pdfplumber
            except ImportError:
                raise ImportError("pdfplumber is required. Install with: pip install pdfplumber")
        return self._pdfplumber
    
    def _lazy_import_ocr(self):
        """Lazy import OCR dependencies."""
        if self._pytesseract is None:
            try:
                import pytesseract
                from pdf2image import convert_from_path
                self._pytesseract = pytesseract
                self._pdf2image = convert_from_path
            except ImportError:
                return None, None
        return self._pytesseract, self._pdf2image
    
    def extract(self, file_path: str) -> Tuple[str, List[List[List[str]]], Dict[str, Any]]:
        """
        Extract content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (raw_text, tables, metadata)
        """
        pdfplumber = self._lazy_import_pdfplumber()
        
        raw_text = ""
        tables = []
        metadata = {}
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                metadata = {
                    'pages': len(pdf.pages),
                    'pdf_info': pdf.metadata or {}
                }
                
                # Extract text and tables from each page
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text() or ""
                    if page_text:
                        raw_text += f"\n--- Page {page_num + 1} ---\n"
                        raw_text += page_text
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            if table and len(table) > 0:
                                # Clean table data
                                cleaned_table = []
                                for row in table:
                                    cleaned_row = [
                                        str(cell).strip() if cell else "" 
                                        for cell in row
                                    ]
                                    cleaned_table.append(cleaned_row)
                                tables.append(cleaned_table)
                
                # If no text extracted, try OCR
                if not raw_text.strip() and self.ocr_fallback:
                    raw_text = self._ocr_extract(file_path)
                    metadata['ocr_used'] = True
                
        except Exception as e:
            metadata['error'] = str(e)
            # Try OCR as fallback
            if self.ocr_fallback:
                try:
                    raw_text = self._ocr_extract(file_path)
                    metadata['ocr_used'] = True
                except Exception as ocr_e:
                    metadata['ocr_error'] = str(ocr_e)
        
        return raw_text.strip(), tables, metadata
    
    def _ocr_extract(self, file_path: str) -> str:
        """
        Extract text using OCR for scanned PDFs.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        pytesseract, convert_from_path = self._lazy_import_ocr()
        
        if pytesseract is None:
            return ""
        
        text = ""
        try:
            images = convert_from_path(file_path)
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                if page_text:
                    text += f"\n--- Page {i + 1} (OCR) ---\n"
                    text += page_text
        except Exception:
            pass
        
        return text
    
    def extract_text_only(self, file_path: str) -> str:
        """
        Extract only text from a PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        text, _, _ = self.extract(file_path)
        return text
    
    def extract_tables_only(self, file_path: str) -> List[List[List[str]]]:
        """
        Extract only tables from a PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of tables (each table is a list of rows)
        """
        _, tables, _ = self.extract(file_path)
        return tables
