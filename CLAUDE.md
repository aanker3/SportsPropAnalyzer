# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

SportsPropAnalyzer (package name: `alphabetter`) is a sports prop analysis tool. It currently covers NBA via PrizePicks, but the long-term goal is to support multiple sports and multiple prop sources.

**Current state:** NBA only, PrizePicks only.

## Long-Term Goals

### Multi-sport support
The pipeline should work for NFL, NHL, MLB, and other sports — not just NBA. The architecture is largely sport-agnostic already:
- PrizePicks uses the same JSON structure across all sports (just change `league_id`)
- ESPN has roster + gamelog APIs for all major sports with the same URL pattern
- The hit rate math, DB schema, and frontend are stat-agnostic

What needs to be built per sport:
- A `STAT_MAPPING` dict mapping that sport's PrizePicks stat names to ESPN column names
- An `UNSUPPORTED_STATS` set for props that can't be calculated (e.g. "First TD Scorer")
- Verification that ESPN's gamelog labels match expectations (they vary by sport)
- A `sport` or `league_id` parameter threaded through the pipeline instead of hardcoded values

The cleanest path: make `STAT_MAPPING`, `UNSUPPORTED_STATS`, and the ESPN endpoints sport-keyed so a single pipeline run can handle multiple sports simultaneously.

### Multi-source props
PrizePicks is the only prop source today. The goal is to support additional books/platforms:
- **Underdog Fantasy** — there is already a scraper in `Research/underdog_scraper/`
- **Other DFS/sportsbook sources** as they become relevant

To add a new source:
- Write a fetcher that outputs props in the same `Prop` dataclass format (`player_name`, `stat`, `target`, `over_under`, `odds_type`)
- The rest of the pipeline (ESPN stats fetch, hit rate calc, DB storage) is shared
- The frontend should eventually show which book a prop is from and allow filtering by source

---

## Short-Term Goals (priority order)

### 1. Data quality
- [x] Fix `oreb`/`dreb` — ESPN doesn't provide per-game offensive/defensive rebound splits. Mark "Offensive Rebounds" and "Defensive Rebounds" as unsupported so they don't show 0% hit rates.

### 2. Deployment blockers
- [x] Replace hardcoded `http://127.0.0.1:8000` with `VITE_API_URL` env var — set in `.env.local` for dev, Vercel dashboard for prod
- [x] `Procfile`, `railway.json`, and `vercel.json` are committed and ready
- [x] Security blockers fixed (CORS, hardcoded credentials, debug endpoints removed)
- [ ] Create Railway project, add PostgreSQL plugin, set `DATABASE_URL` env var, deploy from GitHub
- [ ] Create Vercel project pointing at this repo, set `VITE_API_URL=<railway-url>` env var, deploy
- [ ] Set `ALLOWED_ORIGINS=<vercel-url>` in Railway env vars after Vercel URL is known

### 3. Pipeline reliability
- [ ] No-downtime refresh: fetch new data into staging tables, then swap — currently the DB is empty for ~30s mid-run (Stories 10/11 in JIRA)
- [ ] Scheduled/automatic refresh — currently manual; should run on a cron or be triggerable from the UI
- [ ] Crash recovery: if the pipeline dies mid-run the DB is left empty with no rollback

### 4. Frontend UX gaps
- [x] Refresh button in the UI (triggers POST `/api/fetch_and_calculate_all`)
- [x] Season average shown in the modal next to the line, colored green/red vs the target
- [x] Modal closes on Escape key

### 5. Nice-to-haves
- [ ] Player news / injury feed (Story 15 in JIRA)
- [ ] Defensive matchup rankings — "Spurs give up most 3s" etc. (Story 9 in JIRA)
- [ ] Refactor `fetch_and_calculate_all.py` into an abstract `SportPipeline` base class — `run_nba_pipeline()` and `run_mlb_pipeline()` are structurally identical; a base `run()` loop with 6 sport-specific abstract methods would eliminate the duplication. Worth doing when a third sport (NHL, NFL) is added.

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: React 19 + TypeScript, Vite, React Router, Axios, Chart.js, Tailwind CSS v4
- **Prop fetching**: Python (`gen_prizepicks_json.py`) hitting the PrizePicks public API
- **Stats source**: ESPN undocumented API (`fetch_player_stats_espn.py`) — replaced NBA API which became unreachable
- **Dependency management**: Poetry (backend), npm (frontend)

## Environment Variables

### Backend
| Variable | Where to set | Description |
|----------|-------------|-------------|
| `DATABASE_URL` | Railway dashboard (auto-set by PostgreSQL plugin) | PostgreSQL connection string |
| `ALLOWED_ORIGINS` | Railway dashboard | Comma-separated Vercel URL(s) for CORS. Defaults to `*` if unset (only use `*` locally). |

### Frontend
| Variable | Where to set | Description |
|----------|-------------|-------------|
| `VITE_API_URL` | `.env.local` for dev, Vercel dashboard for prod | Backend URL. Defaults to `http://127.0.0.1:8000` if unset. |

