"""
Validation utilities for PowerPoint MCP Server.
Functions for validating and fixing slide content, text fit, and layouts.
"""
from typing import Dict, List, Optional, Any


def validate_text_fit(shape, text_content: str = None, font_size: int = 12) -> Dict:
    """
    Validate if text content will fit in a shape container.
    
    Args:
        shape: The shape containing the text
        text_content: The text to validate (if None, uses existing text)
        font_size: The font size to check
    
    Returns:
        Dictionary with validation results and suggestions
    """
    result = {
        'fits': True,
        'estimated_overflow': False,
        'suggested_font_size': font_size,
        'suggested_dimensions': None,
        'warnings': [],
        'needs_optimization': False
    }
    
    try:
        # Use existing text if not provided
        if text_content is None and hasattr(shape, 'text_frame'):
            text_content = shape.text_frame.text
        
        if not text_content:
            return result
        
        # Basic heuristic: estimate if text will overflow
        if hasattr(shape, 'width') and hasattr(shape, 'height'):
            # Rough estimation: average character width is about 0.6 * font_size
            avg_char_width = font_size * 0.6
            estimated_width = len(text_content) * avg_char_width
            
            # Convert shape dimensions to points (assuming they're in EMU)
            shape_width_pt = shape.width / 12700  # EMU to points conversion
            shape_height_pt = shape.height / 12700
            
            if estimated_width > shape_width_pt:
                result['fits'] = False
                result['estimated_overflow'] = True
                result['needs_optimization'] = True
                
                # Suggest smaller font size
                suggested_size = int((shape_width_pt / len(text_content)) * 0.8)
                result['suggested_font_size'] = max(suggested_size, 8)
                
                # Suggest larger dimensions
                result['suggested_dimensions'] = {
                    'width': estimated_width * 1.2,
                    'height': shape_height_pt
                }
                
                result['warnings'].append(
                    f"Text may overflow. Consider font size {result['suggested_font_size']} "
                    f"or increase width to {result['suggested_dimensions']['width']:.1f} points"
                )
        
        # Check for very long lines that might cause formatting issues
        lines = text_content.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        if max_line_length > 100:  # Arbitrary threshold
            result['warnings'].append("Very long lines detected. Consider adding line breaks.")
            result['needs_optimization'] = True
        
        return result
        
    except Exception as e:
        result['fits'] = False
        result['error'] = str(e)
        return result


def validate_and_fix_slide(slide, auto_fix: bool = True, min_font_size: int = 8, 
                          max_font_size: int = 72) -> Dict:
    """
    Comprehensively validate and automatically fix slide content issues.
    
    Args:
        slide: The slide object to validate
        auto_fix: Whether to automatically apply fixes
        min_font_size: Minimum allowed font size
        max_font_size: Maximum allowed font size
        
    Returns:
        Dictionary with validation results and applied fixes
    """
    result = {
        'validation_passed': True,
        'issues_found': [],
        'fixes_applied': [],
        'warnings': [],
        'shapes_processed': 0,
        'text_shapes_optimized': 0
    }
    
    try:
        shapes_with_text = []
        
        # Find all shapes with text content
        for i, shape in enumerate(slide.shapes):
            result['shapes_processed'] += 1
            
            if hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
                shapes_with_text.append((i, shape))
        
        # Validate each text shape
        for shape_index, shape in shapes_with_text:
            shape_name = f"Shape {shape_index}"
            
            # Validate text fit
            text_validation = validate_text_fit(shape, font_size=12)
            
            if not text_validation['fits'] or text_validation['needs_optimization']:
                issue = f"{shape_name}: Text may not fit properly"
                result['issues_found'].append(issue)
                result['validation_passed'] = False
                
                if auto_fix and text_validation['suggested_font_size']:
                    try:
                        # Apply suggested font size
                        suggested_size = max(min_font_size, 
                                           min(text_validation['suggested_font_size'], max_font_size))
                        
                        # Apply font size to all runs in the text frame
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if hasattr(run, 'font'):
                                    run.font.size = suggested_size * 12700  # Convert to EMU
                        
                        fix = f"{shape_name}: Adjusted font size to {suggested_size}pt"
                        result['fixes_applied'].append(fix)
                        result['text_shapes_optimized'] += 1
                        
                    except Exception as e:
                        warning = f"{shape_name}: Could not auto-fix font size: {str(e)}"
                        result['warnings'].append(warning)
            
            # Check for other potential issues
            if len(shape.text_frame.text) > 500:  # Very long text
                result['warnings'].append(f"{shape_name}: Contains very long text (>500 chars)")
            
            # Check for empty paragraphs
            empty_paragraphs = sum(1 for p in shape.text_frame.paragraphs if not p.text.strip())
            if empty_paragraphs > 2:
                result['warnings'].append(f"{shape_name}: Contains {empty_paragraphs} empty paragraphs")
        
        # Check slide-level issues
        if len(slide.shapes) > 20:
            result['warnings'].append("Slide contains many shapes (>20), may affect performance")
        
        # Summary
        if result['validation_passed']:
            result['summary'] = "Slide validation passed successfully"
        else:
            result['summary'] = f"Found {len(result['issues_found'])} issues"
            if auto_fix:
                result['summary'] += f", applied {len(result['fixes_applied'])} fixes"
        
        return result
        
    except Exception as e:
        result['validation_passed'] = False
        result['error'] = str(e)
        return result


