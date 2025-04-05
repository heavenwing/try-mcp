# MCP Sample using LM Studio and OpenAI api

This sample reference modelcontextprotocol.io [For Client Developers Quickstart](https://modelcontextprotocol.io/quickstart/client)

## Requirements

- Install LM Studio
- Load model "qwen2.5-7b-instruct-1m" which support tools
- Enable LM Studio OpenAI API Server

## How to run

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate

# Install required packages
uv add mcp openai python-dotenv

python client.py ./server.py

# Input like : 北京时间现在几点？
```

