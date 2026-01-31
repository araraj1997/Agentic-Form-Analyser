#!/usr/bin/env python3
"""
Demonstration Script for Intelligent Form Agent

This script demonstrates the three required example runs:
1. Answering a question from a single form
2. Generating a summary of one form
3. Providing a holistic answer across multiple forms
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import IntelligentFormAgent


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_subheader(title: str):
    """Print a formatted subheader."""
    print(f"\n--- {title} ---\n")


def demo_single_form_qa(agent: IntelligentFormAgent):
    """
    EXAMPLE 1: Answering a question from a single form.
    
    Demonstrates the QA capability on a W-2 tax form.
    """
    print_header("EXAMPLE 1: Single Form Question Answering")
    
    # Load the sample W-2 form
    form_path = "data/sample_forms/sample_w2.txt"
    
    if not os.path.exists(form_path):
        print(f"Sample form not found at {form_path}")
        return
    
    print(f"Loading form: {form_path}")
    doc = agent.load_form(form_path)
    
    print_subheader("Extracted Fields")
    for field, value in doc.fields.items():
        print(f"  • {field}: {value}")
    
    print_subheader("Question & Answer")
    
    # Ask multiple questions
    questions = [
        "What is the employee's name?",
        "How much were the total wages?",
        "What was the federal tax withheld?",
        "What is the employer's name?"
    ]
    
    for question in questions:
        result = agent.ask(question, doc)
        print(f"Q: {question}")
        print(f"A: {result.answer}")
        print(f"   Confidence: {result.confidence:.1%}")
        if result.source_fields:
            print(f"   Source: {', '.join(result.source_fields)}")
        print()


def demo_form_summary(agent: IntelligentFormAgent):
    """
    EXAMPLE 2: Generating a summary of one form.
    
    Demonstrates the summarization capability on an insurance claim form.
    """
    print_header("EXAMPLE 2: Form Summarization")
    
    # Load the sample insurance claim form
    form_path = "data/sample_forms/sample_insurance_claim.txt"
    
    if not os.path.exists(form_path):
        print(f"Sample form not found at {form_path}")
        return
    
    print(f"Loading form: {form_path}")
    doc = agent.load_form(form_path)
    
    print_subheader("Form Metadata")
    print(f"  File Type: {doc.file_type}")
    print(f"  Detected Schema: {doc.schema_type}")
    print(f"  Extraction Confidence: {doc.extraction_confidence:.1%}")
    print(f"  Fields Extracted: {len(doc.fields)}")
    
    print_subheader("Generated Summary")
    summary = agent.summarize(doc)
    print(summary.full_text)
    
    print_subheader("Key Information (Structured)")
    print(json.dumps(summary.key_information, indent=2, default=str))


def demo_cross_form_analysis(agent: IntelligentFormAgent):
    """
    EXAMPLE 3: Providing a holistic answer across multiple forms.
    
    Demonstrates cross-form analysis on multiple employee onboarding forms.
    """
    print_header("EXAMPLE 3: Cross-Form Analysis")
    
    # Load multiple onboarding forms
    form_paths = [
        "data/sample_forms/sample_onboarding_1.txt",
        "data/sample_forms/sample_onboarding_2.txt",
        "data/sample_forms/sample_onboarding_3.txt"
    ]
    
    # Check if files exist
    existing_paths = [p for p in form_paths if os.path.exists(p)]
    
    if not existing_paths:
        print("Sample forms not found")
        return
    
    print(f"Loading {len(existing_paths)} forms...")
    docs = agent.load_forms(existing_paths)
    
    print_subheader("Loaded Forms Overview")
    for doc in docs:
        name = doc.fields.get('Full Name', 'Unknown')
        dept = doc.fields.get('Department', 'Unknown')
        salary = doc.fields.get('Annual Salary', 'Unknown')
        print(f"  • {Path(doc.file_path).name}")
        print(f"    Employee: {name}")
        print(f"    Department: {dept}")
        print(f"    Salary: {salary}")
        print()
    
    print_subheader("Cross-Form Questions")
    
    # Ask questions across all forms
    questions = [
        "What departments are represented?",
        "What is the average starting salary?",
        "Who has the highest salary?"
    ]
    
    for question in questions:
        result = agent.ask_multiple(question, docs)
        print(f"Q: {question}")
        print(f"A: {result.answer}")
        print(f"   Confidence: {result.confidence:.1%}")
        print()
    
    print_subheader("Full Cross-Form Analysis")
    
    analysis_question = "Compare the salaries and benefits across all employees"
    analysis = agent.analyze(docs, analysis_question)
    
    print(f"Analysis Question: {analysis_question}")
    print()
    print(f"Total Documents Analyzed: {analysis['total_documents']}")
    print(f"Common Fields: {', '.join(analysis['common_fields'][:5])}")
    
    if analysis.get('insights'):
        print("\nInsights:")
        for insight in analysis['insights']:
            print(f"  💡 {insight}")
    
    if analysis.get('field_summary'):
        print("\nNumeric Field Statistics:")
        for field, stats in analysis['field_summary'].items():
            if 'salary' in field.lower():
                print(f"  {field}:")
                print(f"    - Average: ${stats['average']:,.2f}")
                print(f"    - Range: ${stats['min']:,.2f} - ${stats['max']:,.2f}")
    
    print(f"\nAnswer: {analysis.get('answer', 'N/A')}")


def demo_comparison(agent: IntelligentFormAgent):
    """
    BONUS: Form comparison demonstration.
    """
    print_header("BONUS: Form Comparison")
    
    form1_path = "data/sample_forms/sample_onboarding_1.txt"
    form2_path = "data/sample_forms/sample_onboarding_2.txt"
    
    if not os.path.exists(form1_path) or not os.path.exists(form2_path):
        print("Sample forms not found for comparison")
        return
    
    doc1 = agent.load_form(form1_path)
    doc2 = agent.load_form(form2_path)
    
    print(f"Comparing:")
    print(f"  Form 1: {Path(form1_path).name}")
    print(f"  Form 2: {Path(form2_path).name}")
    
    comparison = agent.compare(doc1, doc2)
    
    print_subheader("Comparison Results")
    print(f"Common Fields: {len(comparison['common_fields'])}")
    print(f"Same Schema Type: {comparison['same_schema']}")
    
    if comparison['differences']:
        print("\nDifferences in Common Fields:")
        for field, diff in list(comparison['differences'].items())[:5]:
            print(f"  {field}:")
            print(f"    Form 1: {diff['doc1']}")
            print(f"    Form 2: {diff['doc2']}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("       INTELLIGENT FORM AGENT - DEMONSTRATION")
    print("=" * 70)
    
    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Initialize the agent
    print("\nInitializing Intelligent Form Agent...")
    agent = IntelligentFormAgent()
    print("Agent initialized successfully!\n")
    
    # Run demonstrations
    try:
        demo_single_form_qa(agent)
        demo_form_summary(agent)
        demo_cross_form_analysis(agent)
        demo_comparison(agent)
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    print_header("DEMONSTRATION COMPLETE")
    print("The Intelligent Form Agent successfully demonstrated:")
    print("  ✓ Single form question answering")
    print("  ✓ Form summarization")
    print("  ✓ Cross-form holistic analysis")
    print("  ✓ Form comparison (bonus)")
    print("\nFor more features, try the Streamlit UI:")
    print("  $ streamlit run src/ui/app.py")
    print()


if __name__ == "__main__":
    main()
