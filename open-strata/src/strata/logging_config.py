"""Logging configuration for Strata MCP Router."""

import logging
from datetime import datetime
from pathlib import Path

from platformdirs import user_cache_dir


class BannerFormatter(logging.Formatter):
    """Custom formatter for banner messages that shows only the message."""

    def format(self, record):
        return record.getMessage()


def log_banner() -> None:
    """Log the Klavis AI colorful banner using a temporary handler."""
    # Create a temporary logger with custom formatter
    banner_logger = logging.getLogger("banner")
    banner_logger.setLevel(logging.INFO)

    # Create a handler with no formatting for clean output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(BannerFormatter())

    banner_logger.addHandler(console_handler)
    banner_logger.propagate = False  # Don't propagate to root logger

    try:
        banner_text = """
  \033[1;31m██╗  ██╗\033[1;33m██╗      \033[1;32m█████╗ \033[1;36m██╗   ██╗\033[1;34m██╗\033[1;35m███████╗     \033[1;91m█████╗ \033[1;93m██╗\033[0m
  \033[1;31m██║ ██╔╝\033[1;33m██║     \033[1;32m██╔══██╗\033[1;36m██║   ██║\033[1;34m██║\033[1;35m██╔════╝    \033[1;91m██╔══██╗\033[1;93m██║\033[0m
  \033[1;31m█████╔╝ \033[1;33m██║     \033[1;32m███████║\033[1;36m██║   ██║\033[1;34m██║\033[1;35m███████╗    \033[1;91m███████║\033[1;93m██║\033[0m
  \033[1;31m██╔═██╗ \033[1;33m██║     \033[1;32m██╔══██║\033[1;36m╚██╗ ██╔╝\033[1;34m██║\033[1;35m╚════██║    \033[1;91m██╔══██║\033[1;93m██║\033[0m
  \033[1;31m██║  ██╗\033[1;33m███████╗\033[1;32m██║  ██║ \033[1;36m╚████╔╝ \033[1;34m██║\033[1;35m███████║    \033[1;91m██║  ██║\033[1;93m██║\033[0m
  \033[1;31m╚═╝  ╚═╝\033[1;33m╚══════╝\033[1;32m╚═╝  ╚═╝  \033[1;36m╚═══╝  \033[1;34m╚═╝\033[1;35m╚══════╝    \033[1;91m╚═╝  ╚═╝\033[1;93m╚═╝\033[0m

  \033[1;32mEmpowering AI with Seamless Integration\033[0m

  \033[1;36m═════════════════════════════════════════════════════════════════════════════\033[0m
  \033[1;32m STRATA MCP  \033[0m·\033[1;33m  One MCP server that use tools reliably at any scale \033[0m
  \033[1;36m═════════════════════════════════════════════════════════════════════════════\033[0m
  \033[1;33m→ Starting MCP Server...\033[0m
"""
        banner_logger.info(banner_text)
    finally:
        # Clean up the handler
        banner_logger.removeHandler(console_handler)


def setup_logging(log_level: str = "INFO", no_banner: bool = False) -> None:
    """Configure logging to output to both console and file.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        no_banner: Skip displaying the banner on startup
    """
    # Create cache directory for logs
    cache_dir = Path(user_cache_dir("strata"))
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = cache_dir / f"{timestamp}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Log the setup to console only (before adding file handler)
    logger = logging.getLogger(__name__)
    if not no_banner:
        log_banner()
        # Log initialization message without logging prefix using clean formatter
        logger.info(f"Logging initialized - Console: {log_level}, File: {log_file}")

    logger.handlers.clear()

    # File handler (added after the initialization message)
    file_handler = logging.FileHandler(log_file, encoding="utf-8", delay=True)
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG and above to file
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_log_dir() -> Path:
    """Get the directory where log files are stored.

    Returns:
        Path to the log directory
    """
    return Path(user_cache_dir("strata"))
