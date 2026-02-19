"""REST API routes for mdviewer application.

This module defines HTTP endpoints for file browsing,
content retrieval, and search functionality.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Router
from starlette.templating import Jinja2Templates

from app.models import (
    FileListResponse,
    FileContentResponse,
    MarkdownFile,
    SearchQuery,
    SearchResult,
)
from app.services import markdown_renderer
from app.utils import scan_markdown_files, html_cache

templates = Jinja2Templates(directory="templates")


async def list_files(request) -> JSONResponse:
    """Get list of all markdown files.

    Args:
        request: Starlette request object

    Returns:
        JSONResponse: List of files with metadata
    """
    start_time = time.time()
    app_settings = request.app.state.settings

    try:
        files = scan_markdown_files(app_settings.base_dir)

        response = FileListResponse(
            files=files,
            total_count=len(files),
            base_dir=str(app_settings.base_dir),
            scan_time=time.time() - start_time,
        )

        return JSONResponse(response.model_dump(mode="json"))

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_file_content(request) -> JSONResponse:
    """Get file content and metadata.

    Args:
        request: Starlette request object with file_path parameter

    Returns:
        JSONResponse: File content and metadata
    """
    app_settings = request.app.state.settings
    file_path_str = request.path_params["file_path"]
    file_path = app_settings.base_dir / file_path_str

    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    if not file_path.is_relative_to(app_settings.base_dir):
        return JSONResponse({"error": "Access denied"}, status_code=403)

    try:
        stat = file_path.stat()
        markdown_file = MarkdownFile(
            path=file_path,
            relative_path=file_path_str,
            filename=file_path.name,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            preview=None,
        )

        raw_content = file_path.read_text(encoding="utf-8")
        html_content = markdown_renderer.render_file(file_path)

        response = FileContentResponse(
            file=markdown_file,
            raw_content=raw_content,
            html_content=html_content,
            cached=html_cache.get(file_path) is not None,
        )

        return JSONResponse(response.model_dump(mode="json"))

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def search_files(request) -> JSONResponse:
    """Search for content in markdown files.

    Args:
        request: Starlette request object with search query

    Returns:
        JSONResponse: Search results
    """
    try:
        app_settings = request.app.state.settings
        data = await request.json()
        query = SearchQuery(**data)

        files = scan_markdown_files(app_settings.base_dir)
        results = []

        for md_file in files[: query.limit]:
            try:
                content = md_file.path.read_text(encoding="utf-8")

                if not query.case_sensitive:
                    search_content = content.lower()
                    search_query = query.query.lower()
                else:
                    search_content = content
                    search_query = query.query

                if search_query in search_content:
                    matches = _extract_matches(
                        content, query.query, query.case_sensitive
                    )

                    results.append(
                        SearchResult(
                            file=md_file, matches=matches, match_count=len(matches)
                        )
                    )

            except Exception:
                continue

        return JSONResponse([r.model_dump(mode="json") for r in results])

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_cache_stats(request) -> JSONResponse:
    """Get cache statistics.

    Args:
        request: Starlette request object

    Returns:
        JSONResponse: Cache statistics
    """
    stats = html_cache.stats()
    return JSONResponse(stats)


async def clear_cache(request) -> JSONResponse:
    """Clear cache.

    Args:
        request: Starlette request object

    Returns:
        JSONResponse: Success message
    """
    html_cache.clear()
    return JSONResponse({"status": "cache cleared"})


def _extract_matches(
    content: str, query: str, case_sensitive: bool
) -> list[dict[str, str]]:
    """Extract matching lines with context.

    Args:
        content: File content
        query: Search query
        case_sensitive: Case sensitive flag

    Returns:
        list: Matching lines with context
    """
    matches = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        search_line = line if case_sensitive else line.lower()
        search_query = query if case_sensitive else query.lower()

        if search_query in search_line:
            start = max(0, i - 2)
            end = min(len(lines), i + 3)

            matches.append(
                {
                    "line_number": i + 1,
                    "line": line,
                    "context": "\n".join(lines[start:end]),
                }
            )

    return matches


def create_api_router() -> Router:
    """Create and configure API router.

    Returns:
        Router: Configured Starlette router

    Example:
        >>> router = create_api_router()
        >>> app.mount('/api', router)
    """
    router = Router()

    router.add_route("/files", list_files)
    router.add_route("/files/{file_path:path}", get_file_content)
    router.add_route("/search", search_files, methods=["POST"])
    router.add_route("/cache/stats", get_cache_stats)
    router.add_route("/cache", clear_cache, methods=["DELETE"])

    return router


api_router = create_api_router()
