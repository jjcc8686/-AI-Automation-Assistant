import streamlit as st
import faiss
import numpy as np
from openai import OpenAI
from datetime import datetime

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

# ====================== SESSION STATE INITIALIZATION ======================
defaults = {
    "authenticated": False,
    "role": None,
    "history": [],
    "uploader_key": 0,
    "current_page": "AI Tools",
    "dark_mode": False,
    "kb_index": None,
    "kb_chunks": [],
    "kb_files": []
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ====================== LOGIN ======================
if not st.session_state.authenticated:
    st.title("🤖 AI Automation Assistant")
    st.markdown("### Login")
    role_choice = st.radio("Select role", ["User", "Admin"], horizontal=True)
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if role_choice == "Admin" and password == st.secrets.get("admin_password", ""):
            st.session_state.authenticated = True
            st.session_state.role = "admin"
            st.rerun()
        elif role_choice == "User" and password == st.secrets.get("user_password", ""):
            st.session_state.authenticated = True
            st.session_state.role = "user"
            st.rerun()
        else:
            st.error("Incorrect password for the selected role.")
    st.stop()

# ====================== HELPER FUNCTIONS ======================
def detect_code_type(content: str) -> str:
    if not content or not content.strip():
        return "unknown"
    content_lower = content.lower()
    if any(k in content for k in ["<Activity", "<Sequence", "xmlns:ui=", "<ui:", "x:Class="]):
        return "uipath"
    if "let" in content_lower and "in" in content_lower and any(k in content for k in ['#"', "Table.", "Source ="]):
        return "powerquery"
    if any(k in content_lower for k in ["sub ", "function ", "end sub", "end function", "option explicit", "dim "]):
        return "vba"
    return "unknown"


def extract_vba_code(uploaded_file):
    if not uploaded_file:
        return ""
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()
    try:
        if file_name.endswith((".xlsm", ".xlsb")):
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
        return f"Error extracting file content: {str(e)}"


def extract_powerquery_m_code(uploaded_file):
    if not uploaded_file:
        return ""
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()
    if file_name.endswith((".m", ".pq", ".txt")):
        return file_bytes.decode("utf-8", errors="replace")
    return ("⚠️ Excel files do not embed Power Query M code. "
            "Please export the query using Power Query → Advanced Editor → Save as .txt.")


def chunk_text(text, max_chunk_size=800, mode="generic"):
    if not text or not text.strip():
        return []
    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        trigger = False
        if mode == "vba" and line.strip().lower().startswith(("sub ", "function ")) and current_chunk:
            trigger = True
        elif mode == "m" and line.strip().startswith("#") and current_chunk:
            trigger = True
        elif mode == "xaml" and any(k in line for k in ["<ui:", "<Sequence", "<Workflow"]) and current_chunk:
            trigger = True

        if trigger:
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


def embed_chunks(chunks):
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=chunks
    )
    return [item.embedding for item in response.data]


def build_vector_store(chunks):
    embeddings = embed_chunks(chunks)
    embeddings_np = np.array(embeddings).astype("float32")
    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)
    return index, chunks


def retrieve_relevant_chunks(query, index, chunks, k=3):
    if index is None or not chunks:
        return []
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    query_embedding = client.embeddings.create(
        model="text-embedding-3-large",
        input=[query]
    ).data[0].embedding
    query_np = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query_np, min(k, len(chunks)))
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(chunks):
            confidence = 1 / (1 + dist)
            results.append((chunks[idx], confidence))
    return results


# ====================== SIDEBAR NAVIGATION ======================
st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state.role.upper()}**")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🧭 Main")
if st.sidebar.button("AI Tools", use_container_width=True,
                     type="primary" if st.session_state.current_page == "AI Tools" else "secondary"):
    st.session_state.current_page = "AI Tools"
    st.rerun()
