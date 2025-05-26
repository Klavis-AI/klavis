# doc to html
def convert_document_to_html(document: dict) -> str:
    html = (
        "<html><head>"
        f"<title>{document['title']}</title>"
        f'<meta name="documentId" content="{document["documentId"]}">'
        "</head><body>"
    )
    for element in document["body"]["content"]:
        html += convert_structural_element(element)
    html += "</body></html>"
    return html

def convert_structural_element(element: dict, wrap_paragraphs: bool = True) -> str:
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        paragraph_content = ""

        prepend, append = get_paragraph_style_tags(
            style=element["paragraph"]["paragraphStyle"],
            wrap_paragraphs=wrap_paragraphs,
        )

        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            paragraph_content += extract_paragraph_content(item["textRun"])

        if not paragraph_content:
            return ""

        return f"{prepend}{paragraph_content.strip()}{append}"

    elif "table" in element:
        table = [
            [
                "".join([
                    convert_structural_element(element=cell_element, wrap_paragraphs=False)
                    for cell_element in cell["content"]
                ])
                for cell in row["tableCells"]
            ]
            for row in element["table"]["tableRows"]
        ]
        return table_list_to_html(table)

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def extract_paragraph_content(text_run: dict) -> str:
    content = text_run["content"]
    style = text_run["textStyle"]
    return apply_text_style(content, style)


def apply_text_style(content: str, style: dict) -> str:
    content = content.rstrip("\n")
    content = content.replace("\n", "<br>")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"<i>{content}</i>"
    if bold:
        content = f"<b>{content}</b>"
    return content


def get_paragraph_style_tags(style: dict, wrap_paragraphs: bool = True) -> tuple[str, str]:
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


def table_list_to_html(table: list[list[str]]) -> str:
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
        md += convert_structural_element(element)
    return md


def convert_structural_element(element: dict) -> str:
    if "sectionBreak" in element or "tableOfContents" in element:
        return ""

    elif "paragraph" in element:
        md = ""
        prepend = get_paragraph_style_prepend_str(element["paragraph"]["paragraphStyle"])
        for item in element["paragraph"]["elements"]:
            if "textRun" not in item:
                continue
            content = extract_paragraph_content(item["textRun"])
            md += f"{prepend}{content}"
        return md

    elif "table" in element:
        return convert_structural_element(element)

    else:
        raise ValueError(f"Unknown document body element type: {element}")


def extract_paragraph_content(text_run: dict) -> str:
    content = text_run["content"]
    style = text_run["textStyle"]
    return apply_text_style(content, style)


def apply_text_style(content: str, style: dict) -> str:
    append = "\n" if content.endswith("\n") else ""
    content = content.rstrip("\n")
    italic = style.get("italic", False)
    bold = style.get("bold", False)
    if italic:
        content = f"_{content}_"
    if bold:
        content = f"**{content}**"
    return f"{content}{append}"


def get_paragraph_style_prepend_str(style: dict) -> str:
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
