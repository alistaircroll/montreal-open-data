# Montreal Open Data — MCP Read Server

A Model Context Protocol server that gives AI agents deterministic, tool-based access to Montréal's 397+ open datasets.

## Quick Start

### Claude Code
```bash
claude mcp add montreal-data python3 mcp/read-server/server.py
```

### Claude Desktop (claude_desktop_config.json)
```json
{
  "mcpServers": {
    "montreal-data": {
      "command": "python3",
      "args": ["/path/to/montreal-open-data/mcp/read-server/server.py"]
    }
  }
}
```

### Cursor / Other MCP clients
```json
{
  "mcpServers": {
    "montreal-data": {
      "command": "python3",
      "args": ["mcp/read-server/server.py"],
      "cwd": "/path/to/montreal-open-data"
    }
  }
}
```

## Requirements

```bash
pip install mcp
```

No API keys needed for core functionality. STM real-time requires free registration (see SETUP.md).

## Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `search_datasets` | Find datasets by keyword (bilingual) | "search for trees" → arbres |
| `query_dataset` | SQL queries against DataStore | GROUP BY borough, CAST for numbers |
| `get_dataset_fields` | Inspect field names/types | Case-sensitive field discovery |
| `get_borough_info` | Look up borough by alias | "downtown" → Ville-Marie |
| `find_nearby` | Records within radius of a point | Trees within 500m of address |
| `bixi_stations` | Real-time BIXI bike availability | Nearest station with bikes |
| `dataset_stats` | Quick stats for a resource | Record count, fields |
| `list_datasets_by_topic` | Browse datasets by category | "crime", "transit", "budget" |
| `health_check` | Test all endpoints | Diagnose connectivity issues |

## Resources

| URI | Description |
|-----|-------------|
| `montreal://boroughs` | All 19 boroughs with codes and coordinates |
| `montreal://catalog-stats` | Catalog summary (dataset count, organizations, tags) |

## Architecture

```
Skills (SKILL.md files)     →  Documentation, context, recipes
MCP Server (this)           →  Deterministic tools, structured output
Scripts (Python)            →  Maintenance, inspection, health checks
Reference (JSON)            →  Cached lookups, offline data
```

The skills teach an agent *how to think* about Montréal data.
The MCP server gives the agent *tools to act* on that knowledge.
Both can be used independently. Together, they're the full system.
