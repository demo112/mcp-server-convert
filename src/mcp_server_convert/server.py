"""MCP server for converting documents to Markdown.

Supports PDF, DOCX, HTML, EPUB, CSV, JSON, XML, XLSX, PPTX, and plain text.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Import converters
from .converters import (
    convert_bytes,
    convert_file_to_markdown,
    get_supported_formats,
    sniff_format,
)

app = Server("mcp-server-convert")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available conversion tools."""
    return [
        Tool(
            name="convert_file",
            description="Convert a local file to Markdown. Supports PDF, DOCX, HTML, EPUB, CSV, JSON, XML, XLSX, PPTX, and plain text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to convert",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum output length in characters (default: 50000)",
                        "default": 50000,
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="convert_url",
            description="Fetch a URL and convert its HTML content to Markdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch and convert",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum output length in characters (default: 50000)",
                        "default": 50000,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="batch_convert",
            description="Convert multiple files to Markdown at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to convert",
                    },
                    "max_length_per_file": {
                        "type": "integer",
                        "description": "Maximum length per file in characters (default: 50000)",
                        "default": 50000,
                    },
                },
                "required": ["file_paths"],
            },
        ),
        Tool(
            name="convert_directory",
            description="Convert all supported files in a directory to Markdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Path to the directory",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Include subdirectories (default: true)",
                        "default": True,
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to convert (default: 20)",
                        "default": 20,
                    },
                },
                "required": ["dir_path"],
            },
        ),
        Tool(
            name="extract_metadata",
            description="Extract metadata from a file (size, type, dates, etc.) without full conversion.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="list_supported_formats",
            description="List all supported file formats and their conversion methods.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    if name == "convert_file":
        file_path = arguments["file_path"]
        max_length = arguments.get("max_length", 50000)

        path = Path(file_path)
        if not path.exists():
            return [TextContent(type="text", text=f"Error: File not found: {file_path}")]
        if not path.is_file():
            return [TextContent(type="text", text=f"Error: Not a file: {file_path}")]

        try:
            result = convert_file_to_markdown(path)
            if len(result) > max_length:
                result = result[:max_length] + "\n\n... (truncated)"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error converting file: {e}")]

    elif name == "convert_url":
        url = arguments["url"]
        max_length = arguments.get("max_length", 50000)

        try:
            import httpx
            from markdownify import markdownify as md

            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                result = md(resp.text)
                if len(result) > max_length:
                    result = result[:max_length] + "\n\n... (truncated)"
                return [TextContent(type="text", text=result)]
        except ImportError:
            return [TextContent(type="text", text="Error: httpx and markdownify required for URL conversion. Install with: pip install 'mcp-server-convert[full]'")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching URL: {e}")]

    elif name == "batch_convert":
        file_paths = arguments["file_paths"]
        max_length = arguments.get("max_length_per_file", 50000)

        results = []
        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                results.append(f"## {fp}\n\nError: File not found\n")
                continue
            try:
                result = convert_file_to_markdown(path)
                if len(result) > max_length:
                    result = result[:max_length] + "\n\n... (truncated)"
                results.append(f"## {path.name}\n\n{result}")
            except Exception as e:
                results.append(f"## {path.name}\n\nError: {e}")

        return [TextContent(type="text", text="\n\n---\n\n".join(results))]

    elif name == "convert_directory":
        dir_path = arguments["dir_path"]
        recursive = arguments.get("recursive", True)
        max_files = arguments.get("max_files", 20)

        dp = Path(dir_path)
        if not dp.exists() or not dp.is_dir():
            return [TextContent(type="text", text=f"Error: Directory not found: {dir_path}")]

        supported = set(get_supported_formats().keys())
        pattern = "**/*" if recursive else "*"
        files = [
            f
            for f in dp.glob(pattern)
            if f.is_file() and f.suffix.lower().lstrip(".") in supported
        ][:max_files]

        if not files:
            return [TextContent(type="text", text=f"No supported files found in {dir_path}")]

        results = []
        for f in files:
            try:
                result = convert_file_to_markdown(f)
                results.append(f"## {f.relative_to(dp)}\n\n{result}")
            except Exception as e:
                results.append(f"## {f.relative_to(dp)}\n\nError: {e}")

        return [TextContent(type="text", text="\n\n---\n\n".join(results))]

    elif name == "extract_metadata":
        file_path = arguments["file_path"]
        path = Path(file_path)

        if not path.exists():
            return [TextContent(type="text", text=f"Error: File not found: {file_path}")]

        stat = path.stat()
        fmt = sniff_format(path)

        meta = {
            "name": path.name,
            "extension": path.suffix,
            "detected_format": fmt,
            "size_bytes": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "modified": _format_time(stat.st_mtime),
            "created": _format_time(stat.st_ctime),
            "is_text": _is_text_file(path),
        }

        return [TextContent(type="text", text=json.dumps(meta, indent=2))]

    elif name == "list_supported_formats":
        formats = get_supported_formats()
        lines = ["# Supported Formats\n"]
        for ext, info in sorted(formats.items()):
            lines.append(f"- **.{ext}** — {info['description']} (method: {info['method']})")
        return [TextContent(type="text", text="\n".join(lines))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _format_time(timestamp: float) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).isoformat()


def _is_text_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" not in chunk
    except Exception:
        return False


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
