import requests
import re
from typing import Any, Dict
from .auth import get_auth_token


async def create_meeting(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function creates a new meeting space by calling the Google Meet API. 
    We send an empty body because Meet doesn't need extra details for basic creation.
    """
    access_token = get_auth_token()
    try:
        response = requests.post(
            'https://meet.googleapis.com/v2/spaces',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={}
        )
        response.raise_for_status()
        space = response.json()
        if 'name' not in space or 'meetingUri' not in space:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'space_id': space['name'],
            'meet_link': space['meetingUri'],
            'space': space
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to create meeting space: {e.response.status_code if e.response else ''} {e}")


async def get_meeting_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get details of a meeting space."""
    access_token = get_auth_token()
    space_id = args.get('space_id')
    if not space_id or not isinstance(space_id, str) or len(space_id) < 1 or len(space_id) > 1000 or not bool(re.match(r'^spaces/[a-zA-Z0-9\-_]+$', space_id)):
        raise ValueError('Invalid space_id')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(space_id)}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        space = response.json()
        if 'name' not in space or 'meetingUri' not in space:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'space_id': space['name'],
            'meet_link': space['meetingUri'],
            'space': space
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get meeting space: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")
