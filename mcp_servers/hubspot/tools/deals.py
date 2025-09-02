import logging
import json
from hubspot.crm.deals import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

def _build_dealstage_label_map(client) -> dict:
    """
    Build a mapping from deal stage ID to its human-readable label across all deal pipelines.

    Returns:
    - dict mapping stage_id -> label (e.g., {"appointmentscheduled": "Appointment Scheduled", "1890285259": "POC"})
    """
    stage_id_to_label: dict = {}
    try:
        pipelines = client.crm.pipelines.pipelines_api.get_all("deals")
        for pipeline in getattr(pipelines, "results", []) or []:
            try:
                stages = client.crm.pipelines.pipeline_stages_api.get_all("deals", pipeline.id)
                for stage in getattr(stages, "results", []) or []:
                    if getattr(stage, "id", None) and getattr(stage, "label", None):
                        stage_id_to_label[stage.id] = stage.label
            except Exception as inner_exc:
                logger.debug(f"Failed to fetch stages for pipeline {getattr(pipeline, 'id', 'unknown')}: {inner_exc}")
    except Exception as exc:
        logger.debug(f"Failed to fetch pipelines for deals: {exc}")
    return stage_id_to_label

async def hubspot_get_deals(limit: int = 10):
    """
    Fetch a list of deals from HubSpot.

    Parameters:
    - limit: Number of deals to return

    Returns:
    - List of deal records
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching up to {limit} deals...")
        result = client.crm.deals.basic_api.get_page(limit=limit)
        # Enrich with human-readable dealstage label
        stage_label_map = _build_dealstage_label_map(client)
        for obj in getattr(result, "results", []) or []:
            props = getattr(obj, "properties", {}) or {}
            stage_id = props.get("dealstage")
            if stage_id and stage_id in stage_label_map:
                props["dealstage_label"] = stage_label_map[stage_id]
                obj.properties = props
        logger.info(f"Fetched {len(result.results)} deals successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return None

async def hubspot_get_deal_by_id(deal_id: str):
    """
    Fetch a deal by its ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - Deal object
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching deal ID: {deal_id}...")
        result = client.crm.deals.basic_api.get_by_id(deal_id)
        # Enrich with human-readable dealstage label
        stage_label_map = _build_dealstage_label_map(client)
        props = getattr(result, "properties", {}) or {}
        stage_id = props.get("dealstage")
        if stage_id and stage_id in stage_label_map:
            props["dealstage_label"] = stage_label_map[stage_id]
            result.properties = props
        logger.info(f"Fetched deal ID: {deal_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deal by ID: {e}")
        return None

async def hubspot_create_deal(properties: str):
    """
    Create a new deal.

    Parameters:
    - properties: JSON string of deal properties

    Returns:
    - Newly created deal
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info("Creating a new deal...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.deals.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Deal created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return f"Error occurred: {e}"

async def hubspot_update_deal_by_id(deal_id: str, updates: str):
    """
    Update a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Updating deal ID: {deal_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.deals.basic_api.update(deal_id, data)
        logger.info(f"Deal ID: {deal_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for deal ID {deal_id}: {e}")
        return f"Error occurred: {e}"

async def hubspot_delete_deal_by_id(deal_id: str):
    """
    Delete a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - None
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Deleting deal ID: {deal_id}...")
        client.crm.deals.basic_api.archive(deal_id)
        logger.info(f"Deal ID: {deal_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting deal: {e}")
        return f"Error occurred: {e}"