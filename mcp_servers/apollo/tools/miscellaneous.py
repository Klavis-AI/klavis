import httpx
from .base import get_apollo_client

async def apollo_view_api_usage_stats() -> dict:
    """
    Retrieve your team's Apollo API usage statistics and rate limits.

    POST https://api.apollo.io/api/v1/usage_stats/api_usage_stats

    Requirements:
    - Master API key required (403 error if missing).

    Returns:
    - Current API usage details.
    - Rate limits per endpoint (per minute, hour, day).
    - Limits depend on your Apollo pricing plan.
    """

    url = "https://api.apollo.io/api/v1/usage_stats/api_usage_stats"
    headers = get_apollo_client()  # Master API key required

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

async def apollo_list_users() -> dict:
    """
    Retrieve the list of all users (teammates) in your Apollo account.

    GET https://api.apollo.io/api/v1/users/search

    Requirements:
    - Master API key required (403 error if missing).
    - Not available for free Apollo plans.

    Returns:
    - User IDs and details usable in other endpoints like Create Deal, Create Account, Create Task.
    """

    url = "https://api.apollo.io/api/v1/users/search"
    headers = get_apollo_client()  # Master API key required

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

async def apollo_list_email_accounts() -> dict:
    """
    Retrieve information about linked email inboxes used by teammates in your Apollo account.

    GET https://api.apollo.io/api/v1/email_accounts

    Requirements:
    - Master API key required (403 error if missing).
    - No query parameters needed.

    Returns:
    - IDs and details of linked email accounts.
    - These IDs can be used with other endpoints, such as Add Contacts to a Sequence.
    """

    url = "https://api.apollo.io/api/v1/email_accounts"
    headers = get_apollo_client()  # Master API key needed

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

async def apollo_get_all_lists_and_tags() -> dict:
    """
    Retrieve all lists and tags created in your Apollo account.

    GET https://api.apollo.io/api/v1/labels

    Requirements:
    - Master API key required (403 error if missing).
    - No query parameters needed.

    Returns:
    - Information about every list and tag available.
    - Useful to verify lists before creating or updating contacts.
    """

    url = "https://api.apollo.io/api/v1/labels"
    headers = get_apollo_client()  # Master API key required

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

async def apollo_list_all_custom_fields() -> dict:
    """
    Retrieve all custom fields created in your Apollo account.

    GET https://api.apollo.io/api/v1/typed_custom_fields

    Requirements:
    - Master API key required (403 error if missing).
    - No query parameters needed.

    Returns:
    - Details about every custom field available in the account.
    - Useful for managing or using custom data fields.
    """

    url = "https://api.apollo.io/api/v1/typed_custom_fields"
    headers = get_apollo_client()  # Master API key required

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
