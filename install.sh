#!/usr/bin/env bash

set -e

# ANSI colors
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
GRAY='\033[1;90m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${CYAN}"
echo "  ████████  ██████  ██████   ██████ "
echo "     ██    ██    ██ ██   ██ ██    ██"
echo "     ██    ██    ██ ██████  ██    ██"
echo "     ██    ██    ██ ██      ██    ██"
echo "     ██     ██████  ██       ██████ "
echo -e "${NC}"
echo -e " ${CYAN}●${NC} ${BOLD}Topo${NC} ${GRAY}is digging deeper 🦡 🦡 🦡${NC}\n"

# 1. Check prerequisites
echo -e "${CYAN}☉ Checking prerequisites...${NC}"
command -v git >/dev/null 2>&1 || { echo -e "  ${RED}✗ Error: git is required but not installed.${NC}"; exit 1; }
echo -e "  ${GREEN}✓ git installed${NC}"

command -v python3 >/dev/null 2>&1 || { echo -e "  ${RED}✗ Error: python3 is required but not installed.${NC}"; exit 1; }
echo -e "  ${GREEN}✓ python3 installed${NC}"

# 2. Define paths
INSTALL_DIR="$HOME/.topo"
REPO_URL="https://github.com/Jesencloud/Topo.git"

# 3. Clone or update repository
echo -e "\n${CYAN}☉ Fetching Topo...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${GRAY}↺ Updating Topo in ${INSTALL_DIR}...${NC}"
    cd "$INSTALL_DIR"
    # To keep things clean, we reset and pull
    git fetch --quiet --depth 1 origin main
    git reset --hard origin/main --quiet
else
    echo -e "  ${GRAY}↓ Downloading Topo (Production Build)...${NC}"
    git clone --quiet --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

# 4. Clean up non-runtime artifacts (keep it lean and legal)
echo -e "  ${GRAY}🧹 Refining installation directory...${NC}"
cd "$INSTALL_DIR"

# Detect architecture for binary cleanup
ARCH=$(uname -m)
BIN_DIR="src/core/bin"

# If we only have the generic one, treat it as x86_64 (our current default)
if [ -f "$BIN_DIR/topo-core" ] && [ ! -f "$BIN_DIR/topo-core-x86_64" ]; then
    mv "$BIN_DIR/topo-core" "$BIN_DIR/topo-core-x86_64"
fi

if [[ "$ARCH" == "x86_64" ]]; then
    echo -e "  ${GRAY}Detected x86_64, removing ARM64 binaries...${NC}"
    rm -f "$BIN_DIR/topo-core-aarch64"
elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
    echo -e "  ${GRAY}Detected ARM64, removing x86_64 binaries...${NC}"
    rm -f "$BIN_DIR/topo-core-x86_64"
fi

# Keep LICENSE for compliance, but remove everything else non-essential
rm -rf tests/ daily_report.md pytest.ini topo.py .gitignore README.md topo-core/

# 5. Run the linking script
echo -e "\n${CYAN}☉ Configuring system...${NC}"
chmod +x topo
./topo link

# Note: The ./topo link command already prints the success message.
echo -e "\n${GRAY}Note: If you want to uninstall later, run '${NC}topo remove${GRAY}'${NC}"
