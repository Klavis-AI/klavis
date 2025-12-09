"""
Hyperlink management tools for PowerPoint MCP Server.
Implements hyperlink operations for text shapes and runs.
"""

from typing import Dict, List, Optional, Any

def register_hyperlink_tools(app, presentations, get_current_presentation_id, validate_parameters, 
                          is_positive, is_non_negative, is_in_range, is_valid_rgb):
    """Register hyperlink management tools with the FastMCP app."""
    
    @app.tool()
    def manage_hyperlinks(
        operation: str,
        slide_index: int,
        shape_index: int = None,
        text: str = None, 
        url: str = None,
        run_index: int = 0,
        presentation_id: str = None
    ) -> Dict:
        """
        Manage hyperlinks in text shapes and runs.
        
        Args:
            operation: Operation type ("add", "remove", "list", "update")
            slide_index: Index of the slide (0-based)
            shape_index: Index of the shape on the slide (0-based)
            text: Text to make into hyperlink (for "add" operation)
            url: URL for the hyperlink
            run_index: Index of text run within the shape (0-based)
            presentation_id: Optional presentation ID (uses current if not provided)
            
        Returns:
            Dictionary with operation results
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
            
            if operation == "list":
                # List all hyperlinks in the slide
                hyperlinks = []
                for shape_idx, shape in enumerate(slide.shapes):
                    if hasattr(shape, 'text_frame') and shape.text_frame:
                        for para_idx, paragraph in enumerate(shape.text_frame.paragraphs):
                            for run_idx, run in enumerate(paragraph.runs):
                                if run.hyperlink.address:
                                    hyperlinks.append({
                                        "shape_index": shape_idx,
                                        "paragraph_index": para_idx,
                                        "run_index": run_idx,
                                        "text": run.text,
                                        "url": run.hyperlink.address
                                    })
                
                return {
                    "message": f"Found {len(hyperlinks)} hyperlinks on slide {slide_index}",
                    "hyperlinks": hyperlinks
                }
            
            # For other operations, validate shape index
            if shape_index is None or not (0 <= shape_index < len(slide.shapes)):
                return {"error": f"Shape index {shape_index} out of range"}
            
            shape = slide.shapes[shape_index]
            
            # Check if shape has text
            if not hasattr(shape, 'text_frame') or not shape.text_frame:
                return {"error": "Shape does not contain text"}
            
            if operation == "add":
                if not text or not url:
                    return {"error": "Both 'text' and 'url' are required for adding hyperlinks"}
                
                # Add new text run with hyperlink
                paragraph = shape.text_frame.paragraphs[0]
                run = paragraph.add_run()
                run.text = text
                run.hyperlink.address = url
                
                return {
                    "message": f"Added hyperlink '{text}' -> '{url}' to shape {shape_index}",
                    "text": text,
                    "url": url
                }
            
            elif operation == "update":
                if not url:
                    return {"error": "URL is required for updating hyperlinks"}
                
                # Update existing hyperlink
                paragraphs = shape.text_frame.paragraphs
                if run_index < len(paragraphs[0].runs):
                    run = paragraphs[0].runs[run_index]
                    old_url = run.hyperlink.address
                    run.hyperlink.address = url
                    
                    return {
                        "message": f"Updated hyperlink from '{old_url}' to '{url}'",
                        "old_url": old_url,
                        "new_url": url,
                        "text": run.text
                    }
                else:
                    return {"error": f"Run index {run_index} out of range"}
            
            elif operation == "remove":
                # Remove hyperlink from specific run
                paragraphs = shape.text_frame.paragraphs
                if run_index < len(paragraphs[0].runs):
                    run = paragraphs[0].runs[run_index]
                    old_url = run.hyperlink.address
                    run.hyperlink.address = None
                    
                    return {
                        "message": f"Removed hyperlink '{old_url}' from text '{run.text}'",
                        "removed_url": old_url,
                        "text": run.text
                    }
                else:
                    return {"error": f"Run index {run_index} out of range"}
            
            else:
                return {"error": f"Unsupported operation: {operation}. Use 'add', 'remove', 'list', or 'update'"}
                
        except Exception as e:
            return {"error": f"Failed to manage hyperlinks: {str(e)}"}