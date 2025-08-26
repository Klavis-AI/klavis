import logging
from typing import Dict, Any, List, Optional
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_invoices(limit: int = 10, status: str = None) -> Dict[str, Any]:
    """Retrieve a list of invoices from Xero."""
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            limit = min(max(limit, 1), 100)
        
        # Build endpoint with optional status filter
        endpoint = "Invoices"
        if status:
            valid_statuses = ["DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED"]
            if status.upper() in valid_statuses:
                endpoint += f"?where=Status%3D%22{status.upper()}%22"
        
        # Get invoices from API
        response = await make_xero_api_request(endpoint)
        
        invoices_list = []
        if response.get("Invoices"):
            # Limit results to requested amount
            limited_invoices = response["Invoices"][:limit]
            
            for invoice in limited_invoices:
                # Extract line items
                line_items = []
                if invoice.get("LineItems"):
                    for line in invoice["LineItems"]:
                        line_items.append({
                            "line_item_id": line.get("LineItemID"),
                            "description": line.get("Description"),
                            "quantity": line.get("Quantity"),
                            "unit_amount": line.get("UnitAmount"),
                            "line_amount": line.get("LineAmount"),
                            "account_code": line.get("AccountCode"),
                            "tax_type": line.get("TaxType"),
                            "tax_amount": line.get("TaxAmount"),
                            "discount_rate": line.get("DiscountRate"),
                            "discount_amount": line.get("DiscountAmount")
                        })
                
                invoice_data = {
                    "invoice_id": invoice.get("InvoiceID"),
                    "invoice_number": invoice.get("InvoiceNumber"),
                    "reference": invoice.get("Reference"),
                    "type": invoice.get("Type"),
                    "status": invoice.get("Status"),
                    "contact": {
                        "contact_id": invoice.get("Contact", {}).get("ContactID"),
                        "name": invoice.get("Contact", {}).get("Name")
                    },
                    "date": invoice.get("Date"),
                    "due_date": invoice.get("DueDate"),
                    "expected_payment_date": invoice.get("ExpectedPaymentDate"),
                    "planned_payment_date": invoice.get("PlannedPaymentDate"),
                    "line_amount_types": invoice.get("LineAmountTypes"),
                    "line_items": line_items,
                    "sub_total": invoice.get("SubTotal"),
                    "total_tax": invoice.get("TotalTax"),
                    "total": invoice.get("Total"),
                    "total_discount": invoice.get("TotalDiscount"),
                    "currency_code": invoice.get("CurrencyCode"),
                    "currency_rate": invoice.get("CurrencyRate"),
                    "updated_date_utc": invoice.get("UpdatedDateUTC"),
                    "fully_paid_on_date": invoice.get("FullyPaidOnDate"),
                    "amount_due": invoice.get("AmountDue"),
                    "amount_paid": invoice.get("AmountPaid"),
                    "amount_credited": invoice.get("AmountCredited"),
                    "branding_theme_id": invoice.get("BrandingThemeID"),
                    "has_attachments": invoice.get("HasAttachments"),
                    "repeating_invoice_id": invoice.get("RepeatingInvoiceID"),
                    "url": invoice.get("Url")
                }
                
                invoices_list.append(invoice_data)
        
        return {
            "invoices": invoices_list,
            "total_returned": len(invoices_list),
            "limit_requested": limit,
            "status_filter": status,
            "has_more": len(response.get("Invoices", [])) > limit
        }
            
    except Exception as e:
        logger.error(f"Error retrieving invoices: {e}")
        return {"error": f"Failed to retrieve invoices: {str(e)}"}

async def xero_create_invoice(
    contact_id: str,
    type: str = "ACCREC",
    date: Optional[str] = None,
    due_date: Optional[str] = None,
    reference: Optional[str] = None,
    currency_code: str = "USD",
    line_items: Optional[List[Dict[str, Any]]] = None,
    status: str = "DRAFT"
) -> Dict[str, Any]:
    """Create a new invoice in Xero."""
    try:
        # Validate invoice type
        valid_types = ["ACCREC", "ACCPAY"]
        if type.upper() not in valid_types:
            return {
                "success": False,
                "error": f"Invalid invoice type '{type}'. Valid types are: {', '.join(valid_types)}"
            }
        
        # Validate status
        valid_statuses = ["DRAFT", "SUBMITTED", "AUTHORISED"]
        if status.upper() not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status '{status}'. Valid statuses are: {', '.join(valid_statuses)}"
            }
        
        # Build invoice data
        invoice_data = {
            "Type": type.upper(),
            "Contact": {
                "ContactID": contact_id
            },
            "CurrencyCode": currency_code,
            "Status": status.upper()
        }
        
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
                
            invoice_data["LineItems"] = formatted_line_items
        else:
            # Default line item if none provided
            default_account = "200" if type.upper() == "ACCREC" else "400"  # Sales or Purchase account
            invoice_data["LineItems"] = [{
                "Description": "Invoice item",
                "Quantity": 1.0,
                "UnitAmount": 100.0,
                "AccountCode": default_account
            }]
        
        # Prepare request data
        request_data = {
            "Invoices": [invoice_data]
        }
        
        # Make API request
        response = await make_xero_api_request("Invoices", method="POST", data=request_data)
        
        if response.get("Invoices") and len(response["Invoices"]) > 0:
            created_invoice = response["Invoices"][0]
            
            # Extract line items for response
            line_items_response = []
            if created_invoice.get("LineItems"):
                for line in created_invoice["LineItems"]:
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
                "message": "Invoice created successfully",
                "invoice": {
                    "invoice_id": created_invoice.get("InvoiceID"),
                    "invoice_number": created_invoice.get("InvoiceNumber"),
                    "reference": created_invoice.get("Reference"),
                    "type": created_invoice.get("Type"),
                    "status": created_invoice.get("Status"),
                    "contact": {
                        "contact_id": created_invoice.get("Contact", {}).get("ContactID"),
                        "name": created_invoice.get("Contact", {}).get("Name")
                    },
                    "date": created_invoice.get("Date"),
                    "due_date": created_invoice.get("DueDate"),
                    "currency_code": created_invoice.get("CurrencyCode"),
                    "currency_rate": created_invoice.get("CurrencyRate"),
                    "line_items": line_items_response,
                    "sub_total": created_invoice.get("SubTotal"),
                    "total_tax": created_invoice.get("TotalTax"),
                    "total": created_invoice.get("Total"),
                    "amount_due": created_invoice.get("AmountDue"),
                    "amount_paid": created_invoice.get("AmountPaid"),
                    "updated_date_utc": created_invoice.get("UpdatedDateUTC"),
                    "branding_theme_id": created_invoice.get("BrandingThemeID")
                }
            }
        else:
            return {
                "success": False,
                "error": "No invoice was created - unexpected API response",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        return {
            "success": False,
            "error": f"Failed to create invoice: {str(e)}"
        }

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