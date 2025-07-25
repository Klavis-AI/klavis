import logging
from typing import Dict, Any, Optional, List
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

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