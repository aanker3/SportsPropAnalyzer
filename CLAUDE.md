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

## Tech Stack

## Short-Term Goals (priority order)

### 1. Data quality
- [x] Fix `oreb`/`dreb` — ESPN doesn't provide per-game offensive/defensive rebound splits. Mark "Offensive Rebounds" and "Defensive Rebounds" as unsupported so they don't show 0% hit rates.

### 2. Deployment blockers
- [x] Replace hardcoded `http://127.0.0.1:8000` with `VITE_API_URL` env var — set in `.env.local` for dev, Vercel dashboard for prod
- [ ] Set up Railway (backend + PostgreSQL) and Vercel (frontend) — Story 13 in JIRA
- [ ] Confirm `DATABASE_URL` env var is wired through in production

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

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: React 19 + TypeScript, Vite, React Router, Axios, Chart.js
- **Prop fetching**: Python (`gen_prizepicks_json.py`) hitting the PrizePicks public API
- **Stats source**: ESPN undocumented API (`fetch_player_stats_espn.py`) — replaced NBA API which became unreachable
- **Dependency management**: Poetry (backend), npm (frontend)

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
| `database.py` | DB engine/session; `DATABASE_URL` env var |
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
| `player_game_log` | `PlayerGameLog` | One row per player per game; all box score stats |
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
| `GET` | `/api/ping_stats_nba` | Health check for stats.nba.com (currently broken) |
| `GET` | `/api/test_real_stats` | Debug endpoint for NBA API |
| `GET` | `/api/test_real_stats_bbref` | Debug endpoint for Basketball Reference |

### Frontend Pages (`alphabetter/nba_frontend/my-react-ts-project/src/`)

| File | Route | Description |
|------|-------|-------------|
| `PlayerProps.tsx` | `/player-props` | **Main page**: sortable prop table + bar chart modal |
| `PlayerGameLogs.tsx` | `/player-gamelogs` | Per-player game log table (all stats) |
| `PlayerStats.tsx` | `/player-stats` | Prop-by-ID lookup with bar chart |
| `PlayerId.tsx` | `/player-id` | Player ID lookup utility |

## Key Business Logic

### `last_percent` algorithm (`calculate_and_store_lastx.py:last_percent`)

Finds the best hit rate in an expanding window starting at game 0 (most recent). Rules:
- Skip windows of size 1 (1/1 is ignored)
- Skip 100% windows of ≤5 games **unless** followed by 2 consecutive misses
- Returns both the rate and a fraction string (e.g., `"24/25"`)

The game list is sorted **newest first** (`.order_by(game_date.desc())`), so index 0 = most recent game.

### `STAT_MAPPING`

Maps PrizePicks stat names to `PlayerGameLog` column names. Combined stats are lists; at query time they're summed:

```python
"Pts+Rebs+Asts": ["pts", "reb", "ast"]   # sum of three columns
"Fantasy Score": "fantasy_score"           # computed: pts + reb*1.2 + ast*1.5 + blk*3 + stl*3 - tov
```

**Unmapped stats** (fall back to `"pts"`, so calculations are wrong for these):
`Free Throws Attempted`, `Personal Fouls`, `Two Pointers Made`, `Two Pointers Attempted`, `Points - 1st 3 Minutes`

### `OddsType` enum

`standard` / `demon` / `goblin` — mirrors PrizePicks prop tiers.

### ESPN stat labels order

ESPN returns stats as an ordered array matching `data["labels"]`:
`MIN, FG, FG%, 3PT, 3P%, FT, FT%, REB, AST, BLK, STL, PF, TO, PTS`

`FG`, `3PT`, `FT` are in `"made-attempted"` format (e.g., `"10-21"`). The fetcher always parses from `labels` dynamically, not by hardcoded index.

### ESPN player ID mapping

`build_espn_player_map()` fetches all 30 team rosters once at pipeline start. Players not on any current roster (e.g., recently waived) will be missing from the map and skipped. ~537 players are mapped in a typical run.

### Over/Under hit logic

- **Over**: `stat_value >= target` counts as a hit
- **Under**: `stat_value < target` counts as a hit (exact match = miss for under)

---

## Known Bugs

### High Priority