## Commands

### Backend

```bash
# Install dependencies
poetry install

# Initialize/migrate the database (creates all tables)
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.init_db

# Run the FastAPI server (from repo root) — must use poetry run, not system python
PYTHONIOENCODING=utf-8 poetry run uvicorn alphabetter.nba_backend.main:app --reload --host 127.0.0.1 --port 8000

# Full data pipeline: fetch props + player stats + calculate hit rates
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.fetch_and_calculate_all

# Fetch PrizePicks props JSON only
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.get_props.gen_prizepicks_json
```

> **Windows note**: Always prefix `poetry run python` commands with `PYTHONIOENCODING=utf-8` or they crash on emoji in print statements (Windows cp1252 can't encode them).

### Frontend

```bash
cd alphabetter/nba_frontend/my-react-ts-project

npm install
npm run dev      # Dev server at http://localhost:5173
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
ESPN API (rosters + gamelogs) → fetch_player_stats_espn.py → PlayerGameLog table
                                                  ↓
                              calculate_and_store_lastx.py → PlayerStatsCalculated table
                                                  ↓
                              FastAPI (/api/*) ← React frontend
```

### Backend Structure (`alphabetter/nba_backend/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, all route definitions |
| `models.py` | SQLAlchemy ORM models |
| `database.py` | DB engine/session; reads `DATABASE_URL` env var, falls back to local dev URL |
| `fetch_and_calculate_all.py` | **Main pipeline**: clears DB, fetches props + ESPN stats, computes hit rates |
| `fetch_player_stats_espn.py` | **Active stats source**: builds name→ESPN ID map from 30 team rosters; fetches regular season + playoff game logs |
| `fetch_and_store_prop_data.py` | Older prop-loading utility (not used by main pipeline) |
| `fetch_and_store_player_stats.py` | Old NBA API stats fetcher (broken — stats.nba.com unreachable) |
| `stat_collector/calculate_and_store_lastx.py` | Calculates L5/L10/L20 hit rates and `last_percent` |
| `get_props/gen_prizepicks_json.py` | Hits PrizePicks API, writes `prizepicks_props.json` |
| `get_props/get_props.py` | Parses JSON into `Prop` dataclass objects |
| `player_utils.py` | `get_player_id(name, db)` — DB lookup by name |
| `crud/player_gamelogs.py` | Fetches player game logs from DB by name |
| `common/nba_api_common.py` | Old `get_player_id` using nba_api (broken — not called by active pipeline) |

### Database Tables

| Table | Model | Purpose |
|-------|-------|---------|
| `prize_picks_props` | `PrizePicksProp` | One row per prop (player × stat × line × odds_type) |
| `player_game_log` | `PlayerGameLog` | One row per player per game; all box score stats including `pf` |
| `player_stats` | `PlayerStats` | One row per player; summary (PPG/APG/RPG) |
| `player_stats_calculated` | `PlayerStatsCalculated` | One row per prop; L5/L10/L20/last_percent |
| `team_info` | `TeamInfo` | Team game logs (populated by old NBA API path, currently unused) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/props` | All PrizePicks props |
| `GET` | `/api/player-stats-calculated` | All calculated hit rates |
| `GET` | `/api/last_x/{prop_id}/{num_games}` | Last N game values for a prop (used by chart modal) |
| `GET` | `/api/player-gamelogs/{player_name}` | Full game log for a player by name |
| `GET` | `/api/player/{player_name}` | Look up player ID by name |
| `POST` | `/api/fetch_and_calculate_all` | Run full pipeline synchronously |
| `POST` | `/api/fetch_and_calculate_all_bg` | Run full pipeline as background task |

### Frontend Pages (`alphabetter/nba_frontend/my-react-ts-project/src/`)

| File | Route | Description |
|------|-------|-------------|
| `PlayerProps.tsx` | `/player-props` | **Main page**: sortable prop table with hit rate bars, filter/search, bar chart modal with season avg |
| `Players.tsx` | `/players` | Player lookup: autocomplete search, active props table, season averages, full game log |
| `PlayerStats.tsx` | `/player-stats` | Prop-by-ID lookup with bar chart and Hit/Miss table |
| `api.ts` | — | Central API URL config — reads `VITE_API_URL`, falls back to localhost |

## Key Business Logic

### `last_percent` algorithm (`calculate_and_store_lastx.py:last_percent`)

Finds the best hit rate in an expanding window starting at game 0 (most recent). Rules:
- Skip windows of size 1 (1/1 is ignored)
- Skip 100% windows of ≤5 games **unless** followed by 2 consecutive misses
- Returns both the rate and a fraction string (e.g., `"24/25"`)

The game list is sorted **newest first** (`.order_by(game_date.desc())`), so index 0 = most recent game. DNP rows (min == 0) are excluded.

### `STAT_MAPPING`

Maps PrizePicks stat names to `PlayerGameLog` column names. Combined stats are lists; computed stats use special sentinel strings:

```python
"Pts+Rebs+Asts": ["pts", "reb", "ast"]    # summed
"Two Pointers Made": "2pm"                 # computed: fgm - fg3m
"Two Pointers Attempted": "2pa"            # computed: fga - fg3a
"Double-Double": "double_double"           # computed: 1 if ≥10 in 2+ of pts/reb/ast/blk/stl
"Fantasy Score": "fantasy_score"           # computed: pts + reb*1.2 + ast*1.5 + blk*3 + stl*3 - tov
```

### `UNSUPPORTED_STATS`

Props skipped entirely in the pipeline (can't be computed from ESPN game logs):
- `Fantasy Score`, `Dunks`
- `Points/Assists/Rebounds - 1st 3 Minutes` — no per-period splits in ESPN data
- `Offensive Rebounds`, `Defensive Rebounds` — ESPN only provides total REB

### `OddsType` enum

`standard` / `demon` / `goblin` — mirrors PrizePicks prop tiers.

### ESPN stat labels order

ESPN returns stats as an ordered array matching `data["labels"]`:
`MIN, FG, FG%, 3PT, 3P%, FT, FT%, REB, AST, BLK, STL, PF, TO, PTS`

`FG`, `3PT`, `FT` are in `"made-attempted"` format (e.g., `"10-21"`). The fetcher always parses from `labels` dynamically, not by hardcoded index.

### ESPN player ID mapping

`build_espn_player_map()` fetches all 30 team rosters once at pipeline start. Players not on any current roster (e.g., recently waived) will be missing from the map and skipped. ~537 players are mapped in a typical run.

### Over/Under hit logic

- **Over**: `stat_value >= target` counts as a hit (exact match = hit)
- **Under**: `stat_value <= target` counts as a hit (exact match = hit)

Both directions treat an exact line as a hit (push).

---

## Deployment

### Railway (backend + database)
1. Create a new Railway project, connect this GitHub repo
2. Add the **PostgreSQL** plugin — Railway auto-sets `DATABASE_URL`
3. Add env var: `ALLOWED_ORIGINS=https://your-vercel-app.vercel.app`
4. Deploy — Railway uses `railway.json` and `Procfile` automatically

### Vercel (frontend)
1. Create a new Vercel project, connect this GitHub repo
2. Vercel reads `vercel.json` at the root — it points at the frontend subdirectory automatically
3. Add env var: `VITE_API_URL=https://your-railway-app.railway.app`
4. Deploy

### Local dev
- Backend: `http://127.0.0.1:8000` (no env vars needed, uses local Postgres fallback)
- Frontend: reads `VITE_API_URL` from `.env.local` (gitignored); `.env.example` shows the format

---

## Known Bugs

### Medium Priority

**1. `POST /api/fetch_and_calculate_all` has no authentication**
- File: `main.py`
- Anyone with the backend URL can trigger a full data refresh. Fine pre-launch, but should have an API key or IP restriction before the app is widely shared.

**2. Pipeline clears DB before refilling — ~30s downtime on refresh**
- File: `fetch_and_calculate_all.py:delete_all_rows`
- The DB is empty between the delete and the re-insert. Stories 10/11 in JIRA track the staging-table swap fix.

**3. `fetch_and_store_prop_data.py:store_prize_picks_props` is dead code with broken NBA API call**
- File: `fetch_and_store_prop_data.py:25`
- Not called by the active pipeline but would crash if invoked.

### Low Priority

**4. `calculate_and_store_stats_bulk` is unused but has a bug**
- File: `stat_collector/calculate_and_store_lastx.py`
- The bulk recalculation path is not called by the active pipeline. If it were ever wired up, verify prop_stat is correctly threaded through.

**5. `PlayerProps.tsx` slider max is 82 but some players have fewer games**
- File: `PlayerProps.tsx`
- No error, chart just shows fewer bars than the slider suggests.

**6. CORS defaults to `*` if `ALLOWED_ORIGINS` not set**
- File: `main.py`
- Fine locally, but remember to set `ALLOWED_ORIGINS` on Railway before going public.

---

## Important Notes

- **Always use `PYTHONIOENCODING=utf-8`** before `poetry run python` on Windows — print statements contain emoji that crash on cp1252.
- **`stats.nba.com` is unreachable** from this machine. The active pipeline uses ESPN. `fetch_and_store_player_stats.py` is kept for reference but non-functional.
- **ESPN API has no official docs** — endpoints used: `site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{id}/roster` and `site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{id}/gamelog`.
- **PrizePicks only shows active/upcoming games** — in the off-season or between series, `/api/props` may return 0 props even after a successful pipeline run.
- **`oreb` and `dreb` are always 0** in ESPN-sourced data (ESPN only reports total rebounds). These prop types are in `UNSUPPORTED_STATS` and are skipped.
- `legacy_code/` and `Research/` are not part of the active app — ignore for debugging.
- **Local DB password** is `BigStink44` in the `database.py` fallback. This never runs in production — Railway injects `DATABASE_URL` automatically.
