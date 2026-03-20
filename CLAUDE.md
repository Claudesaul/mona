# Mona - Claude Instructions

AI-powered business data assistant for Monumental Markets. React + FastAPI chat app using Claude Sonnet 4.6 with tool_use to query 5 databases via natural language.

## Commands

```bash
cd backend && python main.py       # Start backend (serves frontend at http://localhost:3000)
cd frontend && npm run dev          # Frontend dev server (hot reload, proxies to backend)
cd frontend && npm run build        # Build frontend (output to dist/, committed to repo)
```

## Architecture

```
User question → Claude API (tool_use) → picks database → writes query → executes → formats answer
```

**Frontend:** React 18 + TypeScript + Tailwind + Framer Motion. Built with Vite. Served as static files by FastAPI.

**Backend:** FastAPI + uvicorn. WebSocket streaming at `/ws/chat`. REST fallback at `/api/chat`.

**AI:** Claude Sonnet 4.6 with 6 tool definitions (5 databases + SharePoint file search). System prompt contains database routing table, schemas, join patterns, and common formulas.

### Connected Databases

| Database | Type | What it has | Connection |
|----------|------|-------------|------------|
| Snowflake | Snowflake SQL (ODBC) | Sales revenue, fulfillment, micro market transactions (47M+ rows) | `SnowflakeDSIIDriver` |
| LightSpeed | SQL Server | Order/pick status, no price data | `10.216.207.32` |
| Level | SQL Server | Warehouse inventory, par levels, purchase orders | `10.216.207.32` |
| OOS | PostgreSQL | Fill rates, OOS tracking, product activity (14-day rolling) | `10.7.6.146:5432` |
| Salesforce | SOQL | Accounts, contacts, tasks, cases, opportunities | `simple-salesforce` |
| SharePoint | File Search | Shared drive files, reports, templates (~9.1K files) | OneDrive sync (local) |

## IMPORTANT Rules

- **LightSpeed has NO price/revenue columns** — use Snowflake for financial questions
- **product_activity has NO date column** — it's a rolling 14-day snapshot, don't filter by date
- **Snowflake date keys are serial integers (days since 1899-12-31), NOT YYYYMMDD** — use VISITDATETIME/SALEDATETIME timestamps for date filtering
- **Snowflake fact tables need dimension joins** for readable names (DIMLOCATION_V, DIMITEM_V, DIMROUTE_V)
- **All queries are read-only** — INSERT/UPDATE/DELETE/DROP are blocked in code
- **Row limits enforced** — TOP 500 (SQL Server), LIMIT 500 (PostgreSQL/Snowflake), LIMIT 200 (Salesforce)
- **Credentials live in `.env`** (gitignored) — never commit credentials

## Project Structure

```
backend/
├── main.py              # FastAPI app, WebSocket, static file serving
├── chat.py              # Claude API integration, system prompt, tool execution
├── db/
│   ├── connections.py   # All 5 database connection functions
│   └── schemas.py       # Schema descriptions injected into system prompt
├── tools/
│   └── definitions.py   # Claude tool_use definitions (one per database)
└── requirements.txt

frontend/
├── src/
│   ├── App.tsx                    # Router, theme provider
│   ├── components/
│   │   ├── ChatWindow.tsx         # Chat UI with welcome state + messages
│   │   ├── ChatInput.tsx          # Input box (centered hero + bottom modes)
│   │   ├── MessageBubble.tsx      # Message rendering with markdown + tables
│   │   ├── Header.tsx             # Navbar with logo, nav, theme toggle
│   │   ├── AboutPage.tsx          # About page
│   │   ├── MonumentalLeaf.tsx     # SVG leaf logo component
│   │   ├── ThemeToggle.tsx        # Animated sun/moon toggle
│   │   └── backgrounds/           # 6 animated background options
│   └── hooks/
│       ├── useChat.ts             # WebSocket chat with HTTP fallback
│       └── useTheme.ts            # Dark/light mode with localStorage
├── dist/                          # Built frontend (committed for server deploy)
└── package.json

.env                    # Credentials (gitignored)
deploy.bat              # Manual deploy: git pull + restart on server
auto_deploy.bat         # Auto-deploy: polls GitHub every 5 min on server
start_mona.bat          # Server startup script (runs via scheduled task)
```

## Deployment

**Local:** `cd backend && python main.py` → `http://localhost:3000`

**Server (10.7.6.146):** Runs as Windows scheduled task "Mona AI". Auto-deploys every 5 minutes from GitHub via "Mona Auto Deploy" task.

**Deploy flow:** Push to GitHub → server auto-pulls within 5 minutes → Mona restarts.

## Adding a New Database

1. Add connection function in `backend/db/connections.py`
2. Add schema in `backend/db/schemas.py`
3. Add tool definition in `backend/tools/definitions.py`
4. Add execution branch in `backend/chat.py` `_execute_tool()`
5. Add routing entry in system prompt in `backend/chat.py`
6. Add status label in `backend/chat.py` `db_label` dict
7. Update About page in `frontend/src/components/AboutPage.tsx`

## Environment Variables

Required in `.env`:
```
ANTHROPIC_API_KEY          # Claude API key
DB_USERNAME, DB_PASSWORD   # SQL Server (LightSpeed/Level)
PG_HOST, PG_PORT, PG_DATABASE, PG_USERNAME, PG_PASSWORD  # PostgreSQL
SF_USERNAME, SF_PASSWORD   # Salesforce
Snowflake_USERNAME, Snowflake_PASSWORD  # Snowflake
SHAREPOINT_ROOT                        # Path to OneDrive-synced SharePoint folder
```

## Style

- **Response style:** Concise, no filler, no emoji headers, answer first
- **Frontend:** Dark/light mode, Framer Motion animations, Inter font
- **Backend:** Direct imports, no complex abstractions
