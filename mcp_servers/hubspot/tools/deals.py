"""
HubSpot Deals API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
from typing import Dict, Optional
from hubspot.crm.deals import SimplePublicObjectInputForCreate, SimplePublicObjectInput

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    Deal,
    DealList,
    DealProperties,
    CreateResult,
    UpdateResult,
    DeleteResult,
    normalize_deal
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception
)

# Configure logging
logger = logging.getLogger(__name__)


def _build_dealstage_label_map(client) -> Dict[str, str]:
    """
    Build a mapping from deal stage ID to its human-readable label across all deal pipelines.

    Returns:
    - dict mapping stage_id -> label (e.g., {"appointmentscheduled": "Appointment Scheduled"})
    """
    stage_id_to_label: Dict[str, str] = {}
    try:
        pipelines = client.crm.pipelines.pipelines_api.get_all("deals")
        for pipeline in getattr(pipelines, "results", []) or []:
            try:
                stages = client.crm.pipelines.pipeline_stages_api.get_all("deals", pipeline.id)
                for stage in getattr(stages, "results", []) or []:
                    if getattr(stage, "id", None) and getattr(stage, "label", None):
                        stage_id_to_label[stage.id] = stage.label
            except Exception:
                # Silently ignore pipeline stage fetch errors
                pass
    except Exception:
        # Silently ignore pipeline fetch errors
        pass
    return stage_id_to_label


async def hubspot_get_deals(limit: int = 10) -> DealList:
    """
    Fetch a list of deals from HubSpot.

    Parameters:
    - limit: Number of deals to return

    Returns:
    - Klavis-normalized DealList schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching up to {limit} deals...")
        
        result = safe_api_call(
            client.crm.deals.basic_api.get_page,
            resource_type="deal",
            limit=limit
        )
        
        # Build stage label map for human-readable stage names
        stage_label_map = _build_dealstage_label_map(client)
        
        # Normalize response through Klavis schema
        deals = []
        for raw_deal in getattr(result, 'results', []) or []:
            deals.append(normalize_deal(raw_deal, stage_label_map))
        
        logger.info(f"Fetched {len(deals)} deals successfully.")
        return DealList(
            deals=deals,
            total=len(deals),
            has_more=bool(getattr(result, 'paging', None))
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="deal")


async def hubspot_get_deal_by_id(deal_id: str) -> Deal:
    """
    Fetch a deal by its ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - Klavis-normalized Deal schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching deal ID: {deal_id}...")
        
        result = safe_api_call(
            client.crm.deals.basic_api.get_by_id,
            resource_type="deal",
            resource_id=deal_id,
            deal_id=deal_id
        )
        
        # Build stage label map for human-readable stage name
        stage_label_map = _build_dealstage_label_map(client)
        
        logger.info(f"Fetched deal ID: {deal_id} successfully.")
        return normalize_deal(result, stage_label_map)
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="deal", resource_id=deal_id)


async def hubspot_create_deal(properties: str) -> CreateResult:
    """
    Create a new deal.

    Parameters:
    - properties: JSON string of deal properties

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info("Creating a new deal...")
        
        # Parse and validate input
        try:
            props = json.loads(properties)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="deal")
        
        # Common property name validation
        property_corrections = {
            'deal_name': 'dealname',
            'name': 'dealname',
            'deal_amount': 'amount',
            'value': 'amount',
            'deal_stage': 'dealstage',
            'stage': 'dealstage',
            'close_date': 'closedate',
            'deal_type': 'dealtype',
        }
        
        # Check for common mistakes
        invalid_props = []
        for prop_key in props.keys():
            if prop_key in property_corrections:
                invalid_props.append(prop_key)
        
        if invalid_props:
            raise ValidationError(resource_type="deal")
        
        data = SimplePublicObjectInputForCreate(properties=props)
        result = safe_api_call(
            client.crm.deals.basic_api.create,
            resource_type="deal",
            simple_public_object_input_for_create=data
        )
        
        logger.info("Deal created successfully.")
        return CreateResult(
            status="success",
            message="Deal created successfully",
            resource_id=getattr(result, 'id', None)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="deal")


async def hubspot_update_deal_by_id(deal_id: str, updates: str) -> UpdateResult:
    """
    Update a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID
    - updates: JSON string of updated fields

    Returns:
    - Klavis-normalized UpdateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Updating deal ID: {deal_id}...")
        
        # Parse and validate input
        try:
            updates_dict = json.loads(updates)
        except json.JSONDecodeError:
            raise ValidationError(resource_type="deal")
        
        data = SimplePublicObjectInput(properties=updates_dict)
        safe_api_call(
            client.crm.deals.basic_api.update,
            resource_type="deal",
            resource_id=deal_id,
            deal_id=deal_id,
            simple_public_object_input=data
        )
        
        logger.info(f"Deal ID: {deal_id} updated successfully.")
        return UpdateResult(
            status="success",
            message="Deal updated successfully",
            resource_id=deal_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="deal", resource_id=deal_id)


async def hubspot_delete_deal_by_id(deal_id: str) -> DeleteResult:
    """
    Delete a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Deleting deal ID: {deal_id}...")
        
        safe_api_call(
            client.crm.deals.basic_api.archive,
            resource_type="deal",
            resource_id=deal_id,
            deal_id=deal_id
        )
        
        logger.info(f"Deal ID: {deal_id} deleted successfully.")
        return DeleteResult(
            status="success",
            message="Deal deleted successfully",
            resource_id=deal_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="deal", resource_id=deal_id)
