import httpx
from .base import get_apollo_client

async def apollo_organization_job_postings(
    organization_id: str,
    page: int = 1,
    per_page: int = 50
) -> dict:
    """
    Retrieve current job postings for a specific organization.

    GET https://api.apollo.io/api/v1/organizations/{organization_id}/job_postings

    Path Parameters:
    - organization_id (string, required): The unique Apollo ID of the company.

    Query Parameters:
    - page (int, optional): Page number for paginated results.
    - per_page (int, optional): Number of job postings per page to improve performance.

    Notes:
    - Requires a master API key.
    - Consumes Apollo credits.
    - Max 10,000 records per organization.
    - Use pagination to retrieve all data in batches.
    """

    url = f'https://api.apollo.io/api/v1/organizations/{organization_id}/job_postings'
    params = {
        'page': int(page),
        'per_page': int(per_page)
    }
    headers = get_apollo_client()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def apollo_news_articles_search(
    organization_ids: list,
    categories: list = None,
    published_at_min: str = None,
    published_at_max: str = None,
    page: int = 1,
    per_page: int = 50
) -> dict:
    """
    Search news articles related to companies in the Apollo database.

    POST https://api.apollo.io/api/v1/news_articles/search

    Query Parameters:
    - organization_ids (array of strings, required): Apollo IDs of companies to include in the search.
    - categories (array of strings, optional): Filter by news categories or sub-categories (e.g., hires, investment, contract).
    - published_at_min (date, optional): Start date (YYYY-MM-DD) for the date range filter.
    - published_at_max (date, optional): End date (YYYY-MM-DD) for the date range filter.
    - page (int, optional): Page number for paginated results.
    - per_page (int, optional): Number of results per page to improve performance.

    Notes:
    - Requires a master API key.
    - Consumes Apollo credits.
    - Use pagination for large result sets.
    """

    url = 'https://api.apollo.io/api/v1/news_articles/search'
    params = {
        'organization_ids': organization_ids,
        'categories': categories,
        'published_at[min]': published_at_min,
        'published_at[max]': published_at_max,
        'page': page,
        'per_page': per_page
    }
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

if __name__ == "__main__":
    #print(apollo_organization_job_postings('5e66b6381e05b4008c8331b8', per_page=10))
    pass