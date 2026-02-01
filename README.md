# Intelligent Form Agent

An AI-powered system to extract, understand, and analyze forms (PDFs, images, and text). It turns messy documents into structured data, answers questions, and generates insights across multiple forms.

---

## What It Does

* Multi-format support: PDF, PNG/JPG (OCR), text
* Smart extraction: key–value fields, tables, unstructured text
* Q&A: ask natural-language questions about a form
* Summaries: concise highlights of important details
* Cross-form analysis: insights across multiple documents
* Auto schema detection: identifies form types automatically

Extras include confidence scores, JSON/CSV export, form comparison, semantic search, and a Streamlit UI.

---

## Project Structure (High Level)

```
src/
 ├─ agent.py        # Main orchestrator
 ├─ extractors/     # PDF, image (OCR), text extraction
 ├─ processors/     # Field, table parsing & schema detection
 ├─ qa/             # Retrieval + question answering
 ├─ summarizer/     # Form summarization
 ├─ ui/             # Streamlit web app
```

---

## Quick Start

### Requirements

* Python 3.9+
* Tesseract OCR (for images)

### Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Tesseract:

* macOS: `brew install tesseract`
* Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
* Windows: UB Mannheim build

---

## Usage

### CLI

```bash
python -m src.agent process --file form.pdf
python -m src.agent query --file form.pdf --question "What is the total income?"
python -m src.agent summarize --file form.pdf
python -m src.agent analyze --files forms/*.pdf --question "Average income?"
```

### Python API

```python
from src.agent import IntelligentFormAgent

agent = IntelligentFormAgent()
form = agent.load_form("form.pdf")

fields = agent.extract_fields(form)
answer = agent.ask("Applicant name?", form)
summary = agent.summarize(form)
```

### Web UI

```bash
streamlit run src/ui/app.py
```

Open `http://localhost:8501`

---

## Architecture (Simple View)

Input → Extraction → Parsing → Intelligence (Q&A / Summary) → Output

Modular pipeline with PDF/Image/Text extractors, parsers, and LLM-powered reasoning.

---

## Configuration

Customize via `config.yaml`:

* OCR language and confidence thresholds
* QA model and retrieval settings
* Summary length and style
* Output format (JSON / CSV / Markdown)

---

## Testing

```bash
pytest tests/
pytest tests/ --cov=src
```

---

## Privacy

* PII detection and masking
* Local processing by default
* No data stored unless exported

---

## License

MIT License

---

## Credits

Built with pdfplumber, sentence-transformers, and Tesseract OCR.
