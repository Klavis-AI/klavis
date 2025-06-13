from typing import Annotated

from client import ConfluenceClientV1


async def search_content(
    must_contain_all: Annotated[
        list[str] | None,
        "Words/phrases that content MUST contain (AND logic). Each item can be:\n"
        "- Single word: 'banana' - content must contain this word\n"
        "- Multi-word phrase: 'How to' - content must contain all these words (in any order)\n"
        "- All items in this list must be present for content to match\n"
        "- Example: ['banana', 'apple'] finds content containing BOTH 'banana' AND 'apple'",
    ] = None,
    can_contain_any: Annotated[
        list[str] | None,
        "Words/phrases where content can contain ANY of these (OR logic). Each item can be:\n"
        "- Single word: 'project' - content containing this word will match\n"
        "- Multi-word phrase: 'pen & paper' - content containing all these words will match\n"
        "- Content matching ANY item in this list will be included\n"
        "- Example: ['project', 'documentation'] finds content with 'project' OR 'documentation'",
    ] = None,
    enable_fuzzy: Annotated[
        bool,
        "Enable fuzzy matching to find similar terms (e.g. 'roam' will find 'foam'). "
        "Defaults to True",
    ] = True,
    limit: Annotated[int, "Maximum number of results to return (1-100). Defaults to 25"] = 25,
) -> Annotated[dict, "Search results containing content items matching the criteria"]:
    """Search for content in Confluence.

    The search is performed across all content in the authenticated user's Confluence workspace.
    All search terms in Confluence are case insensitive.

    You can use the parameters in different ways:
    - must_contain_all: For AND logic - content must contain ALL of these
    - can_contain_any: For OR logic - content can contain ANY of these
    - Combine them: must_contain_all=['banana'] AND can_contain_any=['database', 'guide']
    """
    client = ConfluenceClientV1()
    cql = client.construct_cql(must_contain_all, can_contain_any, enable_fuzzy)
    response = await client.get("search", params={"cql": cql, "limit": max(1, min(limit, 100))})

    return client.transform_search_content_response(response) 