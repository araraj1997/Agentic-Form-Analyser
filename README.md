# Intelligent Form Agent

An AI-powered system for processing, understanding, and analyzing forms. The agent extracts information from structured and unstructured fields, answers questions about form content, and generates holistic insights across multiple documents.

## 🌟 Features

### Core Capabilities
- **Multi-Format Support**: Process PDF, image (PNG, JPG), and text-based forms
- **Intelligent Extraction**: Extract key-value pairs, tables, and unstructured text
- **Question Answering**: Natural language Q&A about form content
- **Summarization**: Generate concise summaries highlighting important details
- **Cross-Form Analysis**: Holistic insights across multiple forms
- **Schema Detection**: Automatic form type identification

### Creative Extensions
- **Interactive Web UI**: Streamlit-based interface for easy interaction
- **Confidence Scoring**: Extraction confidence metrics
- **Export Functionality**: Export results to JSON, CSV, or structured reports
- **Form Comparison**: Side-by-side comparison of similar forms
- **Semantic Search**: Find relevant information across form collections

## 📁 Project Structure

```
intelligent-form-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py              # Main agent orchestrator
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py  # PDF processing
│   │   ├── image_extractor.py # Image/OCR processing
│   │   └── text_extractor.py  # Text extraction utilities
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── field_parser.py   # Field identification & parsing
│   │   ├── table_parser.py   # Table extraction
│   │   └── schema_detector.py # Form type detection
│   ├── qa/
│   │   ├── __init__.py
│   │   ├── qa_engine.py      # Question answering engine
│   │   └── retriever.py      # Context retrieval
│   ├── summarizer/
│   │   ├── __init__.py
│   │   └── summarizer.py     # Summarization engine
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py        # Utility functions
│   └── ui/
│       └── app.py            # Streamlit web interface
├── data/
│   └── sample_forms/         # Sample test forms
├── notebooks/
│   └── exploration.ipynb     # Experimental notebooks
├── tests/
│   ├── __init__.py
│   └── test_agent.py         # Unit tests
├── docs/
│   ├── architecture.md       # System architecture
│   └── api_reference.md      # API documentation
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Tesseract OCR (for image processing)

### Installation

1. Clone/extract the repository:
```bash
cd intelligent-form-agent
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR (if processing images):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Basic Usage

#### Command Line Interface

```bash
# Process a single form
python -m src.agent process --file data/sample_forms/tax_form.pdf

# Ask a question about a form
python -m src.agent query --file data/sample_forms/tax_form.pdf \
    --question "What is the total income reported?"

# Summarize a form
python -m src.agent summarize --file data/sample_forms/tax_form.pdf

# Analyze multiple forms
python -m src.agent analyze --files data/sample_forms/*.pdf \
    --question "What is the average income across all forms?"
```

#### Python API

```python
from src.agent import IntelligentFormAgent

# Initialize the agent
agent = IntelligentFormAgent()

# Load a form
form = agent.load_form("path/to/form.pdf")

# Extract all fields
fields = agent.extract_fields(form)
print(fields)

# Ask a question
answer = agent.ask("What is the applicant's name?", form)
print(answer)

# Generate summary
summary = agent.summarize(form)
print(summary)

# Cross-form analysis
forms = agent.load_forms(["form1.pdf", "form2.pdf", "form3.pdf"])
insight = agent.analyze(forms, "Compare the income levels across all forms")
print(insight)
```

#### Web Interface

```bash
# Launch the Streamlit UI
streamlit run src/ui/app.py
```

Then open your browser to `http://localhost:8501`

## 📊 Example Runs

### Example 1: Single Form Question Answering

**Input Form**: W-2 Tax Form (sample)

**Query**: "What is the employee's social security number?"

**Output**:
```json
{
  "answer": "XXX-XX-1234 (partially masked for privacy)",
  "confidence": 0.95,
  "source_field": "Box a - Employee's SSN",
  "context": "Found in the employee information section at the top of the form"
}
```

### Example 2: Form Summarization

**Input Form**: Medical Insurance Claim Form

**Output**:
```
SUMMARY: Medical Insurance Claim Form

KEY INFORMATION:
• Claimant: John Doe (Policy #: INS-2024-78901)
• Date of Service: January 15, 2024
• Provider: City General Hospital
• Diagnosis: Routine checkup (ICD-10: Z00.00)
• Total Charges: $450.00
• Amount Claimed: $360.00 (80% coverage)

STATUS: Pending review
SUBMISSION DATE: January 20, 2024

NOTABLE ITEMS:
- Pre-authorization obtained (Auth #: PA-2024-1234)
- In-network provider
- No prior claims for this condition
```

### Example 3: Cross-Form Analysis

**Input Forms**: 3 Employee Onboarding Forms

**Query**: "What departments are represented and what is the average starting salary?"

**Output**:
```json
{
  "analysis": {
    "departments": ["Engineering", "Marketing", "Sales"],
    "salary_statistics": {
      "average": 85000,
      "min": 65000,
      "max": 110000,
      "by_department": {
        "Engineering": 110000,
        "Marketing": 80000,
        "Sales": 65000
      }
    },
    "common_fields": ["name", "department", "salary", "start_date", "manager"],
    "insights": [
      "Engineering has the highest starting salary",
      "All employees start within the same month",
      "2 of 3 employees report to the same manager"
    ]
  }
}
```

## 🏗️ Architecture

The Intelligent Form Agent uses a modular pipeline architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT FORM AGENT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Input   │───▶│  Extractors  │───▶│  Document Store      │  │
│  │ (Forms)  │    │  PDF/Image   │    │  (Structured Data)   │  │
│  └──────────┘    └──────────────┘    └──────────────────────┘  │
│                                                │                 │
│                                                ▼                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Processing Layer                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │   Field    │  │   Table    │  │     Schema         │  │  │
│  │  │  Parser    │  │  Parser    │  │    Detector        │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                │                 │
│                                                ▼                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Intelligence Layer                     │  │
│  │  ┌────────────────┐    ┌─────────────────────────────┐   │  │
│  │  │   QA Engine    │    │       Summarizer            │   │  │
│  │  │  (Retrieval +  │    │   (Extractive + Abstractive)│   │  │
│  │  │   Generation)  │    │                             │   │  │
│  │  └────────────────┘    └─────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                │                 │
│                                                ▼                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Output Layer                         │  │
│  │    Answers  │  Summaries  │  Insights  │  Exports        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

Create a `config.yaml` file to customize behavior:

```yaml
extraction:
  ocr_language: "eng"
  confidence_threshold: 0.7
  extract_tables: true

qa:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  max_context_length: 512
  top_k_retrieval: 5

summarization:
  max_length: 500
  min_length: 100
  style: "bullet_points"  # or "narrative"

output:
  format: "json"  # json, csv, or markdown
  include_confidence: true
```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_agent.py::TestQuestionAnswering
```

## 📈 Performance Considerations

- **Batch Processing**: Use `agent.process_batch()` for multiple forms
- **Caching**: Enable caching for repeated queries on the same forms
- **GPU Acceleration**: Set `device="cuda"` if available for faster embeddings

## 🔒 Privacy & Security

- PII Detection: Automatically detects and can mask sensitive information
- Local Processing: All processing happens locally by default
- No Data Retention: Form data is not stored unless explicitly exported

## 🤝 Contributing

Contributions are welcome! Please see `docs/contributing.md` for guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF extraction
- Uses [sentence-transformers](https://www.sbert.net/) for semantic search
- OCR powered by [Tesseract](https://github.com/tesseract-ocr/tesseract)
