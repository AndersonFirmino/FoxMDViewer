#!/bin/bash

# MDViewer Installation Script
# This script installs mdviewer and sets up the 'mdv' command

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/anderson/Documentos/Coding/mdviewer"
ALIAS_FILE="$HOME/.zsh_aliases"

echo -e "${CYAN}╔═════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   MDViewer Installation Script      ║${NC}"
echo -e "${CYAN}╚═════════════════════════════════════╝${NC}"
echo ""

# Check if already in project directory
if [ ! -f "$PROJECT_DIR/mdv" ]; then
    echo -e "${RED}✗ Error: MDViewer not found at $PROJECT_DIR${NC}"
    echo -e "${YELLOW}  Please ensure the project is at: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

echo -e "${CYAN}→ Step 1/5: Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

echo ""
echo -e "${CYAN}→ Step 2/5: Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

echo ""
echo -e "${CYAN}→ Step 3/5: Installing dependencies...${NC}"
source venv/bin/activate

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}→ Step 4/5: Setting up 'mdv' command...${NC}"
chmod +x mdv

# Create wrapper script
WRAPPER_SCRIPT="$PROJECT_DIR/mdv-wrapper.sh"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# MDViewer wrapper script

PROJECT_DIR="/home/anderson/Documentos/Coding/mdviewer"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Run mdviewer
cd "$PROJECT_DIR"
python mdv "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"

echo -e "${GREEN}✓ Wrapper script created${NC}"

echo ""
echo -e "${CYAN}→ Step 5/5: Adding alias to ~/.zsh_aliases...${NC}"

# Check if alias already exists
if grep -q "alias mdv=" "$ALIAS_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Alias 'mdv' already exists in $ALIAS_FILE${NC}"
    
    # Backup and update
    cp "$ALIAS_FILE" "$ALIAS_FILE.backup"
    sed -i '/alias mdv=/d' "$ALIAS_FILE"
    echo -e "${GREEN}✓ Old alias removed (backup created)${NC}"
fi

# Add new alias
echo "" >> "$ALIAS_FILE"
echo "# MDViewer - Markdown Viewer" >> "$ALIAS_FILE"
echo "alias mdv='$WRAPPER_SCRIPT'" >> "$ALIAS_FILE"

echo -e "${GREEN}✓ Alias added to $ALIAS_FILE${NC}"

echo ""
echo -e "${GREEN}╔═════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Installation Complete! 🎉       ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}To start using mdv:${NC}"
echo -e "  ${YELLOW}1.${NC} Restart your terminal or run: ${CYAN}source ~/.zshrc${NC}"
echo -e "  ${YELLOW}2.${NC} Navigate to a directory with markdown files"
echo -e "  ${YELLOW}3.${NC} Run: ${CYAN}mdv${NC}"
echo ""
echo -e "${CYAN}Usage examples:${NC}"
echo -e "  ${CYAN}mdv${NC}              # Start in current directory"
echo -e "  ${CYAN}mdv ~/Documents${NC}  # Start in specific directory"
echo -e "  ${CYAN}mdv --port 8080${NC}  # Use specific port"
echo -e "  ${CYAN}mdv --no-browser${NC} # Don't open browser"
echo ""
echo -e "${CYAN}Options:${NC}"
echo -e "  ${YELLOW}-h, --help${NC}      Show help message"
echo -e "  ${YELLOW}-p, --port PORT${NC} Specify port"
echo -e "  ${YELLOW}--no-browser${NC}    Don't open browser"
echo -e "  ${YELLOW}--debug${NC}         Enable debug mode"
echo ""
echo -e "${GREEN}Happy reading! 📚${NC}"
echo ""

deactivate
