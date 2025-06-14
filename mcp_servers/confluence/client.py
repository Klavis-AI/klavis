from enum import Enum
from typing import Any
from urllib.parse import parse_qs, urlparse
from contextvars import ContextVar
import logging

import httpx
from errors import ToolExecutionError, AuthenticationError, TokenExpiredError, InvalidTokenError

# Single auth token context for the entire application
auth_token_context: ContextVar[str] = ContextVar('auth_token')

from enums import BodyFormat, PageUpdateMode
from utils import (
    build_child_url,
    build_hierarchy,
    remove_none_values,
)

# Set up logging
logger = logging.getLogger(__name__)


class ConfluenceAPIVersion(str, Enum):
    V1 = "wiki/rest/api"
    V2 = "wiki/api/v2"


class ConfluenceClient:
    ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
    BASE_URL = "https://api.atlassian.com/ex/confluence"

    def __init__(self, token: str, api_version: ConfluenceAPIVersion):
        self.token = token
        self.api_version = api_version.value
        self.cloud_id = None  # Will be set lazily when first needed

    async def _get_cloud_id(self) -> str:
        """
        Fetch the cloudId for <workspace_name>.atlassian.net
        using the OAuth2 3LO accessible-resources endpoint.

        For details on why this is necessary, see: https://developer.atlassian.com/cloud/oauth/getting-started/making-calls-to-api
        """
        if not self.token or self.token.strip() == "":
            raise InvalidTokenError(
                message="No OAuth token provided",
                developer_message="Please ensure you have a valid OAuth 2.0 access token. You may need to complete the OAuth authorization flow."
            )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        logger.info(f"Fetching cloud ID from accessible-resources endpoint")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.ACCESSIBLE_RESOURCES_URL, headers=headers)
                resp.raise_for_status()
                resp_json = resp.json()
                
                if len(resp_json) == 0:
                    raise ToolExecutionError(
                        message="No workspaces found for the authenticated user.",
                        developer_message="The OAuth token is valid but no Confluence workspaces are accessible. Ensure the user has access to at least one Confluence site."
                    )

                cloud_id = resp_json[0].get("id")
                logger.info(f"Successfully retrieved cloud ID: {cloud_id}")
                return cloud_id

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(f"OAuth token authentication failed: {e}")
                raise TokenExpiredError(
                    message="OAuth token is expired or invalid",
                    developer_message=f"Received 401 Unauthorized when accessing {self.ACCESSIBLE_RESOURCES_URL}. " +
                                    "The OAuth token may have expired or been revoked. " +
                                    "Please re-authenticate using the OAuth 2.0 flow to get a new access token. " +
                                    "For refresh tokens, use the refresh token endpoint to get a new access token."
                )
            elif e.response.status_code == 403:
                logger.error(f"OAuth token insufficient permissions: {e}")
                raise AuthenticationError(
                    message="OAuth token has insufficient permissions",
                    developer_message=f"Received 403 Forbidden when accessing {self.ACCESSIBLE_RESOURCES_URL}. " +
                                    "The OAuth token may not have the required scopes. " +
                                    "Ensure your OAuth app has the necessary Confluence scopes configured."
                )
            else:
                logger.error(f"HTTP error when fetching cloud ID: {e}")
                raise ToolExecutionError(
                    message=f"Failed to fetch cloud ID: HTTP {e.response.status_code}",
                    developer_message=f"Unexpected HTTP error {e.response.status_code} when calling {self.ACCESSIBLE_RESOURCES_URL}: {e}"
                )
        except httpx.RequestError as e:
            logger.error(f"Network error when fetching cloud ID: {e}")
            raise ToolExecutionError(
                message="Network error when connecting to Atlassian API",
                developer_message=f"Request error when calling {self.ACCESSIBLE_RESOURCES_URL}: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected error when fetching cloud ID: {e}")
            raise ToolExecutionError(
                message="Unexpected error when fetching cloud ID",
                developer_message=f"Unexpected error in _get_cloud_id(): {type(e).__name__}: {e}"
            )

    async def _ensure_cloud_id(self) -> str:
        """Ensure cloud_id is available, fetching it if necessary."""
        if self.cloud_id is None:
            self.cloud_id = await self._get_cloud_id()
        return self.cloud_id

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        cloud_id = await self._ensure_cloud_id()
                
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        
        # Merge with any additional headers from kwargs
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/{cloud_id}/{self.api_version}/{path.lstrip('/')}"
            logger.debug(f"Making {method} request to: {url}")
                
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.error(f"Authentication failed for API request: {e}")
                    raise TokenExpiredError(
                        message="OAuth token is expired or invalid",
                        developer_message=f"Received 401 Unauthorized when calling {url}. " +
                                        "The OAuth token may have expired. Please re-authenticate."
                    )
                else:
                    logger.error(f"HTTP error in API request: {e}")
                    raise ToolExecutionError(
                        message=f"API request failed: HTTP {e.response.status_code}",
                        developer_message=f"HTTP {e.response.status_code} error when calling {url}: {e}"
                    )
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                raise ToolExecutionError(
                    message="Unexpected error in API request",
                    developer_message=f"Unexpected error when calling {url}: {type(e).__name__}: {e}"
                )

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Any:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, **kwargs)


