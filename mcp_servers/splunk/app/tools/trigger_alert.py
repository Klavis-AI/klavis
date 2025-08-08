from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.utils import get_splunk_service

router = APIRouter()

class TriggerAlertRequest(BaseModel):
    alert_name: str
    params: dict = {}

@router.post(
    "/trigger_alert",
    summary="Trigger a Splunk Alert",
    description="Manually trigger a saved Splunk alert. Inputs: alert_name (string), params (dict, optional). Returns: status of the trigger action."
)
async def trigger_alert(body: TriggerAlertRequest):
    service = get_splunk_service()
    try:
        alert = service.saved_searches[body.alert_name]
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found.")
        dispatch_args = body.params if body.params else {}
        job = alert.dispatch(**dispatch_args)
        return {"status": "triggered", "sid": job.sid}
    except KeyError:
        raise HTTPException(status_code=404, detail="Alert not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Splunk error: {str(e)}")
