import logging
from typing import Any, Dict
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_company_info(company_id: str) -> Dict[str, Any]:
    """Get information about a company."""
    logger.info(f"Executing tool: get_company_info with company_id: {company_id}")
    try:
        # Try different company endpoint formats
        endpoints_to_try = [
            f"/companies/{company_id}",
            f"/companies/{company_id}:(id,name,description,website-url,industry,company-type,headquarter,founded-on,specialities,logo)",
            f"/companies/{company_id}:(id,localizedName,localizedDescription,localizedWebsite)",
            f"/organizations/{company_id}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                company_data = await make_linkedin_request("GET", endpoint)
                
                # If we get data, format it nicely
                company_info = {
                    "id": company_data.get("id"),
                    "name": company_data.get("localizedName") or company_data.get("name"),
                    "description": company_data.get("localizedDescription") or company_data.get("description"),
                    "website": company_data.get("localizedWebsite") or company_data.get("website-url"),
                    "industry": company_data.get("industries") or company_data.get("industry"),
                    "companyType": company_data.get("companyType") or company_data.get("company-type"),
                    "headquarter": company_data.get("headquarter"),
                    "foundedOn": company_data.get("foundedOn") or company_data.get("founded-on"),
                    "specialities": company_data.get("specialities"),
                    "logo": company_data.get("logoV2", {}).get("original") if company_data.get("logoV2") else company_data.get("logo"),
                    "endpoint_used": endpoint,
                    "raw_data": company_data
                }
                
                return company_info
                
            except Exception as endpoint_error:
                logger.debug(f"Endpoint {endpoint} failed: {endpoint_error}")
                continue
        
        # If all endpoints failed, return informative error
        return {
            "error": "Could not retrieve company information",
            "note": "Company API may require elevated permissions or company ID may be invalid",
            "requested_company_id": company_id,
            "attempted_endpoints": endpoints_to_try,
            "suggestion": "Try using a known company ID like '1035' (Microsoft) or check LinkedIn Developer documentation"
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool get_company_info: {e}")
        return {
            "error": "Function execution failed",
            "requested_company_id": company_id,
            "exception": str(e),
            "note": "Check if company ID is valid and API permissions are sufficient"
        }