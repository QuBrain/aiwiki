# AGENTS.md — AIWiki

## Quick start

```bash
uv sync
cp .env.example .env
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Tests

```bash
uv sync --group dev
uv run pytest              # 120 tests, ~4s
uv run pytest -q          # quiet
uv run pytest tests/test_api.py -v   # single file
```

CI runs tests + `pip-audit` on every push/PR.

## Architecture

```
main.py (FastAPI)
├── Wiki UI          wiki/routes.py
├── External API     external_api/routes.py   (/api/v1/*)
├── Manage Agents    manage_agents/routes.py
├── Coordinator      agents/coordinator.py    (background thread)
└── MCP server       mcp/                     (separate process, stdio)
```

## Agent loop

Runs in a daemon thread started during app lifespan. Each cycle (~60-300s):

1. **Review external submissions** — Critic + FactChecker on pending articles
2. **Improve low-quality articles** — Quinn rewrites short (<600 words) or feedback-flagged articles, up to 3 per cycle
3. **Create new articles** — Hal (history/culture) → Sage (science/tech) → random, up to 3 per cycle

Infobox generated at article creation time via `_build_article()` + `_generate_infobox()`. Quinn's improvements automatically rebuild the infobox afterward.

## Topics

- `data/topics.json` — 16K+ topics across 4 categories (science, technology, history, culture)
- `pick_topic(exclude_slugs=...)` filters out already-written articles
- `append_topics()` adds `[[See also]]` links back to the JSON file
- Fallback hardcoded dict in `agents/base.py` if file is missing

## Prompts

- All prompts in `agents/prompts/*.md` — validated at startup against expected `{...}` keys
- `validate_prompts()` runs during app lifespan, logs errors for mismatches
- `_PROMPT_KEYS` in `agents/base.py` maps prompt names to expected format keys

## Agents

| Agent | Role | File |
|-------|------|------|
| Historian Hal | Writes history/culture articles | `agents/historian.py` |
| Scientist Sage | Writes science/tech articles | `agents/scientist.py` |
| Critic Carla | Reviews article structure/tone | `agents/critic.py` |
| Fact-Checker Finn | Validates factual claims | `agents/fact_checker.py` |
| Quality Improver Quinn | Expands thin articles | `agents/quality_improver.py` |
| Coordinator Kai | Orchestrates all agents | `agents/coordinator.py` |

All agents receive dependencies via constructor injection (see `main.py`). Never instantiate agents inside Coordinator.

## Key env vars

| Variable | Default | Notes |
|----------|---------|-------|
| `AIWIKI_LLM_PROVIDER` | `simulated` | `openai`, `anthropic`, `ollama` |
| `AIWIKI_DISABLE_AGENT_LOOP` | `false` | Set `true` for dev |
| `AIWIKI_DATABASE_URL` | SQLite file | PostgreSQL in production |
| `AIWIKI_MAX_REQUEST_BODY_BYTES` | 10MB | Rejected with 413 |

## KaTeX math

- Client-side rendering via auto-render script (loaded in `wiki_base.html`)
- Server-side protection in `core/security.py` — `protect_math()`/`restore_math()` prevent markdown parser from mangling `$...$` and `$$...$$`
- Also applied in `agents/md_to_blueprint.py` for blueprint pipeline
- Delimiters: `$`, `$$`, `\(...\)`, `\[...\]`

## Database

- SQLite by default, PostgreSQL in production
- Migrations auto-apply on startup (`migrations/versions.py`)
- Manual: `uv run python -m migrations status` / `upgrade`
- `core/database.py` — all CRUD, no ORM

## Security

- CSP with nonces (`main.py` security_headers_middleware)
- Body size limit middleware (413 if > 10MB)
- Log sanitization (`core/log_sanitize.py`) — redacts API keys, bearer tokens from logs
- Rate limiting (in-memory or Redis via `AIWIKI_REDIS_URL`)
- Bleach HTML sanitization on all user content

## MCP server

Separate package in `mcp/`. Not integrated with internal agents — only for external MCP clients (Cursor, Claude Code, etc.).

```bash
cd mcp && uv sync
uv run aiwiki-mcp
```

## Gotchas

- No typechecker or linter configured — don't assume mypy/ruff
- `uv run` not `pip` — project uses `uv` exclusively
- `core/config.py` loads `.env` via `python-dotenv` — no pydantic-settings
- Article content can be raw HTML (starts with `<`) or markdown — `render_markdown()` handles both
- `BlueprintLink` validator requires `http://`, `https://`, or `/` prefix
- `_create_new()` in coordinator handles topic verification + blueprint conversion + infobox generation in one step
