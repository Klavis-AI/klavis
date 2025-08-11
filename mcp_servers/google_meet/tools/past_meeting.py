import requests
import re
from typing import Any, Dict
from .auth import get_auth_token


async def get_past_meetings(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get details for completed meetings."""
    access_token = get_auth_token()
    params = {}
    page_size = args.get('page_size', 10)
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise ValueError('Invalid page_size')
    params['pageSize'] = page_size
    if 'page_token' in args:
        page_token = args['page_token']
        if isinstance(page_token, str) and len(page_token) <= 5000:
            params['pageToken'] = page_token
        else:
            raise ValueError('Invalid page_token')
    if 'filter' in args:
        filter_expr = args['filter']
        if isinstance(filter_expr, str) and len(filter_expr) <= 2000:
            params['filter'] = filter_expr
        else:
            raise ValueError('Invalid filter')
    try:
        response = requests.get(
            'https://meet.googleapis.com/v2/conferenceRecords',
            params=params,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        data = response.json()
        conference_records = data.get('conferenceRecords', [])
        return {
            'conference_records': conference_records,
            'next_page_token': data.get('nextPageToken')
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list conference records: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")


async def get_past_meeting_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get details of a specific meeting."""
    access_token = get_auth_token()
    conference_record_id = args.get('conference_record_id')
    if not conference_record_id or not isinstance(conference_record_id, str) or len(conference_record_id) < 1 or len(conference_record_id) > 1000 or not bool(re.match(r'^conferenceRecords/[a-zA-Z0-9\-_]+$', conference_record_id)):
        raise ValueError('Invalid conference_record_id')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(conference_record_id)}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        record = response.json()
        if 'name' not in record:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'conference_record_id': record['name'],
            'record': record
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get conference record: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")


async def get_past_meeting_participants(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get a list of participants from a past meeting."""
    access_token = get_auth_token()
    conference_record_id = args.get('conference_record_id')
    if not conference_record_id or not isinstance(conference_record_id, str) or len(conference_record_id) < 1 or len(conference_record_id) > 1000 or not bool(re.match(r'^conferenceRecords/[a-zA-Z0-9\-_]+$', conference_record_id)):
        raise ValueError('Invalid conference_record_id')
    params = {}
    page_size = args.get('page_size', 10)
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise ValueError('Invalid page_size')
    params['pageSize'] = page_size
    if 'page_token' in args:
        page_token = args['page_token']
        if isinstance(page_token, str) and len(page_token) <= 5000:
            params['pageToken'] = page_token
        else:
            raise ValueError('Invalid page_token')
    if 'filter' in args:
        filter_expr = args['filter']
        if isinstance(filter_expr, str) and len(filter_expr) <= 2000:
            params['filter'] = filter_expr
        else:
            raise ValueError('Invalid filter')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(conference_record_id)}/participants',
            params=params,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        data = response.json()
        participants = data.get('participants', [])
        return {
            'participants': participants,
            'next_page_token': data.get('nextPageToken'),
            'participant_count': len(participants)
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list participants: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")
