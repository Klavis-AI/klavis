from typing import Any, Dict
from .base import _async_request, _async_paginate_get


async def get_templates() -> dict:
    """
    Retrieve all templates (paginated).
    """
    templates = await _async_paginate_get("/templates")
    return {"templates": templates}


async def render_template(template_id: str, render_data: Dict[str, Any]) -> dict:
    """
    Render a template server-side with given data.

    Args:
        template_id: The ID of the template you want to render.
        render_data: A dictionary containing the dynamic data used to render the template.
                     Example: {"data": {"first_name": "John", "product": "Shoes"}}
    """
    payload = {
        "template_id": template_id,
        "render_options": render_data
    }
    return await _async_request("POST", "/template-render", json=payload)
