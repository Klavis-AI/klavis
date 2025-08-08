import os
import requests
from dotenv import load_dotenv

# Load Amplitude secret key
load_dotenv()
API_SECRET = os.getenv("AMPLITUDE_API_SECRET")
USER_PROFILE_ENDPOINT = "https://profile-api.amplitude.com/v1/userprofile"


def get_user_profile(
    user_id: str,
    get_amp_props: bool = False,
    get_cohort_ids: bool = False,
    get_recs: bool = False,
    get_computations: bool = False
) -> dict:
    """
    Retrieves an Amplitude user profile, including optional flags.

    Inputs:
      user_id: Unique Amplitude user identifier.
      get_amp_props: Include computed and custom user properties.
      get_cohort_ids: Include cohort IDs the user belongs to.
      get_recs: Include recommendation data.
      get_computations: Include computed properties.

    Returns:
      The full JSON response from Amplitude's User Profile API.
    """
    headers = {"Authorization": f"Api-Key {API_SECRET}"}
    params = {"user_id": user_id}
    if get_amp_props:
        params["get_amp_props"] = "true"
    if get_cohort_ids:
        params["get_cohort_ids"] = "true"
    if get_recs:
        params["get_recs"] = "true"
    if get_computations:
        params["get_computations"] = "true"

    resp = requests.get(USER_PROFILE_ENDPOINT, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()