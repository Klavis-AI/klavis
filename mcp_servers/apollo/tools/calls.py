import httpx
from .base import get_apollo_client

async def apollo_create_call_record(
    logged: bool,
    user_ids: list,
    contact_id: str,
    account_id: str = None,
    to_number: str = None,
    from_number: str = None,
    status: str = None,
    start_time: str = None,
    end_time: str = None,
    duration: int = None,
    phone_call_purpose_id: str = None,
    phone_call_outcome_id: str = None,
    note: str = None
):
    """
    Create a call record in Apollo.

    This function calls the Create Call Records endpoint to log calls made using outside systems (e.g., Orum, Nooks) into Apollo.
    It cannot be used to make calls, only to record them.

    Note:
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        logged (bool, optional): True to log the call in Apollo.
        user_id (list[str], optional): Apollo user IDs of the caller(s).
        contact_id (str, optional): Apollo contact ID of the called person.
        account_id (str, optional): Apollo account ID to associate with the call.
        to_number (str, optional): Phone number dialed.
        from_number (str, optional): Phone number that placed the call.
        status (str, optional): Call status ('queued', 'ringing', 'in-progress', 'completed', 'no_answer', 'failed', 'busy').
        start_time (str, optional): ISO 8601 formatted start time (GMT or with offset).
        end_time (str, optional): ISO 8601 formatted end time (GMT or with offset).
        duration (int, optional): Duration of the call in seconds.
        phone_call_purpose_id (str, optional): Call purpose ID in your Apollo account.
        phone_call_outcome_id (str, optional): Call outcome ID in your Apollo account.
        note (str, optional): Additional note for the call record.

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/phone_calls"
    params = {
        "logged": str(logged).lower(),
        "user_id[]": user_ids,
        "contact_id": contact_id,
        "account_id": account_id,
        "to_number": to_number,
        "from_number": from_number,
        "status": status,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "phone_call_purpose_id": phone_call_purpose_id,
        "phone_call_outcome_id": phone_call_outcome_id,
        "note": note
    }

    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_search_calls(
    date_range_max: str = None,
    date_range_min: str = None,
    duration_max: int = None,
    duration_min: int = None,
    inbound: str = None,
    user_ids: list = None,
    contact_label_ids: list = None,
    phone_call_purpose_ids: list = None,
    phone_call_outcome_ids: list = None,
    q_keywords: str = None,
    page: int = None,
    per_page: int = None
):
    """
    Search for calls made or received by your team in Apollo.

    This function calls the Search for Calls endpoint to find calls logged via the Apollo dialer.

    Note:
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        date_range_max (str, optional): Upper bound date (YYYY-MM-DD) for search.
        date_range_min (str, optional): Lower bound date (YYYY-MM-DD) for search.
        duration_max (int, optional): Max call duration in seconds.
        duration_min (int, optional): Min call duration in seconds.
        inbound (str, optional): Filter by call direction ('incoming' or 'outgoing').
        user_ids (list[str], optional): List of Apollo user IDs involved in calls.
        contact_label_ids (list[str], optional): List of contact IDs involved in calls.
        phone_call_purpose_ids (list[str], optional): Filter by call purpose IDs.
        phone_call_outcome_ids (list[str], optional): Filter by call outcome IDs.
        q_keywords (str, optional): Keywords to narrow call search.
        page (str/int, optional): Page number for pagination.
        per_page (str/int, optional): Number of results per page.

    Returns:
        Response text from Apollo API or error details.
    """

    url = "https://api.apollo.io/api/v1/phone_calls/search"
    params = {
        "date_range[max]": date_range_max,
        "date_range[min]": date_range_min,
        "duration[max]": duration_max,
        "duration[min]": duration_min,
        "inbound": inbound,
        "user_ids[]": user_ids,
        "contact_label_ids[]": contact_label_ids,
        "phone_call_purpose_ids[]": phone_call_purpose_ids,
        "phone_call_outcome_ids[]": phone_call_outcome_ids,
        "q_keywords": q_keywords,
        "page": page,
        "per_page": per_page
    }
    headers = get_apollo_client()  # Needs master API key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def apollo_update_call(
    call_id: str,
    logged: bool = None,
    user_ids: list = None,
    contact_id: str = None,
    account_id: str = None,
    to_number: str = None,
    from_number: str = None,
    status: str = None,
    start_time: str = None,
    end_time: str = None,
    duration: int = None,
    phone_call_purpose_id: str = None,
    phone_call_outcome_id: str = None,
    note: str = None
):
    """
    Update an existing call record in Apollo.

    This function calls the Update Call Records endpoint to modify call details logged in your team's Apollo database.

    Note:
    - Requires a master API key; unauthorized calls return 403.

    Parameters:
        call_id (str): Apollo ID of the call record to update (required).
        logged (bool, optional): True to create an individual record for the call.
        user_id (list[str], optional): Apollo user IDs of the caller(s).
        contact_id (str, optional): Apollo contact ID of the called person.
        account_id (str, optional): Apollo account ID associated with the call.
        to_number (str, optional): Phone number dialed.
        from_number (str, optional): Phone number that placed the call.
        status (str, optional): Call status ('queued', 'ringing', 'in-progress', 'completed', 'no_answer', 'failed', 'busy').
        start_time (str, optional): ISO 8601 formatted start time (GMT or with offset).
        end_time (str, optional): ISO 8601 formatted end time (GMT or with offset).
        duration (int, optional): Duration of the call in seconds.
        phone_call_purpose_id (str, optional): Call purpose ID in your Apollo account.
        phone_call_outcome_id (str, optional): Call outcome ID in your Apollo account.
        note (str, optional): Additional note for the call record.

    Returns:
        Response text from Apollo API or error details.
    """

    url = f"https://api.apollo.io/api/v1/phone_calls/{call_id}"
    params = {
        "logged": logged,
        "user_id[]": user_ids,
        "contact_id": contact_id,
        "account_id": account_id,
        "to_number": to_number,
        "from_number": from_number,
        "status": status,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "phone_call_purpose_id": phone_call_purpose_id,
        "phone_call_outcome_id": phone_call_outcome_id,
        "note": note
    }
    headers = get_apollo_client()  # Your master API key headers here

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, headers=headers, params=params)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
