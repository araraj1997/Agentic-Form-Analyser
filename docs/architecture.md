# Intelligent Form Agent - Architecture

## Overview

The Intelligent Form Agent is designed with a modular, layered architecture that separates concerns and allows for easy extension and customization.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   CLI Interface  │  │  Streamlit Web   │  │    Python API            │  │
│  │   (agent.py)     │  │  (ui/app.py)     │  │    (programmatic use)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     IntelligentFormAgent                              │  │
│  │  - load_form()     - ask()           - summarize()                   │  │
│  │  - load_forms()    - ask_multiple()  - analyze()                     │  │
│  │  - extract_fields() - compare()      - export()                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌─────────────────┐ ┌────────────────────────────┐
│   EXTRACTION LAYER    │ │ PROCESSING LAYER│ │   INTELLIGENCE LAYER       │
│                       │ │                 │ │                            │
│ ┌───────────────────┐ │ │┌───────────────┐│ │ ┌────────────────────────┐ │
│ │  PDFExtractor     │ │ ││ FieldParser   ││ │ │      QAEngine          │ │
│ │  - pdfplumber     │ │ ││ - regex       ││ │ │  - semantic search     │ │
│ │  - OCR fallback   │ │ ││ - patterns    ││ │ │  - context retrieval   │ │
│ └───────────────────┘ │ │└───────────────┘│ │ │  - answer generation   │ │
│                       │ │                 │ │ └────────────────────────┘ │
│ ┌───────────────────┐ │ │┌───────────────┐│ │                            │
│ │  ImageExtractor   │ │ ││ TableParser   ││ │ ┌────────────────────────┐ │
│ │  - Tesseract OCR  │ │ ││ - header det. ││ │ │    FormSummarizer      │ │
│ │  - preprocessing  │ │ ││ - aggregation ││ │ │  - key extraction      │ │
│ └───────────────────┘ │ │└───────────────┘│ │ │  - highlight gen       │ │
│                       │ │                 │ │ │  - multi-style output  │ │
│ ┌───────────────────┐ │ │┌───────────────┐│ │ └────────────────────────┘ │
│ │  TextExtractor    │ │ ││SchemaDetector ││ │                            │
│ │  - JSON/CSV/TXT   │ │ ││ - form typing ││ │ ┌────────────────────────┐ │
│ │  - HTML parsing   │ │ ││ - validation  ││ │ │   ContextRetriever     │ │
│ └───────────────────┘ │ │└───────────────┘│ │ │  - keyword matching    │ │
└───────────────────────┘ └─────────────────┘ │ │  - embedding search    │ │
                                              │ └────────────────────────┘ │
                                              └────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            UTILITY LAYER                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  File Detection │  │  Text Cleaning  │  │  Data Masking               │ │
│  │  Config Loading │  │  Text Chunking  │  │  Currency/Date Formatting   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer

#### CLI Interface (`src/agent.py`)
- Provides command-line access to all agent functions
- Supports `process`, `query`, `summarize`, and `analyze` commands
- Outputs JSON, CSV, or Markdown formats

#### Streamlit Web UI (`src/ui/app.py`)
- Interactive file upload and processing
- Real-time Q&A interface
- Visual summary and analysis displays
- Export functionality

#### Python API
- Direct programmatic access via `IntelligentFormAgent` class
- Full access to all components and methods
- Suitable for integration into larger systems

### 2. Orchestration Layer

#### IntelligentFormAgent
The main coordinator that:
- Manages document lifecycle
- Routes requests to appropriate components
- Maintains document store for caching
- Handles multi-document operations

### 3. Extraction Layer

#### PDFExtractor
- Uses `pdfplumber` for native PDF text/table extraction
- Falls back to OCR (Tesseract) for scanned documents
- Preserves document structure and metadata

#### ImageExtractor
- Tesseract OCR for text recognition
- Optional preprocessing (grayscale, thresholding, denoising)
- Table structure detection from OCR output

#### TextExtractor
- Handles plain text, JSON, CSV, HTML, Markdown
- Preserves structured data from JSON/CSV
- Extracts tables from Markdown format

### 4. Processing Layer

#### FieldParser
- Pattern-based field extraction (key: value, key - value, etc.)
- Special field detection (email, phone, SSN, dates, currency)
- Checkbox/selection field parsing
- Confidence scoring

#### TableParser
- Automatic header detection
- Column normalization
- Type inference for table content
- Aggregation operations (sum, avg, min, max)

#### SchemaDetector
- Pattern matching against known form types
- Confidence scoring for schema matches
- Expected field validation
- Support for 15+ form types (tax, medical, employment, etc.)

### 5. Intelligence Layer

#### QAEngine
- Question type classification
- Context retrieval (keyword + semantic)
- Answer generation based on question type
- Cross-document analysis
- Confidence scoring

#### FormSummarizer
- Category-aware summarization
- Key information extraction
- Highlight generation
- Notable item identification
- Multiple output styles (bullet points, narrative)

#### ContextRetriever
- Keyword-based retrieval
- Semantic similarity search (with sentence-transformers)
- Field-aware and table-aware retrieval
- Relevance scoring

### 6. Utility Layer

Provides common functions:
- File type detection
- Text cleaning and normalization
- Sensitive data masking
- Currency and date formatting
- Text chunking for processing
- Similarity calculation

## Data Flow

### Single Form Processing
```
Input File → Detect Type → Extract Content → Parse Fields → Detect Schema → Create FormDocument
```

### Question Answering
```
Question + Document → Retrieve Context → Classify Question Type → Generate Answer → Return QueryResult
```

### Summarization
```
Document → Determine Category → Extract Key Info → Generate Highlights → Format Output → Return Summary
```

### Cross-Form Analysis
```
Question + Documents[] → Aggregate Fields → Calculate Statistics → Generate Insights → Return Analysis
```

## Extension Points

1. **New Extractors**: Add new file format support by implementing the extractor interface
2. **Schema Definitions**: Add new form types to SchemaDetector
3. **QA Patterns**: Extend question handling in QAEngine
4. **Summary Styles**: Add new summarization formats in FormSummarizer
5. **Custom Processors**: Add domain-specific field parsing logic

## Performance Considerations

- **Lazy Loading**: Embedding models loaded on first use
- **Document Caching**: Processed documents stored in memory
- **Batch Processing**: Multiple documents can be processed efficiently
- **GPU Acceleration**: Sentence-transformers can use GPU if available

## Security Considerations

- **PII Masking**: SSN, credit cards automatically masked
- **Local Processing**: All processing happens locally
- **No Data Persistence**: Documents not stored unless explicitly exported
