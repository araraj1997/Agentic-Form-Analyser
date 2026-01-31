# Intelligent Form Agent - API Reference

## Core Classes

### IntelligentFormAgent

The main orchestrator class for all form processing operations.

```python
from src.agent import IntelligentFormAgent

agent = IntelligentFormAgent(config_path=None)
```

**Parameters:**
- `config_path` (str, optional): Path to YAML configuration file

#### Methods

##### `load_form(file_path: str) -> FormDocument`
Load and process a single form file.

```python
doc = agent.load_form("path/to/form.pdf")
```

**Parameters:**
- `file_path`: Path to the form file

**Returns:** `FormDocument` object

**Supported formats:** PDF, PNG, JPG, JPEG, TIFF, BMP, TXT, JSON, CSV, HTML, MD

---

##### `load_forms(file_paths: List[str]) -> List[FormDocument]`
Load multiple form files.

```python
docs = agent.load_forms(["form1.pdf", "form2.pdf", "form3.pdf"])
```

**Parameters:**
- `file_paths`: List of file paths

**Returns:** List of `FormDocument` objects

---

##### `extract_fields(document: FormDocument) -> Dict[str, Any]`
Extract all fields from a form document.

```python
fields = agent.extract_fields(doc)
# {'Name': 'John Doe', 'Amount': {'type': 'currency', 'value': 1000}, ...}
```

---

##### `ask(question: str, document: FormDocument | str) -> QueryResult`
Ask a question about a single form.

```python
result = agent.ask("What is the total amount?", doc)
print(result.answer)       # "The total amount is: $1,500.00"
print(result.confidence)   # 0.85
```

**Parameters:**
- `question`: Natural language question
- `document`: FormDocument object or file path string

**Returns:** `QueryResult` object

---

##### `ask_multiple(question: str, documents: List[FormDocument]) -> QueryResult`
Ask a question across multiple forms.

```python
result = agent.ask_multiple("What is the average salary?", [doc1, doc2, doc3])
```

---

##### `summarize(document: FormDocument | str) -> Summary`
Generate a summary of a form.

```python
summary = agent.summarize(doc)
print(summary.full_text)
print(summary.key_information)
print(summary.highlights)
```

---

##### `analyze(documents: List[FormDocument], question: str) -> Dict[str, Any]`
Perform cross-form analysis.

```python
analysis = agent.analyze(docs, "Compare the salaries across departments")
```

**Returns:** Dictionary with:
- `total_documents`: Number of forms analyzed
- `common_fields`: Fields present in all forms
- `schema_types`: Detected form types
- `field_summary`: Statistics for numeric fields
- `insights`: Generated insights
- `answer`: Answer to the question

---

##### `compare(doc1: FormDocument, doc2: FormDocument) -> Dict[str, Any]`
Compare two forms.

```python
comparison = agent.compare(doc1, doc2)
```

**Returns:** Dictionary with:
- `common_fields`: Fields in both documents
- `only_in_first`: Fields only in first document
- `only_in_second`: Fields only in second document
- `differences`: Different values for common fields
- `same_schema`: Whether documents have same schema type

---

##### `export(document: FormDocument, format: str, output_path: str = None) -> str`
Export extracted data.

```python
json_str = agent.export(doc, 'json')
csv_str = agent.export(doc, 'csv', 'output.csv')
md_str = agent.export(doc, 'markdown')
```

**Formats:** `json`, `csv`, `markdown`

---

### FormDocument

Data class representing a processed form.

```python
@dataclass
class FormDocument:
    file_path: str              # Original file path
    file_type: str              # Detected file type
    raw_text: str               # Extracted raw text
    fields: Dict[str, Any]      # Extracted key-value fields
    tables: List[List[List[str]]]  # Extracted tables
    metadata: Dict[str, Any]    # File/extraction metadata
    schema_type: Optional[str]  # Detected form type
    extraction_confidence: float # Confidence score (0-1)
    processed_at: str           # ISO timestamp
```

**Methods:**
- `to_dict() -> Dict`: Convert to dictionary
- `to_json() -> str`: Convert to JSON string

---

### QueryResult

Data class representing a QA result.

```python
@dataclass
class QueryResult:
    question: str           # Original question
    answer: str             # Generated answer
    confidence: float       # Confidence score (0-1)
    source_fields: List[str]  # Fields used for answer
    context: str            # Retrieved context
```

---

### Summary

Data class representing a form summary.

```python
@dataclass
class Summary:
    form_type: str                  # Detected form type
    key_information: Dict[str, Any] # Key extracted fields
    highlights: List[str]           # Important highlights
    notable_items: List[str]        # Notable observations
    full_text: str                  # Complete summary text
```

---

## Extractor Classes

### PDFExtractor

```python
from src.extractors import PDFExtractor

extractor = PDFExtractor(ocr_fallback=True)
text, tables, metadata = extractor.extract("document.pdf")
```

