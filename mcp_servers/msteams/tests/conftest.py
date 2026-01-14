import sys
from pathlib import Path

# Add the msteams directory to the path so tests can import the tools module
msteams_dir = Path(__file__).parent.parent
sys.path.insert(0, str(msteams_dir))
