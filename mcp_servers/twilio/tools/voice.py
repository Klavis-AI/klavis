import logging
from typing import Optional, Dict, Any
from .base import get_twilio_client, validate_phone_number

# Configure logging
logger = logging.getLogger(__name__)

async def twilio_make_call(
    to: str,
    from_: str,
    url: Optional[str] = None,
    twiml: Optional[str] = None,
    method: str = "POST",
    status_callback: Optional[str] = None,
    timeout: int = 60,
    record: bool = False
) -> dict:
    """
    Make a phone call using Twilio.
    
    Parameters:
    - to: Phone number to call in E.164 format
    - from_: Caller phone number (must be a Twilio phone number)
    - url: URL that returns TwiML instructions for the call
    - twiml: TwiML instructions as a string (alternative to url)
    - method: HTTP method for the webhook (GET or POST)
    - status_callback: URL to receive call status updates
    - timeout: Number of seconds to wait for an answer (default 60)
    - record: Whether to record the call
    
    Returns:
    - Dictionary containing call SID, status, and other details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        # Validate phone numbers
        to_number = validate_phone_number(to)
        from_number = validate_phone_number(from_)
        
        if not url and not twiml:
            raise ValueError("Either 'url' or 'twiml' parameter must be provided")
        
        if url and twiml:
            raise ValueError("Cannot specify both 'url' and 'twiml' parameters")
        
        logger.info(f"Making call from {from_number} to {to_number}")
        
        call_params = {
            'from_': from_number,
            'to': to_number,
            'method': method.upper(),
            'timeout': timeout
        }
        
        if url:
            call_params['url'] = url
        elif twiml:
            call_params['twiml'] = twiml
            
        if status_callback:
            call_params['status_callback'] = status_callback
            
        if record:
            call_params['record'] = record
        
        call = client.calls.create(**call_params)
        
        logger.info(f"Call initiated successfully. SID: {call.sid}")
        
        return {
            'sid': call.sid,
            'status': call.status,
            'direction': call.direction,
            'to': call.to,
            'duration': call.duration,
            'price': call.price,
            'price_unit': call.price_unit,
            'date_created': call.date_created.isoformat() if call.date_created else None,
            'date_updated': call.date_updated.isoformat() if call.date_updated else None,
        }
    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise e

async def twilio_get_calls(
    limit: int = 20,
    status: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None,
    start_time_after: Optional[str] = None,
    start_time_before: Optional[str] = None
) -> dict:
    """
    Retrieve a list of calls from Twilio account.
    
    Parameters:
    - limit: Maximum number of calls to retrieve (default 20, max 1000)
    - status: Filter by call status (queued, ringing, in-progress, completed, busy, failed, no-answer, canceled)
    - from_: Filter by caller phone number
    - to: Filter by called phone number
    - start_time_after: ISO date string to filter calls started after this time
    - start_time_before: ISO date string to filter calls started before this time
    
    Returns:
    - Dictionary with list of calls and metadata
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving up to {limit} calls")
        
        filter_params = {}
        if status:
            valid_statuses = ['queued', 'ringing', 'in-progress', 'completed', 'busy', 'failed', 'no-answer', 'canceled']
            if status.lower() not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            filter_params['status'] = status.lower()
        
        if from_:
            filter_params['from_'] = validate_phone_number(from_)
        if to:
            filter_params['to'] = validate_phone_number(to)
        if start_time_after:
            filter_params['start_time_after'] = start_time_after
        if start_time_before:
            filter_params['start_time_before'] = start_time_before
        
        calls = client.calls.list(limit=limit, **filter_params)
        
        call_list = []
        for call in calls:
            call_list.append({
                'sid': call.sid,
                'status': call.status,
                'direction': call.direction, # Handle reserved keyword
                'to': call.to,
                'duration': call.duration,
                'price': call.price,
                'price_unit': call.price_unit,
                'forwarded_from': call.forwarded_from,
                'caller_name': call.caller_name,
                'date_created': call.date_created.isoformat() if call.date_created else None,
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None,
            })
        
        logger.info(f"Retrieved {len(call_list)} calls")
        
        return {
            'calls': call_list,
            'count': len(call_list),
            'filters_applied': filter_params
        }
    except Exception as e:
        logger.error(f"Error retrieving calls: {e}")
        raise e

async def twilio_get_call_by_sid(call_sid: str) -> dict:
    """
    Retrieve a specific call by its SID.
    
    Parameters:
    - call_sid: Unique identifier for the call
    
    Returns:
    - Dictionary containing call details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info(f"Retrieving call with SID: {call_sid}")
        
        call = client.calls(call_sid).fetch()
        
        return {
            'sid': call.sid,
            'status': call.status,
            'direction': call.direction,
            'to': call.to,
            'duration': call.duration,
            'price': call.price,
            'price_unit': call.price_unit,
            'forwarded_from': call.forwarded_from,
            'caller_name': call.caller_name,
            'parent_call_sid': call.parent_call_sid,
            'answered_by': call.answered_by,
            'date_created': call.date_created.isoformat() if call.date_created else None,
            'date_updated': call.date_updated.isoformat() if call.date_updated else None,
            'start_time': call.start_time.isoformat() if call.start_time else None,
            'end_time': call.end_time.isoformat() if call.end_time else None,
        }
    except Exception as e:
        logger.error(f"Error retrieving call {call_sid}: {e}")
        raise e

async def twilio_get_recordings(
    limit: int = 20,
    call_sid: Optional[str] = None,
    date_created_after: Optional[str] = None,
    date_created_before: Optional[str] = None
) -> dict:
    """
    Retrieve call recordings from Twilio account.
    
    Parameters:
    - limit: Maximum number of recordings to retrieve (default 20, max 1000)
    - call_sid: Filter recordings by specific call SID
    - date_created_after: ISO date string to filter recordings created after this date
    - date_created_before: ISO date string to filter recordings created before this date
    
    Returns:
    - Dictionary with list of recordings and metadata
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving up to {limit} recordings")
        
        filter_params = {}
        if call_sid:
            filter_params['call_sid'] = call_sid
        if date_created_after:
            filter_params['date_created_after'] = date_created_after
        if date_created_before:
            filter_params['date_created_before'] = date_created_before
        
        recordings = client.recordings.list(limit=limit, **filter_params)
        
        recording_list = []
        for recording in recordings:
            recording_list.append({
                'sid': recording.sid,
                'call_sid': recording.call_sid,
                'status': recording.status,
                'duration': recording.duration,
                'channels': recording.channels,
                'source': recording.source,
                'price': recording.price,
                'price_unit': recording.price_unit,
                'uri': recording.uri,
                'date_created': recording.date_created.isoformat() if recording.date_created else None,
                'date_updated': recording.date_updated.isoformat() if recording.date_updated else None,
            })
        
        logger.info(f"Retrieved {len(recording_list)} recordings")
        
        return {
            'recordings': recording_list,
            'count': len(recording_list),
            'filters_applied': filter_params
        }
    except Exception as e:
        logger.error(f"Error retrieving recordings: {e}")
        raise e