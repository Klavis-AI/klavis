import logging
from typing import Optional, List, Dict, Any
from .base import get_twilio_client, validate_phone_number

# Configure logging
logger = logging.getLogger(__name__)

async def twilio_search_available_numbers(
    country_code: str = "US",
    area_code: Optional[str] = None,
    contains: Optional[str] = None,
    sms_enabled: bool = True,
    voice_enabled: bool = True,
    limit: int = 20
) -> dict:
    """
    Search for available phone numbers to purchase.
    
    Parameters:
    - country_code: Two-letter country code (default "US")
    - area_code: Specific area code to search within
    - contains: Search for numbers containing specific digits
    - sms_enabled: Filter for SMS-capable numbers (default True)
    - voice_enabled: Filter for voice-capable numbers (default True)
    - limit: Maximum number of results (default 20, max 50)
    
    Returns:
    - Dictionary with list of available phone numbers and their capabilities
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 50:
            limit = 50
            
        logger.info(f"Searching for available numbers in {country_code}")
        
        search_params = {
            'limit': limit,
            'sms_enabled': sms_enabled,
            'voice_enabled': voice_enabled
        }
        
        if area_code:
            search_params['area_code'] = area_code
        if contains:
            search_params['contains'] = contains
        
        if country_code.upper() == "US":
            numbers = client.available_phone_numbers("US").local.list(**search_params)
        else:
            numbers = client.available_phone_numbers(country_code.upper()).local.list(**search_params)
        
        number_list = []
        for number in numbers:
            number_list.append({
                'phone_number': number.phone_number,
                'friendly_name': number.friendly_name,
                'iso_country': number.iso_country,
                'locality': number.locality,
                'region': number.region,
                'postal_code': number.postal_code,
                'capabilities': {
                    'voice': number.capabilities.get('voice', False),
                    'sms': number.capabilities.get('SMS', False),
                    'mms': number.capabilities.get('MMS', False),
                    'fax': number.capabilities.get('fax', False)
                }
            })
        
        logger.info(f"Found {len(number_list)} available numbers")
        
        return {
            'available_numbers': number_list,
            'count': len(number_list),
            'search_criteria': search_params,
            'country_code': country_code.upper()
        }
    except Exception as e:
        logger.error(f"Error searching available numbers: {e}")
        raise e

async def twilio_purchase_phone_number(
    phone_number: str,
    friendly_name: Optional[str] = None,
    voice_url: Optional[str] = None,
    sms_url: Optional[str] = None,
    status_callback: Optional[str] = None
) -> dict:
    """
    Purchase a phone number from Twilio.
    
    Parameters:
    - phone_number: Phone number to purchase in E.164 format
    - friendly_name: A human-readable name for the number
    - voice_url: URL to handle incoming voice calls
    - sms_url: URL to handle incoming SMS messages
    - status_callback: URL to receive status updates
    
    Returns:
    - Dictionary containing purchased number details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        phone_number = validate_phone_number(phone_number)
        
        logger.info(f"Purchasing phone number: {phone_number}")
        
        purchase_params = {
            'phone_number': phone_number
        }
        
        if friendly_name:
            purchase_params['friendly_name'] = friendly_name
        if voice_url:
            purchase_params['voice_url'] = voice_url
        if sms_url:
            purchase_params['sms_url'] = sms_url
        if status_callback:
            purchase_params['status_callback'] = status_callback
        
        incoming_number = client.incoming_phone_numbers.create(**purchase_params)
        
        logger.info(f"Phone number purchased successfully. SID: {incoming_number.sid}")
        
        return {
            'sid': incoming_number.sid,
            'phone_number': incoming_number.phone_number,
            'friendly_name': incoming_number.friendly_name,
            'voice_url': incoming_number.voice_url,
            'sms_url': incoming_number.sms_url,
            'status_callback': incoming_number.status_callback,
            'capabilities': {
                'voice': incoming_number.capabilities.get('voice', False),
                'sms': incoming_number.capabilities.get('SMS', False),
                'mms': incoming_number.capabilities.get('MMS', False),
                'fax': incoming_number.capabilities.get('fax', False)
            },
            'date_created': incoming_number.date_created.isoformat() if incoming_number.date_created else None,
        }
    except Exception as e:
        logger.error(f"Error purchasing phone number {phone_number}: {e}")
        raise e

