from typing import Optional

from pydantic import BaseModel, Field


class BaseLLMConfig(BaseModel):
    """
    Pydantic model for LLM configuration.
    """

    model: Optional[str] = Field(
        default=None, description="The name of the model to use."
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for the LLM provider."
    )
    temperature: float = Field(
        default=0, ge=0, le=2, description="Randomness in generation (0 to 2)."
    )
    max_tokens: int = Field(
        default=4000, gt=0, description="The maximum number of tokens to generate."
    )
