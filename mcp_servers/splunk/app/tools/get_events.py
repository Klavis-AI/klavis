import asyncio
from fastapi import APIRouter, HTTPException, Query
import json
from app.tools.utils import get_splunk_service

router = APIRouter()

@router.get(
    "/get_events",
    summary="Get Splunk Events",
    description="Fetch recent events from a specified Splunk index. Inputs: index (string), limit (integer). Returns: list of events."
)
async def get_events(
    index: str = Query(..., description="Splunk index to query"),
    limit: int = Query(10, description="Number of events to return")
):
    service = get_splunk_service()
    try:
        search_query = f"search index={index} | head {limit}"
        job = service.jobs.create(search_query, earliest_time="0", latest_time="now")
        while not job.is_done():
            await asyncio.sleep(1)
        search_results = job.results(output_mode='json_rows')
        results_json = json.load(search_results)
        fields = results_json.get("fields", [])
        rows = results_json.get("rows", [])
        events = [dict(zip(fields, row)) for row in rows]
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Splunk error: {str(e)}")
