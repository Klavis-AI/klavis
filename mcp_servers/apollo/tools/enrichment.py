import httpx
from .base import get_apollo_client


async def apollo_organisation_enrichment(domain: str) -> dict:
    """
    Enrich data for a single organization by domain.

    GET https://api.apollo.io/api/v1/organizations/enrich

    Query Parameters:
    - domain (string, required): The domain of the company to enrich (exclude www., @, etc.).
      Example: apollo.io or microsoft.com

    Returns:
    - Industry info, revenue, employee counts, funding rounds, phone numbers, locations, and other enriched company data.
    """

    url = "https://api.apollo.io/api/v1/organizations/enrich"
    parts = domain.split(".")
    if parts[0] == "www":
        domain = ".".join(parts[1:])
    params = {"domain": domain}
    headers = get_apollo_client()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_bulk_organisation_enrichment(domains: list) -> dict:
    """
    Enrich data for up to 10 organizations in one call.

    POST https://api.apollo.io/api/v1/organizations/bulk_enrich

    Query Parameters:
    - domains[] (array of strings, required): List of company domains to enrich (exclude www., @, etc.).
      Example: ["apollo.io", "microsoft.com"]

    Returns:
    - Enriched data for each company including industry, revenue, employee count, funding rounds, phone numbers, and locations.

    Notes:
    - Rate limit is 50% of the single organization enrichment per-minute limit.
    - Hourly and daily limits are the same as the single enrichment endpoint.
    """

    url = "https://api.apollo.io/api/v1/organizations/bulk_enrich"

    # remove 'www'------------------
    new_domains = []
    for d in domains:
        parts = d.split(".")
        if parts[0] == "www":
            new_domains.append(".".join(parts[1:]))
        else:
            new_domains.append(d)
    #-------------------------------

    headers = get_apollo_client()
    params = {"domains": new_domains}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


if __name__ == '__main__':
    #print(apollo_organisation_enrichment("www.apollo.io"))
    #lists = ["www.apollo.io", "wikihow.com"]
    #print(apollo_bulk_organisation_enrichment(lists))
    pass