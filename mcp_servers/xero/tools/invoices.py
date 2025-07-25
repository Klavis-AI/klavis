import logging
from typing import Dict, Any
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