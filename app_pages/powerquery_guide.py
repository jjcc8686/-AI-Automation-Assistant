"""
Power Query Export Guide page.
"""

import streamlit as st

def render_powerquery_guide() -> None:
    st.title("Power Query Export Guide")

    st.markdown(
        """
        ### Why do I need to export the M code?

        Excel files (`.xlsx`, `.xlsm`, `.xlsb`) **do not store** the Power Query M code
        in a way that can be reliably extracted.
        To review your Power Query logic with this tool, export the M code manually.
        """
    )
    st.markdown("---")

    st.subheader("Step-by-Step Instructions")
    st.markdown(
        """
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
        """
    )
    st.markdown("---")

    st.subheader("Tips & Best Practices")
    st.markdown(
        """
        - **Multiple queries**: Export each query as a separate file for clearer reviews.
        - **Parameters**: If your query uses parameters, include them or note their values in your prompt.
        - **Large queries**: Very long M code is supported, but reviewing one focused query at a time usually produces better results.
        - **Naming**: Give your exported file a clear name (e.g. `Sales_Query_M_Code.txt`).
        - **Formatting**: Keep the original formatting from the Advanced Editor — it helps the AI understand step boundaries.
        """
    )
    st.markdown("---")
    st.info(
        "Once the file is uploaded in the AI Tools page, you can add specific instructions "
        '(e.g. “Focus on query folding and performance”) for a more targeted review.'
    )