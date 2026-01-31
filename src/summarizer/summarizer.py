"""
Form Summarizer Module

Generates intelligent summaries of form documents.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


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


class FormSummarizer:
    """
    Generates summaries of form documents.
    
    Features:
    - Key information extraction
    - Highlight generation
    - Multiple summary styles (bullet points, narrative)
    - Schema-aware summarization
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize summarizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.max_length = self.config.get('max_length', 500)
        self.min_length = self.config.get('min_length', 100)
        self.style = self.config.get('style', 'bullet_points')
        
        # Key field priorities for different form types
        self.priority_fields = {
            'tax': ['name', 'ssn', 'wages', 'income', 'tax', 'withheld', 'ein', 'employer'],
            'medical': ['patient', 'date', 'diagnosis', 'provider', 'amount', 'policy', 'claim'],
            'employment': ['name', 'position', 'salary', 'department', 'start', 'manager'],
            'financial': ['name', 'amount', 'loan', 'income', 'assets', 'account'],
            'legal': ['parties', 'date', 'term', 'amount', 'effective'],
            'default': ['name', 'date', 'amount', 'total', 'number', 'id']
        }
    
    def summarize(self, document) -> Summary:
        """
        Generate a summary of a form document.
        
        Args:
            document: FormDocument object
            
        Returns:
            Summary object
        """
        # Determine form type
        form_type = document.schema_type or 'unknown'
        category = self._get_category(form_type)
        
        # Extract key information
        key_info = self._extract_key_information(document, category)
        
        # Generate highlights
        highlights = self._generate_highlights(document, key_info)
        
        # Identify notable items
        notable = self._identify_notable_items(document)
        
        # Generate full text summary
        if self.style == 'bullet_points':
            full_text = self._generate_bullet_summary(form_type, key_info, highlights, notable)
        else:
            full_text = self._generate_narrative_summary(form_type, key_info, highlights, notable)
        
        return Summary(
            form_type=form_type,
            key_information=key_info,
            highlights=highlights,
            notable_items=notable,
            full_text=full_text
        )
    
    def _get_category(self, form_type: str) -> str:
        """Get the category for a form type."""
        categories = {
            'w2': 'tax', 'w4': 'tax', '1099': 'tax', '1040': 'tax',
            'insurance_claim': 'medical', 'medical_intake': 'medical',
            'job_application': 'employment', 'onboarding': 'employment', 'i9': 'employment',
            'loan_application': 'financial', 'bank_account': 'financial',
            'contract': 'legal', 'power_of_attorney': 'legal'
        }
        return categories.get(form_type, 'default')
    
    def _extract_key_information(self, document, category: str) -> Dict[str, Any]:
        """Extract key information based on form category."""
        key_info = {}
        priority = self.priority_fields.get(category, self.priority_fields['default'])
        
        # Sort fields by priority
        for field, value in document.fields.items():
            field_lower = field.lower()
            
            # Check if this is a priority field
            is_priority = any(p in field_lower for p in priority)
            
            if is_priority:
                key_info[field] = value
        
        # Also include any fields with important-looking values
        for field, value in document.fields.items():
            if field in key_info:
                continue
            
            # Include if it's a monetary value
            if isinstance(value, dict) and value.get('type') == 'currency':
                key_info[field] = value
            # Include if it's a date
            elif isinstance(value, dict) and value.get('type') == 'date':
                key_info[field] = value
            # Include if field name suggests importance
            elif any(w in field.lower() for w in ['total', 'amount', 'id', 'number']):
                key_info[field] = value
        
        # Limit to most important fields
        if len(key_info) > 10:
            # Prioritize by field name match to priority list
            scored = []
            for field, value in key_info.items():
                score = sum(1 for p in priority if p in field.lower())
                scored.append((field, value, score))
            
            scored.sort(key=lambda x: x[2], reverse=True)
            key_info = {f: v for f, v, _ in scored[:10]}
        
        return key_info
    
    def _generate_highlights(self, document, key_info: Dict) -> List[str]:
        """Generate highlight statements from key information."""
        highlights = []
        
        # Name/identity highlight
        name_fields = ['name', 'applicant', 'employee', 'patient', 'customer']
        for field, value in key_info.items():
            if any(n in field.lower() for n in name_fields):
                highlights.append(f"{field}: {value}")
                break
        
        # ID/Number highlight
        id_fields = ['id', 'number', 'ssn', 'ein', 'policy', 'account']
        for field, value in key_info.items():
            if any(i in field.lower() for i in id_fields):
                # Mask sensitive numbers
                val_str = str(value)
                if 'ssn' in field.lower() and len(val_str) >= 4:
                    val_str = f"XXX-XX-{val_str[-4:]}"
                highlights.append(f"{field}: {val_str}")
                break
        
        # Date highlight
        for field, value in key_info.items():
            if 'date' in field.lower():
                if isinstance(value, dict):
                    highlights.append(f"{field}: {value.get('value', value)}")
                else:
                    highlights.append(f"{field}: {value}")
                break
        
        # Amount/Total highlight
        amount_fields = ['total', 'amount', 'wage', 'salary', 'income', 'payment']
        for field, value in key_info.items():
            if any(a in field.lower() for a in amount_fields):
                if isinstance(value, dict) and 'value' in value:
                    highlights.append(f"{field}: ${value['value']:,.2f}")
                elif isinstance(value, (int, float)):
                    highlights.append(f"{field}: ${value:,.2f}")
                else:
                    highlights.append(f"{field}: {value}")
                break
        
        return highlights
    
    def _identify_notable_items(self, document) -> List[str]:
        """Identify notable items in the document."""
        notable = []
        
        # Check for tables
        if document.tables:
            notable.append(f"Contains {len(document.tables)} table(s)")
        
        # Check for selected options (checkboxes)
        if 'Selected Options' in document.fields:
            options = document.fields['Selected Options']
            if isinstance(options, list) and options:
                notable.append(f"Selected: {', '.join(options[:3])}")
        
        # Check extraction confidence
        if document.extraction_confidence < 0.5:
            notable.append("Low extraction confidence - manual review recommended")
        
        # Check for schema match
        if document.schema_type:
            notable.append(f"Identified as: {document.schema_type.replace('_', ' ').title()}")
        
        # Look for specific patterns in text
        text_lower = document.raw_text.lower() if document.raw_text else ""
        
        if 'signature' in text_lower:
            notable.append("Contains signature field")
        
        if 'deadline' in text_lower or 'due date' in text_lower:
            notable.append("Has deadline/due date")
        
        if 'required' in text_lower:
            notable.append("Has required fields")
        
        return notable[:5]  # Limit to 5 notable items
    
    def _generate_bullet_summary(self, form_type: str, key_info: Dict,
                                  highlights: List[str], notable: List[str]) -> str:
        """Generate bullet-point style summary."""
        lines = []
        
        # Header
        form_title = form_type.replace('_', ' ').title() if form_type else 'Form'
        lines.append(f"SUMMARY: {form_title}")
        lines.append("")
        
        # Key Information
        if highlights:
            lines.append("KEY INFORMATION:")
            for h in highlights:
                lines.append(f"• {h}")
            lines.append("")
        
        # Additional Details
        if key_info:
            other_info = {k: v for k, v in key_info.items() 
                         if not any(k in h for h in highlights)}
            
            if other_info:
                lines.append("ADDITIONAL DETAILS:")
                for field, value in list(other_info.items())[:5]:
                    if isinstance(value, dict):
                        value = value.get('value', value.get('raw', str(value)))
                    lines.append(f"• {field}: {value}")
                lines.append("")
        
        # Notable Items
        if notable:
            lines.append("NOTABLE ITEMS:")
            for n in notable:
                lines.append(f"- {n}")
        
        return "\n".join(lines)
    
    def _generate_narrative_summary(self, form_type: str, key_info: Dict,
                                     highlights: List[str], notable: List[str]) -> str:
        """Generate narrative style summary."""
        parts = []
        
        # Opening
        form_title = form_type.replace('_', ' ').title() if form_type else 'document'
        parts.append(f"This {form_title} contains the following information.")
        
        # Key details as narrative
        if highlights:
            details = []
            for h in highlights:
                if ':' in h:
                    parts.append(f"The {h.split(':')[0].lower().strip()} is {h.split(':')[1].strip()}.")
        
        # Additional context
        if notable:
            parts.append(f"Additionally, {notable[0].lower()}.")
            if len(notable) > 1:
                parts.append(f"Note that {notable[1].lower()}.")
        
        return " ".join(parts)
    
    def summarize_multiple(self, documents: List) -> str:
        """
        Generate a combined summary of multiple documents.
        
        Args:
            documents: List of FormDocument objects
            
        Returns:
            Combined summary text
        """
        lines = []
        lines.append(f"MULTI-FORM SUMMARY ({len(documents)} forms)")
        lines.append("=" * 40)
        lines.append("")
        
        # Group by form type
        by_type = {}
        for doc in documents:
            form_type = doc.schema_type or 'unknown'
            if form_type not in by_type:
                by_type[form_type] = []
            by_type[form_type].append(doc)
        
        lines.append(f"Form Types: {', '.join(by_type.keys())}")
        lines.append("")
        
        # Individual summaries
        for i, doc in enumerate(documents, 1):
            summary = self.summarize(doc)
            lines.append(f"--- Form {i}: {doc.file_path} ---")
            
            # Compact version
            if summary.highlights:
                for h in summary.highlights[:3]:
                    lines.append(f"  • {h}")
            
            lines.append("")
        
        # Cross-form insights
        lines.append("CROSS-FORM INSIGHTS:")
        
        # Find common fields
        all_fields = [set(doc.fields.keys()) for doc in documents]
        if all_fields:
            common = set.intersection(*all_fields)
            if common:
                lines.append(f"• Common fields: {', '.join(list(common)[:5])}")
        
        # Aggregate numeric values
        totals = {}
        for doc in documents:
            for field, value in doc.fields.items():
                if isinstance(value, (int, float)):
                    if field not in totals:
                        totals[field] = []
                    totals[field].append(value)
                elif isinstance(value, dict) and 'value' in value:
                    try:
                        num_val = float(value['value'])
                        if field not in totals:
                            totals[field] = []
                        totals[field].append(num_val)
                    except (ValueError, TypeError):
                        pass
        
        for field, values in totals.items():
            if len(values) > 1:
                lines.append(f"• {field}: Total=${sum(values):,.2f}, Avg=${sum(values)/len(values):,.2f}")
        
        return "\n".join(lines)
