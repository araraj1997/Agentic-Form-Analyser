"""
Streamlit Web Interface for Intelligent Form Agent

A user-friendly interface for processing forms, asking questions,
and generating summaries.
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agent import IntelligentFormAgent, FormDocument


def initialize_session_state():
    """Initialize session state variables."""
    if 'agent' not in st.session_state:
        st.session_state.agent = IntelligentFormAgent()
    
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []


def render_header():
    """Render the header section."""
    st.set_page_config(
        page_title="Intelligent Form Agent",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Intelligent Form Agent")
    st.markdown("""
    Upload forms, ask questions, and get intelligent summaries.
    Supports PDF, images, and text files.
    """)


def render_sidebar():
    """Render the sidebar with options."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Summary style
        st.session_state.summary_style = st.selectbox(
            "Summary Style",
            ["bullet_points", "narrative"],
            index=0
        )
        
        # Confidence threshold
        st.session_state.confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        
        # Show raw extraction
        st.session_state.show_raw = st.checkbox("Show Raw Extraction", value=False)
        
        st.divider()
        
        # Document list
        st.header("📚 Loaded Documents")
        
        if st.session_state.documents:
            for i, doc in enumerate(st.session_state.documents):
                with st.expander(f"📄 {Path(doc.file_path).name}"):
                    st.write(f"**Type:** {doc.file_type}")
                    st.write(f"**Schema:** {doc.schema_type or 'Unknown'}")
                    st.write(f"**Confidence:** {doc.extraction_confidence:.1%}")
                    st.write(f"**Fields:** {len(doc.fields)}")
                    
                    if st.button(f"Remove", key=f"remove_{i}"):
                        st.session_state.documents.pop(i)
                        st.rerun()
        else:
            st.info("No documents loaded")
        
        st.divider()
        
        # Clear all button
        if st.button("🗑️ Clear All"):
            st.session_state.documents = []
            st.session_state.chat_history = []
            st.rerun()


