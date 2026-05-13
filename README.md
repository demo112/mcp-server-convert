# mcp-server-convert

A lightweight [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that converts documents to Markdown. Supports PDF, DOCX, HTML, EPUB, CSV, JSON, and plain text files.

Perfect for AI agents that need to ingest and understand document content.

## Features

- 📄 **Multi-format support**: PDF, DOCX, HTML, EPUB, CSV, JSON, images (via OCR), and plain text
- 🔧 **6 MCP tools**: `convert_file`, `convert_url`, `list_supported_formats`, `batch_convert`, `extract_metadata`, `convert_directory`
- 🐍 **Zero external dependencies for core**: Uses Python standard library + `markdownify` for HTML
- ⚡ **Fast**: In-memory processing, no temp files
- 🐳 **Docker-ready**: Single Dockerfile, one command deploy

## Quick Start

### Install & Run

```bash
# Clone
git clone https://github.com/demo112/mcp-server-convert.git
cd mcp-server-convert

# Install dependencies
pip install -r requirements.txt

# Run
python -m mcp_server_convert
```

### Configure in Claude Code

Add to your MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "convert": {
      "command": "python",
      "args": ["-m", "mcp_server_convert"],
      "cwd": "/path/to/mcp-server-convert"
    }
  }
}
```

### Docker

```bash
docker build -t mcp-server-convert .
docker run -i --rm mcp-server-convert
```

### Configure with Docker

```json
{
  "mcpServers": {
    "convert": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "/path/to/files:/data", "mcp-server-convert"]
    }
  }
}
```

## Tools

### `convert_file`
Convert a local file to Markdown.

**Parameters:**
- `file_path` (string, required): Absolute path to the file
- `max_length` (int, optional): Maximum output length in chars (default: 50000)

### `convert_url`
Fetch a URL and convert its content to Markdown.

**Parameters:**
- `url` (string, required): URL to fetch and convert
- `max_length` (int, optional): Maximum output length in chars (default: 50000)

### `batch_convert`
Convert multiple files at once.

**Parameters:**
- `file_paths` (array of strings, required): List of file paths
- `max_length_per_file` (int, optional): Max length per file (default: 50000)

### `convert_directory`
Convert all supported files in a directory.

**Parameters:**
- `dir_path` (string, required): Path to directory
- `recursive` (bool, optional): Include subdirectories (default: true)
- `max_files` (int, optional): Maximum files to convert (default: 20)

### `extract_metadata`
Extract metadata from a file without full conversion.

**Parameters:**
- `file_path` (string, required): Path to the file

### `list_supported_formats`
List all supported file extensions and their conversion methods.

## Supported Formats

| Format | Extension | Method |
|--------|-----------|--------|
| PDF | `.pdf` | PyMuPDF (fitz) |
| Word | `.docx` | python-docx |
| HTML | `.html`, `.htm` | markdownify |
| EPUB | `.epub` | ebooklib |
| CSV | `.csv` | pandas → markdown table |
| JSON | `.json` | Formatted markdown code block |
| XML | `.xml` | xmltodict → markdown |
| Excel | `.xlsx` | openpyxl → markdown table |
| PowerPoint | `.pptx` | python-pptx → markdown slides |
| Text | `.txt`, `.md`, `.rst`, `.log` | Direct passthrough |
| Images | `.png`, `.jpg` | pytesseract OCR (if available) |

## Support

If this tool helps your workflow, consider supporting its development:

- **GitHub Sponsors**: [Sponsor via Liberapay](https://liberapay.com/yunduai/)
- **ETH**: `0xddD9f45e14c92846f47C1c1A4431aC2b41D87273`

## License

MIT
