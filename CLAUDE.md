# CLAUDE.md — brain3-mcp
### Project Flux Meridian · MCP Integration Layer · L Melton

---

## What This Project Is

`brain3-mcp` is the Claude integration layer for BRAIN 3.0. It is a Python MCP (Model Context Protocol) server that exposes the BRAIN 3.0 REST API as a set of tools Claude can call through conversation.

This is not the core product. The core product is `brain3`. This repo is an optional integration layer — BRAIN 3.0 runs and functions without it. The MCP makes Claude a partner in the system.

**The relationship:**
```
Claude Desktop / Claude App
        ↓ stdio
   brain3-mcp (this repo)
        ↓ HTTP
   brain3 FastAPI (localhost or TrueNAS IP)
        ↓
   PostgreSQL
```

This repo should always be developed alongside `brain3`. Both repos live in the same parent `_DEVELOPMENT` folder. Always read the root `_DEVELOPMENT/CLAUDE.md` before starting work here.

---

## Tech Stack

- **Language:** Python 3.12+
- **MCP SDK:** Anthropic Python MCP SDK (`mcp` package)
- **Transport:** stdio — runs as a subprocess of the Claude client. No network ports.
- **HTTP client:** `httpx` for async requests to the BRAIN 3.0 API
- **Config:** Environment variable or `config.json` for API base URL

---

## Project Structure

```
brain3-mcp/
├── CLAUDE.md              ← You are here
├── README.md              ← Setup, config, and full tool reference
├── mcp/                   ← MCP server package
│   ├── server.py          ← All tool definitions and MCP server (monolith)
│   ├── client.py          ← HTTP client wrapper for the BRAIN API
│   ├── validation.py      ← Input validation helpers
│   └── requirements.txt   ← Python dependencies
├── docs/                  ← Design documents and ticket specs
└── LICENSE
```

> **Architecture note:** The MCP server is a single-file monolith (`server.py`) by design in v1.0.0. All tool definitions — CRUD for every entity, tag management, routine operations, and reporting — live in one file. This is a deliberate Phase 1 decision: the 1:1 tool mapping doesn't benefit from modular separation yet. Phase 2 may introduce composite tools (e.g., "complete routine + log activity + check in" as a single operation), which could justify splitting into per-entity modules.

---

## Core Design Principles

### 1:1 Tool Mapping

Phase 1 is a thin mapping layer. One MCP tool per API endpoint. No higher-level "smart" tools yet — those come in Phase 2 based on real usage patterns. Claude's intelligence handles the reasoning. The MCP just provides access.

### Tool Naming Convention

`verb_entity` format. Lowercase, underscore separated.

```
create_domain    list_domains     get_domain
update_domain    delete_domain
create_task      list_tasks       get_task
complete_routine tag_task         untag_task
```

### Tool Descriptions Are Written for Claude

Tool descriptions are not dry API docs. They are guidance for a partner. Write them as you would explain the tool to someone who will decide when and why to use it.

**Good:** `"List tasks with composable filters. Use to find tasks matching the user's current energy, context, or cognitive capacity. All filter parameters are optional and combine with AND logic."`

**Bad:** `"GET /api/tasks endpoint wrapper."`

### Stateless

The MCP server is stateless. All state lives in the BRAIN 3.0 database. The MCP server makes HTTP requests and returns responses. Nothing is stored locally.

### Error Handling Philosophy

Three distinct error types — handle each differently:

- **API returned an error** — pass through the error message from the API response. Don't swallow it.
- **API unreachable** — return a clear message: "Cannot reach BRAIN 3.0 API at {url}. Is the server running?"
- **Invalid tool parameters** — return a validation error before making the HTTP request.

Never crash on an API error. Always return a meaningful message to Claude.

---

## Configuration

The API base URL is configurable. Default: `http://localhost:8000`

Override via environment variable: `BRAIN3_API_URL=http://192.168.1.x:8000`

Phase 3 will add API key authentication. The HTTP client layer is designed so adding an `Authorization` header is a one-line change. Do not implement auth now — just keep the client layer clean enough that it's obvious where to add it.

---

## Git Workflow

Same as all Flux Meridian projects. Read `_DEVELOPMENT/CLAUDE.md` for full details.

```
main          ← production only
  └── develop ← integration branch
        └── feature/TICKET-XX-short-description
```

Conventional commits, ticket references, PR template filled out completely.

This repo uses its own issue tracker (`WilliM233/brain3-mcp/issues`). If you find something wrong in `brain3` while working here, file it in the `brain3` issue tracker, not here.

---

## Compatibility

The MCP server must stay in sync with the `brain3` API. When `brain3` adds or changes endpoints, the MCP needs a corresponding update.

Document the compatible `brain3` version in `README.md`. Format:

```
Compatible with: brain3 v1.0.0+
```

---

## What L Cares About Here

The MCP is L's primary interface with BRAIN until the Phase 3 UI exists. That means:

- Tool descriptions have to be good enough that Claude uses the right tool without being explicitly told to
- Error messages have to be clear enough that L understands what went wrong without reading logs
- The full conversation loop — "what tasks do I have that match my current energy?" → `list_tasks` with filters → response — has to feel natural, not like operating a CLI through chat

If the tool descriptions are bad, Claude will misuse the tools or ask clarifying questions that break the flow. That friction is the failure mode to design against.

---

## Settled Decisions

- **Transport:** stdio only. No HTTP server, no WebSocket.
- **Phase 1 scope:** 1:1 tool mapping only. No composite tools, no smart routing.
- **Auth:** Deferred to Phase 3. Design the HTTP client to make it easy to add.
- **Language:** Python. Matches `brain3` stack.
- **No local state:** Stateless server. Everything lives in the API.

---

*brain3-mcp CLAUDE.md · Version 1.0*
*Project Flux Meridian · L Melton · March 2026*
