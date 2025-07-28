import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_quotes(
    limit: int = 10,
    status: Optional[str] = None,
    contact_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve a list of quotes from Xero."""
    try:
        # Validate status if provided
        if status:
            valid_statuses = ["DRAFT", "SENT", "ACCEPTED", "DECLINED", "INVOICED", "DELETED"]
            if status.upper() not in valid_statuses:
                return {
                    "success": False,
                    "error": f"Invalid status '{status}'. Valid statuses are: {', '.join(valid_statuses)}"
                }
        
        # Validate date formats if provided
        if date_from:
            try:
                from datetime import datetime
                datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid date_from format '{date_from}'. Use YYYY-MM-DD format."
                }
        
        if date_to:
            try:
                from datetime import datetime
                datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid date_to format '{date_to}'. Use YYYY-MM-DD format."
                }
        
        # Make API request (Xero Quotes API doesn't support server-side filtering reliably)
        endpoint = "Quotes"
        logger.info(f"Making API request to endpoint: {endpoint}")
        response = await make_xero_api_request(endpoint)
        
        # Get all quotes first
        all_quotes = response.get("Quotes", [])
        logger.info(f"API returned {len(all_quotes)} quotes")
        
        # Apply client-side filtering
        filtered_quotes = all_quotes.copy()
        
        # Filter by status
        if status:
            filtered_quotes = [q for q in filtered_quotes if q.get("Status", "").upper() == status.upper()]
            logger.info(f"After status filter ({status}): {len(filtered_quotes)} quotes")
        
        # Filter by contact ID
        if contact_id:
            filtered_quotes = [q for q in filtered_quotes if q.get("Contact", {}).get("ContactID") == contact_id]
            logger.info(f"After contact filter: {len(filtered_quotes)} quotes")
        
        # Filter by date range
        if date_from or date_to:
            from datetime import datetime
            if date_from:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
            if date_to:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
            
            date_filtered = []
            for quote in filtered_quotes:
                quote_date_str = quote.get("Date", "")
                if quote_date_str:
                    try:
                        # Parse Xero date format /Date(timestamp)/
                        if quote_date_str.startswith("/Date(") and quote_date_str.endswith(")/"):
                            timestamp = int(quote_date_str[6:-2])
                            quote_date = datetime.fromtimestamp(timestamp / 1000)
                            
                            # Check date range
                            if date_from and quote_date < from_date:
                                continue
                            if date_to and quote_date > to_date:
                                continue
                            date_filtered.append(quote)
                    except (ValueError, TypeError):
                        # If date parsing fails, include the quote
                        date_filtered.append(quote)
                else:
                    # If no date, include the quote
                    date_filtered.append(quote)
            
            filtered_quotes = date_filtered
            logger.info(f"After date filter: {len(filtered_quotes)} quotes")
        
        # Apply limit
        quotes = filtered_quotes
        
        # Limit results
        if limit and limit > 0:
            quotes = quotes[:limit]
        
        # Format response
        formatted_quotes = []
        for quote in quotes:
            # Extract line items
            line_items = []
            if quote.get("LineItems"):
                for line in quote["LineItems"]:
                    line_items.append({
                        "description": line.get("Description"),
                        "quantity": line.get("Quantity"),
                        "unit_amount": line.get("UnitAmount"),
                        "line_amount": line.get("LineAmount"),
                        "account_code": line.get("AccountCode"),
                        "tax_type": line.get("TaxType"),
                        "tax_amount": line.get("TaxAmount"),
                        "item_code": line.get("ItemCode")
                    })
            
            formatted_quotes.append({
                "quote_id": quote.get("QuoteID"),
                "quote_number": quote.get("QuoteNumber"),
                "reference": quote.get("Reference"),
                "type": quote.get("Type"),
                "status": quote.get("Status"),
                "contact": {
                    "contact_id": quote.get("Contact", {}).get("ContactID"),
                    "name": quote.get("Contact", {}).get("Name")
                },
                "date": quote.get("Date"),
                "expiry_date": quote.get("ExpiryDate"),
                "currency_code": quote.get("CurrencyCode"),
                "currency_rate": quote.get("CurrencyRate"),
                "line_items": line_items,
                "sub_total": quote.get("SubTotal"),
                "total_tax": quote.get("TotalTax"),
                "total": quote.get("Total"),
                "updated_date_utc": quote.get("UpdatedDateUTC"),
                "branding_theme_id": quote.get("BrandingThemeID"),
                "title": quote.get("Title"),
                "summary": quote.get("Summary"),
                "terms": quote.get("Terms")
            })
        
        return {
            "success": True,
            "message": f"Retrieved {len(formatted_quotes)} quotes",
            "quotes": formatted_quotes,
            "total_count": len(quotes)
        }
        
    except Exception as e:
        logger.error(f"Error listing quotes: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve quotes: {str(e)}"
        }

async def xero_create_quote(
    contact_id: str,
    date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    reference: Optional[str] = None,
    currency_code: str = "USD",
    line_items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new quote in Xero."""
    try:
        # Build quote data - start minimal like the working example
        quote_data = {
            "Contact": {
                "ContactID": contact_id
            }
        }
        
        # Add optional fields with proper date formatting
        if date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                quote_data["Date"] = f"/Date({timestamp})/"
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid date format '{date}'. Use YYYY-MM-DD format."
                }
        else:
            # Use current date if none provided
            from datetime import datetime
            current_timestamp = int(datetime.now().timestamp() * 1000)
            quote_data["Date"] = f"/Date({current_timestamp})/"
            
        if expiry_date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(expiry_date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                quote_data["ExpiryDate"] = f"/Date({timestamp})/"
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid expiry_date format '{expiry_date}'. Use YYYY-MM-DD format."
                }
                
        if reference:
            quote_data["Reference"] = reference
        
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