def validate_slide_layout(slide) -> Dict:
    """
    Validate slide layout for common issues.
    
    Args:
        slide: The slide object
        
    Returns:
        Dictionary with layout validation results
    """
    result = {
        'layout_valid': True,
        'issues': [],
        'suggestions': [],
        'shape_count': len(slide.shapes),
        'overlapping_shapes': []
    }
    
    try:
        shapes = list(slide.shapes)
        
        # Check for overlapping shapes
        for i, shape1 in enumerate(shapes):
            for j, shape2 in enumerate(shapes[i+1:], i+1):
                if shapes_overlap(shape1, shape2):
                    result['overlapping_shapes'].append({
                        'shape1_index': i,
                        'shape2_index': j,
                        'shape1_name': getattr(shape1, 'name', f'Shape {i}'),
                        'shape2_name': getattr(shape2, 'name', f'Shape {j}')
                    })
        
        if result['overlapping_shapes']:
            result['layout_valid'] = False
            result['issues'].append(f"Found {len(result['overlapping_shapes'])} overlapping shapes")
            result['suggestions'].append("Consider repositioning overlapping shapes")
        
        # Check for shapes outside slide boundaries
        slide_width = 10 * 914400  # Standard slide width in EMU
        slide_height = 7.5 * 914400  # Standard slide height in EMU
        
        shapes_outside = []
        for i, shape in enumerate(shapes):
            if (shape.left < 0 or shape.top < 0 or 
                shape.left + shape.width > slide_width or 
                shape.top + shape.height > slide_height):
                shapes_outside.append(i)
        
        if shapes_outside:
            result['layout_valid'] = False
            result['issues'].append(f"Found {len(shapes_outside)} shapes outside slide boundaries")
            result['suggestions'].append("Reposition shapes to fit within slide boundaries")
        
        # Check shape spacing
        if len(shapes) > 1:
            min_spacing = check_minimum_spacing(shapes)
            if min_spacing < 0.1 * 914400:  # Less than 0.1 inch spacing
                result['suggestions'].append("Consider increasing spacing between shapes")
        
        return result
        
    except Exception as e:
        result['layout_valid'] = False
        result['error'] = str(e)
        return result


def shapes_overlap(shape1, shape2) -> bool:
    """
    Check if two shapes overlap.
    
    Args:
        shape1: First shape
        shape2: Second shape
        
    Returns:
        True if shapes overlap, False otherwise
    """
    try:
        # Get boundaries
        left1, top1 = shape1.left, shape1.top
        right1, bottom1 = left1 + shape1.width, top1 + shape1.height
        
        left2, top2 = shape2.left, shape2.top
        right2, bottom2 = left2 + shape2.width, top2 + shape2.height
        
        # Check for overlap
        return not (right1 <= left2 or right2 <= left1 or bottom1 <= top2 or bottom2 <= top1)
    except:
        return False


def check_minimum_spacing(shapes: List) -> float:
    """
    Check minimum spacing between shapes.
    
    Args:
        shapes: List of shapes
        
    Returns:
        Minimum spacing found between shapes (in EMU)
    """
    min_spacing = float('inf')
    
    try:
        for i, shape1 in enumerate(shapes):
            for shape2 in shapes[i+1:]:
                # Calculate distance between shape edges
                distance = calculate_shape_distance(shape1, shape2)
                min_spacing = min(min_spacing, distance)
        
        return min_spacing if min_spacing != float('inf') else 0
    except:
        return 0


def calculate_shape_distance(shape1, shape2) -> float:
    """
    Calculate distance between two shapes.
    
    Args:
        shape1: First shape
        shape2: Second shape
        
    Returns:
        Distance between shape edges (in EMU)
    """
    try:
        # Get centers
        center1_x = shape1.left + shape1.width / 2
        center1_y = shape1.top + shape1.height / 2
        
        center2_x = shape2.left + shape2.width / 2
        center2_y = shape2.top + shape2.height / 2
        
        # Calculate center-to-center distance
        dx = abs(center2_x - center1_x)
        dy = abs(center2_y - center1_y)
        
        # Subtract half-widths and half-heights to get edge distance
        edge_distance_x = max(0, dx - (shape1.width + shape2.width) / 2)
        edge_distance_y = max(0, dy - (shape1.height + shape2.height) / 2)
        
        # Return minimum edge distance
        return min(edge_distance_x, edge_distance_y)
    except:
        return 0