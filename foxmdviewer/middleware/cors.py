"""Middleware components for mdviewer application.

This module provides custom middleware for CORS,
authentication, and request processing.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from typing import Callable, Optional


class CORSMiddleware:
    """CORS middleware for cross-origin requests.

    This middleware enables CORS for development and
    production deployments.

    Attributes:
        app: ASGI application
        allow_origins: List of allowed origins
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers

    Example:
        >>> app.add_middleware(
        ...     CORSMiddleware,
        ...     allow_origins=['*']
        ... )
    """

    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Optional[list[str]] = None,
        allow_methods: Optional[list[str]] = None,
        allow_headers: Optional[list[str]] = None,
    ) -> None:
        """Initialize CORS middleware.

        Args:
            app: ASGI application
            allow_origins: Allowed origins (default: ['*'])
            allow_methods: Allowed methods (default: ['*'])
            allow_headers: Allowed headers (default: ['*'])
        """
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Process request with CORS headers.

        Args:
            scope: ASGI scope
            receive: Receive callable
            send: Send callable
        """
        if scope["type"] == "http":

            async def send_wrapper(message: dict) -> None:
                """Add CORS headers to response.

                Args:
                    message: ASGI message
                """
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))

                    if "*" in self.allow_origins:
                        headers[b"access-control-allow-origin"] = b"*"
                    elif scope.get("headers"):
                        origin = dict(scope["headers"]).get(b"origin")
                        if origin and origin.decode() in self.allow_origins:
                            headers[b"access-control-allow-origin"] = origin

                    headers[b"access-control-allow-methods"] = ", ".join(
                        self.allow_methods
                    ).encode()
                    headers[b"access-control-allow-headers"] = ", ".join(
                        self.allow_headers
                    ).encode()

                    message["headers"] = list(headers.items())

                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests.

    This middleware logs all incoming requests with
    method, path, and processing time.

    Attributes:
        app: ASGI application

    Example:
        >>> app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log request.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        from rich.console import Console

        console = Console()

        method = request.method
        path = request.url.path

        console.print(f"[cyan]→[/cyan] {method} {path}")

        response = await call_next(request)

        console.print(
            f"[green]←[/green] {method} {path} [dim]{response.status_code}[/dim]"
        )

        return response
