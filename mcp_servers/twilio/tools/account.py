import logging
from typing import Optional, Dict, Any
from .base import get_twilio_client

# Configure logging
logger = logging.getLogger(__name__)

async def twilio_get_account_info() -> dict:
    """
    Retrieve Twilio account information and status.
    
    Returns:
    - Dictionary containing account details, status, and settings
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info("Retrieving Twilio account information")
        
        account = client.api.account.fetch()
        
        return {
            'sid': account.sid,
            'friendly_name': account.friendly_name,
            'status': account.status,
            'type': account.type,
            'auth_token': account.auth_token,
            'owner_account_sid': account.owner_account_sid,
            'date_created': account.date_created.isoformat() if account.date_created else None,
            'date_updated': account.date_updated.isoformat() if account.date_updated else None,
        }
    except Exception as e:
        logger.error(f"Error retrieving account information: {e}")
        raise e

async def twilio_get_balance() -> dict:
    """
    Retrieve current account balance.
    
    Returns:
    - Dictionary containing account balance information
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        logger.info("Retrieving account balance")
        
        balance = client.balance.fetch()
        
        return {
            'account_sid': balance.account_sid,
            'balance': balance.balance,
            'currency': balance.currency,
        }
    except Exception as e:
        logger.error(f"Error retrieving account balance: {e}")
        raise e

async def twilio_get_usage_records(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "daily",
    limit: int = 50
) -> dict:
    """
    Retrieve usage records for the account.
    
    Parameters:
    - category: Usage category (sms, calls, recordings, etc.)
    - start_date: Start date for usage period (YYYY-MM-DD format)
    - end_date: End date for usage period (YYYY-MM-DD format)
    - granularity: Time granularity (daily, monthly, yearly, all-time)
    - limit: Maximum number of records to retrieve (default 50, max 1000)
    
    Returns:
    - Dictionary with usage records and totals
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving usage records with granularity: {granularity}")
        
        filter_params = {'limit': limit}
        
        if category:
            filter_params['category'] = category
        if start_date:
            filter_params['start_date'] = start_date
        if end_date:
            filter_params['end_date'] = end_date
        
        # Map granularity to the appropriate usage endpoint
        if granularity.lower() == "daily":
            usage_records = client.usage.records.daily.list(**filter_params)
        elif granularity.lower() == "monthly":
            usage_records = client.usage.records.monthly.list(**filter_params)
        elif granularity.lower() == "yearly":
            usage_records = client.usage.records.yearly.list(**filter_params)
        elif granularity.lower() == "all-time":
            usage_records = client.usage.records.list(**filter_params)
        else:
            raise ValueError("Granularity must be one of: daily, monthly, yearly, all-time")
        
        records_list = []
        total_usage = 0
        total_price = 0
        
        for record in usage_records:
            record_data = {
                'category': record.category,
                'description': record.description,
                'count': record.count,
                'count_unit': record.count_unit,
                'usage': record.usage,
                'usage_unit': record.usage_unit,
                'price': float(record.price) if record.price else 0,
                'price_unit': record.price_unit,
                'start_date': record.start_date.strftime('%Y-%m-%d') if record.start_date else None,
                'end_date': record.end_date.strftime('%Y-%m-%d') if record.end_date else None,
            }
            records_list.append(record_data)
            
            # Accumulate totals
            if record.usage:
                total_usage += int(record.usage)
            if record.price:
                total_price += float(record.price)
        
        logger.info(f"Retrieved {len(records_list)} usage records")
        
        return {
            'usage_records': records_list,
            'count': len(records_list),
            'summary': {
                'total_usage': total_usage,
                'total_price': round(total_price, 4),
                'currency': records_list[0]['price_unit'] if records_list else 'USD',
                'granularity': granularity,
            },
            'filters_applied': {k: v for k, v in filter_params.items() if k != 'limit'}
        }
    except Exception as e:
        logger.error(f"Error retrieving usage records: {e}")
        raise e

async def twilio_get_usage_triggers(limit: int = 50) -> dict:
    """
    Retrieve usage triggers configured for the account.
    
    Parameters:
    - limit: Maximum number of triggers to retrieve (default 50, max 1000)
    
    Returns:
    - Dictionary with list of configured usage triggers
    """
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client not available. Please check authentication.")
    
    try:
        if limit > 1000:
            limit = 1000
            
        logger.info(f"Retrieving up to {limit} usage triggers")
        
        triggers = client.usage.triggers.list(limit=limit)
        
        trigger_list = []
        for trigger in triggers:
            trigger_list.append({
                'sid': trigger.sid,
                'friendly_name': trigger.friendly_name,
                'usage_category': trigger.usage_category,
                'trigger_value': trigger.trigger_value,
                'current_value': trigger.current_value,
                'trigger_by': trigger.trigger_by,
                'recurring': trigger.recurring,
                'callback_url': trigger.callback_url,
                'callback_method': trigger.callback_method,
                'date_created': trigger.date_created.isoformat() if trigger.date_created else None,
                'date_fired': trigger.date_fired.isoformat() if trigger.date_fired else None,
                'date_updated': trigger.date_updated.isoformat() if trigger.date_updated else None,
            })
        
        logger.info(f"Retrieved {len(trigger_list)} usage triggers")
        
        return {
            'usage_triggers': trigger_list,
            'count': len(trigger_list)
        }
    except Exception as e:
        logger.error(f"Error retrieving usage triggers: {e}")
        raise e