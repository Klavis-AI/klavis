import base64
import json
import logging
import os
import re
from contextvars import ContextVar
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from dotenv import load_dotenv

from .utils import format_api_error

# Load environment variables from .env when available
load_dotenv()

logger = logging.getLogger(__name__)

# Context variable populated per-request by the server transport
auth_token_context: ContextVar[str] = ContextVar("auth_token")


def get_auth_token() -> str:
    """Return the auth token set for the current request, or fall back to env vars."""
    try:
        token = auth_token_context.get()
        if token:
            return token
    except LookupError:
        pass

    auth_data = os.getenv("AUTH_DATA")
    if auth_data:
        try:
            auth_json = json.loads(auth_data)
            access_token = auth_json.get('access_token', '')
            if access_token:
                return access_token
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse AUTH_DATA JSON: {e}")
    
    raise RuntimeError("Authentication token not found in context or environment")


def get_excel_client() -> Optional[dict[str, dict[str, str] | str]]:
    """
    Return a simple client dict with base_url and headers for Microsoft Graph Excel APIs.
    """
    try:
        token = get_auth_token()
    except RuntimeError as exc:
        logger.error("Unable to acquire Excel auth token: %s", exc)
        return None

    return {
        "base_url": "https://graph.microsoft.com/v1.0",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    }


def _extract_workbook_id_from_doc_url(url: str) -> Optional[str]:
    """
    Extract workbook ID from OneDrive Doc.aspx URLs.

    Supports two URL formats:
    1. https://onedrive.live.com/personal/{USER_ID}/_layouts/1/Doc.aspx?sourcedoc={SOURCE_DOC}
    2. https://onedrive.live.com/personal/{USER_ID}/_layouts/15/doc.aspx?resid={RESID}&cid={CID}

    Returns workbook_id in format: {USER_ID}!{FILE_ID}
    """
    parsed = urlparse(url)

    # Check if this is a Doc.aspx URL (case insensitive)
    if "doc.aspx" not in parsed.path.lower():
        return None

    user_id_match = re.search(r'/personal/([a-f0-9]+)/', parsed.path, re.IGNORECASE)
    if not user_id_match:
        return None

    user_id = user_id_match.group(1).upper()

    query_params = parse_qs(parsed.query)

    # Try to extract from resid parameter (format 2)
    resid = query_params.get('resid', [None])[0]
    if resid:
        # resid format: fd2f4aab-8777-45a7-9dcd-213627a16f91
        file_id = unquote(resid).strip('{}').replace('-', '').lower()
        return f"{user_id}!s{file_id}"

    # Fall back to sourcedoc parameter (format 1)
    sourcedoc = query_params.get('sourcedoc', [None])[0]
    if sourcedoc:
        file_id = unquote(sourcedoc).strip('{}').replace('-', '').lower()
        return f"{user_id}!s{file_id}"

    return None


def _extract_workbook_id_from_excel_cloud_url(url: str) -> Optional[str]:
    """
    Extract workbook ID from Excel cloud URLs.

    Example URL:
    https://excel.cloud.microsoft/open/onedrive/?docId=EA3D30C7BD1A05D5%21s3032e367437d4a1db3ce229fd76537e7&driveId=EA3D30C7BD1A05D5

    Returns workbook_id from the docId parameter (already in correct format).
    """
    parsed = urlparse(url)

    # Check if this is an Excel cloud URL
    if "excel.cloud.microsoft" not in parsed.netloc:
        return None

    query_params = parse_qs(parsed.query)
    doc_id = query_params.get('docId', [None])[0]

    if doc_id:
        # docId is already in the correct format, just needs URL decoding
        return unquote(doc_id)

    return None

async def parse_share_link(
    share_link: str,
    client: dict[str, dict[str, str] | str],
) -> Dict[str, Any]:
    """
    Parse a standard OneDrive/SharePoint share link using the shares API.

    Args:
        share_link: The share link URL to parse
        client: Excel client dict containing base_url and headers

    Returns:
        Dict containing the drive item information

    Raises:
        RuntimeError if the share link cannot be parsed
    """
    base_url = client["base_url"]
    headers = client["headers"]

    encoded = "u!" + base64.urlsafe_b64encode(share_link.encode()).decode().rstrip("=")
    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            url = f"{base_url}/shares/{encoded}/driveItem"
            response = await httpx_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        error_detail = format_api_error(exc.response.status_code, exc.response.text)
        logger.error("Failed to parse share link: %s", exc.response.text)
        raise RuntimeError(
            f"Failed to parse share link (status {exc.response.status_code}): {error_detail}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error parsing share link")
        raise RuntimeError(f"Failed to parse share link: {exc}") from exc

async def parse_workbook_url(
    shared_url: str,
    client: dict[str, dict[str, str] | str],
) -> Dict[str, Any]:
    """
    Parse a workbook URL (shared link, Excel cloud URL, or direct Doc.aspx URL) and retrieve the drive item information.

    Args:
        shared_url: The workbook URL to parse (supports shared links, Excel cloud URLs, and Doc.aspx URLs)
        client: Excel client dict containing base_url and headers

    Returns:
        Dict containing the drive item information

    Raises:
        RuntimeError if the workbook URL cannot be parsed
    """
    base_url = client["base_url"]
    headers = client["headers"]

    # Try to extract workbook ID from Excel cloud URLs first
    workbook_id = _extract_workbook_id_from_excel_cloud_url(shared_url)
    if not workbook_id:
        # Try to extract workbook ID from Doc.aspx URLs
        workbook_id = _extract_workbook_id_from_doc_url(shared_url)

    if workbook_id:
        logger.info("Extracted workbook ID from URL: %s", workbook_id)
        # Directly fetch the item using the workbook ID
        try:
            async with httpx.AsyncClient(timeout=30.0) as httpx_client:
                # Try personal OneDrive first
                url = f"{base_url}/me/drive/items/{workbook_id}"
                response = await httpx_client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = format_api_error(exc.response.status_code, exc.response.text)
            logger.error("Failed to fetch item with extracted ID: %s", exc.response.text)
            raise RuntimeError(
                f"Failed to fetch workbook (status {exc.response.status_code}): {error_detail}"
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error fetching workbook by ID")
            raise RuntimeError(f"Failed to fetch workbook: {exc}") from exc

    # Fall back to standard shared link parsing
    return await parse_share_link(shared_url, client)


__all__ = ["auth_token_context", "get_auth_token", "get_excel_client", "parse_share_link", "parse_workbook_url"]