if st.sidebar.button("Review History", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Review History" else "secondary"):
    st.session_state.current_page = "Review History"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Guides & Info")
if st.sidebar.button("Power Query Export Guide", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Power Query Export Guide" else "secondary"):
    st.session_state.current_page = "Power Query Export Guide"
    st.rerun()
if st.sidebar.button("Methodology", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Methodology" else "secondary"):
    st.session_state.current_page = "Methodology"
    st.rerun()
if st.sidebar.button("About Us", use_container_width=True,
                     type="primary" if st.session_state.current_page == "About Us" else "secondary"):
    st.session_state.current_page = "About Us"
    st.rerun()
if st.sidebar.button("Sample Files", use_container_width=True,
                     type="primary" if st.session_state.current_page == "Sample Files" else "secondary"):
    st.session_state.current_page = "Sample Files"
    st.rerun()

if st.session_state.role == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 Admin")
    if st.sidebar.button("Knowledge Base", use_container_width=True,
                         type="primary" if st.session_state.current_page == "Knowledge Base" else "secondary"):
        st.session_state.current_page = "Knowledge Base"
        st.rerun()

st.sidebar.markdown("---")

# Dark Mode Toggle
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode

if dark_mode:
    st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #1a1d24 !important;
        }
        .stMarkdown, .stMarkdown p, .stMarkdown span,
        h1, h2, h3, h4, h5, h6, label {
            color: #fafafa !important;
        }
        .stTextArea textarea, .stTextInput input {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        .streamlit-expanderHeader {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #f0f2f6 !important;
        }
        .stMarkdown, .stMarkdown p, .stMarkdown span,
        h1, h2, h3, h4, h5, h6, label {
            color: #1a1a1a !important;
        }
        .stTextArea textarea, .stTextInput input {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #d0d0d0 !important;
        }
        .streamlit-expanderHeader {
            background-color: #f0f2f6 !important;
            color: #1a1a1a !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("AI Automation Assistant v1.1")
st.sidebar.caption("For best widget colours, also set theme in ⋮ → Settings → Theme")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

page = st.session_state.current_page

# ====================== AI TOOLS PAGE ======================
if page == "AI Tools":
    st.title("🤖 AI Automation Assistant")
    st.markdown("**Select a service, upload file(s), and provide your instructions.**")
    st.markdown("---")

    option = st.selectbox(
        "Choose an option:",
        ["Review Excel VBA", "Review Excel PowerQuery", "Review UiPath Code"]
    )

    uploaded_files = []
    user_prompt = ""
    file_content = ""
    all_chunks = []

    if option == "Review Excel VBA":
        st.subheader("📋 Review Excel VBA")
        uploaded_files = st.file_uploader(
            "Upload VBA code files (.txt) or Excel macro-enabled workbooks (.xlsm, .xlsb)",
            type=["txt", "xlsm", "xlsb"],
            accept_multiple_files=True,
            key=f"vba_uploader_{st.session_state.uploader_key}"
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Review the uploaded VBA code for best practices, potential errors, performance improvements, security issues, and UiPath compatibility if applicable.",
            height=150
        )

    elif option == "Review Excel PowerQuery":
        st.subheader("📋 Review Excel PowerQuery")
        uploaded_files = st.file_uploader(
            "Upload PowerQuery M code files (.txt, .m, .pq)",
            type=["txt", "m", "pq"],
            accept_multiple_files=True,
            key=f"pq_uploader_{st.session_state.uploader_key}"
        )
        st.info(
            "Excel files (.xlsx/.xlsm/.xlsb) often do **not** embed Power Query M code.\n\n"
            "To extract M code reliably:\n"
            "1. Open Power Query Editor\n"
            "2. Go to **Advanced Editor**\n"
            "3. Copy the M code\n"
            "4. Save it as a `.txt` file\n"
            "5. Upload the `.txt` file here"
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Review the extracted Power Query M code for efficiency, readability, error handling, performance, and optimization opportunities.",
            height=150
        )

    else:
        st.subheader("📋 Review UiPath Code")
        uploaded_files = st.file_uploader(
            "Upload UiPath XAML files (.xaml or .txt)",
            type=["xaml", "txt"],
            accept_multiple_files=True,
            key=f"uipath_uploader_{st.session_state.uploader_key}"
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value="Review the uploaded UiPath XAML workflow for modularity, best practices, structure, reusability, Workflow Analyzer compliance, and potential improvements.",
            height=150
        )

    # Knowledge Base option
    use_kb = False
    if st.session_state.kb_index is not None and len(st.session_state.kb_chunks) > 0:
        use_kb = st.checkbox("📚 Also use Knowledge Base as reference", value=False)
        st.caption(f"Knowledge Base currently contains {len(st.session_state.kb_files)} document(s).")

    st.markdown("---")

    if uploaded_files:
        st.markdown("##### 📁 Uploaded Files")
        for f in uploaded_files:
            st.markdown(f"- `{f.name}` ({f.size / 1024:.1f} KB)")

        if st.button("🗑️ Clear Uploaded Files"):
            st.session_state.uploader_key += 1
            for key in ["vba_index", "vba_chunks", "pq_index", "pq_chunks", "uipath_index", "uipath_chunks"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Uploaded files cleared.")
            st.rerun()

        for uploaded_file in uploaded_files:
            if option == "Review Excel VBA":
                content = extract_vba_code(uploaded_file)
                chunks = chunk_text(content, mode="vba")
            elif option == "Review Excel PowerQuery":
                content = extract_powerquery_m_code(uploaded_file)
                chunks = chunk_text(content, mode="m")
            else:
                content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                chunks = chunk_text(content, mode="xaml")

            file_content += f"\n\n===== FILE: {uploaded_file.name} =====\n\n{content}"
            all_chunks.extend(chunks)

        if all_chunks:
            with st.spinner("Building vector index..."):
                index, stored_chunks = build_vector_store(all_chunks)

            if option == "Review Excel VBA":
                st.session_state["vba_index"] = index
                st.session_state["vba_chunks"] = stored_chunks
            elif option == "Review Excel PowerQuery":
                st.session_state["pq_index"] = index
                st.session_state["pq_chunks"] = stored_chunks
            else:
                st.session_state["uipath_index"] = index
                st.session_state["uipath_chunks"] = stored_chunks

            st.success(f"✅ Successfully processed **{len(uploaded_files)}** file(s) • **{len(all_chunks)}** chunks created")

            with st.expander("📜 Preview of extracted content (first 3,000 characters)", expanded=False):
                st.code(
                    file_content[:3000] + ("..." if len(file_content) > 3000 else ""),
                    language="vb" if option == "Review Excel VBA" else "text"
                )

            # Content type validation
            detected_types = set()
            for uploaded_file in uploaded_files:
                if option == "Review Excel VBA":
                    content = extract_vba_code(uploaded_file)
                elif option == "Review Excel PowerQuery":
                    content = extract_powerquery_m_code(uploaded_file)
                else:
                    content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                detected_types.add(detect_code_type(content))

            expected_type = {
                "Review Excel VBA": "vba",
                "Review Excel PowerQuery": "powerquery",
                "Review UiPath Code": "uipath"
            }.get(option)

            if expected_type and expected_type not in detected_types:
                st.warning(
                    f"⚠️ **Content Mismatch Detected**\n\n"
                    f"You selected **{option}**, but the uploaded file(s) do not appear to contain {expected_type.upper()} code.\n\n"
                    f"Detected type(s): {', '.join(t.upper() for t in detected_types if t != 'unknown') or 'Unknown'}"
                )
            elif "unknown" in detected_types and len(detected_types) == 1:
                st.info("ℹ️ Could not confidently detect the code type. The review will still proceed.")
        else:
            st.warning("No valid content could be extracted from the uploaded file(s).")
    else:
        st.info("👆 Please upload one or more files above to enable processing.")

    st.markdown("---")

    process_disabled = not uploaded_files

    if st.button("🚀 Process Request", type="primary", use_container_width=True, disabled=process_disabled):

        if not user_prompt.strip():
            st.error("⚠️ Please enter your instructions / prompt before processing.")
            st.stop()

        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🔍 Retrieving relevant chunks...")
        progress_bar.progress(20)

        retrieved_chunks = []
        retrieved_scores = []

        # Retrieve from user upload
        if option == "Review Excel VBA" and "vba_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt, st.session_state["vba_index"], st.session_state["vba_chunks"], k=3
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])

        elif option == "Review Excel PowerQuery" and "pq_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt, st.session_state["pq_index"], st.session_state["pq_chunks"], k=3
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])

        elif option == "Review UiPath Code" and "uipath_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt, st.session_state["uipath_index"], st.session_state["uipath_chunks"], k=3
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])

        # Retrieve from Knowledge Base if selected
        if use_kb and st.session_state.kb_index is not None:
            kb_results = retrieve_relevant_chunks(
                user_prompt, st.session_state.kb_index, st.session_state.kb_chunks, k=2
            )
            retrieved_chunks.extend([c for c, s in kb_results])
            retrieved_scores.extend([s for c, s in kb_results])

        progress_bar.progress(40)

        if retrieved_chunks:
            st.info(f"📊 **{len(retrieved_chunks)}** relevant chunk(s) retrieved via RAG")
            with st.expander("🔍 RAG Retrieved Chunks & Confidence Scores", expanded=False):
                for i, (chunk, score) in enumerate(zip(retrieved_chunks, retrieved_scores)):
                    st.markdown(f"**Chunk {i+1}** — Confidence: **{score:.2f}**")
                    lang = "vb" if option == "Review Excel VBA" else "xml" if option == "Review UiPath Code" else "text"
                    st.code(chunk, language=lang)

        status_text.text("🤖 Generating review with GPT-4o...")
        progress_bar.progress(60)

        try:
            client = OpenAI(api_key=st.secrets["openai_api_key"])

            if option == "Review Excel VBA":
                system_prompt = """You are an expert Excel VBA developer and code reviewer with deep knowledge of oletools (olevba and mraptor).

Your task is to perform a thorough professional review of the provided VBA code.

### Priority Areas

1. **Security**
   - Apply mraptor-style analysis to detect auto-executing macros, obfuscation, suspicious API calls, shellcode, and potential malware indicators
   - Check for unsafe practices and assess overall security risk level

2. **Code Quality & Redundancy**
   - Identify duplicate or nearly identical Sub/Function procedures
   - Detect unnecessary repeated code that can be consolidated
   - Flag overly long procedures and unused variables/procedures

3. **Best Practices & Maintainability**
   - Evaluate naming conventions, code organization, use of Option Explicit, and commenting quality

4. **Performance**
   - Identify inefficient loops, unnecessary Select/Activate statements, and repeated range references
   - Suggest use of arrays and turning off ScreenUpdating/Calculation/Events where appropriate

5. **Bug Detection & Robustness**
   - Identify potential runtime errors, weak error handling, and edge cases

6. **UiPath Compatibility** (if the VBA is intended to be called from UiPath)
   - Review whether the macro provides a clear and usable output for UiPath
   - Suggest structured output patterns (Function return, cell/named range, arguments)

### Output Requirements
- Structure your response with clear headings and bullet points.
- Be concise but thorough.
- When relevant, provide short refactored code examples.
- If context from RAG retrieval is provided, use it to support your analysis.

Maintain a professional and constructive tone throughout."""

            elif option == "Review Excel PowerQuery":
                system_prompt = """You are an expert Power Query (M language) developer and code reviewer.

Your task is to perform a thorough professional review of the provided Power Query M code.

### Priority Areas

1. **Performance & Query Folding**
   - Identify opportunities to improve query folding
   - Detect steps that break folding and expensive operations
   - Recommend early filtering, column selection, and reduction of steps

2. **Redundant Referencing & Step Design**
   - Identify repeated references and steps that can be combined or simplified

3. **Readability & Maintainability**
   - Evaluate step naming, organization, and clarity

4. **Error Handling & Robustness**
   - Check for missing error handling, null handling, and resilience to schema changes

5. **Best Practices**
   - Proper data type handling, use of parameters, and avoidance of anti-patterns

### Output Requirements
- Structure your response with clear headings and bullet points.
- Be concise but thorough.
- When relevant, provide short improved M code examples.
- If context from RAG retrieval is provided, use it to support your analysis.

Maintain a professional and constructive tone throughout."""

            else:
                system_prompt = """You are an expert UiPath RPA developer and code reviewer with deep knowledge of UiPath Studio, Workflow Analyzer, and RPA best practices.

Your task is to perform a thorough professional review of the provided UiPath XAML workflow.

### Priority Areas

1. **UiPath Built-in Validation Rules & Workflow Analyzer**
   - Check for unused variables/arguments, hardcoded values, missing annotations, naming conventions, excessive nesting, and missing Try Catch

2. **Modularity & Reusability**
   - Evaluate use of Invoke Workflow, reusable components, and single-responsibility design

3. **Structure & Design**
   - Review workflow structure, logical flow, and activity hierarchy

4. **Variables, Arguments & Data Handling**
   - Review naming, argument direction, scope, and data types

5. **Error Handling & Robustness**
   - Check Try Catch usage, logging, retries, and selector quality

6. **Performance & Maintainability**
   - Flag inefficient patterns and hardcoded delays

### Output Requirements
- Structure your response with clear headings and bullet points.
- Be concise but thorough.
- When relevant, provide clear improvement suggestions.
- If context from RAG retrieval is provided, use it to support your analysis.

Maintain a professional and constructive tone throughout."""

            rag_context = ""
            if retrieved_chunks:
                for chunk, score in zip(retrieved_chunks, retrieved_scores):
                    rag_context += f"[Confidence {score:.2f}]\n{chunk}\n\n"

            user_message = (
                f"{user_prompt}\n\n"
                f"--- RELEVANT CONTEXT (RAG) ---\n{rag_context}\n\n"
                f"--- FULL FILE CONTENT ---\n{file_content}"
            )

            progress_bar.progress(80)

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
            progress_bar.progress(100)
            status_text.text("✅ Review completed")

        except Exception as e:
            ai_response = (
                f"❌ Error connecting to OpenAI: {str(e)}\n\n"
                "Please verify your API key in .streamlit/secrets.toml."
            )
            progress_bar.progress(100)
            status_text.text("❌ Error occurred")

        st.markdown("---")
        st.subheader("📤 AI Response")

        with st.expander("View Full Review", expanded=True):
            st.markdown(ai_response)

        safe_name = option.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download as Text (.txt)",
                data=ai_response,
                file_name=f"{safe_name}_Review_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📥 Download as Markdown (.md)",
                data=ai_response,
                file_name=f"{safe_name}_Review_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.caption("💡 Tip: You can also select the text above and copy it directly (Ctrl+C / Cmd+C).")

        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "option": option,
            "prompt": user_prompt[:100] + ("..." if len(user_prompt) > 100 else ""),
            "response": ai_response,
            "num_files": len(uploaded_files) if uploaded_files else 0,
            "num_chunks": len(retrieved_chunks)
        })

