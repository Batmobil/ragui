import streamlit as st
import time
import random
import io
import os
import pandas as pd
from docx import Document
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ALL session state variables FIRST to ensure they exist
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Chat"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_answer' not in st.session_state:
    st.session_state.current_answer = None

if 'documents' not in st.session_state:
    st.session_state.documents = [
        {"id": 1, "title": "Research Paper 1", "content": "Content of research paper 1...", "type": "PDF", "selected": False},
        {"id": 2, "title": "Dataset Description", "content": "This dataset contains...", "type": "TXT", "selected": False},
        {"id": 3, "title": "Literature Review", "content": "Recent advances in the field...", "type": "DOCX", "selected": False},
        {"id": 4, "title": "Experiment Results", "content": "The results show significant improvement...", "type": "PDF", "selected": False},
        {"id": 5, "title": "Research Paper 2", "content": "Further explorations in...", "type": "PDF", "selected": False}
    ]

if 'next_doc_id' not in st.session_state:
    st.session_state.next_doc_id = 6

if 'saved_answers' not in st.session_state:
    st.session_state.saved_answers = []

if 'next_answer_id' not in st.session_state:
    st.session_state.next_answer_id = 1

if 'editing_title' not in st.session_state:
    st.session_state.editing_title = None

if 'selected_suggestion' not in st.session_state:
    st.session_state.selected_suggestion = None

if 'left_column_visible' not in st.session_state:
    st.session_state.left_column_visible = True

if 'right_column_visible' not in st.session_state:
    st.session_state.right_column_visible = True

