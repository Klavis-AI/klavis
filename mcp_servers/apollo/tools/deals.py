import httpx
from .base import get_apollo_client

async def apollo_create_deal(
    name: str,
    owner_id: str = None,
    account_id: str = None,
    amount: str = None,
    opportunity_stage_id: str = None,
    closed_date: str = None
) -> dict:
    """
    Create a new deal for an Apollo account.

    POST https://api.apollo.io/api/v1/opportunities

    Parameters:
    - name (str): Required. Human-readable name for the deal.
    - owner_id (str): ID of the deal owner in your Apollo account.
    - account_id (str): ID of the target account (company) for the deal.
    - amount (str): Monetary value of the deal (no commas or currency symbols).
    - opportunity_stage_id (str): ID of the deal stage.
    - closed_date (str): Estimated close date (YYYY-MM-DD).

    Notes:
    - Requires master API key; calls without it return 403.
    - Use Get a List of Users to find owner_id.
    - Use Organization Search to find account_id.
    - Use List Deal Stages to find opportunity_stage_id.

    Returns:
        Response with details of the created deal.
    """

    url = "https://api.apollo.io/api/v1/opportunities"
    params = {
        "name": name,
        "owner_id": owner_id,
        "account_id": account_id,
        "amount": amount,
        "opportunity_stage_id": opportunity_stage_id,
        "closed_date": closed_date
    }
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_list_all_deals(
    sort_by_field: str = None,
    page: int = 1,
    per_page: int = 50
) -> dict:
    """
    Retrieve all deals created for your team's Apollo account.

    GET https://api.apollo.io/api/v1/opportunities/search

    Query Parameters:
    - sort_by_field (str): Sort deals by one of the following:
        - amount: largest deal values first
        - is_closed: closed deals first
        - is_won: won deals first
    - page (int): Page number to retrieve (for pagination).
    - per_page (int): Number of results per page (to improve performance).

    Notes:
    - Requires a master API key; calls without it return 403.
    - Not available for users on free plans.

    Returns:
        A paginated list of deals with their details.
    """

    url = "https://api.apollo.io/api/v1/opportunities/search"
    params = {
        "sort_by_field": sort_by_field,
        "page": page,
        "per_page": per_page
    }
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def apollo_view_deal(opportunity_id: str):
    """
    Retrieve detailed information about a specific deal in your team's Apollo account.

    GET https://api.apollo.io/api/v1/opportunities/{opportunity_id}

    Path Parameters:
    - opportunity_id (str): The unique ID of the deal to retrieve.

    Notes:
    - Requires a master API key; calls without it return a 403 response.
    - Use the List All Deals endpoint to find deal IDs.

    Returns:
        Detailed information about the deal, including owner ID, monetary value, deal stage, and associated account details.
    """

    url = f"https://api.apollo.io/api/v1/opportunities/{opportunity_id}"
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_update_deal(
    opportunity_id: str,
    owner_id: str = None,
    name: str = None,
    amount: str = None,
    opportunity_stage_id: str = None,
    closed_date: str = None,
    is_closed: bool = None,
    is_won: bool = None,
    source: str = None,
    account_id: str = None
):
    """
    Update details of an existing deal in your team's Apollo account.

    PATCH https://api.apollo.io/api/v1/opportunities/{opportunity_id}

    Path Parameters:
    - opportunity_id (str): The unique ID of the deal to update.

    Query Parameters:
    - owner_id (str): New owner ID for the deal.
    - name (str): Updated human-readable deal name.
    - amount (str): Updated monetary value (no commas or currency symbols).
    - opportunity_stage_id (str): New deal stage ID.
    - closed_date (date): Updated estimated close date (YYYY-MM-DD).
    - is_closed (bool): Mark deal as closed if True.
    - is_won (bool): Mark deal as won if True.
    - source (str): Update the deal's source.
    - account_id (str): Update associated company ID.

    Notes:
    - Requires a master API key; unauthorized calls return 403.
    - Use List All Deals to find deal IDs.
    - Use Get a List of Users to find valid owner IDs.
    - Use List Deal Stages to find valid stage IDs.
    - Use Organization Search to find company IDs.

    Example:
    Update deal name to "Massive Q3 Deal", set amount to 55123478, close the deal and mark as won.
    """

    url = f"https://api.apollo.io/api/v1/opportunities/{opportunity_id}"
    headers = get_apollo_client()  # Needs master API key

    params = {
        "owner_id": owner_id,
        "name": name,
        "amount": amount,
        "opportunity_stage_id": opportunity_stage_id,
        "closed_date": closed_date,
        "is_closed": is_closed,
        "is_won": is_won,
        "source": source,
        "account_id": account_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def apollo_list_deal_stages():
    """
    Retrieve all deal stages available in your team's Apollo account.

    GET https://api.apollo.io/api/v1/opportunity_stages

    Notes:
    - Requires a master API key; unauthorized calls return 403.
    - Use the returned stage IDs to set or update deal stages when creating or updating deals.
    """

    url = "https://api.apollo.io/api/v1/opportunity_stages"
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
