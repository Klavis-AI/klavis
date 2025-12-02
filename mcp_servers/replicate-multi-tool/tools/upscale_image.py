import os
from pathlib import Path
from typing import Optional

import replicate
from dotenv import load_dotenv

# Load .env from the server root so this works regardless of CWD
SERVER_ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=SERVER_ROOT_ENV, override=False)


def upscale_image(image_url: str, scale: int = 2) -> Optional[str]:
    """
    Upscale an image using a Replicate super-resolution model.

    Parameters
    - image_url: Publicly accessible URL of the image to upscale
    - scale: Integer upscale factor (typically 2 or 4)

    Returns
    - URL to the upscaled image, or None if the model did not return an output
    """
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_api_token:
        raise ValueError("REPLICATE_API_TOKEN is not set")

    os.environ["REPLICATE_API_TOKEN"] = replicate_api_token

    # Many Replicate SR models accept `image` and `scale` parameters.
    # The following slug targets a general super-resolution model.
    # Adjust the model slug or inputs if you prefer a different SR model.
    output = replicate.run(
        "cjwbw/super-resolution",
        input={
            "image": image_url,
            "scale": int(scale),
        },
    )

    if output:
        # Some models return a single URL; others return a list
        if isinstance(output, str):
            return output
        if isinstance(output, (list, tuple)) and len(output) > 0:
            return str(output[0])
    return None