class ConfluenceClientV1(ConfluenceClient):
    def __init__(self):
        auth_token = auth_token_context.get()
        if not auth_token:
            logger.warning("No auth token found in context")
        super().__init__(auth_token, api_version=ConfluenceAPIVersion.V1)

    def _build_query_cql(self, query: str, enable_fuzzy: bool) -> str:
        """Build CQL for a single query (term or phrase).

        Args:
            query: The search query (single word term or multi-word phrase)
            enable_fuzzy: Whether to enable fuzzy matching for single terms

        Returns:
            CQL string for the query
        """
        query = query.strip()
        if not query:
            return ""

        # For phrases (multiple words), don't use fuzzy matching
        if " " in query:
            return f'(text ~ "{query}" OR title ~ "{query}" OR space.title ~ "{query}")'
        else:
            # For single terms, optionally use fuzzy matching
            term_suffix = "~" if enable_fuzzy else ""
            return f'(text ~ "{query}{term_suffix}" OR title ~ "{query}{term_suffix}" OR space.title ~ "{query}{term_suffix}")'  # noqa: E501

    def _build_and_cql(self, queries: list[str], enable_fuzzy: bool) -> str:
        """Build CQL for queries that must ALL be present (AND logic).

        Args:
            queries: List of queries that must all be present
            enable_fuzzy: Whether to enable fuzzy matching for single terms

        Returns:
            CQL string with AND logic
        """
        and_parts = []
        for query in queries:
            query_cql = self._build_query_cql(query, enable_fuzzy)
            if query_cql:
                and_parts.append(query_cql)

        if not and_parts:
            return ""

        return f"({' AND '.join(and_parts)})"

    def _build_or_cql(self, queries: list[str], enable_fuzzy: bool) -> str:
        """Build CQL for queries where ANY can be present (OR logic).

        Args:
            queries: List of queries where any can be present
            enable_fuzzy: Whether to enable fuzzy matching for single terms

        Returns:
            CQL string with OR logic
        """
        or_parts = []
        for query in queries:
            query_cql = self._build_query_cql(query, enable_fuzzy)
            if query_cql:
                or_parts.append(query_cql)

        if not or_parts:
            return ""

        return f"({' OR '.join(or_parts)})"

    def construct_cql(
        self,
        must_contain_all: list[str] | None,
        can_contain_any: list[str] | None,
        enable_fuzzy: bool = False,
    ) -> str:
        """Construct CQL query with AND/OR logic.

        Learn about advanced searching using CQL here: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/

        Args:
            must_contain_all: Queries that must ALL be present (AND logic)
            can_contain_any: Queries where ANY can be present (OR logic)
            enable_fuzzy: Whether to enable fuzzy matching for single terms

        Returns:
            CQL query string

        Raises:
            ToolExecutionError: If no search parameters are provided
        """
        cql_parts = []

        # Handle must_contain_all (AND logic)
        if must_contain_all:
            and_cql = self._build_and_cql(must_contain_all, enable_fuzzy)
            if and_cql:
                cql_parts.append(and_cql)

        # Handle can_contain_any (OR logic)
        if can_contain_any:
            or_cql = self._build_or_cql(can_contain_any, enable_fuzzy)
            if or_cql:
                cql_parts.append(or_cql)

        # If there's only one part, return it
        if len(cql_parts) == 1:
            return cql_parts[0]

        # AND the must_contain_all with the can_contain_any
        if len(cql_parts) > 1:
            return f"({' AND '.join(cql_parts)})"

        raise ToolExecutionError(message="At least one search parameter must be provided")

    def transform_search_content_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Transform the response from the GET /search endpoint by converting relative webui paths
        to absolute URLs using the base URL from the response.
        """
        base_url = response.get("_links", {}).get("base", "")
        transformed_results = []
        for result in response.get("results", []):
            content = result.get("content", {})
            transformed_result = {
                "id": content.get("id"),
                "title": content.get("title"),
                "type": content.get("type"),
                "status": content.get("status"),
                "excerpt": result.get("excerpt"),
                "url": f"{base_url}{result.get('url')}",
            }
            transformed_results.append(transformed_result)

        return {"results": transformed_results}


class ConfluenceClientV2(ConfluenceClient):
    def __init__(self):
        auth_token = auth_token_context.get()
        if not auth_token:
            logger.warning("No auth token found in context")
        super().__init__(auth_token, api_version=ConfluenceAPIVersion.V2)

    def _transform_links(
        self, response: dict[str, Any], base_url: str | None = None
    ) -> dict[str, Any]:
        """
        Transform the links in a page response by converting relative URLs to absolute URLs.

        Args:
            response: A page object from the API
            base_url: The base URL to use for the transformation

        Returns:
            The transformed response
        """
        result = response.copy()
        if "_links" in result:
            base_url = base_url or result["_links"].get("base", "")
            webui_path = result["_links"].get("webui", "")
            result["url"] = f"{base_url}{webui_path}"
            del result["_links"]
        return result

    def transform_get_spaces_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Transform the response from the GET /spaces endpoint by converting relative webui paths
        to absolute URLs using the base URL from the response.
        """
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor",
            [None],  # type: ignore[list-item]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        results = response.get("results", [])

        transformed_results = []
        for space in results:
            space_copy = space.copy()
            if "_links" in space_copy and "webui" in space_copy["_links"]:
                webui_path = space_copy["_links"]["webui"]
                space_copy["url"] = base_url + webui_path
                del space_copy["_links"]
            transformed_results.append(space_copy)

        results = {"spaces": transformed_results, "pagination_token": pagination_token}
        return remove_none_values(results)

    def transform_list_pages_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Transform the response from the GET /pages endpoint."""
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor",
            [None],  # type: ignore[list-item]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        pages = [self._transform_links(page, base_url) for page in response["results"]]
        results = {"pages": pages, "pagination_token": pagination_token}
        return remove_none_values(results)

    def transform_get_multiple_pages_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Transform the response from the GET /pages endpoint."""
        base_url = response.get("_links", {}).get("base", "")
        pages = [self._transform_links(page, base_url) for page in response["results"]]
        return {"pages": pages}

    def transform_space_response(
        self, response: dict[str, Any], base_url: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Transform API responses that return a space object."""
        return {"space": self._transform_links(response, base_url)}

    def transform_page_response(self, response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Transform API responses that return a page object."""
        return {"page": self._transform_links(response)}

    def transform_get_attachments_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Transform the response from the GET /pages/{id}/attachments endpoint."""
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor",
            [None],  # type: ignore[list-item]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        attachments = []
        for attachment in response["results"]:
            result = attachment.copy()
            if "_links" in result:
                webui_path = result["_links"].get("webui", "")
                download_path = result["_links"].get("download", "")
                result["url"] = f"{base_url}{webui_path}"
                result["download_link"] = f"{base_url}{download_path}"
                del result["_links"]
                del result["webuiLink"]
                del result["downloadLink"]
                del result["version"]
            attachments.append(result)

        return {"attachments": attachments, "pagination_token": pagination_token}

    def prepare_update_page_payload(
        self,
        page_id: str,
        status: str,
        title: str,
        body_representation: str,
        body_value: str,
        version_number: int,
        version_message: str,
    ) -> dict[str, Any]:
        """Prepare a payload for the PUT /pages/{id} endpoint."""
        return {
            "id": page_id,
            "status": status,
            "title": title,
            "body": {
                "representation": body_representation,
                "value": body_value,
            },
            "version": {
                "number": version_number,
                "message": version_message,
            },
        }

    def prepare_update_page_content_payload(
        self,
        content: str,
        update_mode: PageUpdateMode,
        old_content: str,
        page_id: str,
        status: str,
        title: str,
        body_representation: BodyFormat,
        old_version_number: int,
    ) -> dict[str, Any]:
        """Prepare a payload for when updating the content of a page

        Args:
            content: The content to update the page with
            update_mode: The mode of update to use
            old_content: The content of the page before the update
            page_id: The ID of the page to update
            status: The status of the page
            title: The title of the page
            body_representation: The format that the body (content) is in
            old_version_number: The version number of the page before the update

        Returns:
            A payload for the PUT /pages/{id} endpoint's json body
        """
        updated_content = ""
        updated_message = ""
        if update_mode == PageUpdateMode.APPEND:
            updated_content = f"{old_content}<br/>{content}"
            updated_message = "Append content to the page"
        elif update_mode == PageUpdateMode.PREPEND:
            updated_content = f"{content}<br/>{old_content}"
            updated_message = "Prepend content to the page"
        elif update_mode == PageUpdateMode.REPLACE:
            updated_content = content
            updated_message = "Replace the page content"
        payload = self.prepare_update_page_payload(
            page_id=page_id,
            status=status,
            title=title,
            body_representation=body_representation.to_api_value(),
            body_value=updated_content,
            version_number=old_version_number + 1,
            version_message=updated_message,
        )
        return payload

    async def get_root_pages_in_space(self, space_id: str) -> dict[str, Any]:
        """
        Get the root pages in a space.

        Requires Confluence scope 'read:page:confluence'
        """
        params = {
            "depth": "root",
            "limit": 250,
        }
        pages = await self.get(f"spaces/{space_id}/pages", params=params)
        base_url = pages.get("_links", {}).get("base", "")
        return {"pages": [self._transform_links(page, base_url) for page in pages["results"]]}

    async def get_space_homepage(self, space_id: str) -> dict[str, Any]:
        """
        Get the homepage of a space.

        Requires Confluence scope 'read:page:confluence'
        """
        root_pages = await self.get_root_pages_in_space(space_id)
        for page in root_pages["pages"]:
            if page.get("url", "").endswith("overview"):
                return self._transform_links(page)
        raise ToolExecutionError(message="No homepage found for space.")

    async def get_page_by_id(
        self, page_id: str, content_format: BodyFormat = BodyFormat.STORAGE
    ) -> dict[str, Any]:
        """Get a page by its ID.

        Requires Confluence scope 'read:page:confluence'

        Args:
            page_id: The ID of the page to get
            content_format: The format of the page content

        Returns:
            The page object
        """
        params = remove_none_values({
            "body-format": content_format.to_api_value(),
        })
        try:
            page = await self.get(f"pages/{page_id}", params=params)
        except httpx.HTTPStatusError as e:
            # If the page is not found, return an empty page object
            if e.response.status_code in [400, 404]:
                return self.transform_page_response({})
            raise

        return self.transform_page_response(page)

    async def get_page_by_title(
        self, page_title: str, content_format: BodyFormat = BodyFormat.STORAGE
    ) -> dict[str, Any]:
        """Get a page by its title.

        Requires Confluence scope 'read:page:confluence'

        Args:
            page_title: The title of the page to get
            content_format: The format of the page content

        Returns:
            The page object
        """
        params = {
            "title": page_title,
            "body-format": content_format.to_api_value(),
        }
        response = await self.get("pages", params=params)
        pages = response.get("results", [])
        if not pages:
            # If the page is not found, return an empty page object
            return self.transform_page_response({})
        return self.transform_page_response(pages[0])

    async def get_space_by_id(self, space_id: str) -> dict[str, Any]:
        """Get a space by its ID.

        Requires Confluence scope 'read:space:confluence'

        Args:
            space_id: The ID of the space to get

        Returns:
            The space object
        """
        space = await self.get(f"spaces/{space_id}")
        return self.transform_space_response(space)

    async def get_space_by_key(self, space_key: str) -> dict[str, Any]:
        """Get a space by its key.

        Requires Confluence scope 'read:space:confluence'

        Args:
            space_key: The key of the space to get

        Returns:
            The space object
        """
        response = await self.get("spaces", params={"keys": [space_key]})
        base_url = response.get("_links", {}).get("base", "")
        spaces = response.get("results", [])
        if not spaces:
            raise ToolExecutionError(message=f"No space found with key: '{space_key}'")
        return self.transform_space_response(spaces[0], base_url=base_url)

    async def get_space(self, space_identifier: str) -> dict[str, Any]:
        """Get a space from its identifier.

        The identifier can be either a space ID (numeric) or a space key (alphanumeric).

        Args:
            space_identifier: The ID or key of the space to get

        Returns:
            The space object
        """
        if space_identifier.isdigit():
            return await self.get_space_by_id(space_identifier)
        else:
            return await self.get_space_by_key(space_identifier)

    async def get_page_id(self, page_identifier: str) -> str:
        """Get a page ID from its identifier.

        The identifier can be either a page ID (numeric) or a page title (alphanumeric).

        Args:
            page_identifier: The ID or title of the page to get

        Returns:
            The page ID
        """
        if page_identifier.isdigit():
            return page_identifier
        else:
            page = await self.get_page_by_title(page_identifier)
            page_data = page.get("page", {})
            if not page_data:
                raise ToolExecutionError(message=f"No page found with title: '{page_identifier}'")
            return page_data["id"]

    async def get_space_id(self, space_identifier: str) -> str:
        """Get a space ID from its identifier.

        The identifier can be either a space ID (numeric) or a space key (alphanumeric).

        Args:
            space_identifier: The ID or key of the space to get

        Returns:
            The space ID
        """
        space = await self.get_space(space_identifier)
        return space["space"]["id"]

    def create_space_tree(self, space: dict) -> dict:
        """Create a space tree structure from space data."""
        space_data = space.get("space", {})
        
        return {
            "id": space_data.get("id"),
            "key": space_data.get("key"),
            "name": space_data.get("name"),
            "type": "space",
            "url": space_data.get("url", ""),
            "description": space_data.get("description", {}).get("plain", ""),
            "children": []
        }

    def convert_root_pages_to_tree_nodes(self, pages: list) -> list:
        """Convert root pages to tree nodes."""
        tree_nodes = []
        
        for page in pages:
            node = {
                "id": page.get("id"),
                "title": page.get("title"),
                "type": page.get("type", "page"),
                "status": page.get("status", "current"),
                "url": page.get("url", ""),
                "children": []
            }
            tree_nodes.append(node)
        
        return tree_nodes

    async def process_page_descendants(self, root_children: list, base_url: str) -> None:
        """Process page descendants and build the hierarchy."""
        # For each root page, get its descendants
        for root_child in root_children:
            if root_child["type"] == "page":
                try:
                    # Get descendants for this page
                    params = {
                        "expand": "ancestors"
                    }
                    response = await self.get(f"content/{root_child['id']}/descendant", params=params)
                    
                    # Process descendants into hierarchy
                    descendants = response.get("page", {}).get("results", [])
                    if descendants:
                        transformed_children = []
                        for desc in descendants:
                            child_node = {
                                "id": desc.get("id"),
                                "title": desc.get("title"),
                                "type": desc.get("type", "page"),
                                "status": desc.get("status", "current"),
                                "parent_id": None,
                                "children": []
                            }
                            
                            # Determine parent ID from ancestors
                            ancestors = desc.get("ancestors", [])
                            if ancestors:
                                child_node["parent_id"] = ancestors[-1].get("id")
                            
                            # Build URL
                            child_node["url"] = build_child_url(base_url, child_node) or ""
                            
                            transformed_children.append(child_node)
                        
                        # Build hierarchy
                        build_hierarchy(transformed_children, root_child["id"], root_child)
                
                except Exception:
                    # Log the error but continue processing other pages
                    continue 