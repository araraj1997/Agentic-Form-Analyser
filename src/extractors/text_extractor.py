"""
Text Extractor Module

Handles extraction from plain text and structured text files.
"""

import json
import re
from typing import Tuple, List, Dict, Any
from pathlib import Path


class TextExtractor:
    """
    Extracts content from text-based files.
    
    Supports:
    - Plain text (.txt)
    - JSON (.json)
    - CSV (.csv)
    - Markdown (.md)
    - HTML (.html) - basic extraction
    """
    
    def __init__(self):
        """Initialize text extractor."""
        pass
    
    def extract(self, file_path: str) -> Tuple[str, List[List[List[str]]], Dict[str, Any]]:
        """
        Extract content from a text-based file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (raw_text, tables, metadata)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        metadata = {
            'file_path': str(file_path),
            'file_type': suffix[1:] if suffix else 'unknown',
            'file_size': path.stat().st_size if path.exists() else 0
        }
        
        raw_text = ""
        tables = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if suffix == '.json':
                raw_text, tables = self._extract_json(content)
            elif suffix == '.csv':
                raw_text, tables = self._extract_csv(content)
            elif suffix in ['.html', '.htm']:
                raw_text = self._extract_html(content)
            elif suffix == '.md':
                raw_text, tables = self._extract_markdown(content)
            else:
                raw_text = content
            
            metadata['char_count'] = len(content)
            metadata['line_count'] = content.count('\n') + 1
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    raw_text = f.read()
                metadata['encoding'] = 'latin-1'
            except Exception as e:
                metadata['error'] = str(e)
        except Exception as e:
            metadata['error'] = str(e)
        
        return raw_text.strip(), tables, metadata
    
    def _extract_json(self, content: str) -> Tuple[str, List]:
        """Extract content from JSON."""
        try:
            data = json.loads(content)
            # Flatten JSON to text representation
            text = self._json_to_text(data)
            tables = self._json_to_tables(data)
            return text, tables
        except json.JSONDecodeError:
            return content, []
    
    def _json_to_text(self, data: Any, prefix: str = "") -> str:
        """Convert JSON data to readable text."""
        lines = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_key = f"{prefix}{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    lines.append(f"{current_key}:")
                    lines.append(self._json_to_text(value, "  "))
                else:
                    lines.append(f"{current_key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.append(self._json_to_text(item, prefix + "  "))
                else:
                    lines.append(f"{prefix}[{i}]: {item}")
        else:
            lines.append(f"{prefix}{data}")
        
        return "\n".join(lines)
    
    def _json_to_tables(self, data: Any) -> List[List[List[str]]]:
        """Extract table-like structures from JSON."""
        tables = []
        
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # List of objects - convert to table
                headers = list(data[0].keys())
                table = [headers]
                for item in data:
                    row = [str(item.get(h, '')) for h in headers]
                    table.append(row)
                tables.append(table)
        elif isinstance(data, dict):
            # Look for arrays within the dict
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    sub_tables = self._json_to_tables(value)
                    tables.extend(sub_tables)
        
        return tables
    
    def _extract_csv(self, content: str) -> Tuple[str, List]:
        """Extract content from CSV."""
        import csv
        from io import StringIO
        
        tables = []
        try:
            reader = csv.reader(StringIO(content))
            table = [row for row in reader]
            if table:
                tables.append(table)
        except Exception:
            pass
        
        return content, tables
    
    def _extract_html(self, content: str) -> str:
        """Extract text from HTML, removing tags."""
        # Remove script and style elements
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Decode common HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&quot;', '"')
        
        return content.strip()
    
    def _extract_markdown(self, content: str) -> Tuple[str, List]:
        """Extract content from Markdown."""
        tables = []
        
        # Extract markdown tables
        table_pattern = r'\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+'
        matches = re.findall(table_pattern, content)
        
        for match in matches:
            rows = match.strip().split('\n')
            table = []
            for row in rows:
                if '---' in row:  # Skip separator row
                    continue
                cells = [cell.strip() for cell in row.split('|')[1:-1]]
                if cells:
                    table.append(cells)
            if table:
                tables.append(table)
        
        return content, tables
    
    def extract_text_only(self, file_path: str) -> str:
        """
        Extract only text from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text
        """
        text, _, _ = self.extract(file_path)
        return text
