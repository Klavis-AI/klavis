import logging
from typing import List, Optional
from .base import get_hubspot_client

logger = logging.getLogger(__name__)

# HubSpot Association Type IDs (default types)
ASSOCIATION_TYPES = {
    # Contact to Company
    "contacts_to_companies": 1,
    "companies_to_contacts": 2,
    
    # Contact to Deal
    "contacts_to_deals": 3,
    "deals_to_contacts": 4,
    
    # Contact to Ticket
    "contacts_to_tickets": 15,
    "tickets_to_contacts": 16,
    
    # Company to Deal
    "companies_to_deals": 5,
    "deals_to_companies": 6,
    
    # Company to Ticket
    "companies_to_tickets": 25,
    "tickets_to_companies": 26,
    
    # Deal to Ticket
    "deals_to_tickets": 27,
    "tickets_to_deals": 28,
    
    # Contact to Contact (related contacts)
    "contacts_to_contacts": 449,
    
    # Company to Company (parent/child companies)
    "companies_to_companies": 13,
}


async def hubspot_create_association(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    association_type_id: Optional[int] = None
):
    """
    Create an association between two HubSpot objects.
    
    Parameters:
    - from_object_type: The object type to associate from (contacts, companies, deals, tickets)
    - from_object_id: The ID of the source object
    - to_object_type: The object type to associate to (contacts, companies, deals, tickets)
    - to_object_id: The ID of the target object
    - association_type_id: Optional custom association type ID. If not provided, uses default association type.
    
    Returns:
    - Result message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Creating association from {from_object_type}:{from_object_id} to {to_object_type}:{to_object_id}")
        
        # Use the V4 associations API with create_default method
        # This creates the default (most generic) association type between two object types
        result = client.crm.associations.v4.basic_api.create_default(
            from_object_type=from_object_type,
            from_object_id=from_object_id,
            to_object_type=to_object_type,
            to_object_id=to_object_id
        )
        
        logger.info(f"Association created successfully: {from_object_type}:{from_object_id} -> {to_object_type}:{to_object_id}")
        return {
            "status": "success",
            "message": f"Associated {from_object_type} {from_object_id} with {to_object_type} {to_object_id}",
            "from_object_type": from_object_type,
            "from_object_id": from_object_id,
            "to_object_type": to_object_type,
            "to_object_id": to_object_id,
            "result": str(result) if result else "Association created"
        }
    except Exception as e:
        logger.error(f"Error creating association: {e}")
        raise Exception(f"Failed to create association: {str(e)}")


async def hubspot_delete_association(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    association_type_id: Optional[int] = None
):
    """
    Remove an association between two HubSpot objects.
    
    Parameters:
    - from_object_type: The object type to disassociate from (contacts, companies, deals, tickets)
    - from_object_id: The ID of the source object
    - to_object_type: The object type to disassociate from (contacts, companies, deals, tickets)
    - to_object_id: The ID of the target object
    - association_type_id: Optional custom association type ID (not used, kept for compatibility).
    
    Returns:
    - Result message
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Removing association from {from_object_type}:{from_object_id} to {to_object_type}:{to_object_id}")
        
        # Use the V4 associations API archive method
        # This deletes all associations between two records
        client.crm.associations.v4.basic_api.archive(
            object_type=from_object_type,
            object_id=from_object_id,
            to_object_type=to_object_type,
            to_object_id=to_object_id
        )
        
        logger.info(f"Association removed successfully: {from_object_type}:{from_object_id} -> {to_object_type}:{to_object_id}")
        return {
            "status": "success",
            "message": f"Removed association between {from_object_type} {from_object_id} and {to_object_type} {to_object_id}"
        }
    except Exception as e:
        logger.error(f"Error removing association: {e}")
        raise Exception(f"Failed to remove association: {str(e)}")


async def hubspot_get_associations(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str
):
    """
    Get all associations of a specific type for an object.
    
    Parameters:
    - from_object_type: The source object type (contacts, companies, deals, tickets)
    - from_object_id: The ID of the source object
    - to_object_type: The type of objects to get associations for (contacts, companies, deals, tickets)
    
    Returns:
    - List of associated object IDs
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Fetching associations for {from_object_type}:{from_object_id} to {to_object_type}")
        
        # Use the V4 associations API to get associations
        result = client.crm.associations.v4.basic_api.get_page(
            object_type=from_object_type,
            object_id=from_object_id,
            to_object_type=to_object_type
        )
        
        associations = []
        if hasattr(result, 'results') and result.results:
            for assoc in result.results:
                associations.append({
                    "to_object_id": assoc.to_object_id if hasattr(assoc, 'to_object_id') else assoc.id,
                    "association_types": [
                        {
                            "category": at.category if hasattr(at, 'category') else None,
                            "type_id": at.type_id if hasattr(at, 'type_id') else None,
                            "label": at.label if hasattr(at, 'label') else None
                        }
                        for at in (assoc.association_types if hasattr(assoc, 'association_types') else [])
                    ] if hasattr(assoc, 'association_types') else []
                })
        
        logger.info(f"Found {len(associations)} associations from {from_object_type}:{from_object_id} to {to_object_type}")
        return {
            "from_object_type": from_object_type,
            "from_object_id": from_object_id,
            "to_object_type": to_object_type,
            "associations": associations,
            "total": len(associations)
        }
    except Exception as e:
        logger.error(f"Error fetching associations: {e}")
        raise Exception(f"Failed to fetch associations: {str(e)}")


async def hubspot_batch_create_associations(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_ids: List[str],
    association_type_id: Optional[int] = None
):
    """
    Create multiple associations at once (batch operation).
    
    Parameters:
    - from_object_type: The object type to associate from (contacts, companies, deals, tickets)
    - from_object_id: The ID of the source object
    - to_object_type: The object type to associate to (contacts, companies, deals, tickets)
    - to_object_ids: List of target object IDs to associate with
    - association_type_id: Optional custom association type ID (not used, kept for compatibility).
    
    Returns:
    - Result message with count of associations created
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Creating batch associations from {from_object_type}:{from_object_id} to {len(to_object_ids)} {to_object_type}")
        
        # Create associations one by one using create_default
        success_count = 0
        errors = []
        
        for to_id in to_object_ids:
            try:
                client.crm.associations.v4.basic_api.create_default(
                    from_object_type=from_object_type,
                    from_object_id=from_object_id,
                    to_object_type=to_object_type,
                    to_object_id=to_id
                )
                success_count += 1
            except Exception as e:
                errors.append(f"Failed to associate with {to_id}: {str(e)}")
                logger.warning(f"Failed to create association with {to_id}: {e}")
        
        logger.info(f"Batch association completed: {success_count}/{len(to_object_ids)} successful")
        return {
            "status": "completed",
            "total_requested": len(to_object_ids),
            "successful": success_count,
            "failed": len(errors),
            "errors": errors if errors else None
        }
    except Exception as e:
        logger.error(f"Error in batch create associations: {e}")
        raise Exception(f"Failed to create batch associations: {str(e)}")

