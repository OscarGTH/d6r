# How to run?

## Prerequisites

- uv
- k3s running in k3d

## Start MCP server

```bash
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
uv run mcp dev main.py
```