def render_upload_section():
    """Render the file upload section."""
    st.header("📤 Upload Forms")
    
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=['pdf', 'png', 'jpg', 'jpeg', 'txt', 'json', 'csv'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Selected {len(uploaded_files)} file(s)")
        
        with col2:
            if st.button("🔄 Process Files"):
                process_uploaded_files(uploaded_files)


def process_uploaded_files(uploaded_files):
    """Process uploaded files."""
    progress = st.progress(0)
    status = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        status.text(f"Processing: {uploaded_file.name}")
        
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, 
                                             suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Process with agent
            doc = st.session_state.agent.load_form(tmp_path)
            doc.file_path = uploaded_file.name  # Use original name
            
            st.session_state.documents.append(doc)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        progress.progress((i + 1) / len(uploaded_files))
    
    status.text("✅ Processing complete!")
    st.rerun()


def render_qa_section():
    """Render the Question Answering section."""
    st.header("❓ Ask Questions")
    
    if not st.session_state.documents:
        st.warning("Please upload and process some forms first.")
        return
    
    # Question input
    question = st.text_input(
        "Ask a question about your forms:",
        placeholder="e.g., What is the total amount? Who is the applicant?"
    )
    
    # Document selection
    doc_names = [Path(d.file_path).name for d in st.session_state.documents]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_docs = st.multiselect(
            "Select documents to query",
            doc_names,
            default=doc_names
        )
    
    with col2:
        query_btn = st.button("🔍 Ask", type="primary")
    
    if query_btn and question:
        # Get selected documents
        docs = [d for d in st.session_state.documents 
                if Path(d.file_path).name in selected_docs]
        
        if len(docs) == 1:
            result = st.session_state.agent.ask(question, docs[0])
        else:
            result = st.session_state.agent.ask_multiple(question, docs)
        
        # Display result
        st.markdown("### Answer")
        
        confidence_color = "green" if result.confidence > 0.7 else \
                          "orange" if result.confidence > 0.4 else "red"
        
        st.markdown(f"""
        <div style="padding: 1rem; background-color: #f0f2f6; border-radius: 0.5rem;">
            <p style="font-size: 1.1rem;">{result.answer}</p>
            <p style="color: {confidence_color}; font-size: 0.9rem;">
                Confidence: {result.confidence:.1%}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if result.source_fields:
            with st.expander("📋 Source Fields"):
                for field in result.source_fields:
                    st.write(f"• {field}")
        
        # Add to chat history
        st.session_state.chat_history.append({
            'question': question,
            'answer': result.answer,
            'confidence': result.confidence
        })


def render_summary_section():
    """Render the Summary section."""
    st.header("📝 Generate Summary")
    
    if not st.session_state.documents:
        st.warning("Please upload and process some forms first.")
        return
    
    doc_names = [Path(d.file_path).name for d in st.session_state.documents]
    
    selected_doc = st.selectbox("Select document to summarize", doc_names)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("📄 Generate Summary", type="primary"):
            doc = next(d for d in st.session_state.documents 
                       if Path(d.file_path).name == selected_doc)
            
            summary = st.session_state.agent.summarize(doc)
            
            st.session_state.current_summary = summary
    
    # Display summary
    if hasattr(st.session_state, 'current_summary'):
        summary = st.session_state.current_summary
        
        st.markdown("### Summary")
        st.code(summary.full_text, language=None)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Key Information")
            for field, value in summary.key_information.items():
                if isinstance(value, dict):
                    st.write(f"**{field}:** {value.get('value', value)}")
                else:
                    st.write(f"**{field}:** {value}")
        
        with col2:
            st.markdown("#### Notable Items")
            for item in summary.notable_items:
                st.write(f"• {item}")


def render_analysis_section():
    """Render the Cross-Form Analysis section."""
    st.header("📊 Cross-Form Analysis")
    
    if len(st.session_state.documents) < 2:
        st.warning("Please upload at least 2 forms for cross-form analysis.")
        return
    
    analysis_question = st.text_input(
        "Analysis question:",
        placeholder="e.g., Compare incomes across all forms"
    )
    
    if st.button("🔬 Analyze", type="primary") and analysis_question:
        analysis = st.session_state.agent.analyze(
            st.session_state.documents, 
            analysis_question
        )
        
        st.markdown("### Analysis Results")
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Documents", analysis['total_documents'])
        
        with col2:
            unique_schemas = set(s for s in analysis['schema_types'] if s)
            st.metric("Unique Form Types", len(unique_schemas))
        
        with col3:
            st.metric("Common Fields", len(analysis['common_fields']))
        
        # Answer
        if 'answer' in analysis:
            st.markdown("#### Answer")
            st.info(analysis['answer'])
        
        # Insights
        if analysis.get('insights'):
            st.markdown("#### Insights")
            for insight in analysis['insights']:
                st.write(f"💡 {insight}")
        
        # Field statistics
        if analysis.get('field_summary'):
            st.markdown("#### Numeric Field Statistics")
            for field, stats in analysis['field_summary'].items():
                with st.expander(f"📈 {field}"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Count", stats['count'])
                    col2.metric("Average", f"${stats['average']:,.2f}")
                    col3.metric("Min", f"${stats['min']:,.2f}")
                    col4.metric("Max", f"${stats['max']:,.2f}")


def render_extraction_details():
    """Render detailed extraction view."""
    st.header("🔍 Extraction Details")
    
    if not st.session_state.documents:
        st.warning("No documents loaded.")
        return
    
    doc_names = [Path(d.file_path).name for d in st.session_state.documents]
    selected_doc = st.selectbox("Select document", doc_names, key="detail_select")
    
    doc = next(d for d in st.session_state.documents 
               if Path(d.file_path).name == selected_doc)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Fields", "Tables", "Raw Text", "Export"])
    
    with tab1:
        st.markdown("### Extracted Fields")
        if doc.fields:
            for field, value in doc.fields.items():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{field}**")
                with col2:
                    if isinstance(value, dict):
                        st.json(value)
                    else:
                        st.write(value)
        else:
            st.info("No fields extracted")
    
    with tab2:
        st.markdown("### Extracted Tables")
        if doc.tables:
            for i, table in enumerate(doc.tables):
                st.markdown(f"**Table {i+1}**")
                if table:
                    import pandas as pd
                    try:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        st.dataframe(df)
                    except:
                        for row in table:
                            st.write(row)
        else:
            st.info("No tables extracted")
    
    with tab3:
        st.markdown("### Raw Text")
        if doc.raw_text:
            st.text_area("", doc.raw_text, height=400)
        else:
            st.info("No text extracted")
    
    with tab4:
        st.markdown("### Export")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export JSON"):
                st.download_button(
                    "Download JSON",
                    doc.to_json(),
                    file_name=f"{Path(doc.file_path).stem}_extracted.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📥 Export Markdown"):
                md_output = st.session_state.agent.export(doc, 'markdown')
                st.download_button(
                    "Download Markdown",
                    md_output,
                    file_name=f"{Path(doc.file_path).stem}_extracted.md",
                    mime="text/markdown"
                )
        
        with col3:
            if st.button("📥 Export CSV"):
                csv_output = st.session_state.agent.export(doc, 'csv')
                st.download_button(
                    "Download CSV",
                    csv_output,
                    file_name=f"{Path(doc.file_path).stem}_extracted.csv",
                    mime="text/csv"
                )


def render_chat_history():
    """Render chat history section."""
    if st.session_state.chat_history:
        st.header("💬 Chat History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                st.markdown(f"**Q:** {chat['question']}")
                st.markdown(f"**A:** {chat['answer']}")
                st.caption(f"Confidence: {chat['confidence']:.1%}")
                st.divider()


def main():
    """Main application entry point."""
    initialize_session_state()
    render_header()
    render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload", 
        "❓ Q&A", 
        "📝 Summary",
        "📊 Analysis",
        "🔍 Details"
    ])
    
    with tab1:
        render_upload_section()
    
    with tab2:
        render_qa_section()
        render_chat_history()
    
    with tab3:
        render_summary_section()
    
    with tab4:
        render_analysis_section()
    
    with tab5:
        render_extraction_details()


if __name__ == "__main__":
    main()