# ====================== KNOWLEDGE BASE (ADMIN ONLY) ======================
elif page == "Knowledge Base":
    if st.session_state.role != "admin":
        st.warning("This page is only available to Admin users.")
        st.stop()

    st.title("📚 Knowledge Base Management")
    st.markdown("Upload reference documents that can be used during reviews by all users.")
    st.markdown("---")

    kb_files = st.file_uploader(
        "Upload reference documents (.txt, .md, .vba, .m, .pq, .xaml)",
        type=["txt", "md", "vba", "m", "pq", "xaml"],
        accept_multiple_files=True,
        key="kb_uploader"
    )

    if kb_files and st.button("Add to Knowledge Base", type="primary"):
        new_chunks = []
        new_names = []
        for f in kb_files:
            content = f.getvalue().decode("utf-8", errors="replace")
            chunks = chunk_text(content, mode="generic")
            new_chunks.extend(chunks)
            new_names.append(f.name)

        if new_chunks:
            if st.session_state.kb_index is None:
                index, stored = build_vector_store(new_chunks)
                st.session_state.kb_index = index
                st.session_state.kb_chunks = stored
            else:
                all_kb_chunks = st.session_state.kb_chunks + new_chunks
                index, stored = build_vector_store(all_kb_chunks)
                st.session_state.kb_index = index
                st.session_state.kb_chunks = stored

            st.session_state.kb_files.extend(new_names)
            st.success(f"Added {len(new_names)} document(s) to Knowledge Base.")
            st.rerun()

    st.markdown("---")
    st.subheader("Current Knowledge Base")
    if st.session_state.kb_files:
        for name in st.session_state.kb_files:
            st.markdown(f"- `{name}`")
        st.caption(f"Total chunks: {len(st.session_state.kb_chunks)}")
        if st.button("🗑️ Clear Knowledge Base"):
            st.session_state.kb_index = None
            st.session_state.kb_chunks = []
            st.session_state.kb_files = []
            st.success("Knowledge Base cleared.")
            st.rerun()
    else:
        st.info("Knowledge Base is empty. Upload documents above.")

