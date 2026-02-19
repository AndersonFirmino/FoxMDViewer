# FoxMDViewer 🦊⛩️

A beautiful, fast, and feature-rich markdown viewer with a Shinto-inspired theme.

## Features

✨ **Auto-detection**: Automatically scans directories for markdown files  
🎨 **Beautiful UI**: Modern, responsive interface with dark/light themes  
⚡ **Real-time Updates**: Live file watching with WebSocket updates  
🔍 **Search**: Full-text search across all markdown files  
✏️ **Inline Editor**: Edit markdown files directly in the browser  
📦 **Cache**: Intelligent HTML caching for fast rendering  
🔌 **WebSocket**: Real-time collaboration support  
🎯 **Zero Configuration**: Works out of the box  

## Installation

### Quick Install

```bash
cd /home/anderson/Documentos/Coding/mdviewer
chmod +x install.sh
./install.sh
```

### Manual Install

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Add alias to ~/.zsh_aliases**:
   ```bash
   echo "alias mdv='/home/anderson/Documentos/Coding/mdviewer/mdv-wrapper.sh'" >> ~/.zsh_aliases
   source ~/.zshrc
   ```

## Usage

### Basic Usage

```bash
# Start in current directory
mdv

# Start in specific directory
mdv /path/to/documents

# Use specific port
mdv --port 8080

# Don't open browser
mdv --no-browser

# Debug mode
mdv --debug
```

### Command Line Options

```
Usage: mdv [OPTIONS] [DIRECTORY]

Options:
  -p, --port INTEGER     Port to run server on (default: auto-detect)
  -h, --host TEXT        Host to bind server to (default: 127.0.0.1)
  --no-browser           Do not open browser automatically
  --debug                Enable debug mode with auto-reload
  --version              Show version and exit
  --help                 Show this message and exit
```

## Architecture

### Project Structure

```
mdviewer/
├── app/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── api/                 # REST API and WebSocket
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   ├── utils/               # Utilities
│   └── middleware/          # Middleware components
├── static/                  # Frontend assets
│   ├── css/
│   └── js/
├── templates/               # HTML templates
├── tests/                   # Test suite
├── mdv                      # Main CLI script
├── install.sh               # Installation script
└── requirements.txt         # Dependencies
```

### Technology Stack

- **Backend**: Starlette + Uvicorn
- **Markdown**: Mistune (GitHub Flavored Markdown)
- **File Watching**: Watchdog
- **Frontend**: Vanilla JS + Tailwind-inspired CSS
- **Real-time**: WebSocket

## Development

### Prerequisites

- Python 3.8+
- pip

### Running in Development Mode

```bash
source venv/bin/activate
python mdv --debug
```

### Running Tests

```bash
pytest tests/
```

## API Reference

### REST Endpoints

- `GET /api/files` - List all markdown files
- `GET /api/files/{path}` - Get file content
- `POST /api/search` - Search files
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache` - Clear cache

### WebSocket

Connect to `ws://localhost:{port}/ws/` for real-time updates.

**Message Types**:
- `ping` / `pong` - Connection keepalive
- `file_update` - File change notification
- `subscribe` - Subscribe to file updates

## Configuration

### Environment Variables

All configuration can be set via environment variables with `MDVIEWER_` prefix:

```bash
export MDVIEWER_HOST=127.0.0.1
export MDVIEWER_PORT=8080
export MDVIEWER_DEBUG=true
export MDVIEWER_AUTO_OPEN_BROWSER=true
export MDVIEWER_CACHE_ENABLED=true
export MDVIEWER_CACHE_TTL=300
export MDVIEWER_WATCH_FILES=true
export MDVIEWER_MAX_FILE_SIZE=10485760
```

## Troubleshooting

### Port Already in Use

If the default port is busy, MDViewer will automatically find an available port, or you can specify one:

```bash
mdv --port 9000
```

### No Files Found

Make sure you're in a directory with `.md` files or specify the correct path:

```bash
mdv /path/to/markdown/files
```

### Browser Doesn't Open

If the browser doesn't open automatically, you can manually open the URL shown in the terminal.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Author

Created by Anderson

---

Happy reading! 📚✨
