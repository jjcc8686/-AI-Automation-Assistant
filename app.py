import streamlit as st
import zipfile
import io
import re

# ====================== OLETOOLS AVAILABILITY CHECK ======================
try:
    from oletools.olevba import VBA_Parser
    OLETOOLS_AVAILABLE = True
except ImportError:
    OLETOOLS_AVAILABLE = False

st.set_page_config(
    page_title="AI Automation Assistant",
    page_icon="🤖",
    layout="wide"
)

# ====================== PASSWORD PROTECTION ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🤖 AI Automation Assistant")
    password = st.text_input("Enter application password", type="password")
    if st.button("Login"):
        if password == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

# ====================== HELPER FUNCTION: VBA EXTRACTION ======================
def extract_vba_code(uploaded_file):
    """Extract VBA code from .xlsm/.xlsb using oletools or return text content for other files."""
    if not uploaded_file:
        return ""
    
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()
    
    try:
        if file_name.endswith(('.xlsm', '.xlsb')):
            if not OLETOOLS_AVAILABLE:
                return "⚠️ oletools is not installed. Please add 'oletools' to requirements.txt and restart the app."
            
            vbaparser = VBA_Parser(file_name, data=file_bytes)
            
            if vbaparser.detect_vba_macros():
                vba_code = ""
                for (_, _, vba_filename, vba_code_chunk) in vbaparser.extract_macros():
                    vba_code += f"''' Module: {vba_filename} '''\n{vba_code_chunk}\n\n"
                vbaparser.close()
                return vba_code.strip()
            else:
                vbaparser.close()
                return "No VBA macros detected in the uploaded Excel file."
        else:
            return file_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error extracting file content: {str(e)}\n\nFor .xlsm/.xlsb files, ensure oletools is installed."

# ====================== HELPER FUNCTION: POWER QUERY M CODE EXTRACTION ======================
import base64
import xml.etree.ElementTree as ET
import struct

def extract_powerquery_m_code(uploaded_file):
    if not uploaded_file:
        return ""

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    # Only support direct text-based M code
    if file_name.endswith(('.m', '.pq', '.txt')):
        return file_bytes.decode("utf-8", errors="replace")

    return "⚠️ Excel files do not embed Power Query M code. Please export the query using Power Query → Advanced Editor → Save as .txt."

# ====================== HELPER FUNCTION: VBA CHUNKING ======================
def chunk_vba_code(vba_code, max_chunk_size=800):
    """
    Chunk VBA code into meaningful segments based on Sub/Function boundaries.
    Falls back to character-based chunking if needed.
    """
    if not vba_code or len(vba_code.strip()) == 0:
        return []

    chunks = []
    current_chunk = ""

    lines = vba_code.split("\n")

    for line in lines:
        # VBA boundaries: Sub, Function, End Sub, End Function
        if (line.strip().lower().startswith(("sub ", "function ")) and current_chunk):
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

        # Safety: prevent overly large chunks
        if len(current_chunk) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = ""

    # Add last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# ====================== HELPER FUNCTION: POWER QUERY CHUNKING ======================
def chunk_m_code(m_code, max_chunk_size=800):
    """
    Chunk Power Query M code into meaningful segments based on step boundaries.
    Falls back to character-based chunking if needed.
    """
    if not m_code or len(m_code.strip()) == 0:
        return []

    chunks = []
    current_chunk = ""

    lines = m_code.split("\n")

    for line in lines:
        # Step boundaries usually start with #"Step Name"
        if line.strip().startswith("#") and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

        # Safety: prevent overly large chunks
        if len(current_chunk) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = ""

    # Add last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# ====================== HELPER FUNCTION: UiPath XAML CHUNKING ======================
def chunk_xaml_code(xaml_code, max_chunk_size=800):
    """
    Chunk UiPath XAML into segments based on activity boundaries.
    Simple heuristic: split on lines containing '<ui:' or '<Sequence' or '<Workflow'.
    """
    if not xaml_code or len(xaml_code.strip()) == 0:
        return []

    chunks = []
    current_chunk = ""

    lines = xaml_code.split("\n")

    for line in lines:
        if (("<ui:" in line or "<Sequence" in line or "<Workflow" in line) and current_chunk):
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

        if len(current_chunk) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = ""

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


