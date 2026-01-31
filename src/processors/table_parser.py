"""
Table Parser Module

Processes and structures tabular data extracted from forms.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedTable:
    """Represents a parsed table with metadata."""
    headers: List[str]
    rows: List[List[str]]
    column_count: int
    row_count: int
    has_header: bool
    table_type: Optional[str] = None


class TableParser:
    """
    Parses and structures tabular data from various sources.
    
    Features:
    - Header detection
    - Data type inference
    - Table normalization
    - Aggregation support
    """
    
    def __init__(self):
        """Initialize table parser."""
        pass
    
    def parse(self, raw_tables: List[List[List[str]]]) -> List[ParsedTable]:
        """
        Parse raw table data into structured format.
        
        Args:
            raw_tables: List of raw tables (each table is a list of rows)
            
        Returns:
            List of ParsedTable objects
        """
        parsed = []
        
        for raw_table in raw_tables:
            if not raw_table or len(raw_table) < 1:
                continue
            
            # Normalize the table
            normalized = self._normalize_table(raw_table)
            
            if not normalized:
                continue
            
            # Detect headers
            has_header, headers = self._detect_headers(normalized)
            
            if has_header:
                rows = normalized[1:]
            else:
                headers = [f"Column {i+1}" for i in range(len(normalized[0]))]
                rows = normalized
            
            # Infer table type
            table_type = self._infer_table_type(headers, rows)
            
            parsed.append(ParsedTable(
                headers=headers,
                rows=rows,
                column_count=len(headers),
                row_count=len(rows),
                has_header=has_header,
                table_type=table_type
            ))
        
        return parsed
    
    def _normalize_table(self, table: List[List[str]]) -> List[List[str]]:
        """
        Normalize table to have consistent column count.
        
        Args:
            table: Raw table data
            
        Returns:
            Normalized table
        """
        if not table:
            return []
        
        # Find maximum column count
        max_cols = max(len(row) for row in table)
        
        # Normalize each row
        normalized = []
        for row in table:
            # Clean cells
            clean_row = [str(cell).strip() if cell else "" for cell in row]
            
            # Pad if necessary
            while len(clean_row) < max_cols:
                clean_row.append("")
            
            normalized.append(clean_row)
        
        return normalized
    
    def _detect_headers(self, table: List[List[str]]) -> Tuple[bool, List[str]]:
        """
        Detect if first row is a header row.
        
        Args:
            table: Normalized table data
            
        Returns:
            Tuple of (has_header, headers)
        """
        if not table or len(table) < 2:
            return False, []
        
        first_row = table[0]
        second_row = table[1]
        
        # Heuristics for header detection
        header_score = 0
        
        # Check if first row has mostly text/labels
        first_row_text_ratio = sum(
            1 for cell in first_row 
            if cell and not self._is_numeric(cell)
        ) / max(1, len(first_row))
        
        if first_row_text_ratio > 0.5:
            header_score += 1
        
        # Check if second row has different type distribution
        second_row_numeric_ratio = sum(
            1 for cell in second_row 
            if cell and self._is_numeric(cell)
        ) / max(1, len(second_row))
        
        if second_row_numeric_ratio > first_row_text_ratio:
            header_score += 1
        
        # Check for common header words
        common_headers = [
            'name', 'date', 'amount', 'total', 'description', 'id', 'number',
            'quantity', 'price', 'item', 'type', 'status', 'value', 'count'
        ]
        
        for cell in first_row:
            if cell and any(h in cell.lower() for h in common_headers):
                header_score += 1
                break
        
        # Check if first row is different from pattern of other rows
        if len(table) > 2:
            # Compare first row pattern to average of other rows
            other_rows_numeric = [
                sum(1 for cell in row if self._is_numeric(cell)) / max(1, len(row))
                for row in table[1:]
            ]
            avg_numeric = sum(other_rows_numeric) / len(other_rows_numeric)
            first_numeric = sum(1 for cell in first_row if self._is_numeric(cell)) / max(1, len(first_row))
            
            if first_numeric < avg_numeric - 0.2:
                header_score += 1
        
        has_header = header_score >= 2
        headers = first_row if has_header else []
        
        return has_header, headers
    
    def _is_numeric(self, value: str) -> bool:
        """Check if value is numeric."""
        if not value:
            return False
        
        # Remove common numeric formatting
        cleaned = re.sub(r'[\$,€£%\s]', '', value)
        
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _infer_table_type(self, headers: List[str], rows: List[List[str]]) -> Optional[str]:
        """
        Infer the type/purpose of the table.
        
        Args:
            headers: Table headers
            rows: Table data rows
            
        Returns:
            Inferred table type or None
        """
        header_lower = [h.lower() for h in headers]
        
        # Financial/accounting table
        if any(h in ' '.join(header_lower) for h in ['amount', 'total', 'price', 'cost', 'balance']):
            return 'financial'
        
        # Contact/person table
        if any(h in ' '.join(header_lower) for h in ['name', 'email', 'phone', 'address']):
            return 'contact'
        
        # Schedule/time table
        if any(h in ' '.join(header_lower) for h in ['date', 'time', 'schedule', 'due']):
            return 'schedule'
        
        # Inventory/item table
        if any(h in ' '.join(header_lower) for h in ['item', 'quantity', 'stock', 'product']):
            return 'inventory'
        
        return 'general'
    
    def to_dict_list(self, parsed_table: ParsedTable) -> List[Dict[str, str]]:
        """
        Convert parsed table to list of dictionaries.
        
        Args:
            parsed_table: ParsedTable object
            
        Returns:
            List of row dictionaries
        """
        return [
            {header: row[i] for i, header in enumerate(parsed_table.headers)}
            for row in parsed_table.rows
        ]
    
    def aggregate(self, parsed_table: ParsedTable, column: str, 
                  operation: str = 'sum') -> Optional[float]:
        """
        Perform aggregation on a table column.
        
        Args:
            parsed_table: ParsedTable object
            column: Column name to aggregate
            operation: Aggregation operation (sum, avg, min, max, count)
            
        Returns:
            Aggregation result or None
        """
        if column not in parsed_table.headers:
            return None
        
        col_idx = parsed_table.headers.index(column)
        values = []
        
        for row in parsed_table.rows:
            if col_idx < len(row):
                cell = row[col_idx]
                # Clean and convert to number
                cleaned = re.sub(r'[\$,€£%\s]', '', cell)
                try:
                    values.append(float(cleaned))
                except ValueError:
                    continue
        
        if not values:
            return None
        
        if operation == 'sum':
            return sum(values)
        elif operation == 'avg':
            return sum(values) / len(values)
        elif operation == 'min':
            return min(values)
        elif operation == 'max':
            return max(values)
        elif operation == 'count':
            return len(values)
        
        return None
    
    def find_totals(self, parsed_table: ParsedTable) -> Dict[str, float]:
        """
        Find total/summary rows in a table.
        
        Args:
            parsed_table: ParsedTable object
            
        Returns:
            Dictionary of column totals
        """
        totals = {}
        
        # Look for rows with "total" in first column
        for row in parsed_table.rows:
            if row and 'total' in row[0].lower():
                for i, header in enumerate(parsed_table.headers):
                    if i < len(row):
                        cell = row[i]
                        cleaned = re.sub(r'[\$,€£%\s]', '', cell)
                        try:
                            totals[header] = float(cleaned)
                        except ValueError:
                            continue
        
        return totals
    
    def to_markdown(self, parsed_table: ParsedTable) -> str:
        """
        Convert table to markdown format.
        
        Args:
            parsed_table: ParsedTable object
            
        Returns:
            Markdown table string
        """
        lines = []
        
        # Header row
        lines.append("| " + " | ".join(parsed_table.headers) + " |")
        
        # Separator row
        lines.append("| " + " | ".join("---" for _ in parsed_table.headers) + " |")
        
        # Data rows
        for row in parsed_table.rows:
            # Pad row if necessary
            padded = row + [""] * (len(parsed_table.headers) - len(row))
            lines.append("| " + " | ".join(padded[:len(parsed_table.headers)]) + " |")
        
        return "\n".join(lines)
