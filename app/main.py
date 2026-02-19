"""Main application module for mdviewer.

This module creates and configures the Starlette application
with all routes, middleware, and services.
"""

import asyncio
from pathlib import Path
from typing import Optional

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from rich.console import Console

from app.api import api_router, websocket_router, broadcast_file_update
from app.config import settings, get_settings
from app.middleware import CORSMiddleware, RequestLoggingMiddleware
from app.services import create_file_watcher
from app.utils import find_available_port, open_browser

console = Console()
templates = Jinja2Templates(directory="templates")


async def homepage(request) -> HTMLResponse:
    """Render homepage with file list.

    Args:
        request: Starlette request object

    Returns:
        HTMLResponse: Rendered homepage
    """
    app_settings = request.app.state.settings
    return templates.TemplateResponse(
        request,
        "index.html",
        {"base_dir": str(app_settings.base_dir), "title": "MDViewer"},
    )


async def viewer_page(request) -> HTMLResponse:
    """Render markdown viewer page.

    Args:
        request: Starlette request object

    Returns:
        HTMLResponse: Rendered viewer page
    """
    file_path = request.path_params.get("file_path", "")

    return templates.TemplateResponse(
        request, "viewer.html", {"file_path": file_path, "title": "MDViewer - Reader"}
    )


def create_app(base_dir: Optional[Path] = None, debug: bool = False) -> Starlette:
    """Create and configure Starlette application.

    Args:
        base_dir: Base directory to scan for markdown files
        debug: Enable debug mode

    Returns:
        Starlette: Configured application instance

    Example:
        >>> app = create_app(Path("/home/user/docs"))
        >>> uvicorn.run(app, host="127.0.0.1", port=8000)
    """
    if base_dir:
        global settings
        from app.config import get_settings

        settings = get_settings(base_dir)

    routes = [
        Route("/", homepage),
        Route("/viewer/{file_path:path}", viewer_page),
        Mount("/api", app=api_router),
        Mount("/ws", app=websocket_router),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ]

    middleware = [
        (CORSMiddleware, [], {"allow_origins": ["*"]}),
    ]

    if debug or settings.debug:
        middleware.append((RequestLoggingMiddleware, [], {}))

    # Capture settings for closure
    app_settings = settings

    async def on_startup() -> None:
        """Application startup handler."""
        console.print("[bold cyan]🚀 MDViewer Starting...[/bold cyan]")
        console.print(f"[cyan]📁[/cyan] Watching: {app_settings.base_dir}")

        loop = asyncio.get_event_loop()

        async def handle_file_change(event_type: str, file_path: Path) -> None:
            """Handle file system changes."""
            console.print(
                f"[yellow]📝[/yellow] File {event_type}: "
                f"{file_path.relative_to(app_settings.base_dir)}"
            )
            await broadcast_file_update(event_type, file_path)

        file_watcher = create_file_watcher(
            watch_path=app_settings.base_dir, callback=handle_file_change, loop=loop
        )

        if file_watcher:
            try:
                file_watcher.start()
                new_app.state.file_watcher = file_watcher
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to start file watcher: {e}")

    async def on_shutdown() -> None:
        """Application shutdown handler."""
        console.print("[bold yellow]🛑 MDViewer Shutting down...[/bold yellow]")
        if hasattr(new_app.state, "file_watcher") and new_app.state.file_watcher:
            new_app.state.file_watcher.stop()

    new_app = Starlette(
        debug=debug or settings.debug,
        routes=routes,
        middleware=middleware,
        on_startup=[on_startup],
        on_shutdown=[on_shutdown],
    )

    new_app.state.file_watcher = None
    new_app.state.settings = settings

    return new_app


app = create_app()


def run_server(
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    base_dir: Optional[Path] = None,
    open_browser_flag: bool = True,
) -> None:
    """Run the mdviewer server.

    Args:
        host: Server host address
        port: Server port (0 or None for auto-detect)
        base_dir: Base directory to scan
        open_browser_flag: Whether to open browser automatically

    Example:
        >>> run_server(port=8000, base_dir=Path("."))
    """
    import uvicorn
    import app.config as config_module

    if base_dir:
        config_module.settings = get_settings(base_dir)

    global settings, app
    settings = config_module.settings
    app = create_app(base_dir=base_dir)

    port = port or settings.port
    if port == 0:
        port = find_available_port()

    console.print("\n[bold green]╔═════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║      MDViewer - Markdown Viewer     ║[/bold green]")
    console.print("[bold green]╚═════════════════════════════════════╝[/bold green]\n")

    console.print(f"[cyan]🌐 Server:[/cyan]  http://{host}:{port}")
    console.print(f"[cyan]📁 Watching:[/cyan] {settings.base_dir}\n")

    if open_browser_flag and settings.auto_open_browser:
        import threading

        def open_browser_delayed():
            """Open browser after server starts."""
            import time

            time.sleep(1.5)
            open_browser(host, port, delay=0)

        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if settings.debug else "warning",
    )


if __name__ == "__main__":
    import sys

    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    run_server(base_dir=base_dir)
