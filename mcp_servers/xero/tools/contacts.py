import logging
from typing import Dict, Any, List
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_contacts(limit: int = 10) -> Dict[str, Any]:
    """Retrieve a list of contacts from Xero."""
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            limit = min(max(limit, 1), 100)
        
        # Get contacts from API
        response = await make_xero_api_request("Contacts")
        
        contacts_list = []
        if response.get("Contacts"):
            # Limit results to requested amount
            limited_contacts = response["Contacts"][:limit]
            
            for contact in limited_contacts:
                contact_data = {
                    "contact_id": contact.get("ContactID"),
                    "contact_number": contact.get("ContactNumber"),
                    "account_number": contact.get("AccountNumber"),
                    "contact_status": contact.get("ContactStatus"),
                    "name": contact.get("Name"),
                    "first_name": contact.get("FirstName"),
                    "last_name": contact.get("LastName"),
                    "email_address": contact.get("EmailAddress"),
                    "skype_user_name": contact.get("SkypeUserName"),
                    "contact_persons": contact.get("ContactPersons", []),
                    "bank_account_details": contact.get("BankAccountDetails"),
                    "tax_number": contact.get("TaxNumber"),
                    "accounts_receivable_tax_type": contact.get("AccountsReceivableTaxType"),
                    "accounts_payable_tax_type": contact.get("AccountsPayableTaxType"),
                    "addresses": contact.get("Addresses", []),
                    "phones": contact.get("Phones", []),
                    "is_supplier": contact.get("IsSupplier"),
                    "is_customer": contact.get("IsCustomer"),
                    "default_currency": contact.get("DefaultCurrency"),
                    "website": contact.get("Website"),
                    "discount": contact.get("Discount"),
                    "purchase_tracking": contact.get("PurchaseTracking", []),
                    "sales_tracking": contact.get("SalesTracking", []),
                    "payment_terms": contact.get("PaymentTerms"),
                    "updated_date_utc": contact.get("UpdatedDateUTC"),
                    "contact_groups": contact.get("ContactGroups", [])
                }
                
                contacts_list.append(contact_data)
        
        return {
            "contacts": contacts_list,
            "total_returned": len(contacts_list),
            "limit_requested": limit,
            "has_more": len(response.get("Contacts", [])) > limit
        }
            
    except Exception as e:
        logger.error(f"Error retrieving contacts: {e}")
        return {"error": f"Failed to retrieve contacts: {str(e)}"}