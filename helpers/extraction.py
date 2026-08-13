"""
File extraction helpers for VBA and Power Query.
"""

try:
    from oletools.olevba import VBA_Parser
    OLETOOLS_AVAILABLE = True
except ImportError:
    OLETOOLS_AVAILABLE = False

def extract_vba_code(uploaded_file) -> str:
    """Extract VBA code from .xlsm/.xlsb or return text content for .txt."""
    if not uploaded_file:
        return ""

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    try:
        if file_name.endswith((".xlsm", ".xlsb")):
            if not OLETOOLS_AVAILABLE:
                return (
                    "oletools is not installed. "
                    "Please add 'oletools' to requirements.txt and restart the app."
                )
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

def extract_powerquery_m_code(uploaded_file) -> str:
    """Extract Power Query M code from .txt / .m / .pq files."""
    if not uploaded_file:
        return ""

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if file_name.endswith((".m", ".pq", ".txt")):
        return file_bytes.decode("utf-8", errors="replace")

    return (
        "Excel files do not embed Power Query M code. "
        "Please export the query using Power Query → Advanced Editor → Save as .txt."
    )