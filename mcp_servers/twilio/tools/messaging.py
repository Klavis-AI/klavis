import logging
from typing import Optional, List
from .base import get_twilio_client, validate_phone_number

# Configure logging
logger = logging.getLogger(__name__)

async def twilio_send_sms(
    to: str,
    from_: str,
    body: str,
    status_callback: Optional[str] = None
) -> dict:
    """
    Send an SMS message using Twilio.
    
    Parameters:
    - to: Recipient phone number in E.164 format (e.g., +1234567890)
    - from_: Sender phone number (must be a Twilio phone number)
    - body: Message content (up to 1600 characters)
    - status_callback: Optional webhook URL for delivery status updates
    
    Returns:
    - Dictionary containing message SID, status, and other details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        # Validate phone numbers
        to_number = validate_phone_number(to)
        from_number = validate_phone_number(from_)
        
        if len(body) > 1600:
            raise ValueError("SMS body cannot exceed 1600 characters")
        
        logger.info(f"Sending SMS from {from_number} to {to_number}")
        
        message_params = {
            'body': body,
            'from_': from_number,
            'to': to_number
        }
        
        if status_callback:
            message_params['status_callback'] = status_callback
        
        message = client.messages.create(**message_params)
        
        logger.info(f"SMS sent successfully. SID: {message.sid}")
        
        return {
            'sid': message.sid,
            'status': message.status,
            'direction': message.direction, # Handle reserved keyword
            'to': message.to,
            'body': message.body,
            'num_segments': message.num_segments,
            'price': message.price,
            'price_unit': message.price_unit,
            'date_created': message.date_created.isoformat() if message.date_created else None,
            'date_sent': message.date_sent.isoformat() if message.date_sent else None,
        }
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise e

async def twilio_send_mms(
    to: str,
    from_: str,
    body: Optional[str] = None,
    media_url: Optional[List[str]] = None,
    status_callback: Optional[str] = None
) -> dict:
    """
    Send an MMS message with media attachments using Twilio.
    
    Parameters:
    - to: Recipient phone number in E.164 format
    - from_: Sender phone number (must be a Twilio phone number)
    - body: Optional message text
    - media_url: List of media URLs to attach (images, videos, audio, PDFs)
    - status_callback: Optional webhook URL for delivery status updates
    
    Returns:
    - Dictionary containing message SID, status, and other details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        # Validate phone numbers
        to_number = validate_phone_number(to)
        from_number = validate_phone_number(from_)
        
        if not body and not media_url:
            raise ValueError("MMS must contain either body text or media URL")
        
        if media_url and len(media_url) > 10:
            raise ValueError("Maximum 10 media attachments allowed per MMS")
        
        logger.info(f"Sending MMS from {from_number} to {to_number}")
        
        message_params = {
            'from_': from_number,
            'to': to_number
        }
        
        if body:
            message_params['body'] = body
        
        if media_url:
            message_params['media_url'] = media_url
            
        if status_callback:
            message_params['status_callback'] = status_callback
        
        message = client.messages.create(**message_params)
        
        logger.info(f"MMS sent successfully. SID: {message.sid}")
        
        return {
            'sid': message.sid,
            'status': message.status,
            'direction': message.direction,  # Handle reserved keyword
            'to': message.to,
            'body': message.body,
            'num_media': message.num_media,
            'num_segments': message.num_segments,
            'price': message.price,
            'price_unit': message.price_unit,
            'date_created': message.date_created.isoformat() if message.date_created else None,
            'date_sent': message.date_sent.isoformat() if message.date_sent else None,
        }
    except Exception as e:
        logger.error(f"Error sending MMS: {e}")
        raise e

async def twilio_get_messages(
    limit: int = 20,
    date_sent_after: Optional[str] = None,
    date_sent_before: Optional[str] = None,
    from_: Optional[str] = None,
    to: Optional[str] = None
) -> dict:
    """
    Retrieve a list of messages from Twilio account.
    
    Parameters:
    - limit: Maximum number of messages to retrieve (default 20, max 1000)
    - date_sent_after: ISO date string to filter messages sent after this date
    - date_sent_before: ISO date string to filter messages sent before this date
    - from_: Filter by sender phone number
    - to: Filter by recipient phone number
    
    Returns:
    - Dictionary with list of messages and metadata
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving up to {limit} messages")
        
        filter_params = {}
        if date_sent_after:
            filter_params['date_sent_after'] = date_sent_after
        if date_sent_before:
            filter_params['date_sent_before'] = date_sent_before
        if from_:
            filter_params['from_'] = validate_phone_number(from_)
        if to:
            filter_params['to'] = validate_phone_number(to)
        
        messages = client.messages.list(limit=limit, **filter_params)
        
        message_list = []
        for message in messages:
            message_list.append({
                'sid': message.sid,
                'status': message.status,
                'direction': message.direction, # Handle reserved keyword
                'to': message.to,
                'body': message.body,
                'num_segments': message.num_segments,
                'num_media': message.num_media,
                'price': message.price,
                'price_unit': message.price_unit,
                'date_created': message.date_created.isoformat() if message.date_created else None,
                'date_sent': message.date_sent.isoformat() if message.date_sent else None,
            })
        
        logger.info(f"Retrieved {len(message_list)} messages")
        
        return {
            'messages': message_list,
            'count': len(message_list),
            'filters_applied': filter_params
        }
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        raise e

async def twilio_get_message_by_sid(message_sid: str) -> dict:
    """
    Retrieve a specific message by its SID.
    
    Parameters:
    - message_sid: Unique identifier for the message
    
    Returns:
    - Dictionary containing message details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info(f"Retrieving message with SID: {message_sid}")
        
        message = client.messages(message_sid).fetch()
        
        return {
            'sid': message.sid,
            'status': message.status,
            'direction': message.direction, # Handle reserved keyword
            'to': message.to,
            'body': message.body,
            'num_segments': message.num_segments,
            'num_media': message.num_media,
            'price': message.price,
            'price_unit': message.price_unit,
            'error_code': message.error_code,
            'error_message': message.error_message,
            'date_created': message.date_created.isoformat() if message.date_created else None,
            'date_sent': message.date_sent.isoformat() if message.date_sent else None,
            'date_updated': message.date_updated.isoformat() if message.date_updated else None,
        }
    except Exception as e:
        logger.error(f"Error retrieving message {message_sid}: {e}")
        raise e