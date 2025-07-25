import logging
from typing import Dict, Any, Optional
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

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