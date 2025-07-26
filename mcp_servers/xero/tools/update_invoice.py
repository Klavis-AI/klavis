import logging
from typing import Dict, Any, Optional, List
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_update_invoice(
    invoice_id: str,
    contact_id: Optional[str] = None,
    type: Optional[str] = None,
    date: Optional[str] = None,
    due_date: Optional[str] = None,
    reference: Optional[str] = None,
    currency_code: Optional[str] = None,
    line_items: Optional[List[Dict[str, Any]]] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing draft invoice in Xero."""
    try:
        # Validate invoice type if provided
        if type is not None:
            valid_types = ["ACCREC", "ACCPAY"]
            if type.upper() not in valid_types:
                return {
                    "success": False,
                    "error": f"Invalid invoice type '{type}'. Valid types are: {', '.join(valid_types)}"
                }
        
        # Validate status if provided
        if status is not None:
            valid_statuses = ["DRAFT", "SUBMITTED", "AUTHORISED"]
            if status.upper() not in valid_statuses:
                return {
                    "success": False,
                    "error": f"Invalid status '{status}'. Valid statuses are: {', '.join(valid_statuses)}"
                }
        
        # Build invoice data with only fields that are provided
        invoice_data = {
            "InvoiceID": invoice_id
        }
        
        # Add optional fields only if provided
        if contact_id:
            invoice_data["Contact"] = {
                "ContactID": contact_id
            }
        
        if type is not None:
            invoice_data["Type"] = type.upper()
            
        if currency_code:
            invoice_data["CurrencyCode"] = currency_code
            
        if status is not None:
            invoice_data["Status"] = status.upper()
        
        # Add optional fields with proper date formatting
        if date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                invoice_data["Date"] = f"/Date({timestamp})/"
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid date format '{date}'. Use YYYY-MM-DD format."
                }
        
        if due_date:
            # Convert YYYY-MM-DD to /Date(timestamp)/ format expected by Xero
            from datetime import datetime
            try:
                dt = datetime.strptime(due_date, "%Y-%m-%d")
                timestamp = int(dt.timestamp() * 1000)
                invoice_data["DueDate"] = f"/Date({timestamp})/"
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid due_date format '{due_date}'. Use YYYY-MM-DD format."
                }
        
        if reference:
            invoice_data["Reference"] = reference
        
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
                
            invoice_data["LineItems"] = formatted_line_items
        
        # Prepare request data
        request_data = {
            "Invoices": [invoice_data]
        }
        
        # Make API request using POST (Xero uses POST for updates)
        response = await make_xero_api_request("Invoices", method="POST", data=request_data)
        
        if response.get("Invoices") and len(response["Invoices"]) > 0:
            updated_invoice = response["Invoices"][0]
            
            # Extract line items for response
            line_items_response = []
            if updated_invoice.get("LineItems"):
                for line in updated_invoice["LineItems"]:
                    line_items_response.append({
                        "description": line.get("Description"),
                        "quantity": line.get("Quantity"),
                        "unit_amount": line.get("UnitAmount"),
                        "line_amount": line.get("LineAmount"),
                        "account_code": line.get("AccountCode"),
                        "tax_type": line.get("TaxType"),
                        "tax_amount": line.get("TaxAmount"),
                        "item_code": line.get("ItemCode")
                    })
            
            return {
                "success": True,
                "message": "Invoice updated successfully",
                "invoice": {
                    "invoice_id": updated_invoice.get("InvoiceID"),
                    "invoice_number": updated_invoice.get("InvoiceNumber"),
                    "reference": updated_invoice.get("Reference"),
                    "type": updated_invoice.get("Type"),
                    "status": updated_invoice.get("Status"),
                    "contact": {
                        "contact_id": updated_invoice.get("Contact", {}).get("ContactID"),
                        "name": updated_invoice.get("Contact", {}).get("Name")
                    },
                    "date": updated_invoice.get("Date"),
                    "due_date": updated_invoice.get("DueDate"),
                    "currency_code": updated_invoice.get("CurrencyCode"),
                    "currency_rate": updated_invoice.get("CurrencyRate"),
                    "line_items": line_items_response,
                    "sub_total": updated_invoice.get("SubTotal"),
                    "total_tax": updated_invoice.get("TotalTax"),
                    "total": updated_invoice.get("Total"),
                    "amount_due": updated_invoice.get("AmountDue"),
                    "amount_paid": updated_invoice.get("AmountPaid"),
                    "updated_date_utc": updated_invoice.get("UpdatedDateUTC"),
                    "branding_theme_id": updated_invoice.get("BrandingThemeID")
                }
            }
        else:
            return {
                "success": False,
                "error": "No invoice was updated - invoice may not exist or no changes were made",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error updating invoice: {e}")
        return {
            "success": False,
            "error": f"Failed to update invoice: {str(e)}"
        }