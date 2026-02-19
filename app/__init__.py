"""MDViewer - A beautiful markdown viewer for the web."""

__version__ = "1.0.0"
__author__ = "Anderson"
__email__ = "anderson@example.com"

from app.main import create_app, run_server
from app.config import settings

__all__ = [
    "create_app",
    "run_server",
    "settings",
    "__version__",
]
