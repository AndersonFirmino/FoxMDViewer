"""Port finder utility for automatic port detection.

This module provides functionality to find available ports
for the server to bind to.
"""

import socket
from typing import Optional

from rich.console import Console

console = Console()


class PortFinder:
    """Finds available ports for server binding.

    This class provides methods to find free ports dynamically,
    avoiding common conflicts with well-known services.

    Attributes:
        start_port: Starting port for search
        max_attempts: Maximum number of ports to try
        preferred_ports: List of preferred ports to try first

    Example:
        >>> finder = PortFinder(start_port=8000)
        >>> port = finder.find_available_port()
        >>> print(f"Using port {port}")
    """

    def __init__(
        self,
        start_port: int = 8000,
        max_attempts: int = 100,
        preferred_ports: Optional[list[int]] = None,
    ) -> None:
        """Initialize port finder.

        Args:
            start_port: Starting port for search (default: 8000)
            max_attempts: Maximum ports to try (default: 100)
            preferred_ports: Preferred ports to try first

        Raises:
            ValueError: If start_port is invalid
        """
        if not (1024 <= start_port <= 65535):
            raise ValueError(f"Invalid port range: {start_port}")

        self.start_port = start_port
        self.max_attempts = max_attempts
        self.preferred_ports = preferred_ports or [8000, 8080, 3000, 5000, 9000]

    def find_available_port(self) -> int:
        """Find an available port for binding.

        Returns:
            int: Available port number

        Raises:
            RuntimeError: If no available port is found

        Example:
            >>> finder = PortFinder()
            >>> port = finder.find_available_port()
        """
        for port in self.preferred_ports:
            if self._is_port_available(port):
                console.print(f"[green]✓[/green] Using preferred port {port}")
                return port

        for offset in range(self.max_attempts):
            port = self.start_port + offset
            if port not in self.preferred_ports and self._is_port_available(port):
                console.print(f"[green]✓[/green] Found available port {port}")
                return port

        raise RuntimeError(
            f"No available port found in range {self.start_port}-"
            f"{self.start_port + self.max_attempts}"
        )

    def _is_port_available(self, port: int, host: str = "127.0.0.1") -> bool:
        """Check if a specific port is available.

        Args:
            port: Port number to check
            host: Host address to bind (default: 127.0.0.1)

        Returns:
            bool: True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0
        except (socket.error, OSError):
            return False


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Convenience function to find an available port.

    Args:
        start_port: Starting port for search
        max_attempts: Maximum ports to try

    Returns:
        int: Available port number

    Raises:
        RuntimeError: If no available port is found

    Example:
        >>> port = find_available_port()
        >>> print(f"Using port {port}")
    """
    finder = PortFinder(start_port=start_port, max_attempts=max_attempts)
    return finder.find_available_port()
