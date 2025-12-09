"""
Slide master management tools for PowerPoint MCP Server.
Implements slide master and layout access capabilities.
"""

from typing import Dict, List, Optional, Any

def register_master_tools(app, presentations, get_current_presentation_id, validate_parameters, 
                          is_positive, is_non_negative, is_in_range, is_valid_rgb):
    """Register slide master management tools with the FastMCP app."""
    
    @app.tool()
    def manage_slide_masters(
        operation: str,
        master_index: int = 0,
        layout_index: int = None,
        presentation_id: str = None
    ) -> Dict:
        """
        Access and manage slide master properties and layouts.
        
        Args:
            operation: Operation type ("list", "get_layouts", "get_info")
            master_index: Index of the slide master (0-based)
            layout_index: Index of specific layout within master (0-based)
            presentation_id: Optional presentation ID (uses current if not provided)
            
        Returns:
            Dictionary with slide master information
        """
        try:
            # Get presentation
            pres_id = presentation_id or get_current_presentation_id()
            if pres_id not in presentations:
                return {"error": "Presentation not found"}
            
            pres = presentations[pres_id]
            
            if operation == "list":
                # List all slide masters
                masters_info = []
                for idx, master in enumerate(pres.slide_masters):
                    masters_info.append({
                        "index": idx,
                        "layout_count": len(master.slide_layouts),
                        "name": getattr(master, 'name', f"Master {idx}")
                    })
                
                return {
                    "message": f"Found {len(masters_info)} slide masters",
                    "masters": masters_info,
                    "total_masters": len(pres.slide_masters)
                }
            
            # Validate master index
            if not (0 <= master_index < len(pres.slide_masters)):
                return {"error": f"Master index {master_index} out of range"}
            
            master = pres.slide_masters[master_index]
            
            if operation == "get_layouts":
                # Get all layouts for a specific master
                layouts_info = []
                for idx, layout in enumerate(master.slide_layouts):
                    layouts_info.append({
                        "index": idx,
                        "name": layout.name,
                        "placeholder_count": len(layout.placeholders) if hasattr(layout, 'placeholders') else 0
                    })
                
                return {
                    "message": f"Master {master_index} has {len(layouts_info)} layouts",
                    "master_index": master_index,
                    "layouts": layouts_info
                }
            
            elif operation == "get_info":
                # Get detailed info about master or specific layout
                if layout_index is not None:
                    if not (0 <= layout_index < len(master.slide_layouts)):
                        return {"error": f"Layout index {layout_index} out of range"}
                    
                    layout = master.slide_layouts[layout_index]
                    placeholders_info = []
                    
                    if hasattr(layout, 'placeholders'):
                        for placeholder in layout.placeholders:
                            placeholders_info.append({
                                "idx": placeholder.placeholder_format.idx,
                                "type": str(placeholder.placeholder_format.type),
                                "name": getattr(placeholder, 'name', 'Unnamed')
                            })
                    
                    return {
                        "message": f"Layout info for master {master_index}, layout {layout_index}",
                        "master_index": master_index,
                        "layout_index": layout_index,
                        "layout_name": layout.name,
                        "placeholders": placeholders_info
                    }
                else:
                    # Master info
                    return {
                        "message": f"Master {master_index} information",
                        "master_index": master_index,
                        "layout_count": len(master.slide_layouts),
                        "name": getattr(master, 'name', f"Master {master_index}")
                    }
            
            else:
                return {"error": f"Unsupported operation: {operation}. Use 'list', 'get_layouts', or 'get_info'"}
                
        except Exception as e:
            return {"error": f"Failed to manage slide masters: {str(e)}"}