### ImageExtractor

```python
from src.extractors import ImageExtractor

extractor = ImageExtractor(language='eng', preprocess=True)
text, tables, metadata = extractor.extract("form.png")
```

### TextExtractor

```python
from src.extractors import TextExtractor

extractor = TextExtractor()
text, tables, metadata = extractor.extract("data.json")
```

---

## Processor Classes

### FieldParser

```python
from src.processors import FieldParser

parser = FieldParser()
fields = parser.parse(raw_text)
# Returns: {'Field Name': 'value', ...}

# With confidence scores
matches = parser.parse_with_confidence(raw_text)
# Returns: [FieldMatch(name, value, confidence, position), ...]
```

### TableParser

```python
from src.processors import TableParser

parser = TableParser()
parsed_tables = parser.parse(raw_tables)
# Returns: [ParsedTable(headers, rows, ...), ...]

# Convert to dictionaries
dict_list = parser.to_dict_list(parsed_table)
# Returns: [{'Column1': 'val1', 'Column2': 'val2'}, ...]

# Aggregate values
total = parser.aggregate(parsed_table, 'Amount', 'sum')
```

### SchemaDetector

```python
from src.processors import SchemaDetector

detector = SchemaDetector()

# Simple detection
schema_type = detector.detect(text, fields)
# Returns: 'w2', 'insurance_claim', etc.

# With confidence
match = detector.detect_with_confidence(text, fields)
# Returns: SchemaMatch(schema_type, confidence, matched_indicators, category)

# Get expected fields for a schema
expected = detector.get_expected_fields('w2')
# Returns: ['Employee SSN', 'Employer EIN', ...]
```

---

## Utility Functions

```python
from src.utils import (
    detect_file_type,
    load_config,
    clean_text,
    mask_sensitive_data,
    format_currency,
    parse_date,
    chunk_text,
    calculate_text_similarity
)

# Detect file type
file_type = detect_file_type("document.pdf")  # Returns: 'pdf'

# Load YAML config
config = load_config("config.yaml")

# Clean text
cleaned = clean_text("  messy   text  ")

# Mask sensitive data
masked = mask_sensitive_data("SSN: 123-45-6789", mask_ssn=True)
# Returns: "SSN: XXX-XX-6789"

# Format currency
formatted = format_currency(1234.56)  # Returns: "$1,234.56"

# Parse date
normalized = parse_date("01/15/2024")  # Returns: "2024-01-15"

# Chunk text for processing
chunks = chunk_text(long_text, chunk_size=500, overlap=50)

# Calculate similarity
similarity = calculate_text_similarity(text1, text2)  # Returns: 0.0-1.0
```

---

## Configuration

Configuration file format (YAML):

```yaml
extraction:
  ocr_language: "eng"          # Tesseract language code
  confidence_threshold: 0.7    # Minimum confidence threshold
  extract_tables: true         # Whether to extract tables

qa:
  model: "sentence-transformers/all-MiniLM-L6-v2"  # Embedding model
  max_context_length: 512      # Maximum context for answers
  top_k_retrieval: 5           # Number of chunks to retrieve

summarization:
  max_length: 500              # Maximum summary length
  min_length: 100              # Minimum summary length
  style: "bullet_points"       # "bullet_points" or "narrative"

output:
  format: "json"               # Default output format
  include_confidence: true     # Include confidence scores
```

---

## Error Handling

All methods can raise the following exceptions:

- `FileNotFoundError`: When the specified file doesn't exist
- `ValueError`: When invalid parameters are provided
- `ImportError`: When required dependencies are missing

Example:

```python
try:
    doc = agent.load_form("nonexistent.pdf")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Error processing form: {e}")
```

---

## Examples

### Complete Workflow

```python
from src.agent import IntelligentFormAgent

# Initialize
agent = IntelligentFormAgent()

# Load forms
doc = agent.load_form("tax_form.pdf")

# Extract fields
print("Fields:", agent.extract_fields(doc))

# Ask questions
answer = agent.ask("What is the total income?", doc)
print(f"Answer: {answer.answer} (confidence: {answer.confidence:.1%})")

# Generate summary
summary = agent.summarize(doc)
print("Summary:", summary.full_text)

# Export results
agent.export(doc, 'json', 'extracted_data.json')
```

### Multi-Form Analysis

```python
# Load multiple forms
docs = agent.load_forms([
    "onboarding_1.txt",
    "onboarding_2.txt", 
    "onboarding_3.txt"
])

# Cross-form question
result = agent.ask_multiple(
    "What departments are represented?",
    docs
)
print(result.answer)

# Full analysis
analysis = agent.analyze(
    docs,
    "Compare the starting salaries by department"
)

print("Insights:", analysis['insights'])
print("Statistics:", analysis['field_summary'])
```
