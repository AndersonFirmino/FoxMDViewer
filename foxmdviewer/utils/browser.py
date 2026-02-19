"""Browser utility for automatic browser opening.

This module provides cross-platform functionality to automatically
open the default web browser with the application URL.
"""

import webbrowser
from time import sleep
from typing import Optional
from urllib.parse import urljoin

from rich.console import Console

console = Console()


class BrowserOpener:
    """Opens web browser with the application URL.

    This class handles automatic browser opening with:
    - Cross-platform support (Linux, macOS, Windows)
    - Configurable delay before opening
    - Multiple browser fallback options
    - Error handling for headless environments

    Attributes:
        host: Server host address
        port: Server port number
        delay: Delay in seconds before opening browser
        preferred_browser: Preferred browser name (optional)

    Example:
        >>> opener = BrowserOpener("127.0.0.1", 8000)
        >>> opener.open_browser()
    """

    def __init__(
        self,
        host: str,
        port: int,
        delay: float = 1.5,
        preferred_browser: Optional[str] = None,
    ) -> None:
        """Initialize browser opener.

        Args:
            host: Server host address
            port: Server port number
            delay: Delay before opening (default: 1.5s)
            preferred_browser: Browser name (e.g., 'firefox', 'chrome')

        Raises:
            ValueError: If port is invalid
        """
        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port: {port}")

        self.host = host
        self.port = port
        self.delay = delay
        self.preferred_browser = preferred_browser
        self.url = self._build_url()

    def _build_url(self) -> str:
        """Build full URL from host and port.

        Returns:
            str: Complete URL string
        """
        return f"http://{self.host}:{self.port}"

    def open_browser(self) -> bool:
        """Open browser with application URL.

        Returns:
            bool: True if browser opened successfully, False otherwise

        Example:
            >>> opener = BrowserOpener("127.0.0.1", 8000)
            >>> success = opener.open_browser()
        """
        if self.delay > 0:
            console.print(f"[cyan]⏳[/cyan] Opening browser in {self.delay}s...")
            sleep(self.delay)

        try:
            if self.preferred_browser:
                return self._open_specific_browser()
            else:
                return self._open_default_browser()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to open browser: {e}")
            console.print(f"[yellow]ℹ[/yellow]  Please open manually: {self.url}")
            return False

    def _open_default_browser(self) -> bool:
        """Open default system browser.

        Returns:
            bool: True if successful, False otherwise
        """
        console.print(f"[green]🌐[/green] Opening browser: {self.url}")
        success = webbrowser.open(self.url)

        if success:
            console.print("[green]✓[/green] Browser opened successfully")
        else:
            console.print(
                "[yellow]⚠[/yellow]  Browser opened but may not be in foreground"
            )

        return success

    def _open_specific_browser(self) -> bool:
        """Open specific browser by name.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            browser = webbrowser.get(self.preferred_browser)
            console.print(
                f"[green]🌐[/green] Opening {self.preferred_browser}: {self.url}"
            )
            success = browser.open(self.url)

            if success:
                console.print("[green]✓[/green] Browser opened successfully")

            return success
        except webbrowser.Error:
            console.print(
                f"[yellow]⚠[/yellow]  Browser '{self.preferred_browser}' not found, "
                f"using default"
            )
            return self._open_default_browser()


def open_browser(
    host: str, port: int, delay: float = 1.5, browser: Optional[str] = None
) -> bool:
    """Convenience function to open browser.

    Args:
        host: Server host address
        port: Server port number
        delay: Delay before opening
        browser: Preferred browser name

    Returns:
        bool: True if successful, False otherwise

    Example:
        >>> success = open_browser("127.0.0.1", 8000)
    """
    opener = BrowserOpener(host, port, delay, browser)
    return opener.open_browser()
