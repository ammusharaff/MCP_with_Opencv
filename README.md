# MCP_with_Opencv

## Overview

**MCP_with_Opencv** is a Python server that provides advanced image enhancement and processing using OpenCV, accessible via the Model Context Protocol (MCP). It’s designed for easy integration with intelligent platforms, including **Claude Desktop**.

## Features

- Image enhancement (sharpen, denoise, contrast, grayscale, etc.)
- Fast OpenCV backend
- Structured MCP server for automated requests/responses
- Compatible with Claude Desktop and other MCP clients

## Integrating with Claude Desktop

Claude Desktop can interact with this MCP server by sending image data and enhancement prompts. Output images are returned as binary data, ready for direct use or display in Claude Desktop.

**Basic Integration Steps:**

1. **Run MCP_with_Opencv locally:**
python opencv-image-enhancer.py

2. **Configure Claude Desktop to point at your MCP server (e.g., `http://localhost:8080`).**

3. **Send an image and a prompt ("sharpen", "denoise", etc.) through Claude Desktop's MCP connector.**

#### Example Claude Desktop Integration (Python-like pseudo-code):

from mcp.client import MCPClient

client = MCPClient("http://localhost:8080")
with open("input.png", "rb") as f:
img_bytes = f.read()
result = client.call_tool(
"enhance_image",
{"image": {"data": img_bytes, "format": "png"}, "prompt": "denoise"}
)
with open("output.png", "wb") as out_f:
out_f.write(result["enhanced_image"]["data"])

The enhanced image is now ready for display in Claude Desktop

## Installation

1. **Python 3.14 or newer**
2. **Dependencies:**
pip install mcp[cli] opencv-python numpy Pillow


3. **Clone this repo:**
git clone https://github.com/ammusharaff/MCP_with_Opencv.git
cd MCP_with_Opencv


## Usage

- Start the server:
python opencv-image-enhancer.py

- Send a request from Claude Desktop (or any MCP client).

## Project Structure

- `opencv-image-enhancer.py` — main server logic
- `pyproject.toml` — dependencies
- `.python-version` — ensures correct interpreter version
- `.gitignore` — recommended ignores for Python
