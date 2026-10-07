import sys
from pathlib import Path

# Add project root to sys.path so library_management can be imported cleanly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from library_management import app
