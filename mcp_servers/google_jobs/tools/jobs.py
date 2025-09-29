import logging
from typing import Any, Dict, List, Optional
from .base import make_serpapi_request

logger = logging.getLogger(__name__)

async def search_jobs(
    query: str,
    location: Optional[str] = None,
    date_posted: Optional[str] = None,
    employment_type: Optional[str] = None,
    salary_min: Optional[int] = None,
    company: Optional[str] = None,
    radius: Optional[int] = None,
    start: int = 0
) -> Dict[str, Any]:
    """Search for jobs on Google Jobs."""
    logger.info(f"Executing tool: search_jobs with query: {query}")
    try:
        params = {"q": query}
        
        if location:
            params["location"] = location
        if date_posted:
            params["date_posted"] = date_posted
        if employment_type:
            params["employment_type"] = employment_type
        if salary_min:
            params["salary_min"] = salary_min
        if company:
            params["company"] = company
        if radius:
            params["radius"] = radius
        if start > 0:
            params["start"] = start
        
        result = await make_serpapi_request(params)
        
        jobs = result.get("jobs_results", [])
        total_results = result.get("search_information", {}).get("total_results", 0)
        
        if not jobs:
            return {
                "message": f"No job listings found for query: '{query}'",
                "total_results": 0,
                "jobs": []
            }
        
        formatted_jobs = []
        for job in jobs[:10]:  # limiting to first 10 results
            job_info = {
                "title": job.get("title", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("location", "N/A"),
                "description_snippet": job.get("description", "N/A")[:200] + "..." if job.get("description") else "N/A",
                "posted_date": job.get("detected_extensions", {}).get("posted_at", "N/A"),
                "job_id": job.get("job_id", "N/A"),
                "apply_options": [opt.get("link", "") for opt in job.get("apply_options", [])]
            }
            formatted_jobs.append(job_info)
        
        response = {
            "total_results": total_results,
            "showing_results": len(formatted_jobs),
            "search_query": query,
            "location_filter": location,
            "jobs": formatted_jobs
        }
        
        return response
        
    except Exception as e:
        logger.exception(f"Error executing tool search_jobs: {e}")
        return {
            "error": "Job search failed",
            "query": query,
            "exception": str(e)
        }

async def get_job_details(job_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific job listing."""
    logger.info(f"Executing tool: get_job_details with job_id: {job_id}")
    try:
        params = {
            "engine": "google_jobs_listing",
            "q": job_id
        }
        
        result = await make_serpapi_request(params)
        
        # Extract job details
        job_details = result.get("job", {})
        
        if not job_details:
            return {
                "error": f"No job details found for job ID: {job_id}",
                "job_id": job_id
            }
        
        formatted_details = {
            "job_id": job_id,
            "title": job_details.get("title", "N/A"),
            "company": job_details.get("company_name", "N/A"),
            "location": job_details.get("location", "N/A"),
            "employment_type": job_details.get("detected_extensions", {}).get("employment_type", "N/A"),
            "posted_date": job_details.get("detected_extensions", {}).get("posted_at", "N/A"),
            "salary": job_details.get("detected_extensions", {}).get("salary", "N/A"),
            "description": job_details.get("description", "N/A"),
            "qualifications": job_details.get("qualifications", []),
            "responsibilities": job_details.get("responsibilities", []),
            "apply_options": job_details.get("apply_options", [])
        }
        
        return formatted_details
        
    except Exception as e:
        logger.exception(f"Error executing tool get_job_details: {e}")
        return {
            "error": "Failed to get job details",
            "job_id": job_id,
            "exception": str(e)
        }

async def search_jobs_by_company(
    company_name: str,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    start: int = 0
) -> Dict[str, Any]:
    """Search for all job openings at a specific company."""
    logger.info(f"Executing tool: search_jobs_by_company with company: {company_name}")
    try:
        # Use company name as both query and company filter
        query = f"jobs at {company_name}"
        
        params = {"q": query}
        
        if location:
            params["location"] = location
        if employment_type:
            params["employment_type"] = employment_type
        if company_name:
            params["company"] = company_name
        if start > 0:
            params["start"] = start
        
        result = await make_serpapi_request(params)
        
        jobs = result.get("jobs_results", [])
        
        if not jobs:
            return {
                "message": f"No job listings found for company: {company_name}",
                "company": company_name,
                "jobs": []
            }
        
        formatted_jobs = []
        for job in jobs:
            job_info = {
                "title": job.get("title", "N/A"),
                "location": job.get("location", "N/A"),
                "employment_type": job.get("detected_extensions", {}).get("employment_type", "N/A"),
                "posted_date": job.get("detected_extensions", {}).get("posted_at", "N/A"),
                "job_id": job.get("job_id", "N/A"),
                "description_snippet": job.get("description", "N/A")[:150] + "..." if job.get("description") else "N/A"
            }
            formatted_jobs.append(job_info)
        
        response = {
            "company": company_name,
            "total_jobs_found": len(formatted_jobs),
            "location_filter": location,
            "jobs": formatted_jobs
        }
        
        return response
        
    except Exception as e:
        logger.exception(f"Error executing tool search_jobs_by_company: {e}")
        return {
            "error": "Company job search failed",
            "company_name": company_name,
            "exception": str(e)
        }

async def search_remote_jobs(
    query: str,
    employment_type: Optional[str] = None,
    date_posted: Optional[str] = None,
    salary_min: Optional[int] = None,
    start: int = 0
) -> Dict[str, Any]:
    """Search specifically for remote job opportunities."""
    logger.info(f"Executing tool: search_remote_jobs with query: {query}")
    try:
        # Modify query to include remote keywords
        remote_query = f"{query} remote"
        
        params = {"q": remote_query, "location": "Remote"}
        
        if employment_type:
            params["employment_type"] = employment_type
        if date_posted:
            params["date_posted"] = date_posted
        if salary_min:
            params["salary_min"] = salary_min
        if start > 0:
            params["start"] = start
        
        result = await make_serpapi_request(params)
        
        jobs = result.get("jobs_results", [])
        
        if not jobs:
            return {
                "message": f"No remote job listings found for query: '{query}'",
                "search_query": query,
                "jobs": []
            }
        
        remote_jobs = []
        for job in jobs:
            location = job.get("location", "").lower()
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            
            if any(remote_keyword in location or remote_keyword in title or remote_keyword in description
                   for remote_keyword in ["remote", "work from home", "anywhere", "virtual"]):
                job_info = {
                    "title": job.get("title", "N/A"),
                    "company": job.get("company_name", "N/A"),
                    "location": job.get("location", "N/A"),
                    "employment_type": job.get("detected_extensions", {}).get("employment_type", "N/A"),
                    "posted_date": job.get("detected_extensions", {}).get("posted_at", "N/A"),
                    "salary": job.get("detected_extensions", {}).get("salary", "N/A"),
                    "job_id": job.get("job_id", "N/A"),
                    "description_snippet": job.get("description", "N/A")[:200] + "..." if job.get("description") else "N/A"
                }
                remote_jobs.append(job_info)
        
        response = {
            "search_query": query,
            "remote_jobs_found": len(remote_jobs),
            "jobs": remote_jobs
        }
        
        return response
        
    except Exception as e:
        logger.exception(f"Error executing tool search_remote_jobs: {e}")
        return {
            "error": "Remote job search failed",
            "query": query,
            "exception": str(e)
        }

async def get_job_search_suggestions(query: str) -> Dict[str, Any]:
    """Get search suggestions and related job titles based on a query."""
    logger.info(f"Executing tool: get_job_search_suggestions with query: {query}")
    try:
        params = {"q": query}
        
        result = await make_serpapi_request(params)
        
        # Extract job titles and companies for suggestions
        jobs = result.get("jobs_results", [])
        related_searches = result.get("related_searches", [])
        
        suggestions = {
            "original_query": query,
            "related_searches": [search.get("query", "") for search in related_searches],
            "popular_job_titles": list(set([job.get("title", "") for job in jobs[:10] if job.get("title")])),
            "companies_hiring": list(set([job.get("company_name", "") for job in jobs[:10] if job.get("company_name")])),
            "common_locations": list(set([job.get("location", "") for job in jobs[:10] if job.get("location")]))
        }
        
        return suggestions
        
    except Exception as e:
        logger.exception(f"Error executing tool get_job_search_suggestions: {e}")
        return {
            "error": "Failed to get search suggestions",
            "query": query,
            "exception": str(e)
        }
        
