#!/usr/bin/env bash
# ==============================================================================
# AI Chemistry Video Request Service - 1-Minute Reviewer Reproduction Script
# ==============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}==============================================================================${NC}"
echo -e "${BOLD}${BLUE}   AI Chemistry Video Request Service - Reviewer Reproduction Flow           ${NC}"
echo -e "${BOLD}${BLUE}==============================================================================${NC}"

# 1. Check System Prerequisites
echo -e "\n${BOLD}[1/4] Checking System Prerequisites...${NC}"

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[!] Error: ffmpeg is not installed on PATH.${NC}"
    echo "    macOS: brew install ffmpeg"
    echo "    Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ffmpeg"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} ffmpeg found: $(ffmpeg -version | head -n1)"

if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[!] 'uv' package manager not found. Installing uv via Astral script...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo -e "  ${GREEN}✓${NC} uv found: $(uv --version)"

# 2. Virtual Environment & Dependencies
echo -e "\n${BOLD}[2/4] Setting up Python 3.12 Virtual Environment & Installing Dependencies...${NC}"
if [ ! -d ".venv" ]; then
    uv venv --python 3.12 .venv
fi
uv pip install -e ".[dev]"
echo -e "  ${GREEN}✓${NC} Virtual environment configured (.venv)"

# 3. Environment Configuration
echo -e "\n${BOLD}[3/4] Checking Environment Configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} Created .env from .env.example"
else
    echo -e "  ${GREEN}✓${NC} Existing .env found"
fi

if [ -n "${GEMINI_API_KEY:-}" ]; then
    echo -e "  ${GREEN}✓${NC} GEMINI_API_KEY detected in environment (Gemini 3.5 Flash Lite enabled)"
elif grep -E "^GEMINI_API_KEY=AI" .env >/dev/null 2>&1 || grep -E "^GEMINI_API_KEY=AQ" .env >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} GEMINI_API_KEY configured in .env (Gemini 3.5 Flash Lite enabled)"
else
    echo -e "  ${YELLOW}[!] Note: GEMINI_API_KEY is required to generate new videos with Gemini 3.5 Flash Lite.${NC}"
    echo -e "      Set your key in .env or export GEMINI_API_KEY=..."
fi

# 4. Run Test Suite
echo -e "\n${BOLD}[4/4] Running Automated Test Suite (Unit, Integration, E2E)...${NC}"
uv run --python .venv pytest -v

echo -e "\n${BOLD}${GREEN}==============================================================================${NC}"
echo -e "${BOLD}${GREEN}   Reproduction Verification Complete! All tests passed successfully.        ${NC}"
echo -e "${BOLD}${GREEN}==============================================================================${NC}"
echo -e "\nNext steps for the reviewer:"
echo -e "  1. Start the FastAPI backend server:"
echo -e "     ${BOLD}uv run --python .venv uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload${NC}"
echo -e "     or: ${BOLD}make run${NC}"
echo -e "     Interactive API documentation will be available at: ${BLUE}http://localhost:8000/docs${NC}"
echo -e ""
echo -e "  2. Test video generation via the live REST API:"
echo -e "     ${BOLD}uv run --python .venv python -m scripts.generate_via_api${NC}"
echo -e "     or: ${BOLD}make demo${NC}"
echo -e ""
echo -e "  3. Inspect committed sample videos in:"
echo -e "     ${BLUE}artifacts/videos/${NC}"
