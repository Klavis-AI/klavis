# doc to html
def convert_document_to_html(document: dict) -> str:
    html = (
        "<html><head>"
        f"<title>{document['title']}</title>"
        f'<meta name="documentId" content="{document["documentId"]}">'
        "</head><body>"
    )
    for element in document["body"]["content"]:
        html += _convert_structural_element_html(element)
    html += "</body></html>"
    return html


def _convert_structural_element_html(element: dict, wrap_paragraphs: bool = True) -> str:
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        paragraph_content = ""

        prepend, append = _get_paragraph_style_tags_html(
            style=element["paragraph"]["paragraphStyle"],
            wrap_paragraphs=wrap_paragraphs,
        )

        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            paragraph_content += _extract_paragraph_content_html(item["textRun"])

        if not paragraph_content:
            return ""

        return f"{prepend}{paragraph_content.strip()}{append}"

    elif "table" in element:
        table = [
            [
                "".join([
                    _convert_structural_element_html(element=cell_element, wrap_paragraphs=False)
                    for cell_element in cell["content"]
                ])
                for cell in row["tableCells"]
            ]
            for row in element["table"]["tableRows"]
        ]
        return _table_list_to_html(table)

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def _extract_paragraph_content_html(text_run: dict) -> str:
    content = text_run["content"]
    style = text_run["textStyle"]
    return _apply_text_style_html(content, style)


def _apply_text_style_html(content: str, style: dict) -> str:
    content = content.rstrip("\n")
    content = content.replace("\n", "<br>")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"<i>{content}</i>"
    if bold:
        content = f"<b>{content}</b>"
    return content


def _get_paragraph_style_tags_html(style: dict, wrap_paragraphs: bool = True) -> tuple[str, str]:
    named_style = style["namedStyleType"]
    if named_style == "NORMAL_TEXT":
        return ("<p>", "</p>") if wrap_paragraphs else ("", "")
    elif named_style == "TITLE":
        return "<h1>", "</h1>"
    elif named_style == "SUBTITLE":
        return "<h2>", "</h2>"
    elif named_style.startswith("HEADING_"):
        try:
            heading_level = int(named_style.split("_")[1])
        except ValueError:
            return ("<p>", "</p>") if wrap_paragraphs else ("", "")
        else:
            return f"<h{heading_level}>", f"</h{heading_level}>"
    return ("<p>", "</p>") if wrap_paragraphs else ("", "")


def _table_list_to_html(table: list[list[str]]) -> str:
    html = "<table>"
    for row in table:
        html += "<tr>"
        for cell in row:
            if cell.endswith("<br>"):
                cell = cell[:-4]
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    return html


# doc to markdown
def convert_document_to_markdown(document: dict) -> str:
    md = f"---\ntitle: {document['title']}\ndocumentId: {document['documentId']}\n---\n"
    for element in document["body"]["content"]:
        md += _convert_structural_element_md(element)
    return md


def _convert_structural_element_md(element: dict, in_table: bool = False) -> str:
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        md = ""
        prepend = _get_paragraph_style_prepend_str_md(element["paragraph"]["paragraphStyle"]) if not in_table else ""
        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            content = _extract_paragraph_content_md(item["textRun"], in_table=in_table)
            md += f"{prepend}{content}"
        return md

    elif "table" in element:
        return _table_to_markdown(element["table"])

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def _extract_paragraph_content_md(text_run: dict, in_table: bool = False) -> str:
    content = text_run["content"]
    style = text_run["textStyle"]
    return _apply_text_style_md(content, style, in_table=in_table)


def _apply_text_style_md(content: str, style: dict, in_table: bool = False) -> str:
    append = "\n" if content.endswith("\n") and not in_table else ""
    content = content.rstrip("\n")
    if in_table:
        # Replace newlines with spaces in table cells, and escape pipes
        content = content.replace("\n", " ").replace("|", "\\|")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"_{content}_"
    if bold:
        content = f"**{content}**"
    return f"{content}{append}"


def _get_paragraph_style_prepend_str_md(style: dict) -> str:
    named_style = style["namedStyleType"]
    if named_style == "NORMAL_TEXT":
        return ""
    elif named_style == "TITLE":
        return "# "
    elif named_style == "SUBTITLE":
        return "## "
    elif named_style.startswith("HEADING_"):
        try:
            heading_level = int(named_style.split("_")[1])
            return f"{'#' * heading_level} "
        except ValueError:
            return ""
    return ""


def _table_to_markdown(table: dict) -> str:
    """Convert a Google Docs table to Markdown format."""
    rows = table.get("tableRows", [])
    if not rows:
        return ""

    md_rows = []
    for row in rows:
        cells = []
        for cell in row.get("tableCells", []):
            cell_content = "".join([
                _convert_structural_element_md(element, in_table=True)
                for element in cell.get("content", [])
            ])
            # Clean up cell content for markdown table
            cell_content = cell_content.strip()
            cells.append(cell_content)
        md_rows.append(cells)

    if not md_rows:
        return ""

    # Build markdown table
    md = "\n"
    # Header row
    md += "| " + " | ".join(md_rows[0]) + " |\n"
    # Separator row
    md += "| " + " | ".join(["---"] * len(md_rows[0])) + " |\n"
    # Data rows
    for row in md_rows[1:]:
        # Ensure row has same number of columns as header
        while len(row) < len(md_rows[0]):
            row.append("")
        md += "| " + " | ".join(row) + " |\n"
    md += "\n"
    return md
