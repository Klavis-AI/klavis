from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import success, failure
from .base import get_auth_token

logger = logging.getLogger(__name__)

MEET_API_DISABLED_ENV = os.getenv("MEET_API_DISABLED_ENV", "MEET_API_V2_DISABLED")
MEET_API_BASE = os.getenv("MEET_API_BASE", "https://meet.googleapis.com/v2")


def _meet_service(access_token: str):
    creds = Credentials(token=access_token)
    return build("meet", "v2", credentials=creds, cache_discovery=False)


def _http_get_json(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    token = get_auth_token()
    if not token:
        raise RuntimeError("Missing access token")
    url = f"{MEET_API_BASE}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=15) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data) if data else {}


@lru_cache(maxsize=1)
def _capability_probe() -> Dict[str, Any]:
    if os.getenv(MEET_API_DISABLED_ENV, "").lower() in {"1", "true", "yes"}:
        return {"enabled": False, "code": "disabled_env", "error": "Meet API v2 disabled by env"}
    token = get_auth_token()
    if not token:
        return {"enabled": False, "code": "unauthorized", "error": "Missing access token"}
    try:
        svc = _meet_service(token)
        spaces_res = svc.spaces()
        has_list = hasattr(spaces_res, "list")
        has_create = hasattr(spaces_res, "create")
        if has_list:
            try:
                resp = spaces_res.list(pageSize=1).execute()
                logger.debug("meet_v2 probe success keys=%s", list(resp.keys()))
                return {"enabled": True, "mode": "list_probe"}
            except AttributeError:
                has_list = False
        if not has_list and has_create:
            logger.debug("meet_v2 probe falling back to create capability assumption")
            return {"enabled": True, "mode": "assumed_via_create"}
        if not (has_list or has_create):
            return {"enabled": False, "code": "unsupported_client", "error": "Meet API v2 methods not present in discovery"}
        return {"enabled": True, "mode": "unknown_fallback"}
    except HttpError as e: 
        status = getattr(e.resp, "status", 0)
        try:
            detail = json.loads(e.content.decode("utf-8"))
        except Exception:
            detail = {}
        logger.info("meet_v2 probe http_error status=%s detail=%s", status, detail)
        code = "meet_api_unavailable"
        if status == 403:
            code = "forbidden_or_consumer"
        elif status == 404:
            code = "not_enabled"
        return {"enabled": False, "code": code, "error": "Meet API v2 not available"}
    except Exception as e:
        logger.warning("meet_v2 probe unexpected=%s", e)
        return {"enabled": False, "code": "probe_error", "error": str(e)}


def _ensure_enabled() -> Optional[Dict[str, Any]]:
    probe = _capability_probe()
    if not probe.get("enabled"):
        return failure(
            probe.get("error", "Meet API v2 unavailable"),
            code=probe.get("code", "meet_api_unavailable"),
            details={k: v for k, v in probe.items() if k != "enabled" and v is not None},
        )
    return None


def _shape_space(space: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "space_id": space.get("name") or space.get("id"),
        "display_name": space.get("displayName") or space.get("topic"),
        "meeting_url": space.get("meetingUri") or space.get("meetingUrl"),
        "create_time": space.get("createTime"),
        "end_time": space.get("endTime"),
        "state": space.get("state"),
        "raw": space,  
    }


async def create_instant_meeting() -> Dict[str, Any]:
    logger.info("tool=google_meet_v2_create_instant action=start")
    fail = _ensure_enabled()
    if fail:
        return fail
    token = get_auth_token()
    try:
        svc = _meet_service(token)
        space = svc.spaces().create(body={}).execute()
        shaped = _shape_space(space)
        logger.info("tool=google_meet_v2_create_instant action=success space_id=%s", shaped.get("space_id"))
        return success(shaped)
    except HttpError as e:
        status = getattr(e.resp, "status", 0)
        try:
            detail = json.loads(e.content.decode("utf-8"))
        except Exception:
            detail = {}
        logger.error("tool=google_meet_v2_create_instant http_error status=%s", status)
        return failure("Meet API error", code=str(status or "http_error"), details=detail)
    except Exception as e:
        logger.exception("tool=google_meet_v2_create_instant unexpected_error=%s", e)
        return failure("Unexpected server error", code="internal_error")


async def get_meeting(space_id: str) -> Dict[str, Any]:
    logger.info("tool=google_meet_v2_get_meeting action=start space_id=%s", space_id)
    if not space_id:
        return failure("space_id is required")
    fail = _ensure_enabled()
    if fail:
        return fail
    token = get_auth_token()
    try:
        svc = _meet_service(token)
        space = svc.spaces().get(name=space_id if space_id.startswith("spaces/") else f"spaces/{space_id}").execute()
        return success(_shape_space(space))
    except HttpError as e:
        status = getattr(e.resp, "status", 0)
        try:
            detail = json.loads(e.content.decode("utf-8"))
        except Exception:
            detail = {}
        return failure("Failed to fetch meeting", code=str(status or "http_error"), details=detail)
    except Exception as e:
        logger.exception("tool=google_meet_v2_get_meeting unexpected_error=%s", e)
        return failure("Unexpected server error", code="internal_error")


# NOTE:
# Leaving implementation for future enablement when API/scopes are broadly available.
async def list_meetings(max_results: int = 10) -> Dict[str, Any]:
    logger.info("tool=google_meet_v2_list_meetings action=start max_results=%s", max_results)
    if max_results <= 0 or max_results > 100:
        return failure("max_results must be between 1 and 100")
    fail = _ensure_enabled()
    if fail:
        return fail
    token = get_auth_token()
    try:
        svc = _meet_service(token)
        spaces_res = svc.spaces()
        use_http_fallback = not hasattr(spaces_res, "list")
        page_token = None
        spaces: List[Dict[str, Any]] = []
        while len(spaces) < max_results:
            page_size = min(50, max_results - len(spaces))
            if not use_http_fallback:
                resp = spaces_res.list(pageSize=page_size, pageToken=page_token).execute() if page_token else spaces_res.list(pageSize=page_size).execute()
            else:
                # Fallback to raw HTTP if discovery lacks list
                params = {"pageSize": page_size}
                if page_token:
                    params["pageToken"] = page_token
                try:
                    resp = _http_get_json("/spaces", params)
                except HTTPError as e:
                    try:
                        detail = json.loads(e.read().decode("utf-8"))
                    except Exception:
                        detail = {"body": e.read().decode("utf-8", "ignore") if hasattr(e, 'read') else None}
                    return failure("Failed to list meetings", code=str(e.code or "http_error"), details=detail)
            batch = resp.get("spaces", []) or resp.get("items", [])
            for sp in batch:
                if len(spaces) >= max_results:
                    break
                spaces.append(sp)
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        shaped = [_shape_space(sp) for sp in spaces]
        return success({"meetings": shaped, "total_count": len(shaped)})
    except HttpError as e:
        status = getattr(e.resp, "status", 0)
        try:
            detail = json.loads(e.content.decode("utf-8"))
        except Exception:
            detail = {}
        return failure("Failed to list meetings", code=str(status or "http_error"), details=detail)
    except Exception as e:
        logger.exception("tool=google_meet_v2_list_meetings unexpected_error=%s", e)
        return failure("Unexpected server error", code="internal_error")


# NOTE:
# Leaving implementation for future enablement when API/scopes are broadly available.
async def get_participants(space_id: str, max_results: int = 50) -> Dict[str, Any]:
    logger.info("tool=google_meet_v2_get_participants action=start space_id=%s", space_id)
    if not space_id:
        return failure("space_id is required")
    if max_results <= 0 or max_results > 300:
        return failure("max_results must be between 1 and 300")
    fail = _ensure_enabled()
    if fail:
        return fail
    token = get_auth_token()
    try:
        svc = _meet_service(token)
        parent = space_id if space_id.startswith("spaces/") else f"spaces/{space_id}"
        spaces_res = svc.spaces()
        has_nested_participants = hasattr(spaces_res, "participants")
        participants: List[Dict[str, Any]] = []
        page_token = None
        while len(participants) < max_results:
            page_size = min(50, max_results - len(participants))
            if has_nested_participants:
                kwargs = {"parent": parent, "pageSize": page_size}
                if page_token:
                    kwargs["pageToken"] = page_token
                resp = spaces_res.participants().list(**kwargs).execute()
            else:
                # Fallback to raw HTTP: GET /v2/{parent}/participants
                params = {"pageSize": page_size}
                if page_token:
                    params["pageToken"] = page_token
                try:
                    resp = _http_get_json(f"/{parent}/participants", params)
                except HTTPError as e:
                    try:
                        detail = json.loads(e.read().decode("utf-8"))
                    except Exception:
                        detail = {"body": e.read().decode("utf-8", "ignore") if hasattr(e, 'read') else None}
                    return failure("Failed to get participants", code=str(e.code or "http_error"), details=detail)
            batch = resp.get("participants", []) or resp.get("items", [])
            for p in batch:
                if len(participants) >= max_results:
                    break
                participants.append(p)
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        shaped = [
            {
                "user": (p.get("user") or {}).get("name") or p.get("name"),
                "role": p.get("role"),
                "state": p.get("state"),
                "raw": p,
            }
            for p in participants
        ]
        return success({"participants": shaped, "total_count": len(shaped)})
    except HttpError as e:
        status = getattr(e.resp, "status", 0)
        try:
            detail = json.loads(e.content.decode("utf-8"))
        except Exception:
            detail = {}
        return failure("Failed to get participants", code=str(status or "http_error"), details=detail)
    except Exception as e:      
        logger.exception("tool=google_meet_v2_get_participants unexpected_error=%s", e)
        return failure("Unexpected server error", code="internal_error")


__all__ = [
    "create_instant_meeting",
    "get_meeting",
    "list_meetings",
    "get_participants",
]
