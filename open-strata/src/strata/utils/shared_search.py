"""
Shared search utility for both single_server and strata_server.
Provides type-safe interfaces for searching through MCP tools
Uses a unified generic approach to reduce code duplication.
"""

from typing import Any, Dict, List, Optional

from mcp import types

from strata.utils.bm25_search import BM25SearchEngine


class UniversalToolSearcher:
    """
    Universal searcher that handles all tool types
    using a single unified approach based on function names.
    """

    def __init__(self, mixed_tools_map: Dict[str, List[Any]]):
        """
        Initialize universal searcher with mixed tool types.

        Args:
            mixed_tools_map: Dictionary mapping categories to tools.
                           Tools can be either types.Tool objects or dict objects.
        """
        self.tools_map = mixed_tools_map
        self.search_engine = self._build_index()

    def _get_tool_name(self, tool: Any) -> Optional[str]:
        """Extract name from any tool type."""
        if isinstance(tool, types.Tool):
            return tool.name if tool.name else None
        elif isinstance(tool, dict):
            return tool.get("name")
        return None

    def _get_tool_field(self, tool: Any, field_name: str, default: Any = None) -> Any:
        """Extract field value from any tool type."""
        if isinstance(tool, types.Tool):
            return getattr(tool, field_name, default)
        elif isinstance(tool, dict):
            return tool.get(field_name, default)
        return default

    def _build_index(self) -> BM25SearchEngine:
        """Build unified search index from all tools."""
        documents = []

        for category_name, tools in self.tools_map.items():
            for tool in tools:
                # Get tool name (function name)
                tool_name = self._get_tool_name(tool)
                if not tool_name:
                    continue

                # Build weighted fields
                fields = []

                # Core identifiers - highest weight
                fields.append(("category", category_name.lower(), 30))
                fields.append(("operation", tool_name.lower(), 30))

                # Title if available
                title = self._get_tool_field(tool, "title", "")
                if title:
                    fields.append(("title", str(title).lower(), 30))

                # Description/Summary - highest weight
                description = self._get_tool_field(tool, "description", "")
                if description:
                    fields.append(("description", str(description).lower(), 30))

                summary = self._get_tool_field(tool, "summary", "")
                if summary:
                    fields.append(("summary", str(summary).lower(), 30))

                tags = self._get_tool_field(tool, "tags", [])
                if isinstance(tags, list):
                    for tag in tags:
                        if tag:
                            fields.append(("tag", str(tag).lower(), 30))

                path = self._get_tool_field(tool, "path", "")
                if path:
                    fields.append(("path", str(path).lower(), 30))

                method = self._get_tool_field(tool, "method", "")
                if method:
                    fields.append(("method", str(method).lower(), 15))

                for param_type in ["path_params", "query_params"]:
                    params = self._get_tool_field(tool, param_type, {})
                    for param_name, param_info in params.items():
                        fields.append(
                            (f"{param_type}/{param_name}", param_name.lower(), 15)
                        )
                        if isinstance(param_info, dict):
                            param_desc = param_info.get("description", "")
                            if param_desc:
                                fields.append(
                                    (
                                        f"{param_type}/{param_name}_desc",
                                        param_desc.lower(),
                                        15,
                                    )
                                )

                # Body schema fields
                body_schema = self._get_tool_field(tool, "body_schema", {})
                for param_name, param_info in body_schema.get("properties", {}).items():
                    fields.append((f"body_schema/{param_name}", param_name.lower(), 15))
                    if isinstance(param_info, dict):
                        param_desc = param_info.get("description", "")
                        if param_desc:
                            fields.append(
                                (
                                    f"body_schema/{param_name}_desc",
                                    param_desc.lower(),
                                    15,
                                )
                            )

                response_schema = self._get_tool_field(tool, "response_schema", {})
                for param_name, param_info in response_schema.get(
                    "properties", {}
                ).items():
                    fields.append(
                        (f"response_schema/{param_name}", param_name.lower(), 5)
                    )
                    if isinstance(param_info, dict):
                        param_desc = param_info.get("description", "")
                        if param_desc:
                            fields.append(
                                (
                                    f"response_schema/{param_name}_desc",
                                    param_desc.lower(),
                                    5,
                                )
                            )

                # Create document ID
                doc_id = f"{category_name}::{tool_name}"
                if fields:
                    documents.append((fields, doc_id))

        # Build search index
        search_engine = BM25SearchEngine()
        search_engine.build_index(documents)
        return search_engine

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search through all tools.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with tool information
        """
        if self.search_engine is None:
            return []

        # Perform search
        search_results = self.search_engine.search(query.lower(), top_k=max_results)

        # Build results
        results = []

        for score, doc_id in search_results:
            # Parse doc_id
            if "::" not in doc_id:
                continue

            category_name, tool_name = doc_id.split("::", 1)

            # Find the tool
            if category_name in self.tools_map:
                for tool in self.tools_map[category_name]:
                    if self._get_tool_name(tool) == tool_name:
                        result = {
                            "name": tool_name,
                            "description": self._get_tool_field(
                                tool, "description", ""
                            ),
                            "category_name": category_name,
                            # "relevance_score": score,
                        }

                        # Add optional fields if they exist
                        for field in ["title", "summary"]:
                            value = self._get_tool_field(tool, field)
                            if value:
                                result[field] = value

                        results.append(result)
                        break

        return results
