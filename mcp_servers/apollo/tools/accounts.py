import httpx
from .base import get_apollo_client

async def apollo_create_account(
    name: str = None,
    domain: str = None,
    owner_id: str = None,
    account_stage_id: str = None,
    phone: str = None,
    raw_address: str = None
) -> dict:
    """
    Create a new account in Apollo.

    This function calls the Create an Account endpoint to add a company to your team's Apollo database.

    Note:
    - Apollo does not deduplicate on create. If an account with the same name or domain exists, a new account will still be created.
    - Use the Update endpoint to modify existing accounts.
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        name (str): Human-readable name of the account (e.g., "The Irish Copywriters").
        domain (str): Domain name of the account without "www." (e.g., "apollo.io").
        owner_id (str): ID of the account owner within your Apollo team.
        account_stage_id (str): Apollo ID for the account stage to assign the account.
        phone (str): Primary phone number for the account, any format accepted.
        raw_address (str): Corporate location like city, state, country.

    Returns:
        Response text from Apollo API or error details.
    """

    if name is None and domain is None:
        return {"error": "Either name or domain must be provided"}

    url = 'https://api.apollo.io/api/v1/accounts'
    data = {
        'name': name,
        'domain': domain,
        'owner_id': owner_id,
        'account_stage_id': account_stage_id,
        'phone': phone,
        'raw_address': raw_address
    }

    headers = get_apollo_client()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()  # raises if not 2xx
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def apollo_update_account(
    account_id: str,
    name: str = None,
    domain: str = None,
    owner_id: str = None,
    account_stage_id: str = None,
    raw_address: str = None,
    phone: str = None
) -> dict:
    """
    Update an existing account in Apollo.

    This function calls the Update an Account endpoint to modify details of a company already in your team's Apollo database.

    Note:
    - To create new accounts, use the Create Account endpoint.
    - To update stages for multiple accounts, use the bulk Update Account Stage endpoint.
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        account_id (str): Apollo ID of the account to update (required).
        name (str, optional): New human-readable name for the account.
        domain (str, optional): New domain name without "www.".
        owner_id (str, optional): New owner ID within your Apollo team.
        account_stage_id (str, optional): New account stage ID.
        raw_address (str, optional): Updated corporate location (city, state, country).
        phone (str, optional): Updated primary phone number in any format.

    Returns:
        Response text from Apollo API or error details.
    """

    if not account_id:
        return {"error": "account_id is required"}

    url = f"https://api.apollo.io/api/v1/accounts/{account_id}"
    data = {
        "name": name,
        "domain": domain,
        "owner_id": owner_id,
        "account_stage_id": account_stage_id,
        "raw_address": raw_address,
        "phone": phone
    }
    headers = get_apollo_client()  # Must return master API key headers

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=data)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_search_accounts(
    q_organization_name: str = None,
    account_stage_ids: list = None,
    sort_by_field: str = None,
    sort_ascending: bool = False,
    page: int = 1,
    per_page: int = 50
)->dict:
    """
    Search for accounts in your team's Apollo database.

    This function calls the Search for Accounts endpoint to find accounts explicitly added to your Apollo team.

    Notes:
    - Only searches accounts added by your team, not the full Apollo database.
    - Max 50,000 records can be retrieved (100 per page, up to 500 pages).
    - Use filters to narrow results.
    - Not available on Apollo free plans.

    Parameters:
        q_organization_name (str, optional): Keywords to match part of the account name.
        account_stage_ids (list[str], optional): List of account stage IDs to filter results.
        sort_by_field (str, optional): Field to sort by ('account_last_activity_date', 'account_created_at', 'account_updated_at').
        sort_ascending (bool, optional): Sort order; true for ascending, false for descending (requires sort_by_field).
        page (int, optional): Page number of results to retrieve.
        per_page (int, optional): Number of results per page for pagination.

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/accounts/search"
    params = {
        "q_organization_name": q_organization_name,
        "account_stage_ids": account_stage_ids,
        "sort_by_field": sort_by_field,
        "sort_ascending": sort_ascending,
        "page": page,
        "per_page": per_page
    }

    headers = get_apollo_client()  # Needs API key

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

async def apollo_view_account(account_id: str)->dict:
    """
    Retrieve details of an existing account in Apollo.

    This function calls the View an Account endpoint to get full info for a company in your team's Apollo database.

    Note:
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        id (str): Apollo ID of the account to retrieve (required).

    Returns:
        Response text from Apollo API or error details.
    """

    url = f"https://api.apollo.io/api/v1/accounts/{account_id}"
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.text
    except Exception as e:
        return {"error": str(e)}

async def apollo_update_account_stage_bulk(
    account_ids: list,
    account_stage_id: str
)->dict:
    """
    Update the account stage for multiple accounts in Apollo.

    This function calls the bulk Update Account Stage endpoint to change the stage of several accounts in your team's Apollo database.

    Note:
    - To update fields other than account stage, use the Update an Account endpoint.
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        account_ids (list[str]): List of Apollo account IDs to update (required).
        account_stage_id (str): Apollo ID of the new account stage to assign (required).

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/accounts/bulk_update"
    params = {
        "account_ids": account_ids,
        "account_stage_id": account_stage_id
    }
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            return response.text
    except Exception as e:
        return {"error": str(e)}

async def apollo_update_account_owner_bulk(
    account_ids: list,
    owner_id: str
)->dict:
    """
    Assign multiple accounts to a different owner in Apollo.

    This function calls the Update Account Owner for Multiple Accounts endpoint to change ownership of several accounts in your team's Apollo database.

    Note:
    - To update fields other than owner, use the Update an Account endpoint.
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        account_ids (list[str]): List of Apollo account IDs to reassign (required).
        owner_id (str): Apollo user ID of the new account owner (required).

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/accounts/update_owners"
    params = {
        "account_ids": account_ids,
        "owner_id": owner_id
    }

    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            return response.text
    except Exception as e:
        return {"error": str(e)}

async def apollo_list_account_stages()->dict:
    """
    Retrieve all account stage IDs in your Apollo team.

    This function calls the List Account Stages endpoint to get available account stages for use in updating accounts.

    Note:
    - No parameters required.
    - Requires a master API key; unauthorized calls return 403.

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/account_stages"
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.text
    except Exception as e:
        return {"error": str(e)}

