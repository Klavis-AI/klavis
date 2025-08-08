import asyncio
import time
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.utils import get_splunk_service

router = APIRouter()

class SearchLogsRequest(BaseModel):
    query: str
    earliest_time: str = "-24h"
    latest_time: str = "now"

@router.post("/search_logs", summary="Search Splunk logs")
async def search_logs(body: SearchLogsRequest):
    service = get_splunk_service()
    try:
        job = service.jobs.create(
            body.query,
            earliest_time=body.earliest_time,
            latest_time=body.latest_time
        )
        timeout = 60
        start = time.time()
        while not job.is_done():
            await asyncio.sleep(1)
            if time.time() - start > timeout:
                raise HTTPException(status_code=504, detail="Splunk search timed out")
        search_results = job.results(output_mode='json_rows')
        results_json = json.load(search_results)
        fields = results_json.get("fields", [])
        rows = results_json.get("rows", [])
        results = [dict(zip(fields, row)) for row in rows]
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Splunk error: {str(e)}")
