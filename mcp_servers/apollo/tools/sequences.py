import httpx
from .base import get_apollo_client

async def apollo_search_sequences(
    q_name: str = None,
    page: int = None,
    per_page: int = None
):
    """
    Search for sequences created in your team's Apollo account.

    POST https://api.apollo.io/api/v1/emailer_campaigns/search

    Query Parameters:
    - q_name (string, optional): Keywords to filter sequence names (partial matches only).
    - page (string, optional): Page number to retrieve for paginated results.
    - per_page (string, optional): Number of results per page to improve performance.

    Notes:
    - Requires a master API key.
    - Only searches sequence names.
    - Not available for free Apollo plans.
    """

    url = "https://api.apollo.io/api/v1/emailer_campaigns/search"
    params = {
        "q_name": q_name,
        "page": page,
        "per_page": per_page
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

async def apollo_add_contacts_to_sequence(
    sequence_id: str,
    emailer_campaign_id: str,
    contact_ids: list,
    send_email_from_email_account_id: str,
    sequence_no_email: bool = False,
    sequence_unverified_email: bool = False,
    sequence_job_change: bool = False,
    sequence_active_in_other_campaigns: bool = False,
    sequence_finished_in_other_campaigns: bool = False,
    user_id: str = None
):
    """
    Add contacts to an existing sequence in your Apollo account.

    POST https://api.apollo.io/api/v1/emailer_campaigns/{sequence_id}/add_contact_ids

    Path Parameters:
    - sequence_id (string, required): Apollo ID of the sequence to add contacts to.

    Query Parameters:
    - emailer_campaign_id (string, required): Same as sequence_id.
    - contact_ids (array of strings, required): List of Apollo contact IDs to add.
    - send_email_from_email_account_id (string, required): Apollo email account ID used to send emails.
    - sequence_no_email (boolean, optional, default=False): Add contacts without email addresses.
    - sequence_unverified_email (boolean, optional, default=False): Add contacts with unverified emails.
    - sequence_job_change (boolean, optional, default=False): Add contacts who recently changed jobs.
    - sequence_active_in_other_campaigns (boolean, optional, default=False): Add contacts active in other sequences.
    - sequence_finished_in_other_campaigns (boolean, optional, default=False): Add contacts finished in other sequences.
    - user_id (string, optional): Apollo user ID performing the action (for activity logs).

    Notes:
    - Requires master API key.
    - Only contacts can be added.
    - Use Search for Sequences and Search for Contacts endpoints to find IDs.
    - Use Get a List of Email Accounts endpoint to find email account IDs.
    """

    url = f"https://api.apollo.io/api/v1/emailer_campaigns/{sequence_id}/add_contact_ids"
    headers = get_apollo_client()  # Needs master API key

    params = {
        "emailer_campaign_id": emailer_campaign_id,
        "contact_ids[]": contact_ids,
        "send_email_from_email_account_id": send_email_from_email_account_id,
        "sequence_no_email": sequence_no_email,
        "sequence_unverified_email": sequence_unverified_email,
        "sequence_job_change": sequence_job_change,
        "sequence_active_in_other_campaigns": sequence_active_in_other_campaigns,
        "sequence_finished_in_other_campaigns": sequence_finished_in_other_campaigns,
    }

    if user_id:
        params["user_id"] = user_id

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


async def apollo_update_contact_status_in_sequence(
    emailer_campaign_ids: list,
    contact_ids: list,
    mode: str
):
    """
    Update contact status in one or more sequences.

    POST https://api.apollo.io/api/v1/emailer_campaigns/remove_or_stop_contact_ids

    Query Parameters:
    - emailer_campaign_ids[] (array of strings, required): Apollo IDs of sequences to update.
    - contact_ids[] (array of strings, required): Apollo contact IDs whose sequence status will be updated.
    - mode (string, required): Action to perform on contacts within sequences.
        Options:
          * "mark_as_finished" — mark contacts as finished in the sequence.
          * "remove" — remove contacts from the sequence.
          * "stop" — stop contacts' progress in the sequence.

    Notes:
    - Requires master API key.
    - Use Search for Sequences and Search for Contacts endpoints to get IDs.
    """

    url = "https://api.apollo.io/api/v1/emailer_campaigns/remove_or_stop_contact_ids"
    headers = get_apollo_client()  # Needs master API key

    params = {
        "emailer_campaign_ids[]": emailer_campaign_ids,
        "contact_ids[]": contact_ids,
        "mode": mode  # must be 'mark_as_finished', 'remove', or 'stop'
    }

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

async def apollo_search_outreach_emails(
    emailer_message_stats: list = None,
    emailer_message_reply_classes: list = None,
    user_ids: list = None,
    email_account_id_and_aliases: str = None,
    emailer_campaign_ids: list = None,
    not_emailer_campaign_ids: list = None,
    emailer_message_date_range_mode: str = None,
    emailerMessageDateRange_max: str = None,
    emailerMessageDateRange_min: str = None,
    not_sent_reason_cds: list = None,
    q_keywords: str = None,
    page: int = None,
    per_page: int = None
):
    """
    Search for outreach emails sent as part of Apollo sequences.

    Parameters:
    - emailer_message_stats (list of str, optional): Filter emails by their status (e.g., delivered, opened).
    - emailer_message_reply_classes (list of str, optional): Filter emails by recipient response sentiment (e.g., willing_to_meet).
    - user_ids (list of str, optional): Filter emails sent by specific user IDs.
    - email_account_id_and_aliases (str, optional): Filter by linked email account and its aliases.
    - emailer_campaign_ids (list of str, optional): Include emails from specific sequences only.
    - not_emailer_campaign_ids (list of str, optional): Exclude emails from specific sequences.
    - emailer_message_date_range_mode (str, optional): Mode for date filtering, either "due_at" or "completed_at".
    - emailerMessageDateRange_max (str, optional): Upper bound date (YYYY-MM-DD).
    - emailerMessageDateRange_min (str, optional): Lower bound date (YYYY-MM-DD).
    - not_sent_reason_cds (list of str, optional): Filter emails by reasons for not being sent.
    - q_keywords (str, optional): Keyword search in email content or sender.
    - page (int, optional): Page number for pagination.
    - per_page (int, optional): Number of results per page.

    Returns:
    - JSON response with filtered outreach emails matching the criteria.

    Note:
    - Requires a master API key.
    - Limited to 50,000 records (100 per page, max 500 pages).
    """

    url = "https://api.apollo.io/api/v1/emailer_messages/search"
    params = {
        "emailer_message_stats[]": emailer_message_stats,
        "emailer_message_reply_classes[]": emailer_message_reply_classes,
        "user_ids[]": user_ids,
        "email_account_id_and_aliases": email_account_id_and_aliases,
        "emailer_campaign_ids[]": emailer_campaign_ids,
        "not_emailer_campaign_ids[]": not_emailer_campaign_ids,
        "emailer_message_date_range_mode": emailer_message_date_range_mode,
        "emailerMessageDateRange[max]": emailerMessageDateRange_max,
        "emailerMessageDateRange[min]": emailerMessageDateRange_min,
        "not_sent_reason_cds[]": not_sent_reason_cds,
        "q_keywords": q_keywords,
        "page": page,
        "per_page": per_page,
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

async def apollo_check_email_stats(email_id: str):
    """
    Retrieve detailed statistics and information for a specific outreach email sent via an Apollo sequence.

    Parameters:
    - id (str): Required. The unique ID of the email to retrieve stats for.

    Returns:
    - JSON response containing email content, open and click statistics, and contact details.

    Notes:
    - Requires a master API key.
    - Accessible only to paid Apollo plans.
    """

    url = f"https://api.apollo.io/api/v1/emailer_messages/{email_id}/activities"
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
