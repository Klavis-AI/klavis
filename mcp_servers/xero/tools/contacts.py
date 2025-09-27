import logging
from typing import Dict, Any, List, Optional
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

async def xero_create_contact(
    name: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email_address: Optional[str] = None,
    phone_number: Optional[str] = None,
    is_supplier: bool = False,
    is_customer: bool = True,
    address_line1: Optional[str] = None,
    address_city: Optional[str] = None,
    address_postal_code: Optional[str] = None,
    address_country: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new contact in Xero."""
    try:
        # Build contact data
        contact_data = {
            "Name": name,
            "IsSupplier": is_supplier,
            "IsCustomer": is_customer
        }
        
        # Add optional fields
        if first_name:
            contact_data["FirstName"] = first_name
        if last_name:
            contact_data["LastName"] = last_name
        if email_address:
            contact_data["EmailAddress"] = email_address
        
        # Add phone if provided
        if phone_number:
            contact_data["Phones"] = [{
                "PhoneType": "DEFAULT",
                "PhoneNumber": phone_number
            }]
        
        # Add address if any address fields provided
        if any([address_line1, address_city, address_postal_code, address_country]):
            address = {
                "AddressType": "POBOX"  # Default address type
            }
            if address_line1:
                address["AddressLine1"] = address_line1
            if address_city:
                address["City"] = address_city
            if address_postal_code:
                address["PostalCode"] = address_postal_code
            if address_country:
                address["Country"] = address_country
                
            contact_data["Addresses"] = [address]
        
        # Prepare request data
        request_data = {
            "Contacts": [contact_data]
        }
        
        # Make API request
        response = await make_xero_api_request("Contacts", method="POST", data=request_data)
        
        if response.get("Contacts") and len(response["Contacts"]) > 0:
            created_contact = response["Contacts"][0]
            
            return {
                "success": True,
                "message": "Contact created successfully",
                "contact": {
                    "contact_id": created_contact.get("ContactID"),
                    "name": created_contact.get("Name"),
                    "contact_number": created_contact.get("ContactNumber"),
                    "first_name": created_contact.get("FirstName"),
                    "last_name": created_contact.get("LastName"),
                    "email_address": created_contact.get("EmailAddress"),
                    "contact_status": created_contact.get("ContactStatus"),
                    "is_supplier": created_contact.get("IsSupplier"),
                    "is_customer": created_contact.get("IsCustomer"),
                    "addresses": created_contact.get("Addresses", []),
                    "phones": created_contact.get("Phones", []),
                    "updated_date_utc": created_contact.get("UpdatedDateUTC")
                }
            }
        else:
            return {
                "success": False,
                "error": "No contact was created - unexpected API response",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        return {
            "success": False,
            "error": f"Failed to create contact: {str(e)}"
        }

async def xero_update_contact(
    contact_id: str,
    name: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email_address: Optional[str] = None,
    phone_number: Optional[str] = None,
    is_supplier: Optional[bool] = None,
    is_customer: Optional[bool] = None,
    address_line1: Optional[str] = None,
    address_city: Optional[str] = None,
    address_postal_code: Optional[str] = None,
    address_country: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing contact in Xero."""
    try:
        # Build contact data with only provided fields
        contact_data = {
            "ContactID": contact_id
        }
        
        # Add optional fields only if provided
        if name is not None:
            contact_data["Name"] = name
        if first_name is not None:
            contact_data["FirstName"] = first_name
        if last_name is not None:
            contact_data["LastName"] = last_name
        if email_address is not None:
            contact_data["EmailAddress"] = email_address
        if is_supplier is not None:
            contact_data["IsSupplier"] = is_supplier
        if is_customer is not None:
            contact_data["IsCustomer"] = is_customer
        
        # Add phone if provided
        if phone_number is not None:
            contact_data["Phones"] = [{
                "PhoneType": "DEFAULT",
                "PhoneNumber": phone_number
            }]
        
        # Add address if any address fields provided
        if any([address_line1, address_city, address_postal_code, address_country]):
            address = {
                "AddressType": "POBOX"  # Default address type
            }
            if address_line1 is not None:
                address["AddressLine1"] = address_line1
            if address_city is not None:
                address["City"] = address_city
            if address_postal_code is not None:
                address["PostalCode"] = address_postal_code
            if address_country is not None:
                address["Country"] = address_country
                
            contact_data["Addresses"] = [address]
        
        # Prepare request data
        request_data = {
            "Contacts": [contact_data]
        }
        
        # Make API request using POST (Xero uses POST for updates)
        response = await make_xero_api_request("Contacts", method="POST", data=request_data)
        
        if response.get("Contacts") and len(response["Contacts"]) > 0:
            updated_contact = response["Contacts"][0]
            
            return {
                "success": True,
                "message": "Contact updated successfully",
                "contact": {
                    "contact_id": updated_contact.get("ContactID"),
                    "name": updated_contact.get("Name"),
                    "contact_number": updated_contact.get("ContactNumber"),
                    "first_name": updated_contact.get("FirstName"),
                    "last_name": updated_contact.get("LastName"),
                    "email_address": updated_contact.get("EmailAddress"),
                    "contact_status": updated_contact.get("ContactStatus"),
                    "is_supplier": updated_contact.get("IsSupplier"),
                    "is_customer": updated_contact.get("IsCustomer"),
                    "addresses": updated_contact.get("Addresses", []),
                    "phones": updated_contact.get("Phones", []),
                    "updated_date_utc": updated_contact.get("UpdatedDateUTC")
                }
            }
        else:
            return {
                "success": False,
                "error": "No contact was updated - contact may not exist or no changes were made",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        return {
            "success": False,
            "error": f"Failed to update contact: {str(e)}"
        }