import faiss
import numpy as np
from openai import OpenAI

# ====================== RAG: EMBEDDINGS ======================
def embed_chunks(chunks):
    """

    Generate embeddings for each chunk using OpenAI embeddings.
    Returns a list of embedding vectors.
    """


    client = OpenAI(api_key=st.secrets["openai_api_key"])

    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=chunks
    )

    embeddings = [item.embedding for item in response.data]
    return embeddings


# ====================== RAG: BUILD VECTOR STORE ======================
def build_vector_store(chunks):
    """
    Build a FAISS vector store from chunk embeddings.
    Returns the FAISS index and the original chunks.
    """
    embeddings = embed_chunks(chunks)

    # Convert to numpy array
    embeddings_np = np.array(embeddings).astype("float32")

    # Create FAISS index
    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)

    return index, chunks

# ====================== RAG: RETRIEVAL ======================
def retrieve_relevant_chunks(query, index, chunks, k=3):
    """
    Retrieve the top-k most relevant chunks for a given query.
    Returns list of (chunk, confidence_score).
    """
    client = OpenAI(api_key=st.secrets["openai_api_key"])

    # Embed the query
    query_embedding = client.embeddings.create(
        model="text-embedding-3-large",
        input=[query]
    ).data[0].embedding

    query_np = np.array([query_embedding]).astype("float32")

    # Search FAISS index
    distances, indices = index.search(query_np, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        confidence = 1 / (1 + dist)
        results.append((chunks[idx], confidence))

    return results

# ====================== SIDEBAR NAVIGATION ======================
page = st.sidebar.selectbox(
    "Navigation",
    ["AI Tools", "Power Query Export Guide", "About Us", "Methodology"]
)

if page == "AI Tools":
    st.title("🤖 AI Automation Assistant")

    with st.expander("⚠️ IMPORTANT NOTICE — Please Read"):
        st.markdown("""
        **This web application is developed as a proof-of-concept prototype.**

        The information provided here is **NOT** intended for actual usage and should **not** be relied upon for making any decisions, especially those related to **financial, legal, or healthcare matters**.

        The LLM may generate **inaccurate or incorrect information**.  
        You assume **full responsibility** for how you use any generated output.

        Always consult **qualified professionals** for accurate and personalised advice.
        """)

    st.markdown("**Select a service below, upload a file, and provide your instructions.**")

    option = st.selectbox(
        "Choose an option:",
        ["Review Excel VBA", "Review Excel PowerQuery", "Create UiPath Workflows (XAML)"]
    )

    uploaded_file = None
    user_prompt = ""


    # ====================== OPTION SELECTORS ======================
    if option == "Review Excel VBA":
        st.subheader("📋 Review Excel VBA")
        uploaded_file = st.file_uploader(
            "Upload VBA code file (.txt) or Excel macro-enabled workbook (.xlsm, .xlsb)",
            type=["txt", "xlsm", "xlsb"]
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Review the uploaded VBA code for best practices, potential errors, performance improvements, and security issues.",
            height=150
        )

    elif option == "Review Excel PowerQuery":
        st.subheader("📋 Review Excel PowerQuery")
        uploaded_file = st.file_uploader(
            "Upload PowerQuery M code file (.txt, .m, .pq)",
            type=["txt", "m", "pq"]
        )
        st.info(
            "Excel files (.xlsx/.xlsm/.xlsb) often do **not** embed Power Query M code.\n"
            "To extract M code reliably:\n"
            "1. Open Power Query Editor\n"
            "2. Go to **Advanced Editor**\n"
            "3. Copy the M code\n"
            "4. Save it as a `.txt` file\n"
            "5. Upload the `.txt` file here"
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Review the extracted Power Query M code for efficiency, readability, error handling, and optimization opportunities.",
            height=150
        )

    else:  # Create UiPath Workflows
        st.subheader("🔧 Create / Modify UiPath Workflows (XAML)")
        uploaded_file = st.file_uploader(
            "Upload existing XAML file (optional)",
            type=["xaml", "txt"]
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Create a complete UiPath XAML workflow that performs the following automation task:",
            height=150
        )

    # ====================== FILE PROCESSING (FIXED POSITION) ======================
    file_content = ""
    if uploaded_file is not None:
        if option == "Review Excel VBA":
            file_content = extract_vba_code(uploaded_file)
            chunks = chunk_vba_code(file_content)
            index, stored_chunks = build_vector_store(chunks)
            st.session_state["vba_index"] = index
            st.session_state["vba_chunks"] = stored_chunks

        elif option == "Review Excel PowerQuery":
            file_content = extract_powerquery_m_code(uploaded_file)
            chunks = chunk_m_code(file_content)
            index, stored_chunks = build_vector_store(chunks)
            st.session_state["pq_index"] = index
            st.session_state["pq_chunks"] = stored_chunks

        else:  # UiPath
            file_content = uploaded_file.getvalue().decode("utf-8", errors="replace")
            if file_content.strip():
                chunks = chunk_xaml_code(file_content)
                if chunks:
                    index, stored_chunks = build_vector_store(chunks)
                    st.session_state["uipath_index"] = index
                    st.session_state["uipath_chunks"] = stored_chunks

        st.success(f"✅ File uploaded successfully: **{uploaded_file.name}**")

        with st.expander("📜 Preview of extracted file content (first 2,000 characters)"):
            st.code(
                file_content[:2000] + ("..." if len(file_content) > 2000 else ""),
                language="vb" if option == "Review Excel VBA" else "text"
            )

        # ====================== POWER QUERY WARNING ======================
        if option == "Review Excel PowerQuery":
            if uploaded_file.name.lower().endswith(("xlsx", "xlsm", "xlsb")):
                if file_content == "No Power Query M code found.":
                    st.warning(
                        "⚠️ This Excel file does not contain embedded Power Query M code.\n\n"
                        "To review Power Query code:\n"
                        "1. Open Power Query Editor\n"
                        "2. Go to **Advanced Editor**\n"
                        "3. Copy the M code\n"
                        "4. Save it as a `.txt` file\n"
                        "5. Upload the `.txt` file here\n\n"
                        "This behaviour is normal — many Excel files store queries externally."
                    )

# ====================== PROCESS BUTTON (ONLY ON AI TOOLS) ======================
if page == "AI Tools":
    if st.button("🚀 Process Request", type="primary", use_container_width=True):

        if not user_prompt.strip():
            st.error("⚠️ Please enter your instructions / prompt before processing.")
        else:
            # ---------- RAG RETRIEVAL ----------
            retrieved_chunks = []
            retrieved_scores = []

            if option == "Review Excel VBA":
                if "vba_index" in st.session_state and "vba_chunks" in st.session_state:
                    retrieved_results = retrieve_relevant_chunks(
                        user_prompt,
                        st.session_state["vba_index"],
                        st.session_state["vba_chunks"],
                        k=3
                    )
                    retrieved_chunks = [c for c, s in retrieved_results]
                    retrieved_scores = [s for c, s in retrieved_results]

            elif option == "Review Excel PowerQuery":
                if "pq_index" in st.session_state and "pq_chunks" in st.session_state:
                    retrieved_results = retrieve_relevant_chunks(
                        user_prompt,
                        st.session_state["pq_index"],
                        st.session_state["pq_chunks"],
                        k=3
                    )
                    retrieved_chunks = [c for c, s in retrieved_results]
                    retrieved_scores = [s for c, s in retrieved_results]

            elif option == "Create UiPath Workflows (XAML)":
                if "uipath_index" in st.session_state and "uipath_chunks" in st.session_state:
                    retrieved_results = retrieve_relevant_chunks(
                        user_prompt,
                        st.session_state["uipath_index"],
                        st.session_state["uipath_chunks"],
                        k=3
                    )
                    retrieved_chunks = [c for c, s in retrieved_results]
                    retrieved_scores = [s for c, s in retrieved_results]

            # ---------- RAG EXPANDERS ----------
            if retrieved_chunks:
                if option == "Review Excel VBA":
                    with st.expander("🔍 RAG Retrieved VBA Chunks & Confidence Scores"):
                        for i, (chunk, score) in enumerate(zip(retrieved_chunks, retrieved_scores)):
                            st.markdown(f"### Chunk {i+1} — Confidence: **{score:.2f}**")
                            st.code(chunk, language="vb")

                elif option == "Review Excel PowerQuery":
                    with st.expander("🔍 RAG Retrieved PowerQuery Chunks & Confidence Scores"):
                        for i, (chunk, score) in enumerate(zip(retrieved_chunks, retrieved_scores)):
                            st.markdown(f"### Chunk {i+1} — Confidence: **{score:.2f}**")
                            st.code(chunk, language="text")

                elif option == "Create UiPath Workflows (XAML)":
                    with st.expander("🔍 RAG Retrieved UiPath XAML Chunks & Confidence Scores"):
                        for i, (chunk, score) in enumerate(zip(retrieved_chunks, retrieved_scores)):
                            st.markdown(f"### Chunk {i+1} — Confidence: **{score:.2f}**")
                            st.code(chunk, language="xml")

            # ---------- OPENAI CALL ----------
            with st.spinner("Processing request with OpenAI..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai_api_key"])

                    # ====================== SYSTEM PROMPT SELECTION ======================
                    if option == "Review Excel VBA":
                        system_prompt = """You are an expert Excel VBA developer and code reviewer with deep knowledge of oletools (olevba + mraptor).
                        Always reference oletools/mraptor analysis techniques when reviewing code.
                        Use mraptor-style detection to identify malicious/suspicious patterns such as:
                        - Auto-executing macros (AutoOpen, Workbook_Open, etc.)
                        - Obfuscation techniques
                        - Suspicious API calls / shellcode
                        - Potential malware indicators

                        Additionally, pay special attention to redundant Sub / Function creation:
                        - Duplicate or nearly identical Sub procedures
                        - Unnecessary repeated Subs that can be consolidated into a single reusable procedure
                        - Redundant code blocks that can be refactored

                        Provide a professional, structured review that includes:
                        - Best practices and maintainability
                        - Performance improvements
                        - Security issues (with mraptor-based risk assessment)
                        - Bug detection
                        - Identification and removal of redundant Subs / Functions
                        - Refactored code suggestions

                        Structure your response clearly with headings and bullet points."""

                    elif option == "Review Excel PowerQuery":
                        system_prompt = """You are an expert Power Query (M language) developer and code reviewer.
                        Provide detailed, professional feedback focusing on:
                        - Efficiency and performance optimization
                        - Readability and maintainability
                        - Error handling and robustness
                        - Redundant referencing (repeated Table.SelectColumns, Table.AddColumn, or referencing the same table multiple times unnecessarily)
                        - Performance bottlenecks (avoiding heavy operations inside loops, unnecessary Table.Buffer usage, etc.)
                        - Opportunities to reduce steps and improve query folding

                        Highlight any redundant referencing patterns and suggest cleaner, more performant alternatives.
                        Structure your response clearly with headings and bullet points."""

                    else:  # Create UiPath Workflows
                        system_prompt = """You are an expert UiPath RPA developer.

                        Your task:
                        - Generate or modify UiPath workflows using valid XAML.
                        - Use the RAG context provided to understand the existing workflow structure.
                        - If RAG context is present, preserve namespaces, structure, and activity hierarchy.
                        - If no RAG context is present, generate a clean workflow from scratch.

                        STRICT RULES:
                        - Output ONLY valid XAML.
                        - Do NOT include explanations, markdown, comments outside XML, or conversational text.
                        - The root element MUST be <Activity>, <Workflow>, or <Sequence>.
                        - All required UiPath namespaces MUST be included.
                        - The output MUST be directly loadable in UiPath Studio without errors.
                        - If modifying an existing workflow, keep the original structure unless the user explicitly requests changes.

                        Your output must be production-ready UiPath XAML.
                        """

                    # ====================== BUILD USER MESSAGE (WITH RAG) ======================
                    rag_context = ""
                    if retrieved_chunks:
                        for chunk, score in zip(retrieved_chunks, retrieved_scores):
                            rag_context += f"[Confidence {score:.2f}]\n{chunk}\n\n"

                    user_message = (
                        f"{user_prompt}\n\n"
                        f"--- RELEVANT CONTEXT (RAG) ---\n{rag_context}\n\n"
                        f"--- FULL FILE CONTENT ---\n{file_content}"
                    )

                    # ====================== OPENAI CALL ======================
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.3,
                        max_tokens=4000
                    )

                    ai_response = response.choices[0].message.content

                except Exception as e:
                    ai_response = (
                        f"❌ Error connecting to OpenAI: {str(e)}\n\n"
                        "Please verify your API key in .streamlit/secrets.toml."
                    )

            # ====================== DISPLAY RESPONSE ======================
            st.subheader("📤 AI Response")
            st.markdown(ai_response)

            if "Create UiPath" in option:
                st.download_button(
                    label="📥 Download Generated XAML",
                    data=ai_response,
                    file_name="generated_workflow.xaml",
                    mime="application/xml"
                )