# Custom CSS with fixed ribbon positioning and improved column toggles
st.markdown("""
<style>
    .main {
        background-color: #f9f9f9;
    }
    .stApp {
        font-family: 'Google Sans', sans-serif;
    }
    /* POC Ribbon */
    .ribbon-container {
        position: absolute;
        top: 0;
        left: 0;
        overflow: hidden;
        height: 100px;
        width: 100px;
        z-index: 999;
        pointer-events: none;
    }
    .ribbon {
        position: relative;
        top: 15px;
        left: -40px;
        width: 120px;
        height: 24px;
        background-color: #FF5722;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 12px;
        line-height: 24px;
        transform: rotate(-45deg);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .result-container {
        margin-top: 2rem;
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .source-box {
        background-color: #f0f7ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.9rem;
        border-left: 4px solid #4285f4;
    }
    .sidebar .sidebar-content {
        background-color: white;
    }
    .document-item {
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        transition: background-color 0.3s;
    }
    .document-item:hover {
        background-color: #f0f7ff;
    }
    .document-item.active {
        background-color: #e6f2ff;
        border-left: 3px solid #4285f4;
    }
    .stButton button {
        background-color: #4285f4;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .stButton button:hover {
        background-color: #5c9aff;
    }
    .search-box {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 8px 16px;
        margin-bottom: 20px;
        width: 100%;
    }
    .tab-container {
        display: flex;
        border-bottom: 1px solid #ddd;
        margin-bottom: 1rem;
    }
    .tab {
        padding: 0.5rem 1rem;
        cursor: pointer;
        margin-right: 1rem;
        border-bottom: 2px solid transparent;
    }
    .tab.active {
        border-bottom: 2px solid #4285f4;
        color: #4285f4;
        font-weight: 500;
    }
    .doc-checkbox {
        margin-right: 10px;
    }
    .doc-list, .saved-answers-list {
        max-height: 60vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    .upload-section {
        padding: 1.5rem;
        border: 2px dashed #ddd;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .save-button {
        color: #4285f4;
        background-color: transparent;
        border: none;
        cursor: pointer;
        float: right;
    }
    .saved-answer {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .saved-answer-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .saved-answer-title {
        font-weight: 500;
        color: #4285f4;
    }
    .saved-answer-date {
        color: #777;
        font-size: 0.8rem;
    }
    .saved-answer-content {
        color: #333;
        font-size: 0.95rem;
    }
    .saved-answer-actions {
        margin-top: 0.5rem;
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
    }
    .action-button {
        color: #777;
        background-color: transparent;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
    }
    .action-button:hover {
        color: #4285f4;
    }
    /* Suggested questions styling */
    .suggestions-container {
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .suggestions-title {
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        color: #555;
    }
    .suggestion-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .suggestion-chip {
        background-color: #e8f0fe;
        border: 1px solid #d2e3fc;
        border-radius: 16px;
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
        color: #1a73e8;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
        max-width: 100%;
    }
    .suggestion-chip:hover {
        background-color: #d2e3fc;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .suggestion-category {
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #555;
    }
    /* Improved column toggle buttons */
    .toggle-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #4285f4;
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        font-size: 11px;
        cursor: pointer;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        position: relative;
        top: 0px;
        z-index: 100;
        margin-top: 8px;
    }
    .toggle-btn:hover {
        background-color: #f5f5f5;
        color: #1a73e8;
    }
    .toggle-left {
        float: right;
        margin-right: -15px;
    }
    .toggle-right {
        float: left;
        margin-left: -15px;
    }
    /* Header styling for toggle integration */
    .column-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .column-title {
        font-size: 1.5rem;
        font-weight: 500;
        margin: 0;
    }
    /* Show answers button */
    .show-answers-btn {
        margin-top: 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: flex-end;
    }
    /* Result section styling */
    .result-heading {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 1rem;
        color: #333;
    }
    .result-content {
        font-size: 1rem;
        line-height: 1.6;
        color: #333;
    }
    .sources-heading {
        font-size: 1rem;
        font-weight: 500;
        margin: 1.5rem 0 0.5rem 0;
        color: #555;
    }
    /* Placeholder text style */
    .placeholder-text {
        color: #999;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Add POC Ribbon after CSS but before content
st.markdown("""
<div class="ribbon-container">
    <div class="ribbon">POC</div>
</div>
""", unsafe_allow_html=True)

# Function to toggle column visibility
def toggle_left_column():
    st.session_state.left_column_visible = not st.session_state.left_column_visible

def toggle_right_column():
    st.session_state.right_column_visible = not st.session_state.right_column_visible

# Function to read docx file
def read_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Function to simulate RAG retrieval
def retrieve_sources(query):
    # Only retrieve from selected documents
    selected_docs = [doc for doc in st.session_state.documents if doc.get("selected", False)]
    
    # If no documents are selected, return an empty list
    if not selected_docs:
        return []
    
    # Simulate retrieval delay
    time.sleep(1)
    
    # Generate random sources from the selected documents
    sources = random.sample(selected_docs, k=min(2, len(selected_docs)))
    return sources

# Function to simulate AI response generation
def generate_response(query, sources):
    # Simulate thinking delay
    time.sleep(1.5)
    
    # If no sources, indicate that
    if not sources:
        return "I don't have any documents selected to analyze. Please select at least one document from the list on the left side."
    
    if "paper" in query.lower() or "research" in query.lower():
        return "Based on the selected research papers, the key findings suggest a 23% improvement in efficiency using the new methodology. The authors highlight potential applications in fields ranging from healthcare to finance."
    elif "data" in query.lower() or "dataset" in query.lower():
        return "Your selected dataset contains 10,000 samples with 15 features. The data is relatively balanced with minimal missing values. I'd recommend standardizing the numeric features before proceeding with your analysis."
    elif "method" in query.lower() or "technique" in query.lower():
        return "The methodology described in your selected documents combines traditional statistical approaches with modern machine learning techniques. This hybrid approach is particularly effective for handling the kind of sparse data present in your corpus."
    elif "summarize" in query.lower() or "summary" in query.lower():
        return "The documents collectively describe a novel approach to data analysis that combines statistical methods with machine learning. Key findings include a 23% efficiency improvement and potential applications across multiple sectors. The methodology is particularly effective for sparse datasets and shows promising results in preliminary testing."
    else:
        return "Based on the documents you've selected, I can see several interesting patterns emerging. The research indicates a strong correlation between variables X and Y, with statistical significance (p<0.01). Would you like me to elaborate on any particular aspect of these findings?"

# Function to get suggested questions based on selected documents
def get_suggested_questions():
    selected_docs = [doc for doc in st.session_state.documents if doc.get("selected", False)]
    
    # If no documents selected, return generic suggestions
    if not selected_docs:
        return {
            "Getting Started": [
                "What types of documents should I upload?",
                "How does the document analysis work?",
                "Can you explain how the RAG system operates?"
            ],
            "Tasks": [
                "Help me select appropriate documents",
                "Show me an example analysis"
            ]
        }
    else:
        # Return document-specific suggestions
        return {
            "Research Questions": [
                "What are the key findings in these documents?",
                "Summarize the methodology described in these papers",
                "What are the limitations of the research?",
                "How do these findings compare to previous work?",
                "Identify potential applications of this research"
            ],
            "Analysis Tasks": [
                "Create a literature review based on these documents",
                "Extract all datasets mentioned in these papers",
                "Compare the methodologies across different papers",
                "Identify gaps in the current research",
                "Suggest future research directions"
            ],
            "Data Analysis": [
                "What's the sample size in these studies?",
                "Explain the statistical methods used",
                "Extract all tables and figures described",
                "Identify potential biases in the data collection"
            ]
        }

# Function to save an answer
def save_answer(content, sources=None):
    timestamp = datetime.now()
    
    # Create a default title based on content
    default_title = f"Answer {st.session_state.next_answer_id}"
    
    answer = {
        "id": st.session_state.next_answer_id,
        "title": default_title,
        "content": content,
        "sources": sources if sources else [],
        "timestamp": timestamp,
        "date_str": timestamp.strftime("%Y-%m-%d %H:%M")
    }
    
    st.session_state.saved_answers.append(answer)
    st.session_state.next_answer_id += 1
    return answer["id"]

# Function to export answer as txt
def export_as_txt(answer):
    content = f"Title: {answer['title']}\n"
    content += f"Date: {answer['date_str']}\n\n"
    content += f"{answer['content']}\n\n"
    
    if answer['sources']:
        content += "Sources:\n"
        for src in answer['sources']:
            content += f"- {src['title']} ({src['type']})\n"
    
    return content

# Function to export answers as xlsx
def export_as_xlsx(answers):
    # Create DataFrame
    data = []
    for answer in answers:
        sources_str = ", ".join([f"{s['title']} ({s['type']})" for s in answer['sources']]) if answer['sources'] else ""
        data.append({
            "Title": answer['title'],
            "Content": answer['content'],
            "Date": answer['date_str'],
            "Sources": sources_str
        })
    
    df = pd.DataFrame(data)
    
    # Create a bytes buffer
    output = io.BytesIO()
    
    # Write to Excel
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Saved Answers', index=False)
        
    return output.getvalue()

# Check if a suggestion was selected
if st.session_state.selected_suggestion is not None:
    user_input = st.session_state.selected_suggestion
    st.session_state.selected_suggestion = None
    
    # Get sources from RAG system
    with st.spinner("Searching through your documents..."):
        sources = retrieve_sources(user_input)
    
    # Generate AI response
    with st.spinner("Crafting response..."):
        response = generate_response(user_input, sources)
    
    # Update current answer
    st.session_state.current_answer = {
        "query": user_input,
        "response": response,
        "sources": sources
    }
    
    st.rerun()

# Determine column widths based on visibility
if st.session_state.left_column_visible and st.session_state.right_column_visible:
    # All columns visible
    col_widths = [1, 1.5, 1]
elif st.session_state.left_column_visible and not st.session_state.right_column_visible:
    # Only left and middle visible
    col_widths = [1, 2.5, 0.0001]  # Tiny width for hidden column
elif not st.session_state.left_column_visible and st.session_state.right_column_visible:
    # Only middle and right visible
    col_widths = [0.0001, 2.5, 1]
else:
    # Only middle visible
    col_widths = [0.0001, 3, 0.0001]

# Main layout with three columns
left_col, middle_col, right_col = st.columns(col_widths)

# Left column - Document Management
with left_col:
    if st.session_state.left_column_visible:
        # Column header with toggle button
        left_toggle = "◀" if st.session_state.left_column_visible else "▶"
        
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown("## 📁 Document Library")
        with col2:
            if st.button(left_toggle, key="toggle_left_column", help="Hide document panel", 
                        type="secondary", use_container_width=True):
                toggle_left_column()
                st.rerun()
        
        # Document upload section
        st.markdown("### Upload New Document")
        uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])
        
        if uploaded_file is not None:
            try:
                # Process the uploaded docx file
                content = read_docx(uploaded_file)
                
                # Create a new document entry
                new_doc = {
                    "id": st.session_state.next_doc_id,
                    "title": uploaded_file.name,
                    "content": content,
                    "type": "DOCX",
                    "selected": True  # Auto-select newly uploaded documents
                }
                
                # Add to documents list
                st.session_state.documents.append(new_doc)
                st.session_state.next_doc_id += 1
                
                st.success(f"Successfully uploaded: {uploaded_file.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error processing file: {e}")
        
        # Document list with checkboxes for selection
        st.markdown("### Available Documents")
        
        # Search filter for documents
        doc_search = st.text_input("🔍 Search documents", "")
        
        st.markdown("#### Select documents for analysis:")
        
        # Display document list with scrollbar
        st.markdown('<div class="doc-list">', unsafe_allow_html=True)
        
        for doc in st.session_state.documents:
            # Apply search filter
            if doc_search.lower() in doc["title"].lower() or doc_search == "":
                # Create a unique key for each checkbox
                checkbox_key = f"doc_select_{doc['id']}"
                
                # Display document with checkbox
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    if st.checkbox("", value=doc.get("selected", False), key=checkbox_key):
                        doc["selected"] = True
                    else:
                        doc["selected"] = False
                
                with col2:
                    st.markdown(f"""
                    <div class="document-item">
                        <small>{doc['type']}</small><br>
                        {doc['title']}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display count of selected documents
        selected_count = sum(1 for doc in st.session_state.documents if doc.get("selected", False))
        st.info(f"{selected_count} document(s) selected for analysis")

# Show expand button for left column if hidden        
if not st.session_state.left_column_visible:
    st.sidebar.markdown('<br>', unsafe_allow_html=True)
    if st.sidebar.button("▶ Show Documents", key="expand_left"):
        toggle_left_column()
        st.rerun()

# Middle column - One-Turn Generation Interface
with middle_col:
    # Interface title
    st.markdown("## Research Assistant")
    st.markdown("Ask a question about your selected documents and get an AI-generated response.")
    
    # Display suggested questions as clickable chips
    suggested_questions = get_suggested_questions()
    
    st.markdown('<div class="suggestions-container">', unsafe_allow_html=True)
    st.markdown('<div class="suggestions-title">Try asking one of these questions:</div>', unsafe_allow_html=True)
    
    # Display suggestion categories
    for category, questions in suggested_questions.items():
        st.markdown(f'<div class="suggestion-category">{category}:</div>', unsafe_allow_html=True)
        st.markdown('<div class="suggestion-chips">', unsafe_allow_html=True)
        
        # Display each suggestion as a clickable chip
        for idx, question in enumerate(questions):
            question_id = f"sugg_{category}_{idx}"
            
            # Create a clickable suggestion chip that sets session state
            col = st.columns([1])[0]
            with col:
                if st.button(question, key=question_id):
                    st.session_state.selected_suggestion = question
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area with placeholder text
    user_input = st.text_area(
        "Enter your question:",
        placeholder="e.g., Summarize the key points from these documents...",
        key="query_input", 
        height=100
    )
    
    # Generate button
    col1, col2 = st.columns([1, 7])
    with col1:
        if st.button("Generate", key="generate_button"):
            if user_input:
                # Get sources from RAG system
                with st.spinner("Searching through your documents..."):
                    sources = retrieve_sources(user_input)
                
                # Generate AI response
                with st.spinner("Generating response..."):
                    response = generate_response(user_input, sources)
                
                # Update current answer
                st.session_state.current_answer = {
                    "query": user_input,
                    "response": response,
                    "sources": sources
                }
                
                # Rerun to display result
                st.rerun()
    
    # Clear button
    with col2:
        if st.session_state.current_answer and st.button("Clear", key="clear_button"):
            st.session_state.current_answer = None
            st.rerun()
    
    # Display result if available
    if st.session_state.current_answer:
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        
        # Save button for the response
        save_col1, save_col2 = st.columns([7, 1])
        with save_col2:
            if st.button("💾 Save", key="save_result"):
                save_answer(
                    st.session_state.current_answer["response"], 
                    st.session_state.current_answer["sources"]
                )
                st.success("Answer saved successfully!")
                time.sleep(1)
                st.rerun()
        
        # Display the result
        st.markdown(f"""
        <div class="result-heading">Response to: <em>{st.session_state.current_answer['query']}</em></div>
        <div class="result-content">
            {st.session_state.current_answer['response']}
        </div>
        """, unsafe_allow_html=True)
        
        # Display sources if any
        if st.session_state.current_answer['sources']:
            st.markdown('<div class="sources-heading">Sources:</div>', unsafe_allow_html=True)
            
            for src in st.session_state.current_answer['sources']:
                title = src.get("title", "Untitled")
                doc_type = src.get("type", "Document")
                content = src.get("content", "No content available")
                
                st.markdown(f"""
                <div class="source-box">
                    <strong>{title}</strong><br>
                    <small>{doc_type} · Relevant excerpt</small><br>
                    {content[:200]}...
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show expand button for right column if hidden
    if not st.session_state.right_column_visible:
        st.markdown("""
        <div class="show-answers-btn" style="text-align: right; margin-top: 20px;">
        """, unsafe_allow_html=True)
        
        right_col_button = st.button("◀ Show Saved Answers", key="expand_right", help="Show saved answers panel")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if right_col_button:
            toggle_right_column()
            st.rerun()

# Right column - Saved Answers
with right_col:
    if st.session_state.right_column_visible:
        # Column header with toggle button
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.button("▶", key="toggle_right_column", help="Hide saved answers panel", 
                        type="secondary", use_container_width=True):
                toggle_right_column()
                st.rerun()
        with col2:
            st.markdown("## 📌 Saved Answers")
        
        # Export All Answers buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All as TXT"):
                if st.session_state.saved_answers:
                    # Combine all answers into a single TXT file
                    all_content = ""
                    for answer in st.session_state.saved_answers:
                        all_content += export_as_txt(answer)
                        all_content += "\n" + "-"*50 + "\n\n"  # Separator
                    
                    # Create download button
                    st.download_button(
                        label="Download TXT",
                        data=all_content,
                        file_name="all_saved_answers.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("No saved answers to export")
        
        with col2:
            if st.button("Export All as XLSX"):
                if st.session_state.saved_answers:
                    # Export all answers as XLSX
                    excel_data = export_as_xlsx(st.session_state.saved_answers)
                    
                    # Create download button
                    st.download_button(
                        label="Download XLSX",
                        data=excel_data,
                        file_name="all_saved_answers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No saved answers to export")
        
        # Display saved answers
        if not st.session_state.saved_answers:
            st.info("No saved answers yet. Use the '💾 Save' button when you get a response.")
        else:
            st.markdown("### Your Saved Research Notes")
            st.markdown('<div class="saved-answers-list">', unsafe_allow_html=True)
            
            # Display each saved answer
            for answer in sorted(st.session_state.saved_answers, key=lambda x: x["timestamp"], reverse=True):
                # Title editing mode
                if st.session_state.editing_title == answer["id"]:
                    new_title = st.text_input("Edit title", answer["title"], key=f"edit_title_{answer['id']}")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Save Title", key=f"save_title_{answer['id']}"):
                            answer["title"] = new_title
                            st.session_state.editing_title = None
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_edit_{answer['id']}"):
                            st.session_state.editing_title = None
                            st.rerun()
                else:
                    # Display the saved answer card
                    st.markdown(f"""
                    <div class="saved-answer">
                        <div class="saved-answer-header">
                            <div class="saved-answer-title">{answer['title']}</div>
                            <div class="saved-answer-date">{answer['date_str']}</div>
                        </div>
                        <div class="saved-answer-content">{answer['content'][:300]}{"..." if len(answer['content']) > 300 else ""}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                    
                    with col1:
                        # Rename button
                        if st.button("Rename", key=f"rename_{answer['id']}"):
                            st.session_state.editing_title = answer["id"]
                            st.rerun()
                    
                    with col2:
                        # Export as TXT button
                        txt_content = export_as_txt(answer)
                        st.download_button(
                            label="Export TXT",
                            data=txt_content,
                            file_name=f"{answer['title'].replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"export_txt_{answer['id']}"
                        )
                    
                    with col3:
                        # View full button (for long answers)
                        if len(answer['content']) > 300:
                            if st.button("View Full", key=f"view_{answer['id']}"):
                                st.info(answer['content'])
                    
                    with col4:
                        # Delete button
                        if st.button("Delete", key=f"delete_{answer['id']}"):
                            st.session_state.saved_answers = [a for a in st.session_state.saved_answers if a['id'] != answer['id']]
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
