import replicate
import os
from dotenv import load_dotenv

load_dotenv()

def generate_image(prompt: str) -> str:
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_api_token:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    
    # Set the API token as environment variable
    os.environ["REPLICATE_API_TOKEN"] = replicate_api_token
    
    input = {"prompt": prompt}

    output = replicate.run(
        # This model I found on replicate has a good balance between speed and quality. You may choose your own.
        "black-forest-labs/flux-schnell", 
        # Each model has its own input parameters. You may customize to your liking. I went with the default settings.
        input={
        "prompt": prompt,
        "go_fast": True,
        "megapixels": "1",
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "output_quality": 80,
        "num_inference_steps": 4
        }
    )
    
    # Return the first URL as a string, or None if no output
    if output and len(output) > 0:
        return str(output[0])
    else:
        return None