"""
HubSpot Associations API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
from typing import List, Optional

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    AssociationType,
    AssociationRecord,
    AssociationResult,
    AssociationCreateResult,
    BatchAssociationResult,
    DeleteResult
)
from .errors import (
    KlavisError,
    sanitize_exception
)

logger = logging.getLogger(__name__)


async def hubspot_create_association(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    association_type_id: Optional[int] = None
) -> AssociationCreateResult:
    """
    Create an association between two HubSpot objects.
    
    Parameters:
    - from_object_type: The object type to associate from (contacts, companies, deals, tickets)
    - from_object_id: The ID of the source object
    - to_object_type: The object type to associate to (contacts, companies, deals, tickets)
    - to_object_id: The ID of the target object
    - association_type_id: Optional custom association type ID
    
    Returns:
    - Klavis-normalized AssociationCreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Creating association from {from_object_type}:{from_object_id} to {to_object_type}:{to_object_id}")
        
        safe_api_call(
            client.crm.associations.v4.basic_api.create_default,
            resource_type="association",
            from_object_type=from_object_type,
            from_object_id=from_object_id,
            to_object_type=to_object_type,
            to_object_id=to_object_id
        )
        
        logger.info(f"Association created successfully")
        return AssociationCreateResult(
            status="success",
            message=f"Association created successfully",
            from_object_type=from_object_type,
            from_object_id=from_object_id,
            to_object_type=to_object_type,
            to_object_id=to_object_id
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="association")


async def hubspot_delete_association(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    association_type_id: Optional[int] = None
) -> DeleteResult:
    """
    Remove an association between two HubSpot objects.
    
    Parameters:
    - from_object_type: The object type to disassociate from
    - from_object_id: The ID of the source object
    - to_object_type: The object type to disassociate from
    - to_object_id: The ID of the target object
    - association_type_id: Optional custom association type ID
    
    Returns:
    - Klavis-normalized DeleteResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Removing association from {from_object_type}:{from_object_id} to {to_object_type}:{to_object_id}")
        
        safe_api_call(
            client.crm.associations.v4.basic_api.archive,
            resource_type="association",
            object_type=from_object_type,
            object_id=from_object_id,
            to_object_type=to_object_type,
            to_object_id=to_object_id
        )
        
        logger.info(f"Association removed successfully")
        return DeleteResult(
            status="success",
            message="Association removed successfully",
            resource_id=f"{from_object_id}->{to_object_id}"
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="association")


async def hubspot_get_associations(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str
) -> AssociationResult:
    """
    Get all associations of a specific type for an object.
    
    Parameters:
    - from_object_type: The source object type
    - from_object_id: The ID of the source object
    - to_object_type: The type of objects to get associations for
    
    Returns:
    - Klavis-normalized AssociationResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Fetching associations for {from_object_type}:{from_object_id} to {to_object_type}")
        
        result = safe_api_call(
            client.crm.associations.v4.basic_api.get_page,
            resource_type="association",
            object_type=from_object_type,
            object_id=from_object_id,
            to_object_type=to_object_type
        )
        
        # Normalize associations through Klavis schema
        associations = []
        if hasattr(result, 'results') and result.results:
            for assoc in result.results:
                to_obj_id = getattr(assoc, 'to_object_id', None) or getattr(assoc, 'id', '')
                
                # Normalize association types
                assoc_types = []
                if hasattr(assoc, 'association_types'):
                    for at in assoc.association_types:
                        assoc_types.append(AssociationType(
                            category=getattr(at, 'category', None),
                            type_id=getattr(at, 'type_id', None),
                            label=getattr(at, 'label', None)
                        ))
                
                associations.append(AssociationRecord(
                    to_object_id=str(to_obj_id),
                    association_types=assoc_types
                ))
        
        logger.info(f"Found {len(associations)} associations")
        return AssociationResult(
            from_object_type=from_object_type,
            from_object_id=from_object_id,
            to_object_type=to_object_type,
            associations=associations,
            total=len(associations)
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="association")


async def hubspot_batch_create_associations(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_ids: List[str],
    association_type_id: Optional[int] = None
) -> BatchAssociationResult:
    """
    Create multiple associations at once (batch operation).
    
    Parameters:
    - from_object_type: The object type to associate from
    - from_object_id: The ID of the source object
    - to_object_type: The object type to associate to
    - to_object_ids: List of target object IDs to associate with
    - association_type_id: Optional custom association type ID
    
    Returns:
    - Klavis-normalized BatchAssociationResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Creating batch associations from {from_object_type}:{from_object_id} to {len(to_object_ids)} {to_object_type}")
        
        success_count = 0
        errors = []
        
        for to_id in to_object_ids:
            try:
                safe_api_call(
                    client.crm.associations.v4.basic_api.create_default,
                    resource_type="association",
                    from_object_type=from_object_type,
                    from_object_id=from_object_id,
                    to_object_type=to_object_type,
                    to_object_id=to_id
                )
                success_count += 1
            except KlavisError as e:
                # Record the Klavis error code only, no vendor details
                errors.append(f"Failed for ID {to_id}: {e.code.value}")
            except Exception:
                # Sanitize any unexpected errors
                errors.append(f"Failed for ID {to_id}: OPERATION_FAILED")
        
        logger.info(f"Batch association completed: {success_count}/{len(to_object_ids)} successful")
        return BatchAssociationResult(
            status="completed",
            total_requested=len(to_object_ids),
            successful=success_count,
            failed=len(errors),
            errors=errors if errors else None
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="association")