# ====================== POWER QUERY EXPORT GUIDE ======================
if page == "Power Query Export Guide":
    st.title("📤 Power Query Export Guide")
    st.markdown("""
    ### How to Export Power Query M Code

    Excel does **not** embed M code inside `.xlsx`, `.xlsm`, or `.xlsb` files.

    To export your Power Query M code:

    1. Open **Power Query Editor**
    2. Click **Advanced Editor**
    3. Copy all the M code
    4. Paste it into a `.txt`, `.m`, or `.pq` file
    5. Upload that file in the AI Tools page
    """)

# ====================== ABOUT US PAGE ======================
if page == "About Us":
    st.title("About Us")
    st.markdown("""
    ### Project Title: AI Automation Assistant

    **Project Scope**  
    This web application provides an intelligent AI-powered assistant for Excel automation developers and RPA practitioners.

    **Key Features**  
    - Native VBA macro extraction from .xlsm and .xlsb files using oletools  
    - Native Power Query M code extraction from Excel workbooks  
    - Secure OpenAI integration via Streamlit secrets  

    **Contact Us**  
    - Chng Chyi Da - chng_chyi_da@vital.gov.sg  
    - Jean Chua Yi Juan - jean_chua@vital.gov.sg  
    - Lim Yi Jun - lim_yi_jun@vital.gov.sg
    """)

