import logging
from typing import Dict, Any
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_items(limit: int = 10) -> Dict[str, Any]:
    """Retrieve a list of items from Xero."""
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            limit = min(max(limit, 1), 100)
        
        # Get items from API
        response = await make_xero_api_request("Items")
        
        items_list = []
        if response.get("Items"):
            # Limit results to requested amount
            limited_items = response["Items"][:limit]
            
            for item in limited_items:
                # Extract purchase details
                purchase_details = None
                if item.get("PurchaseDetails"):
                    purchase_details = {
                        "unit_price": item["PurchaseDetails"].get("UnitPrice"),
                        "account_code": item["PurchaseDetails"].get("AccountCode"),
                        "cogs_account_code": item["PurchaseDetails"].get("COGSAccountCode"),
                        "tax_type": item["PurchaseDetails"].get("TaxType")
                    }
                
                # Extract sales details
                sales_details = None
                if item.get("SalesDetails"):
                    sales_details = {
                        "unit_price": item["SalesDetails"].get("UnitPrice"),
                        "account_code": item["SalesDetails"].get("AccountCode"),
                        "cogs_account_code": item["SalesDetails"].get("COGSAccountCode"),
                        "tax_type": item["SalesDetails"].get("TaxType")
                    }
                
                item_data = {
                    "item_id": item.get("ItemID"),
                    "code": item.get("Code"),
                    "name": item.get("Name"),
                    "description": item.get("Description"),
                    "purchase_description": item.get("PurchaseDescription"),
                    "purchase_details": purchase_details,
                    "sales_details": sales_details,
                    "is_tracked_as_inventory": item.get("IsTrackedAsInventory"),
                    "inventory_asset_account_code": item.get("InventoryAssetAccountCode"),
                    "total_cost_pool": item.get("TotalCostPool"),
                    "quantity_on_hand": item.get("QuantityOnHand"),
                    "updated_date_utc": item.get("UpdatedDateUTC")
                }
                
                items_list.append(item_data)
        
        return {
            "success": True,
            "message": f"Retrieved {len(items_list)} items",
            "items": items_list,
            "total_returned": len(items_list),
            "limit_requested": limit,
            "has_more": len(response.get("Items", [])) > limit
        }
            
    except Exception as e:
        logger.error(f"Error retrieving items: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve items: {str(e)}"
        }