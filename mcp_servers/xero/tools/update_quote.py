import logging
from typing import Dict, Any, Optional, List
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_update_quote(
    quote_id: str,
    contact_id: Optional[str] = None,
    date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    reference: Optional[str] = None,
    branding_theme_id: Optional[str] = None,
    currency_code: Optional[str] = None,
    line_items: Optional[List[Dict[str, Any]]] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    terms: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing draft quote in Xero."""
    try:
        # First, get the existing quote to retrieve required fields
        from .quotes import xero_list_quotes
        quotes_result = await xero_list_quotes(limit=100)
        if not quotes_result.get("success"):
            return {
                "success": False,
                "error": "Failed to retrieve existing quote data for update"
            }
        
        # Find the target quote
        existing_quote = None
        for quote in quotes_result.get("quotes", []):
            if quote.get("quote_id") == quote_id:
                existing_quote = quote
                break
        
        if not existing_quote:
            return {
                "success": False,
                "error": f"Quote with ID {quote_id} not found"
            }
        
        # Build quote data with required fields from existing quote
        quote_data = {
            "QuoteID": quote_id,
            "Type": "ACCREC",  # Required field
            "Contact": {
                "ContactID": existing_quote["contact"]["contact_id"]
            },
            "Date": existing_quote["date"]  # Required field
        }
        
        # Include existing line items (required for updates)
        if existing_quote.get("line_items"):
            line_items_data = []
            for item in existing_quote["line_items"]:
                line_item = {
                    "Description": item.get("description"),
                    "Quantity": item.get("quantity"),
                    "UnitAmount": item.get("unit_amount"),
                    "AccountCode": item.get("account_code", "200")
                }
                line_items_data.append(line_item)
            quote_data["LineItems"] = line_items_data
        
        # Override contact if provided
        if contact_id:
            quote_data["Contact"] = {
                "ContactID": contact_id
            }
        
        if currency_code:
            quote_data["CurrencyCode"] = currency_code
            
        if title:
            quote_data["Title"] = title
            
        if summary:
            quote_data["Summary"] = summary
            
        if terms:
            quote_data["Terms"] = terms
        
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
        
        # Add line items if provided
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
        
        # Prepare request data
        request_data = {
            "Quotes": [quote_data]
        }
        
        # Make API request to update quote - use POST method like other Xero updates
        response = await make_xero_api_request("Quotes", method="POST", data=request_data)
        
        if response.get("Quotes") and len(response["Quotes"]) > 0:
            updated_quote = response["Quotes"][0]
            
            # Extract line items for response
            line_items_response = []
            if updated_quote.get("LineItems"):
                for line in updated_quote["LineItems"]:
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
                "message": "Quote updated successfully",
                "quote": {
                    "quote_id": updated_quote.get("QuoteID"),
                    "quote_number": updated_quote.get("QuoteNumber"),
                    "reference": updated_quote.get("Reference"),
                    "type": updated_quote.get("Type"),
                    "status": updated_quote.get("Status"),
                    "contact": {
                        "contact_id": updated_quote.get("Contact", {}).get("ContactID"),
                        "name": updated_quote.get("Contact", {}).get("Name")
                    },
                    "date": updated_quote.get("Date"),
                    "expiry_date": updated_quote.get("ExpiryDate"),
                    "currency_code": updated_quote.get("CurrencyCode"),
                    "currency_rate": updated_quote.get("CurrencyRate"),
                    "line_items": line_items_response,
                    "sub_total": updated_quote.get("SubTotal"),
                    "total_tax": updated_quote.get("TotalTax"),
                    "total": updated_quote.get("Total"),
                    "updated_date_utc": updated_quote.get("UpdatedDateUTC"),
                    "branding_theme_id": updated_quote.get("BrandingThemeID"),
                    "title": updated_quote.get("Title"),
                    "summary": updated_quote.get("Summary"),
                    "terms": updated_quote.get("Terms")
                }
            }
        else:
            return {
                "success": False,
                "error": "No quote was updated - unexpected API response",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error updating quote: {e}")
        return {
            "success": False,
            "error": f"Failed to update quote: {str(e)}"
        }