**1. `calculate_and_store_stats_bulk` always uses `log.pts` for `last_percent`**
- File: `stat_collector/calculate_and_store_lastx.py:229`
- The hit list hardcodes `log.pts` instead of using the actual prop's stat. Any bulk recalculation via this function produces wrong `last_percent` for non-points props.
- The main pipeline uses `calculate_hit_rates` (per-prop, correct) so this only affects the unused bulk path.

**2. CLI `main()` passes `prop.id` instead of `prop` object**
- File: `stat_collector/calculate_and_store_lastx.py:305`
- `calculate_hit_rates(session, prop.id)` — should be `calculate_hit_rates(session, prop)`. Crashes if you run `python -m alphabetter.nba_backend.stat_collector.calculate_and_store_lastx` in batch mode.

**3. L5/L10/L20 include DNP game rows; `last_percent` does not**
- File: `stat_collector/calculate_and_store_lastx.py:112-114` vs `:134`
- `_calc_hit_rate` has no `game.min > 0` guard, so it includes rows where the player had 0 minutes (team schedule rows where the player was inactive). `last_percent` filters these out. This inflates denominators and deflates L5/L10/L20 hit rates.

**4. `gen_prizepicks_json.py` calls `sys.exit(1)` on failure**
- File: `get_props/gen_prizepicks_json.py:18,51,65`
- Crashes the entire pipeline process instead of raising an exception. If PrizePicks API is temporarily down, the whole pipeline dies rather than the error being caught by the caller.

### Medium Priority

**5. `fetch_and_store_prop_data.py:store_prize_picks_props` still uses broken NBA API**
- File: `fetch_and_store_prop_data.py:25`
- Calls `get_player_id` from `common/nba_api_common.py` which hits `stats.nba.com` (unreachable). This function is dead code in the current pipeline but would break if called.

**6. Frontend bar colors use strict `>` but hit rate uses `>=`**
- File: `PlayerProps.tsx:73-76`
- Bars are green if `value > target`, grey if `value == target`. But hit rates count `value >= target` as a hit for "over" props. A player who exactly hits the line appears grey (miss) visually but is counted as a hit in the stats.

**7. `fetch_and_store_player_stats.py` season hardcoded to `'2024-25'`**
- File: `fetch_and_store_player_stats.py:17,20`
- Would need updating if the old NBA API path is ever restored. Currently irrelevant since ESPN is used.

### Low Priority

**8. Unused import in `fetch_and_calculate_all.py`**
- File: `fetch_and_calculate_all.py:12`
- `from alphabetter.nba_backend.fetch_and_store_player_stats import store_player_stats` — `fetch_player_stats` is imported here but no longer needed; `store_player_stats` is the only one used.

**9. `PlayerProps.tsx` slider max hardcoded to 30**
- File: `PlayerProps.tsx:287`
- Players may have fewer than 30 games (e.g., injury returns, rookies). No user-visible error occurs but the chart just shows fewer bars.

**10. CORS fully open**
- File: `main.py:17`
- `allow_origins=["*"]` is fine locally but should be restricted to the frontend origin in production.

**11. Two FastAPI route functions share the name `fetch_and_calculate_all`**
- File: `main.py:31,38`
- Python overwrites the first definition with the second at module scope. FastAPI registers both routes correctly at decoration time, so it works, but it's confusing and fragile.

**12. `STAT_MAPPING` `TODO` comment in `main.py`**
- File: `main.py:128`
- `#TODO most of the right side is wrong...` — the stat_mapping in `main.py` duplicates the one in `calculate_and_store_lastx.py` and they should be kept in sync. Consider importing one from the other.

---

## Important Notes

- **Always use `PYTHONIOENCODING=utf-8`** before `poetry run python` on Windows — print statements contain emoji that crash on cp1252.
- **`stats.nba.com` is unreachable** from this machine. The active pipeline uses ESPN. `fetch_and_store_player_stats.py` is kept for reference but non-functional.
- **ESPN API has no official docs** — endpoints used: `site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{id}/roster` and `site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{id}/gamelog`.
- **PrizePicks only shows active/upcoming games** — in the off-season or between series, `/api/props` may return 0 props even after a successful pipeline run.
- **`oreb` and `dreb` are always 0** in ESPN-sourced data (ESPN only reports total rebounds). Props for those stats would show 0% hit rate.
- `legacy_code/` and `Research/` are not part of the active app — ignore for debugging.
- The database password `BigStink44` is in `database.py`. Use `DATABASE_URL` env var for production.