# ====================== SAMPLE FILES PAGE ======================
elif page == "Sample Files":
    st.title("📄 Sample Files")
    st.markdown("Download these sample files to test the three review tools.")
    st.markdown("---")

    sample_vba = '''Attribute VB_Name = "Module1"
Option Explicit

Sub ProcessData()
    Dim ws As Worksheet
    Set ws = ActiveSheet
    ws.Range("A1").Select
    Selection.Value = "Start"
    
    Dim i As Long
    For i = 1 To 100
        Cells(i, 1).Value = i
        Cells(i, 1).Select
    Next i
End Sub

Sub ProcessData2()
    ' Almost identical to ProcessData - redundant
    Dim ws As Worksheet
    Set ws = ActiveSheet
    Dim i As Long
    For i = 1 To 100
        Cells(i, 2).Value = i * 2
    Next i
End Sub

Sub Auto_Open()
    ' Auto-executing macro
    MsgBox "Workbook opened"
    Shell "cmd.exe /c echo test"
End Sub
'''

    sample_pq = '''let
    Source = Excel.CurrentWorkbook(){[Name="Table1"]}[Content],
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Date", type date}, {"Amount", type number}}),
    #"Filtered Rows" = Table.SelectRows(#"Changed Type", each [Amount] > 0),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows", "Year", each Date.Year([Date])),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Custom",{{"Year", Int64.Type}}),
    #"Filtered Rows1" = Table.SelectRows(#"Changed Type1", each [Amount] > 0),
    #"Removed Columns" = Table.RemoveColumns(#"Filtered Rows1",{"Temp"}),
    #"Added Custom1" = Table.AddColumn(#"Removed Columns", "Year2", each Date.Year([Date]))
in
    #"Added Custom1"
'''

    sample_uipath = '''<Activity mc:Ignorable="sap sap2010" x:Class="Main"
 xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
 xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
 xmlns:ui="http://schemas.uipath.com/workflow/activities"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <Sequence DisplayName="Main Sequence">
    <ui:LogMessage DisplayName="Log start" Text="Process started" />
    <ui:Delay DisplayName="Wait" Duration="00:00:05" />
    <ui:LogMessage DisplayName="Log end" Text="Process finished" />
  </Sequence>
</Activity>
'''

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("VBA Sample")
        st.download_button(
            "📥 Download Sample_VBA.txt",
            data=sample_vba,
            file_name="Sample_VBA.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.caption("Contains redundant procedures and an auto-executing macro.")

    with col2:
        st.subheader("Power Query Sample")
        st.download_button(
            "📥 Download Sample_PowerQuery.txt",
            data=sample_pq,
            file_name="Sample_PowerQuery.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.caption("Contains redundant filters and repeated column additions.")

    with col3:
        st.subheader("UiPath Sample")
        st.download_button(
            "📥 Download Sample_UiPath.txt",
            data=sample_uipath,
            file_name="Sample_UiPath.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.caption("Minimal sequence with hardcoded delay.")

# ====================== REVIEW HISTORY PAGE ======================
elif page == "Review History":
    st.title("🗂️ Review History")
    st.markdown("Previous reviews from this session are shown below.")
    st.markdown("---")

    if not st.session_state.history:
        st.info("No reviews yet. Process a request in the **AI Tools** page to start building history.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"**{item['option']}** — {item['timestamp']} • {item['num_files']} file(s) • {item['num_chunks']} chunks"):
                st.markdown(f"**Prompt preview:** {item['prompt']}")
                st.markdown("---")
                st.markdown(item["response"])

                safe_name = item["option"].replace(" ", "_")
                ts_clean = item["timestamp"].replace(":", "-").replace(" ", "_")

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download .txt",
                        data=item["response"],
                        file_name=f"{safe_name}_Review_{ts_clean}.txt",
                        mime="text/plain",
                        key=f"hist_txt_{i}"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download .md",
                        data=item["response"],
                        file_name=f"{safe_name}_Review_{ts_clean}.md",
                        mime="text/markdown",
                        key=f"hist_md_{i}"
                    )

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# ====================== POWER QUERY EXPORT GUIDE ======================
elif page == "Power Query Export Guide":
    st.title("📤 Power Query Export Guide")

    st.markdown("""
    ### Why do I need to export the M code?

    Excel files (`.xlsx`, `.xlsm`, `.xlsb`) **do not store** the Power Query M code in a way that can be reliably extracted.  
    To review your Power Query logic with this tool, you need to export the M code manually.
    """)

    st.markdown("---")

    st.subheader("📋 Step-by-Step Instructions")
    st.markdown("""
    1. Open your Excel file.
    2. Go to the **Data** tab → click **Queries & Connections** (or open **Power Query Editor**).
    3. In the Power Query Editor, select the query you want to review.
    4. Click **Advanced Editor** (usually found in the Home tab).
    5. Select all the M code (`Ctrl + A`) and copy it (`Ctrl + C`).
    6. Paste the code into a text editor (Notepad, VS Code, etc.).
    7. Save the file with one of these extensions:
       - `.txt` (recommended)
       - `.m`
       - `.pq`
    8. Upload the saved file in the **AI Tools** page under **Review Excel PowerQuery**.
    """)

    st.markdown("---")

    st.subheader("💡 Tips & Best Practices")
    st.markdown("""
    - **Multiple queries**: Export each query as a separate file for clearer reviews.
    - **Parameters**: If your query uses parameters, include them or note their values in your prompt.
    - **Large queries**: Very long M code is supported, but reviewing one focused query at a time usually produces better results.
    - **Naming**: Give your exported file a clear name (e.g. `Sales_Query_M_Code.txt`).
    - **Formatting**: Keep the original formatting from the Advanced Editor — it helps the AI understand step boundaries.
    """)

    st.markdown("---")
    st.info("Once the file is uploaded in the AI Tools page, you can add specific instructions (e.g. “Focus on query folding and performance”) for a more targeted review.")

# ====================== ABOUT US PAGE ======================
elif page == "About Us":
    st.title("ℹ️ About Us")

    st.markdown("""
    ### AI Automation Assistant
    A secure, AI-powered web application designed to help Excel automation developers and RPA practitioners review and improve VBA, Power Query, and UiPath workflows.
    """)

    st.markdown("---")

    st.subheader("🎯 Project Purpose")
    st.markdown("""
    Manual code review of VBA macros, Power Query (M) scripts, and UiPath XAML workflows is time-consuming and inconsistent.  

    This application uses **Retrieval-Augmented Generation (RAG)** together with domain-specific expertise to deliver structured, professional code reviews that focus on:
    - Security and best practices
    - Performance and maintainability
    - Redundancy detection
    - UiPath compatibility (for VBA)
    """)

    st.subheader("✨ Key Features")
    st.markdown("""
    - Native VBA macro extraction from `.xlsm` / `.xlsb` files using **oletools**
    - Power Query M code review and optimisation suggestions
    - UiPath XAML workflow review (modularity, structure, Workflow Analyzer rules)
    - Context-aware analysis powered by vector retrieval (FAISS + OpenAI embeddings)
    - Role-based access (Admin / User)
    - Knowledge Base for reference documents
    - Downloadable review reports (`.txt` and `.md`) with date-time stamp
    - Session review history
    - Sample files for testing
    """)

    st.subheader("🛠️ Technology Stack")
    st.markdown("""
    - **Frontend**: Streamlit  
    - **VBA Extraction**: oletools  
    - **Embeddings**: OpenAI `text-embedding-3-large`  
    - **Vector Store**: FAISS  
    - **LLM**: OpenAI GPT-4o  
    - **Security**: Streamlit Secrets + role-based password protection
    """)

    st.markdown("---")

    st.subheader("👥 Project Team")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Chng Chyi Da**  
        chng_chyi_da@vital.gov.sg
        """)

    with col2:
        st.markdown("""
        **Jean Chua Yi Juan**  
        jean_chua@vital.gov.sg
        """)

    with col3:
        st.markdown("""
        **Lim Yi Jun**  
        lim_yi_jun@vital.gov.sg
        """)

    st.markdown("---")
    st.caption("AI Automation Assistant • Version 1.0 • Last updated: 10 August 2026")

# ====================== METHODOLOGY PAGE ======================
elif page == "Methodology":
    st.title("📋 Methodology")

    st.markdown("""
    ### Overview
    The AI Automation Assistant is a secure Streamlit application that combines domain-specific code analysis with Retrieval-Augmented Generation (RAG). 

    Users can upload VBA, Power Query (M), or UiPath XAML files. The system extracts and chunks the content, generates embeddings, stores them in a FAISS vector index, retrieves the most relevant segments based on the user’s prompt, and uses GPT-4o to produce structured professional reviews. Results can be downloaded with a date-time stamp and previous reviews are kept in session history.
    """)

    st.subheader("🛠️ Technology Stack")
    st.markdown("""
    - **Frontend**: Streamlit  
    - **VBA Extraction**: oletools (`olevba`)  
    - **Embeddings**: OpenAI `text-embedding-3-large`  
    - **Vector Store**: FAISS  
    - **Language Model**: OpenAI GPT-4o  
    - **Secrets Management**: Streamlit Secrets  
    """)

    st.subheader("🏗️ High-Level Architecture")
    st.markdown("""
    **Upload → Extract → Chunk → Embed → Store (FAISS) → Retrieve → Generate Review → Download / History**
    """)

    st.subheader("👥 Roles")
    st.markdown("""
    - **Admin**: Can manage a Knowledge Base of reference documents that can be optionally used during reviews.
    - **User**: Can upload files for review and optionally include the Knowledge Base.
    """)

    st.header("📋 Use Case 1: Review Excel VBA")
    st.markdown("""
    1. User uploads one or more VBA files (`.txt`, `.xlsm`, `.xlsb`)  
    2. System extracts VBA macros using **oletools**  
    3. Code is chunked by `Sub` / `Function` boundaries  
    4. Chunks are converted into embeddings using OpenAI  
    5. A FAISS vector index is built  
    6. User submits a review prompt  
    7. Most relevant chunks are retrieved (RAG)  
    8. GPT-4o performs a structured review  
    9. Results are displayed, downloadable (with date-time), and saved to history
    """)

    st.header("📋 Use Case 2: Review Excel Power Query")
    st.markdown("""
    1. User uploads one or more Power Query files (`.txt`, `.m`, `.pq`)  
    2. System reads the M code  
    3. Code is chunked by step boundaries  
    4. Chunks are converted into embeddings using OpenAI  
    5. A FAISS vector index is built  
    6. User submits a review prompt  
    7. Most relevant chunks are retrieved (RAG)  
    8. GPT-4o performs a structured review  
    9. Results are displayed, downloadable (with date-time), and saved to history
    """)

    st.header("📋 Use Case 3: Review UiPath Code")
    st.markdown("""
    1. User uploads one or more UiPath XAML files (`.xaml`, `.txt`)  
    2. System extracts the XAML content  
    3. Code is chunked by activity boundaries  
    4. Chunks are converted into embeddings using OpenAI  
    5. A FAISS vector index is built  
    6. User submits a review prompt  
    7. Most relevant chunks are retrieved (RAG)  
    8. GPT-4o performs a structured review  
    9. Results are displayed, downloadable (with date-time), and saved to history
    """)

    st.subheader("🔒 Security Considerations")
    st.markdown("""
    - Application access is protected by role-based password authentication.  
    - API keys and credentials are stored securely using Streamlit Secrets.  
    - No uploaded files or analysis results are permanently stored on the server.  
    - All processing occurs in-memory during the session.
    """)
