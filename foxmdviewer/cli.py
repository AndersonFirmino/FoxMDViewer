#!/usr/bin/env python3
"""FoxMDViewer - Command Line Interface."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


@click.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    required=False,
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=None,
    help="Port to run server on (default: auto-detect)",
)
@click.option(
    "--host",
    "-h",
    type=str,
    default="127.0.0.1",
    help="Host to bind server to (default: 127.0.0.1)",
)
@click.option("--no-browser", is_flag=True, help="Do not open browser automatically")
@click.option("--debug", is_flag=True, help="Enable debug mode with auto-reload")
@click.version_option(version="1.0.0", prog_name="mdv")
def main(
    directory: Path, port: Optional[int], host: str, no_browser: bool, debug: bool
) -> None:
    """
    FoxMDViewer - Visualize markdown files in your browser.

    Scans DIRECTORY recursively for .md files and opens a web interface
    for easy navigation, reading, and editing.

    DIRECTORY defaults to current directory if not specified.
    """
    try:
        from foxmdviewer.main import run_server
        from foxmdviewer.config import get_settings

        base_dir = directory.resolve()

        console.print("\n[bold cyan]═════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]      🦊 FoxMDViewer - Markdown Viewer[/bold cyan]")
        console.print("[bold cyan]═════════════════════════════════════[/bold cyan]\n")

        console.print(f"[green]📁 Directory:[/green] {base_dir}")

        if not any(base_dir.rglob("*.md")):
            console.print("[yellow]⚠[/yellow]  No .md files found in this directory")
            console.print("[dim]   Create some markdown files to get started[/dim]\n")

        run_server(
            host=host, port=port, base_dir=base_dir, open_browser_flag=not no_browser
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
