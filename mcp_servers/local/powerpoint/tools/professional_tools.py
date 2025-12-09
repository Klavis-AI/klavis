"""
Professional design tools for PowerPoint MCP Server.
Handles themes, effects, fonts, and advanced formatting.
"""
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import utils as ppt_utils


def register_professional_tools(app: FastMCP, presentations: Dict, get_current_presentation_id):
    """Register professional design tools with the FastMCP app"""
    
    @app.tool()
    def apply_professional_design(
        operation: str,  # "professional_slide", "theme", "enhance", "get_schemes"
        slide_index: Optional[int] = None,
        slide_type: str = "title_content",
        color_scheme: str = "modern_blue",
        title: Optional[str] = None,
        content: Optional[List[str]] = None,
        apply_to_existing: bool = True,
        enhance_title: bool = True,
        enhance_content: bool = True,
        enhance_shapes: bool = True,
        enhance_charts: bool = True,
        presentation_id: Optional[str] = None
    ) -> Dict:
        """Unified professional design tool for themes, slides, and visual enhancements.
        This applies professional styling and themes rather than structural layout changes."""
        pres_id = presentation_id if presentation_id is not None else get_current_presentation_id()
        
        if operation == "get_schemes":
            # Return available color schemes
            return ppt_utils.get_color_schemes()
        
        if pres_id is None or pres_id not in presentations:
            return {
                "error": "No presentation is currently loaded or the specified ID is invalid"
            }
        
        pres = presentations[pres_id]
        
        try:
            if operation == "professional_slide":
                # Add professional slide with advanced styling
                if slide_index is not None and (slide_index < 0 or slide_index >= len(pres.slides)):
                    return {
                        "error": f"Invalid slide index: {slide_index}. Available slides: 0-{len(pres.slides) - 1}"
                    }
                
                result = ppt_utils.add_professional_slide(
                    pres,
                    slide_type=slide_type,
                    color_scheme=color_scheme,
                    title=title,
                    content=content
                )
                
                return {
                    "message": f"Added professional {slide_type} slide",
                    "slide_index": len(pres.slides) - 1,
                    "color_scheme": color_scheme,
                    "slide_type": slide_type
                }
            
            elif operation == "theme":
                # Apply professional theme
                ppt_utils.apply_professional_theme(
                    pres,
                    color_scheme=color_scheme,
                    apply_to_existing=apply_to_existing
                )
                
                return {
                    "message": f"Applied {color_scheme} theme to presentation",
                    "color_scheme": color_scheme,
                    "applied_to_existing": apply_to_existing
                }
            
            elif operation == "enhance":
                # Enhance existing slide
                if slide_index is None:
                    return {
                        "error": "slide_index is required for enhance operation"
                    }
                
                if slide_index < 0 or slide_index >= len(pres.slides):
                    return {
                        "error": f"Invalid slide index: {slide_index}. Available slides: 0-{len(pres.slides) - 1}"
                    }
                
                slide = pres.slides[slide_index]
                result = ppt_utils.enhance_existing_slide(
                    slide,
                    color_scheme=color_scheme,
                    enhance_title=enhance_title,
                    enhance_content=enhance_content,
                    enhance_shapes=enhance_shapes,
                    enhance_charts=enhance_charts
                )
                
                return {
                    "message": f"Enhanced slide {slide_index} with {color_scheme} scheme",
                    "slide_index": slide_index,
                    "color_scheme": color_scheme,
                    "enhancements_applied": result.get("enhancements_applied", [])
                }
            
            else:
                return {
                    "error": f"Invalid operation: {operation}. Must be 'slide', 'theme', 'enhance', or 'get_schemes'"
                }
        
        except Exception as e:
            return {
                "error": f"Failed to apply professional design: {str(e)}"
            }

    @app.tool()
    def apply_picture_effects(
        slide_index: int,
        shape_index: int,
        effects: Dict[str, Dict],  # {"shadow": {"blur_radius": 4.0, ...}, "glow": {...}}
        presentation_id: Optional[str] = None
    ) -> Dict:
        """Apply multiple picture effects in combination."""
        pres_id = presentation_id if presentation_id is not None else get_current_presentation_id()
        
        if pres_id is None or pres_id not in presentations:
            return {
                "error": "No presentation is currently loaded or the specified ID is invalid"
            }
        
        pres = presentations[pres_id]
        
        if slide_index < 0 or slide_index >= len(pres.slides):
            return {
                "error": f"Invalid slide index: {slide_index}. Available slides: 0-{len(pres.slides) - 1}"
            }
        
        slide = pres.slides[slide_index]
        
        if shape_index < 0 or shape_index >= len(slide.shapes):
            return {
                "error": f"Invalid shape index: {shape_index}. Available shapes: 0-{len(slide.shapes) - 1}"
            }
        
        shape = slide.shapes[shape_index]
        
        try:
            applied_effects = []
            warnings = []
            
            # Apply each effect
            for effect_type, effect_params in effects.items():
                try:
                    if effect_type == "shadow":
                        ppt_utils.apply_picture_shadow(
                            shape,
                            shadow_type=effect_params.get("shadow_type", "outer"),
                            blur_radius=effect_params.get("blur_radius", 4.0),
                            distance=effect_params.get("distance", 3.0),
                            direction=effect_params.get("direction", 315.0),
                            color=effect_params.get("color", [0, 0, 0]),
                            transparency=effect_params.get("transparency", 0.6)
                        )
                        applied_effects.append("shadow")
                    
                    elif effect_type == "reflection":
                        ppt_utils.apply_picture_reflection(
                            shape,
                            size=effect_params.get("size", 0.5),
                            transparency=effect_params.get("transparency", 0.5),
                            distance=effect_params.get("distance", 0.0),
                            blur=effect_params.get("blur", 4.0)
                        )
                        applied_effects.append("reflection")
                    
                    elif effect_type == "glow":
                        ppt_utils.apply_picture_glow(
                            shape,
                            size=effect_params.get("size", 5.0),
                            color=effect_params.get("color", [0, 176, 240]),
                            transparency=effect_params.get("transparency", 0.4)
                        )
                        applied_effects.append("glow")
                    
                    elif effect_type == "soft_edges":
                        ppt_utils.apply_picture_soft_edges(
                            shape,
                            radius=effect_params.get("radius", 2.5)
                        )
                        applied_effects.append("soft_edges")
                    
                    elif effect_type == "rotation":
                        ppt_utils.apply_picture_rotation(
                            shape,
                            rotation=effect_params.get("rotation", 0.0)
                        )
                        applied_effects.append("rotation")
                    
                    elif effect_type == "transparency":
                        ppt_utils.apply_picture_transparency(
                            shape,
                            transparency=effect_params.get("transparency", 0.0)
                        )
                        applied_effects.append("transparency")
                    
                    elif effect_type == "bevel":
                        ppt_utils.apply_picture_bevel(
                            shape,
                            bevel_type=effect_params.get("bevel_type", "circle"),
                            width=effect_params.get("width", 6.0),
                            height=effect_params.get("height", 6.0)
                        )
                        applied_effects.append("bevel")
                    
                    elif effect_type == "filter":
                        ppt_utils.apply_picture_filter(
                            shape,
                            filter_type=effect_params.get("filter_type", "none"),
                            intensity=effect_params.get("intensity", 0.5)
                        )
                        applied_effects.append("filter")
                    
                    else:
                        warnings.append(f"Unknown effect type: {effect_type}")
                
                except Exception as e:
                    warnings.append(f"Failed to apply {effect_type} effect: {str(e)}")
            
            result = {
                "message": f"Applied {len(applied_effects)} effects to shape {shape_index} on slide {slide_index}",
                "applied_effects": applied_effects
            }
            
            if warnings:
                result["warnings"] = warnings
            
            return result
        
        except Exception as e:
            return {
                "error": f"Failed to apply picture effects: {str(e)}"
            }

    @app.tool()
    def manage_fonts(
        operation: str,  # "analyze", "optimize", "recommend"
        font_path: str,
        output_path: Optional[str] = None,
        presentation_type: str = "business",
        text_content: Optional[str] = None
    ) -> Dict:
        """Unified font management tool for analysis, optimization, and recommendations."""
        try:
            if operation == "analyze":
                # Analyze font file
                return ppt_utils.analyze_font_file(font_path)
            
            elif operation == "optimize":
                # Optimize font file
                optimized_path = ppt_utils.optimize_font_for_presentation(
                    font_path,
                    output_path=output_path,
                    text_content=text_content
                )
                
                return {
                    "message": f"Optimized font: {font_path}",
                    "original_path": font_path,
                    "optimized_path": optimized_path
                }
            
            elif operation == "recommend":
                # Get font recommendations
                return ppt_utils.get_font_recommendations(
                    font_path,
                    presentation_type=presentation_type
                )
            
            else:
                return {
                    "error": f"Invalid operation: {operation}. Must be 'analyze', 'optimize', or 'recommend'"
                }
        
        except Exception as e:
            return {
                "error": f"Failed to {operation} font: {str(e)}"
            }