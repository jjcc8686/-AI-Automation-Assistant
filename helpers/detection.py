"""
Code type detection helper.
"""

def detect_code_type(content: str) -> str:
    """Detect whether content is VBA, Power Query, UiPath or unknown."""
    if not content or not content.strip():
        return "unknown"

    content_lower = content.lower()

    # 1. UiPath – very distinctive markers
    if any(
        k in content
        for k in ["<Activity", "<Sequence", "xmlns:ui=", "<ui:", "x:Class="]
    ):
        return "uipath"

    # 2. Strong Power Query indicators
    pq_strong = [
        "table.selectcolumns",
        "table.nestedjoin",
        "table.expandtablecolumn",
        "table.addcolumn",
        "table.transformcolumntypes",
        "table.selectrows",
        "excel.currentworkbook",
        '#"changed type"',
        '#"filtered rows"',
        '#"removed other columns"',
        "joinkind.",
    ]
    if any(k in content_lower for k in pq_strong):
        return "powerquery"

    # 3. Strong VBA indicators
    vba_strong = [
        "option explicit",
        "attribute vb_name",
        "private sub ",
        "public sub ",
        "end sub",
        "end function",
        "dim ",
        "as worksheet",
        "as workbook",
        "thisworkbook",
    ]
    if any(k in content_lower for k in vba_strong):
        return "vba"

    # 4. Weaker fallbacks
    if (
        "let" in content_lower
        and "in" in content_lower
        and any(k in content for k in ['#"', "Source ="])
    ):
        return "powerquery"

    if any(k in content_lower for k in ["sub ", "function "]):
        return "vba"

    return "unknown"