"""
Utility Helpers Module

Common utility functions for the Intelligent Form Agent.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


def detect_file_type(file_path: str) -> str:
    """
    Detect the type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type string (pdf, png, jpg, txt, etc.)
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    # Map extensions to types
    type_map = {
        '.pdf': 'pdf',
        '.png': 'png',
        '.jpg': 'jpg',
        '.jpeg': 'jpg',
        '.tiff': 'tiff',
        '.tif': 'tiff',
        '.bmp': 'bmp',
        '.gif': 'gif',
        '.txt': 'txt',
        '.text': 'txt',
        '.json': 'json',
        '.csv': 'csv',
        '.html': 'html',
        '.htm': 'html',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.xml': 'xml'
    }
    
    file_type = type_map.get(extension)
    
    if file_type:
        return file_type
    
    # Try to detect by magic bytes if extension unknown
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        # PDF
        if header.startswith(b'%PDF'):
            return 'pdf'
        
        # PNG
        if header.startswith(b'\x89PNG'):
            return 'png'
        
        # JPEG
        if header.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        
        # GIF
        if header.startswith(b'GIF'):
            return 'gif'
        
        # TIFF
        if header.startswith(b'II') or header.startswith(b'MM'):
            return 'tiff'
        
    except Exception:
        pass
    
    # Default to text
    return 'txt'


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception:
        return {}


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration
        
    Returns:
        True if successful
    """
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception:
        return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters except newlines
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text.strip()


def mask_sensitive_data(text: str, mask_ssn: bool = True, 
                        mask_credit_card: bool = True,
                        mask_email: bool = False) -> str:
    """
    Mask sensitive data in text.
    
    Args:
        text: Input text
        mask_ssn: Whether to mask SSN
        mask_credit_card: Whether to mask credit cards
        mask_email: Whether to mask email addresses
        
    Returns:
        Text with sensitive data masked
    """
    if not text:
        return text
    
    # Mask SSN
    if mask_ssn:
        # Pattern: XXX-XX-XXXX or XXXXXXXXX
        text = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', 
                      lambda m: 'XXX-XX-' + m.group()[-4:], text)
    
    # Mask credit card
    if mask_credit_card:
        # Pattern: 16 digits with optional separators
        text = re.sub(r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                      lambda m: '**** **** **** ' + m.group()[-4:], text)
    
    # Mask email
    if mask_email:
        def mask_email_fn(match):
            email = match.group()
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                masked = username[0] + '***' + '@' + parts[1]
                return masked
            return email
        
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                      mask_email_fn, text)
    
    return text


def format_currency(value: float, currency: str = 'USD') -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: Numeric value
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}
    symbol = symbols.get(currency, '$')
    
    return f"{symbol}{value:,.2f}"


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse and normalize a date string.
    
    Args:
        date_str: Input date string
        
    Returns:
        Normalized date string (YYYY-MM-DD) or None
    """
    from datetime import datetime
    
    formats = [
        '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
        '%Y-%m-%d', '%Y/%m/%d',
        '%d/%m/%Y', '%d-%m-%Y',
        '%B %d, %Y', '%b %d, %Y',
        '%d %B %Y', '%d %b %Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def chunk_text(text: str, chunk_size: int = 500, 
               overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end in last 20% of chunk
            search_start = int(end - chunk_size * 0.2)
            sentence_end = text.rfind('.', search_start, end)
            
            if sentence_end > search_start:
                end = sentence_end + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity using word overlap.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    # Remove stop words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
                  'into', 'through', 'during', 'before', 'after', 'above', 'below',
                  'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
                  'under', 'again', 'further', 'then', 'once', 'and', 'but', 'or',
                  'nor', 'so', 'yet', 'both', 'each', 'few', 'more', 'most',
                  'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same',
                  'than', 'too', 'very', 'just', 'also'}
    
    words1 -= stop_words
    words2 -= stop_words
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def extract_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extract all numbers from text with context.
    
    Args:
        text: Input text
        
    Returns:
        List of dictionaries with number info
    """
    numbers = []
    
    # Currency pattern
    currency_pattern = r'\$[\d,]+(?:\.\d{2})?'
    for match in re.finditer(currency_pattern, text):
        value = float(match.group().replace('$', '').replace(',', ''))
        numbers.append({
            'value': value,
            'type': 'currency',
            'raw': match.group(),
            'position': match.start()
        })
    
    # Percentage pattern
    percent_pattern = r'\d+(?:\.\d+)?%'
    for match in re.finditer(percent_pattern, text):
        value = float(match.group().replace('%', ''))
        numbers.append({
            'value': value,
            'type': 'percentage',
            'raw': match.group(),
            'position': match.start()
        })
    
    # Plain numbers (not already matched)
    plain_pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
    for match in re.finditer(plain_pattern, text):
        # Skip if this position was already matched
        pos = match.start()
        if any(n['position'] <= pos < n['position'] + len(n['raw']) for n in numbers):
            continue
        
        value = float(match.group().replace(',', ''))
        numbers.append({
            'value': value,
            'type': 'number',
            'raw': match.group(),
            'position': match.start()
        })
    
    return sorted(numbers, key=lambda x: x['position'])


def create_output_filename(input_path: str, suffix: str = '_output', 
                          extension: str = None) -> str:
    """
    Create an output filename based on input filename.
    
    Args:
        input_path: Original input file path
        suffix: Suffix to add
        extension: New extension (or keep original)
        
    Returns:
        Output filename
    """
    path = Path(input_path)
    stem = path.stem
    ext = extension or path.suffix
    
    return f"{stem}{suffix}{ext}"
