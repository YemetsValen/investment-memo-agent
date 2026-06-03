# Investment Memo Agent

AI-powered investment due-diligence assistant built with **LangGraph**, **FastAPI**, and **MCP**.

A multi-agent pipeline that analyzes any public company by ticker: collects financial data, produces an investment thesis, evaluates risks, and generates a structured investment memo — with a **human-in-the-loop REVIEW queue** for low-confidence or high-risk outputs.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Researcher  │───▶│   Analyst   │───▶│    Risk     │───▶│   Writer    │
│              │    │             │    │             │    │             │
│ • yfinance   │    │ • LLM call  │    │ • Rule-based│    │ • Markdown  │
│ • news feed  │    │ • Thesis    │    │ • LLM qual. │    │ • Report    │
│ • price hist │    │ • Recommend │    │ • Risk flags│    │ • Metrics   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  REVIEW Queue   │
                                    │                 │
                                    │ confidence < θ  │
                                    │ CRITICAL flags  │
                                    │ ≥3 HIGH flags   │
                                    └─────────────────┘
```

### REVIEW Queue Logic

Mirrors the [strict-moderator](https://github.com/YemetsValen/strict-moderator) pattern:

| Trigger | Action |
|---------|--------|
| Confidence < threshold (default 0.7) | → REVIEW queue |
| Any CRITICAL risk flag | → REVIEW queue |
| ≥ 3 HIGH risk flags | → REVIEW queue |
| Otherwise | → Auto-publish (COMPLETED) |

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic v2 |
| Agents | LangGraph (StateGraph) |
| LLM | Anthropic Claude / OpenAI (configurable) |
| Data | yfinance (free, no API key) |
| MCP | `mcp` SDK — tools for Claude Desktop / Cursor |
| Storage | In-memory (swap for SQLite/Postgres) |
| Lint | ruff |
| Tests | pytest + pytest-asyncio |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
# Clone
git clone https://github.com/YemetsValen/investment-memo-agent.git
cd investment-memo-agent

# Install dependencies
uv sync

# Copy env template
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### Run the API

```bash
uv run python -m src.main
# or
uv run memo-api
```

API available at `http://localhost:8000`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Run full analysis pipeline |
| `GET` | `/api/v1/memo/{id}` | Get memo by ID |
| `GET` | `/api/v1/memos` | List all memos |
| `GET` | `/api/v1/review-queue` | Memos pending human review |
| `POST` | `/api/v1/review-queue/{id}/approve` | Approve a review item |
| `POST` | `/api/v1/review-queue/{id}/reject` | Reject a review item |
| `GET` | `/api/v1/health` | Health check |

#### Example: Analyze a Company

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### MCP Server (for Claude Desktop / Cursor)

```bash
uv run memo-mcp
```

Add to your MCP config (`claude_desktop_config.json` or Cursor settings):

```json
{
  "mcpServers": {
    "investment-memo-agent": {
      "command": "uv",
      "args": ["run", "memo-mcp"],
      "cwd": "/path/to/investment-memo-agent"
    }
  }
}
```

**Available MCP tools:**
- `get_financials` — Fetch financial metrics for a ticker
- `generate_memo` — Full multi-agent analysis pipeline
- `screen_company` — Quick rule-based screen (no LLM)
- `list_review_queue` — View pending reviews

### Run Tests

```bash
uv run pytest -v
```

### Run Evals (rule-based risk detection)

```bash
uv run python -m evals.run_evals
```

Evaluates the deterministic risk-detection rules against a 47-company dataset.

### Lint

```bash
uv run ruff check src/ tests/ evals/
```

## Project Structure

```
├── src/
│   ├── main.py              # FastAPI entrypoint
│   ├── config.py             # Settings (env vars)
│   ├── models/
│   │   └── memo.py           # Pydantic models
│   ├── agents/
│   │   ├── graph.py          # LangGraph orchestration
│   │   ├── state.py          # Shared agent state
│   │   ├── researcher.py     # Data collection
│   │   ├── analyst.py        # Investment analysis (LLM)
│   │   ├── risk.py           # Risk assessment (rules + LLM)
│   │   ├── writer.py         # Markdown report generator
│   │   └── llm.py            # LLM factory
│   ├── tools/
│   │   ├── financials.py     # yfinance wrapper
│   │   └── news.py           # News fetcher
│   ├── services/
│   │   ├── storage.py        # In-memory store
│   │   └── review_queue.py   # REVIEW queue logic
│   ├── mcp_server.py         # MCP server
│   └── api/
│       └── routes.py         # FastAPI routes
├── evals/
│   ├── dataset.json          # 47-company eval dataset
│   └── run_evals.py          # Eval runner
├── reports/                   # Generated memo reports
├── tests/                     # pytest suite
├── pyproject.toml
└── .env.example
```

## License

MIT
