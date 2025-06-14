import logging
from typing import Any, Dict, List, Optional

from .base import post

logger = logging.getLogger(__name__)

async def get_extensive_data(
    call_ids: List[str],
    cursor: Optional[str] = None,
    include_parties: bool = True,
    include_transcript: bool = False,
) -> Dict[str, Any]:
    """Retrieve extensive call data for one or more call IDs.

    Parameters
    ----------
    call_ids : list[str]
        List of Gong call IDs to fetch.
    cursor : str, optional
        Pagination cursor returned by a previous request.
    include_parties : bool, optional
        Whether to include party metadata in the response.
    include_transcript : bool, optional
        Whether to include transcript in the response (may be large).
    """

    if not call_ids:
        raise ValueError("call_ids list cannot be empty")

    logger.info("Executing get_extensive_data for %s calls", len(call_ids))

    exposed_fields: Dict[str, Any] = {
        "content": {},
    }
    if include_parties:
        exposed_fields["parties"] = True
    if include_transcript:
        exposed_fields["content"]["transcript"] = True

    payload: Dict[str, Any] = {
        "callIds": call_ids,
        "contentSelector": {
            "context": "Extended",
            "exposedFields": exposed_fields,
        },
    }
    if cursor:
        payload["cursor"] = cursor

    return await post("/v2/calls/extensive", payload) 