import logging
from typing import Dict, Any, Optional, List
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_create_quote(
    contact_id: str,
    date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    reference: Optional[str] = None,
    branding_theme_id: Optional[str] = None,
    currency_code: str = "USD",
    line_items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new quote in Xero."""
    try:
        # Build quote data
        quote_data = {
            "Type": "ACCREC",  # Accounts Receivable
            "Contact": {
                "ContactID": contact_id
            },
            "CurrencyCode": currency_code,
            "Status": "DRAFT"
        }
        
        # Add optional fields with proper date formatting
        if date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                quote_data["Date"] = f"/Date({timestamp})/"
            except:
                quote_data["Date"] = date  # fallback to original format
        if expiry_date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(expiry_date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                quote_data["ExpiryDate"] = f"/Date({timestamp})/"
            except:
                quote_data["ExpiryDate"] = expiry_date  # fallback to original format
        if reference:
            quote_data["Reference"] = reference
        if branding_theme_id:
            quote_data["BrandingThemeID"] = branding_theme_id
        
        # Add line items
        if line_items:
            formatted_line_items = []
            for item in line_items:
                line_item = {}
                
                # Required fields for line item
                if item.get("description"):
                    line_item["Description"] = item["description"]
                if item.get("quantity"):
                    line_item["Quantity"] = float(item["quantity"])
                if item.get("unit_amount"):
                    line_item["UnitAmount"] = float(item["unit_amount"])
                if item.get("account_code"):
                    line_item["AccountCode"] = item["account_code"]
                
                # Optional fields
                if item.get("item_code"):
                    line_item["ItemCode"] = item["item_code"]
                if item.get("tax_type"):
                    line_item["TaxType"] = item["tax_type"]
                if item.get("discount_rate"):
                    line_item["DiscountRate"] = float(item["discount_rate"])
                
                formatted_line_items.append(line_item)
                
            quote_data["LineItems"] = formatted_line_items
        else:
            # Default line item if none provided
            quote_data["LineItems"] = [{
                "Description": "Quote item",
                "Quantity": 1.0,
                "UnitAmount": 100.0,
                "AccountCode": "200"  # Sales account
            }]
        
        # Prepare request data
        request_data = {
            "Quotes": [quote_data]
        }
        
        # Make API request
        response = await make_xero_api_request("Quotes", method="POST", data=request_data)
        
        if response.get("Quotes") and len(response["Quotes"]) > 0:
            created_quote = response["Quotes"][0]
            
            # Extract line items for response
            line_items_response = []
            if created_quote.get("LineItems"):
                for line in created_quote["LineItems"]:
                    line_items_response.append({
                        "description": line.get("Description"),
                        "quantity": line.get("Quantity"),
                        "unit_amount": line.get("UnitAmount"),
                        "line_amount": line.get("LineAmount"),
                        "account_code": line.get("AccountCode"),
                        "tax_type": line.get("TaxType"),
                        "tax_amount": line.get("TaxAmount")
                    })
            
            return {
                "success": True,
                "message": "Quote created successfully",
                "quote": {
                    "quote_id": created_quote.get("QuoteID"),
                    "quote_number": created_quote.get("QuoteNumber"),
                    "reference": created_quote.get("Reference"),
                    "type": created_quote.get("Type"),
                    "status": created_quote.get("Status"),
                    "contact": {
                        "contact_id": created_quote.get("Contact", {}).get("ContactID"),
                        "name": created_quote.get("Contact", {}).get("Name")
                    },
                    "date": created_quote.get("Date"),
                    "expiry_date": created_quote.get("ExpiryDate"),
                    "currency_code": created_quote.get("CurrencyCode"),
                    "currency_rate": created_quote.get("CurrencyRate"),
                    "line_items": line_items_response,
                    "sub_total": created_quote.get("SubTotal"),
                    "total_tax": created_quote.get("TotalTax"),
                    "total": created_quote.get("Total"),
                    "updated_date_utc": created_quote.get("UpdatedDateUTC"),
                    "branding_theme_id": created_quote.get("BrandingThemeID"),
                    "title": created_quote.get("Title"),
                    "summary": created_quote.get("Summary"),
                    "terms": created_quote.get("Terms")
                }
            }
        else:
            return {
                "success": False,
                "error": "No quote was created - unexpected API response",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        return {
            "success": False,
            "error": f"Failed to create quote: {str(e)}"
        }