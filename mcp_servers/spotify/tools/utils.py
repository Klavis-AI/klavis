from pydantic import BaseModel

class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None

def tool_desc(desc, use, side=None):
    return RichToolDescription(description=desc, use_when=use, side_effects=side).model_dump_json()