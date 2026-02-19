"""FoxMDViewer - A beautiful markdown viewer with Shinto theme."""

__version__ = "1.0.0"
__author__ = "Anderson"

from foxmdviewer.main import create_app, run_server
from foxmdviewer.config import settings

__all__ = [
    "create_app",
    "run_server",
    "settings",
    "__version__",
]