# ====================== METHODOLOGY PAGE ======================
if page == "Methodology":
    st.title("📋 Methodology")
    st.markdown("""
    ### Overview
    The AI Automation Assistant is built using a modular and secure architecture. It enables users to review Excel VBA and PowerQuery code or generate UiPath workflows through an intuitive web interface powered by large language models.
    """)

    st.header("Use Case 1: Excel & VBA Analysis")
    st.markdown("""
    User Uploads Excel File<br>
    ↓<br>
    Identify File Type (.xlsx / .xlsm / .xlsb / .xls)<br>
    ↓<br>
    Extract Sheet Data (pandas / openpyxl)<br>
    ↓<br>
    Check If File Contains VBA<br>
    ↓<br>
    Yes → Extract VBA (oletools or fallback)<br>
    No → Skip VBA Extraction<br>
    ↓<br>
    Combine Extracted Data + VBA (if any)<br>
    ↓<br>
    Store Content for RAG<br>
    ↓<br>
    Display Results in Streamlit
    """, unsafe_allow_html=True)


    st.header("Use Case 2: Power Query M Code Analysis")
    st.markdown("""
    User Uploads Power Query File (.txt / .m / .pq)<br>
    ↓<br>
    Read File Content (text extraction)<br>
    ↓<br>
    Validate M Code Format<br>
    ↓<br>
    Store Extracted M Code for RAG<br>
    ↓<br>
    Embed M Code (OpenAI Embeddings)<br>
    ↓<br>
    FAISS Index Updated<br>
    ↓<br>
    Display M Code + AI Insights in Streamlit
    """, unsafe_allow_html=True)

    st.header("Use Case 3: UiPath Workflow Generation")
    st.markdown("""
    User Selects UiPath Workflow Generation<br>
    ↓<br>
    User Provides Description of Desired Automation<br>
    ↓<br>
    Embed User Description (OpenAI Embeddings)<br>
    ↓<br>
    Generate UiPath Workflow Steps (LLM)<br>
    ↓<br>
    Format Output into UiPath-Compatible Structure<br>
    ↓<br>
    Display Workflow Steps in Streamlit
    """, unsafe_allow_html=True)