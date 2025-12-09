"""
Slide transition management tools for PowerPoint MCP Server.
Implements slide transition and timing capabilities.
"""

from typing import Dict, List, Optional, Any

def register_transition_tools(app, presentations, get_current_presentation_id, validate_parameters, 
                          is_positive, is_non_negative, is_in_range, is_valid_rgb):
    """Register slide transition management tools with the FastMCP app."""
    
    @app.tool()
    def manage_slide_transitions(
        slide_index: int,
        operation: str,
        transition_type: str = None,
        duration: float = 1.0,
        presentation_id: str = None
    ) -> Dict:
        """
        Manage slide transitions and timing.
        
        Args:
            slide_index: Index of the slide (0-based)
            operation: Operation type ("set", "remove", "get")
            transition_type: Type of transition (basic support)
            duration: Duration of transition in seconds
            presentation_id: Optional presentation ID (uses current if not provided)
            
        Returns:
            Dictionary with transition information
        """
        try:
            # Get presentation
            pres_id = presentation_id or get_current_presentation_id()
            if pres_id not in presentations:
                return {"error": "Presentation not found"}
            
            pres = presentations[pres_id]
            
            # Validate slide index
            if not (0 <= slide_index < len(pres.slides)):
                return {"error": f"Slide index {slide_index} out of range"}
            
            slide = pres.slides[slide_index]
            
            if operation == "get":
                # Get current transition info (limited python-pptx support)
                return {
                    "message": f"Transition info for slide {slide_index}",
                    "slide_index": slide_index,
                    "note": "Transition reading has limited support in python-pptx"
                }
            
            elif operation == "set":
                return {
                    "message": f"Transition setting requested for slide {slide_index}",
                    "slide_index": slide_index,
                    "transition_type": transition_type,
                    "duration": duration,
                    "note": "Transition setting has limited support in python-pptx - this is a placeholder for future enhancement"
                }
            
            elif operation == "remove":
                return {
                    "message": f"Transition removal requested for slide {slide_index}",
                    "slide_index": slide_index,
                    "note": "Transition removal has limited support in python-pptx - this is a placeholder for future enhancement"
                }
            
            else:
                return {"error": f"Unsupported operation: {operation}. Use 'set', 'remove', or 'get'"}
                
        except Exception as e:
            return {"error": f"Failed to manage slide transitions: {str(e)}"}