async def twilio_list_phone_numbers(limit: int = 20) -> dict:
    """
    List all phone numbers owned by the Twilio account.
    
    Parameters:
    - limit: Maximum number of numbers to retrieve (default 20, max 1000)
    
    Returns:
    - Dictionary with list of owned phone numbers
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving up to {limit} phone numbers")
        
        numbers = client.incoming_phone_numbers.list(limit=limit)
        
        number_list = []
        for number in numbers:
            number_list.append({
                'sid': number.sid,
                'phone_number': number.phone_number,
                'friendly_name': number.friendly_name,
                'voice_url': number.voice_url,
                'sms_url': number.sms_url,
                'status_callback': number.status_callback,
                'capabilities': {
                    'voice': number.capabilities.get('voice', False),
                    'sms': number.capabilities.get('SMS', False),
                    'mms': number.capabilities.get('MMS', False),
                    'fax': number.capabilities.get('fax', False)
                },
                'date_created': number.date_created.isoformat() if number.date_created else None,
                'date_updated': number.date_updated.isoformat() if number.date_updated else None,
            })
        
        logger.info(f"Retrieved {len(number_list)} phone numbers")
        
        return {
            'phone_numbers': number_list,
            'count': len(number_list)
        }
    except Exception as e:
        logger.error(f"Error listing phone numbers: {e}")
        raise e

async def twilio_update_phone_number(
    phone_number_sid: str,
    friendly_name: Optional[str] = None,
    voice_url: Optional[str] = None,
    sms_url: Optional[str] = None,
    status_callback: Optional[str] = None
) -> dict:
    """
    Update configuration of an existing phone number.
    
    Parameters:
    - phone_number_sid: SID of the phone number to update
    - friendly_name: New friendly name for the number
    - voice_url: New URL to handle incoming voice calls
    - sms_url: New URL to handle incoming SMS messages
    - status_callback: New URL to receive status updates
    
    Returns:
    - Dictionary containing updated phone number details
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info(f"Updating phone number with SID: {phone_number_sid}")
        
        update_params = {}
        if friendly_name is not None:
            update_params['friendly_name'] = friendly_name
        if voice_url is not None:
            update_params['voice_url'] = voice_url
        if sms_url is not None:
            update_params['sms_url'] = sms_url
        if status_callback is not None:
            update_params['status_callback'] = status_callback
        
        if not update_params:
            raise ValueError("At least one parameter must be provided to update")
        
        incoming_number = client.incoming_phone_numbers(phone_number_sid).update(**update_params)
        
        logger.info(f"Phone number updated successfully")
        
        return {
            'sid': incoming_number.sid,
            'phone_number': incoming_number.phone_number,
            'friendly_name': incoming_number.friendly_name,
            'voice_url': incoming_number.voice_url,
            'sms_url': incoming_number.sms_url,
            'status_callback': incoming_number.status_callback,
            'capabilities': {
                'voice': incoming_number.capabilities.get('voice', False),
                'sms': incoming_number.capabilities.get('SMS', False),
                'mms': incoming_number.capabilities.get('MMS', False),
                'fax': incoming_number.capabilities.get('fax', False)
            },
            'date_updated': incoming_number.date_updated.isoformat() if incoming_number.date_updated else None,
        }
    except Exception as e:
        logger.error(f"Error updating phone number {phone_number_sid}: {e}")
        raise e

async def twilio_release_phone_number(phone_number_sid: str) -> dict:
    """
    Release (delete) a phone number from the Twilio account.
    
    Parameters:
    - phone_number_sid: SID of the phone number to release
    
    Returns:
    - Dictionary confirming the release operation
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info(f"Releasing phone number with SID: {phone_number_sid}")
        
        # Fetch number details before deletion for confirmation
        number = client.incoming_phone_numbers(phone_number_sid).fetch()
        phone_number = number.phone_number
        
        # Delete the number
        client.incoming_phone_numbers(phone_number_sid).delete()
        
        logger.info(f"Phone number {phone_number} released successfully")
        
        return {
            'success': True,
            'message': f"Phone number {phone_number} has been released",
            'released_number': phone_number,
            'sid': phone_number_sid
        }
    except Exception as e:
        logger.error(f"Error releasing phone number {phone_number_sid}: {e}")
        raise e