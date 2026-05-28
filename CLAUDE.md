# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SportsPropAnalyzer (package name: `alphabetter`) is an NBA sports prop analysis tool. It fetches live PrizePicks props, pulls player game logs via the NBA API, and calculates historical hit rates to help evaluate over/under bets.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: React 19 + TypeScript, Vite, React Router, Axios
- **Prop fetching**: Python (`gen_prizepicks_json.py`) or a compiled Go binary (`gen_nba_prizepicks.exe`) — both hit the PrizePicks public API
- **Dependency management**: Poetry (backend), npm (frontend)

## Commands

### Backend

```bash
# Install dependencies
poetry install

# Initialize/migrate the database (creates all tables)
python -m alphabetter.nba_backend.init_db

# Run the FastAPI server (from repo root) — must use poetry run, not system python
poetry run uvicorn alphabetter.nba_backend.main:app --reload --host 127.0.0.1 --port 8000

# Full data pipeline: fetch props + player stats + calculate hit rates
python -m alphabetter.nba_backend.fetch_and_calculate_all

# Fetch PrizePicks props JSON only
python -m alphabetter.nba_backend.get_props.gen_prizepicks_json

# Fetch and store all player stats from NBA API
python -m alphabetter.nba_backend.fetch_and_store_player_stats

# Calculate and store hit rates for all props in DB
python -m alphabetter.nba_backend.stat_collector.calculate_and_store_lastx
```

### Frontend

```bash
cd alphabetter/nba_frontend/my-react-ts-project

npm install
npm run dev      # Dev server (Vite)
npm run build    # Production build
npm run lint     # ESLint
```

## Architecture

### Data Flow

```
PrizePicks API → gen_prizepicks_json.py → prizepicks_props.json
                                                  ↓
                                          get_props.py (parse into Prop objects)
                                                  ↓
NBA API (nba_api) → fetch_and_store_player_stats → PlayerGameLog table
                                                  ↓
                              calculate_and_store_lastx → PlayerStatsCalculated table
                                                  ↓
                              FastAPI (/api/*) ← React frontend
```

### Backend Structure (`alphabetter/nba_backend/`)

- **`main.py`** — FastAPI app, all route definitions
- **`models.py`** — SQLAlchemy ORM models: `PlayerStats`, `PlayerGameLog`, `TeamInfo`, `PrizePicksProp`, `PlayerStatsCalculated`
- **`database.py`** — DB engine/session setup; `DATABASE_URL` defaults to `postgresql://postgres:BigStink44@localhost/nba_stats` (override via env var)
- **`fetch_and_calculate_all.py`** — Main orchestrator: clears DB, fetches props + player stats, computes hit rates
- **`fetch_and_store_prop_data.py`** — Fetches PrizePicks JSON and loads into DB
- **`fetch_and_store_player_stats.py`** — Fetches current season game logs from NBA API and stores them
- **`stat_collector/calculate_and_store_lastx.py`** — Calculates L5/L10/L20 hit rates and `last_percent` (best historical hit streak)
- **`get_props/`** — PrizePicks API fetching (`gen_prizepicks_json.py`, `bets.go`) and JSON parsing (`get_props.py`)
- **`common/nba_api_common.py`** — `get_player_id(name)` utility using `nba_api`

### Key Business Logic

**`last_percent`** algorithm (`calculate_and_store_lastx.py:last_percent`): finds the best hit rate from game index 0 expanding outward. Skips 100% windows of ≤5 games unless followed by 2 losses. Returns both the rate and a fraction string (e.g. `"24/25"`).

**`STAT_MAPPING`**: maps PrizePicks stat names (e.g. `"Points"`, `"Pts+Rebs+Asts"`) to `PlayerGameLog` column names. Combined stats are stored as lists and summed at query time.

**`OddsType` enum**: `standard` / `demon` / `goblin` — mirrors PrizePicks prop tiers.

### Frontend Structure (`alphabetter/nba_frontend/my-react-ts-project/src/`)

Four pages, each a standalone component making Axios calls to `http://localhost:8000`:
- `PlayerProps.tsx` — main view; lists PrizePicks props with calculated stats
- `PlayerGameLogs.tsx` — per-player game log lookup
- `PlayerStats.tsx` — season-level stats
- `PlayerId.tsx` — player ID lookup utility

### Database

PostgreSQL. Default local DB: `nba_stats`. Tables are created via `init_db.py` (calls `Base.metadata.create_all`). The `DATABASE_URL` env var can point to a remote Render.com instance (see commented-out URL in `database.py`).

## Important Notes

- The NBA API (`stats.nba.com`) is rate-limited and sometimes requires specific headers. Sleeps are intentional (`time.sleep(0.2–1.0)` between calls).
- The season is hardcoded to `'2024-25'` in `fetch_and_store_player_stats.py` — update when the season changes.
- `Fantasy Score` and `Dunks` prop types are explicitly skipped during processing (unsupported stats).
- `legacy_code/` contains an older standalone Python implementation; `Research/` contains exploratory scripts — neither is part of the active app.
