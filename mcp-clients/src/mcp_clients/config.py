"""
Configuration module.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Flag to control whether database operations are performed
# Set to False to skip all database operations
USE_PRODUCTION_DB = os.getenv("USE_PRODUCTION_DB", "False").lower() == "true"
