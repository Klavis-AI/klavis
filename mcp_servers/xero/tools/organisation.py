import logging
from typing import Dict, Any
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_organisation_details() -> Dict[str, Any]:
    """
    Retrieve details about the Xero organisation.
    
    Returns:
        Dict containing organisation details
    """
    try:
        # Get organisation details from API
        response = await make_xero_api_request("Organisation")
        
        if response.get("Organisations"):
            org = response["Organisations"][0]
            return {
                "organisation_id": org.get("OrganisationID"),
                "name": org.get("Name"),
                "legal_name": org.get("LegalName"),
                "pays_tax": org.get("PaysTax"),
                "version": org.get("Version"),
                "organisation_type": org.get("OrganisationType"),
                "base_currency": org.get("BaseCurrency"),
                "country_code": org.get("CountryCode"),
                "is_demo_company": org.get("IsDemoCompany"),
                "organisation_status": org.get("OrganisationStatus"),
                "registration_number": org.get("RegistrationNumber"),
                "employer_identification_number": org.get("EmployerIdentificationNumber"),
                "tax_number": org.get("TaxNumber"),
                "financial_year_end_day": org.get("FinancialYearEndDay"),
                "financial_year_end_month": org.get("FinancialYearEndMonth"),
                "sales_tax_basis": org.get("SalesTaxBasis"),
                "sales_tax_period": org.get("SalesTaxPeriod"),
                "default_sales_tax": org.get("DefaultSalesTax"),
                "default_purchases_tax": org.get("DefaultPurchasesTax"),
                "period_lock_date": org.get("PeriodLockDate"),
                "end_of_year_lock_date": org.get("EndOfYearLockDate"),
                "created_date_utc": org.get("CreatedDateUTC"),
                "timezone": org.get("Timezone"),
                "organisation_entity_type": org.get("OrganisationEntityType"),
                "short_code": org.get("ShortCode"),
                "class_type": org.get("Class"),
                "edition": org.get("Edition"),
                "line_of_business": org.get("LineOfBusiness"),
            }
        else:
            return {"error": "No organisation found"}
            
    except Exception as e:
        logger.error(f"Error retrieving organisation details: {e}")
        return {"error": f"Failed to retrieve organisation details: {str(e)}"}