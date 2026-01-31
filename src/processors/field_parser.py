"""
Field Parser Module

Parses and extracts key-value fields from form text.
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class FieldMatch:
    """Represents a matched field."""
    name: str
    value: str
    confidence: float
    position: Tuple[int, int]  # start, end positions


class FieldParser:
    """
    Parses form text to extract structured key-value fields.
    
    Supports various field patterns:
    - Label: Value
    - Label - Value
    - Label = Value
    - Label [Value]
    - Checkbox patterns
    - Date patterns
    - Currency patterns
    """
    
    def __init__(self):
        """Initialize field parser with patterns."""
        self.patterns = self._build_patterns()
        self.date_patterns = self._build_date_patterns()
        self.currency_pattern = re.compile(
            r'\$[\d,]+(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|dollars?)'
        )
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        self.phone_pattern = re.compile(
            r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        )
        self.ssn_pattern = re.compile(
            r'\d{3}[-\s]?\d{2}[-\s]?\d{4}'
        )
    
    def _build_patterns(self) -> List[re.Pattern]:
        """Build regex patterns for field extraction."""
        return [
            # Pattern: Label: Value
            re.compile(r'^([A-Za-z][A-Za-z0-9\s\-_/()]+?):\s*(.+)$', re.MULTILINE),
            # Pattern: Label - Value (with dash separator)
            re.compile(r'^([A-Za-z][A-Za-z0-9\s_]+?)\s*[-–—]\s*(.+)$', re.MULTILINE),
            # Pattern: Label = Value
            re.compile(r'^([A-Za-z][A-Za-z0-9\s_]+?)\s*=\s*(.+)$', re.MULTILINE),
            # Pattern: LABEL (all caps) followed by value
            re.compile(r'^([A-Z][A-Z0-9\s]+):\s*(.+)$', re.MULTILINE),
            # Pattern: Numbered fields (1. Label: Value)
            re.compile(r'^\d+\.\s*([A-Za-z][A-Za-z0-9\s]+?):\s*(.+)$', re.MULTILINE),
            # Pattern: Boxed fields [X] Label or [ ] Label
            re.compile(r'\[([xX✓✔]|\s)\]\s*(.+)$', re.MULTILINE),
        ]
    
    def _build_date_patterns(self) -> List[re.Pattern]:
        """Build date recognition patterns."""
        return [
            # MM/DD/YYYY or MM-DD-YYYY
            re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
            # YYYY-MM-DD
            re.compile(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'),
            # Month DD, YYYY
            re.compile(
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
                r'\s+\d{1,2},?\s+\d{4}',
                re.IGNORECASE
            ),
            # DD Month YYYY
            re.compile(
                r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
                r'\s+\d{4}',
                re.IGNORECASE
            ),
        ]
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse text to extract fields.
        
        Args:
            text: Raw text from form
            
        Returns:
            Dictionary of field names to values
        """
        fields = {}
        
        if not text:
            return fields
        
        # Extract fields using patterns
        for pattern in self.patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 2:
                    name = self._normalize_field_name(match[0])
                    value = match[1].strip()
                    
                    # Skip if value is too long (likely not a field)
                    if len(value) > 500:
                        continue
                    
                    # Skip if name is too generic
                    if name.lower() in ['a', 'b', 'c', 'i', 'ii', 'iii', 'the', 'and', 'or']:
                        continue
                    
                    if name and value:
                        # Process value based on type
                        processed_value = self._process_value(value)
                        fields[name] = processed_value
        
        # Extract special fields
        fields.update(self._extract_special_fields(text))
        
        # Extract checkbox fields
        fields.update(self._extract_checkboxes(text))
        
        return fields
    
    def _normalize_field_name(self, name: str) -> str:
        """Normalize field name for consistency."""
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Title case
        name = name.strip()
        return name
    
    def _process_value(self, value: str) -> Any:
        """Process and type-convert value."""
        value = value.strip()
        
        # Check for currency
        if self.currency_pattern.match(value):
            # Extract numeric value
            numeric = re.sub(r'[^\d.]', '', value)
            try:
                return {'type': 'currency', 'value': float(numeric), 'raw': value}
            except ValueError:
                pass
        
        # Check for date
        for pattern in self.date_patterns:
            if pattern.match(value):
                return {'type': 'date', 'value': value}
        
        # Check for boolean
        if value.lower() in ['yes', 'no', 'true', 'false', 'y', 'n']:
            return value.lower() in ['yes', 'true', 'y']
        
        # Check for number
        try:
            if '.' in value:
                return float(value.replace(',', ''))
            elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value.replace(',', ''))
        except ValueError:
            pass
        
        return value
    
    def _extract_special_fields(self, text: str) -> Dict[str, Any]:
        """Extract special field types."""
        fields = {}
        
        # Extract emails
        emails = self.email_pattern.findall(text)
        if emails:
            if len(emails) == 1:
                fields['Email'] = emails[0]
            else:
                for i, email in enumerate(emails, 1):
                    fields[f'Email {i}'] = email
        
        # Extract phone numbers
        phones = self.phone_pattern.findall(text)
        if phones:
            if len(phones) == 1:
                fields['Phone'] = phones[0]
            else:
                for i, phone in enumerate(phones, 1):
                    fields[f'Phone {i}'] = phone
        
        # Extract SSN (masked)
        ssns = self.ssn_pattern.findall(text)
        if ssns:
            # Mask for privacy
            for i, ssn in enumerate(ssns):
                masked = 'XXX-XX-' + ssn[-4:]
                key = 'SSN' if len(ssns) == 1 else f'SSN {i+1}'
                fields[key] = masked
        
        # Extract dates with context
        for pattern in self.date_patterns:
            for match in pattern.finditer(text):
                # Look for context before the date
                start = max(0, match.start() - 50)
                context = text[start:match.start()].strip()
                
                # Try to find a label
                label_match = re.search(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)\s*[:\-]?\s*$', context)
                if label_match:
                    label = label_match.group(1).strip()
                    if label.lower() not in ['on', 'of', 'the', 'at', 'by']:
                        fields[f'{label} Date'] = match.group()
        
        return fields
    
    def _extract_checkboxes(self, text: str) -> Dict[str, Any]:
        """Extract checkbox/selection fields."""
        fields = {}
        
        # Pattern for checked/unchecked boxes
        checkbox_patterns = [
            (r'\[([xX✓✔])\]\s*(.+?)(?:\n|$)', True),
            (r'\[\s*\]\s*(.+?)(?:\n|$)', False),
            (r'☑\s*(.+?)(?:\n|$)', True),
            (r'☐\s*(.+?)(?:\n|$)', False),
            (r'\(([xX✓✔])\)\s*(.+?)(?:\n|$)', True),
            (r'\(\s*\)\s*(.+?)(?:\n|$)', False),
        ]
        
        checked_items = []
        unchecked_items = []
        
        for pattern, is_checked in checkbox_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    item = match[-1].strip()
                else:
                    item = match.strip()
                
                if item and len(item) < 100:  # Reasonable length
                    if is_checked:
                        checked_items.append(item)
                    else:
                        unchecked_items.append(item)
        
        if checked_items:
            fields['Selected Options'] = checked_items
        if unchecked_items:
            fields['Unselected Options'] = unchecked_items
        
        return fields
    
    def parse_with_confidence(self, text: str) -> List[FieldMatch]:
        """
        Parse text and return fields with confidence scores.
        
        Args:
            text: Raw text from form
            
        Returns:
            List of FieldMatch objects
        """
        results = []
        
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                if len(match.groups()) >= 2:
                    name = self._normalize_field_name(match.group(1))
                    value = match.group(2).strip()
                    
                    # Calculate confidence based on pattern match quality
                    confidence = self._calculate_confidence(name, value)
                    
                    if confidence > 0.3:
                        results.append(FieldMatch(
                            name=name,
                            value=value,
                            confidence=confidence,
                            position=(match.start(), match.end())
                        ))
        
        return sorted(results, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_confidence(self, name: str, value: str) -> float:
        """Calculate confidence score for a field match."""
        confidence = 0.5  # Base confidence
        
        # Boost for reasonable name length
        if 2 < len(name) < 50:
            confidence += 0.1
        
        # Boost for reasonable value length
        if 1 < len(value) < 200:
            confidence += 0.1
        
        # Boost for common field name patterns
        common_fields = [
            'name', 'date', 'address', 'phone', 'email', 'ssn', 'dob',
            'number', 'amount', 'total', 'id', 'signature', 'account'
        ]
        if any(cf in name.lower() for cf in common_fields):
            confidence += 0.2
        
        # Penalize very long values
        if len(value) > 200:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
