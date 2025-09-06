""" tools for Datadog """
import re
import logging
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as parse_date


logger = logging.getLogger("datadog-mcp-server-utilities")


def parse_human_readable_date(date_str: str) -> int:
    """Convert human-readable date string to Unix timestamp.
    
    Accepts formats like:
    - "2024-01-15 14:30:00"
    - "2024-01-15T14:30:00Z" 
    - "2024-01-15"
    - "1 hour ago", "2 days ago", "30 minutes ago"
    - "yesterday", "today"
    - Unix timestamps (as strings)
    """
    try:
        # Handle Unix timestamp strings
        if date_str.isdigit():
            return int(date_str)
            
        # Handle relative time expressions
        if "ago" in date_str.lower():
            now = datetime.now(timezone.utc)
            
            # Extract number and unit using regex
            match = re.match(r'(\d+)\s*(minute|hour|day|week|month)s?\s+ago', date_str.lower())
            if match:
                value, unit = match.groups()
                value = int(value)
                
                if unit == 'minute':
                    target_time = now - timedelta(minutes=value)
                elif unit == 'hour':
                    target_time = now - timedelta(hours=value)
                elif unit == 'day':
                    target_time = now - timedelta(days=value)
                elif unit == 'week':
                    target_time = now - timedelta(weeks=value)
                elif unit == 'month':
                    target_time = now - timedelta(days=value * 30)  # Approximate
                else:
                    raise ValueError(f"Unsupported time unit: {unit}")
            else:
                raise ValueError(f"Cannot parse relative time: {date_str}")
                
        # Handle common keywords
        elif date_str.lower() == "now":
            target_time = datetime.now(timezone.utc)
        elif date_str.lower() == "today":
            target_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str.lower() == "yesterday":
            target_time = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Parse standard date formats using dateutil
            target_time = parse_date(date_str)
            
        return int(target_time.timestamp())
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        raise ValueError(f"Unable to parse date: {date_str}. Supported formats: '2024-01-15', '1 hour ago', 'yesterday', Unix timestamp")


# Configure logging
def setup_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: str = "datadog_mcp_server.log"):
    """Setup logging with optional file output.
    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_to_file: Whether to log to a file in addition to console.
        log_file_path: Path to the log file if log_to_file is True.
    """
    log_level = getattr(logging, level.upper())
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if log_to_file:
        try:
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Log the file path
            logging.getLogger("datadog-mcp-server").info(f"Logging to file: {log_file_path}")
        except Exception as e:
            logging.getLogger("datadog-mcp-server").warning(f"Failed to setup file logging: {e}")
