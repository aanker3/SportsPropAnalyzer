# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

SportsPropAnalyzer (package name: `alphabetter`) is a sports prop analysis tool covering NBA and MLB via PrizePicks. The long-term goal is to support additional sports and prop sources.

**Current state:** NBA + MLB, PrizePicks only.

## Long-Term Goals

### Multi-sport support
NBA and MLB are live. The same architecture supports additional sports:
- PrizePicks uses the same JSON structure across all sports (just change `league_id`)
- ESPN has roster + gamelog APIs for all major sports with the same URL pattern
- The hit rate math, DB schema, and frontend are already sport-agnostic

**Other live PrizePicks league IDs found:** PGA(1), NBA(7), WNBA(3), NASCAR(4), Tennis(5), NHL(8), NFL(9), UFC(12), MLB(2)

To add a new sport:
1. Create `fetch_player_stats_espn_{sport}.py` — roster map + gamelog fetcher
2. Create `stat_collector/{sport}_stat_mapping.py` — `STAT_MAPPING`, `UNSUPPORTED_STATS`, `_get_stat_value()`, `_is_active()`
3. Add `run_{sport}_pipeline()` to `fetch_and_calculate_all.py` (mirrors `run_nba_pipeline` / `run_mlb_pipeline`)
4. Add `POST /api/run_{sport}_pipeline` endpoint to `main.py`
5. Wire into `fetch_and_calculate_all.py:fetch_and_calculate_and_store()`
6. Update `crud/player_gamelogs.py` to route to the new game log table

**Future refactor:** When a third sport is added, extract an abstract `SportPipeline` base class from the two near-identical pipeline functions in `fetch_and_calculate_all.py`.

### Multi-source props
PrizePicks is the only prop source today. The goal is to support additional books/platforms:
- **Underdog Fantasy** — there is already a scraper in `Research/underdog_scraper/`
- **Other DFS/sportsbook sources** as they become relevant

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
- [ ] MLB pipeline speed — currently ~3-4 min due to per-player ESPN fetches + 0.3s sleeps. Fix: drop sleep, batch DB writes, or parallelize player fetches.

### 4. Frontend UX gaps
- [x] Refresh button in the UI (triggers POST `/api/fetch_and_calculate_all`)
- [x] Season average shown in the modal next to the line, colored green/red vs the target
- [x] Modal closes on Escape key
- [x] NBA / MLB sport tabs in nav
- [x] Top Picks modal with Goblin / Demon / Standard ↑ / Standard ↓ tabs
- [x] Long Shots modal (props with L10 < 20% and L20 < 25%)
- [x] Player headshots from ESPN CDN in table rows and modals

### 5. Nice-to-haves
- [ ] Player news / injury feed (Story 15 in JIRA)
- [ ] Defensive matchup rankings — "Spurs give up most 3s" etc. (Story 9 in JIRA)
- [ ] Refactor `fetch_and_calculate_all.py` into an abstract `SportPipeline` base class — `run_nba_pipeline()` and `run_mlb_pipeline()` are structurally identical. Worth doing when a third sport is added.
- [ ] Worst % column — mirror of Best %, finds the minimum hit rate in any expanding window ≥ 2 games from the most recent game. Backend: add `worst_percent()` function (already written, reverted), store `worst_percent_rate`/`worst_percent_total` in `PlayerStatsCalculated`. Frontend: red sortable column in the props table + badge in chart modal.

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: React 19 + TypeScript, Vite, React Router, Axios, Chart.js, Tailwind CSS v4
- **Prop fetching**: Python (`gen_prizepicks_json.py`) hitting the PrizePicks public API
- **NBA stats source**: ESPN undocumented API (`fetch_player_stats_espn.py`)
- **MLB stats source**: ESPN undocumented API (`fetch_player_stats_espn_mlb.py`)
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

# Full data pipeline: fetch props + player stats + calculate hit rates (NBA + MLB)
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.fetch_and_calculate_all

# MLB pipeline only (via API endpoint while server is running)
# POST http://127.0.0.1:8000/api/run_mlb_pipeline
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
PrizePicks API → gen_prizepicks_json.py (league_id=7) → prizepicks_props.json         ← NBA
PrizePicks API → gen_mlb_prizepicks_json.py (league_id=2) → prizepicks_props_mlb.json ← MLB
                                                  ↓
                                          get_props.py (parse into Prop objects)
                                                  ↓
ESPN NBA API → fetch_player_stats_espn.py     → PlayerGameLog table      ← NBA
ESPN MLB API → fetch_player_stats_espn_mlb.py → MLBPlayerGameLog table   ← MLB
                                                  ↓
                    calculate_and_store_lastx.py (NBA: calculate_hit_rates)
                    calculate_and_store_lastx.py (MLB: calculate_mlb_hit_rates)
                                                  ↓
                                       PlayerStatsCalculated table (sport column)
                                                  ↓
                              FastAPI (/api/*) ← React frontend
```

### Backend Structure (`alphabetter/nba_backend/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, all route definitions |
| `models.py` | SQLAlchemy ORM models (includes `MLBPlayerGameLog`) |
| `database.py` | DB engine/session; reads `DATABASE_URL` env var, falls back to local dev URL |
| `fetch_and_calculate_all.py` | **Main pipeline**: `run_nba_pipeline()`, `run_mlb_pipeline()`, `fetch_and_calculate_and_store()` |
| `fetch_player_stats_espn.py` | NBA stats: builds name→ESPN ID map from 30 team rosters; fetches game logs |
| `fetch_player_stats_espn_mlb.py` | MLB stats: builds name→{id, is_pitcher} map; fetches batting/pitching logs |
| `fetch_and_store_prop_data.py` | Older prop-loading utility (not used by main pipeline) |
| `fetch_and_store_player_stats.py` | Old NBA API stats fetcher (broken — stats.nba.com unreachable) |
| `stat_collector/calculate_and_store_lastx.py` | `calculate_hit_rates()` (NBA), `calculate_mlb_hit_rates()` (MLB), `store_calculated_stats()` |
| `stat_collector/mlb_stat_mapping.py` | `MLB_STAT_MAPPING`, `MLB_UNSUPPORTED_STATS`, `_get_mlb_stat_value()`, `_is_mlb_active()` |
| `get_props/gen_prizepicks_json.py` | Hits PrizePicks API; `gen_prizepicks_json(league_id, filename)` + `gen_mlb_prizepicks_json()` |
| `get_props/get_props.py` | Parses JSON into `Prop` dataclass objects (sport-agnostic) |
| `player_utils.py` | `get_player_id(name, db)` — legacy NBA-only lookup, not used by active gamelogs path |
| `crud/player_gamelogs.py` | Routes player game log queries to `PlayerGameLog` or `MLBPlayerGameLog` based on `PrizePicksProp.sport` |
| `common/nba_api_common.py` | Old `get_player_id` using nba_api (broken — not called by active pipeline) |

### Database Tables

| Table | Model | Purpose |
|-------|-------|---------|
| `prize_picks_props` | `PrizePicksProp` | One row per prop; includes `sport` column ('NBA' or 'MLB') |
| `player_game_log` | `PlayerGameLog` | NBA game logs — one row per player per game |
| `mlb_player_game_log` | `MLBPlayerGameLog` | MLB game logs — batting + pitching stats in same row; `is_pitcher` flag |
| `player_stats` | `PlayerStats` | NBA player summary (PPG/APG/RPG) — populated by NBA pipeline |
| `player_stats_calculated` | `PlayerStatsCalculated` | One row per prop; L5/L10/L20/last_percent; includes `sport` column |
| `team_info` | `TeamInfo` | Team game logs (populated by old NBA API path, currently unused) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/props?sport=NBA` | All PrizePicks props; optional `?sport=NBA` or `?sport=MLB` filter |
| `GET` | `/api/player-stats-calculated` | All calculated hit rates |
| `GET` | `/api/last_x/{prop_id}/{num_games}` | Last N game values for a prop; routes to NBA or MLB game log based on prop.sport |
| `GET` | `/api/player-gamelogs/{player_name}` | Full game log for a player; returns `{sport, player_id, game_logs}` |
| `GET` | `/api/player/{player_name}` | Look up player ID by name (NBA-only legacy) |
| `POST` | `/api/fetch_and_calculate_all` | Run full NBA + MLB pipeline synchronously |
| `POST` | `/api/fetch_and_calculate_all_bg` | Run full pipeline as background task |
| `POST` | `/api/run_mlb_pipeline` | Run MLB pipeline only |

### Frontend Pages (`alphabetter/nba_frontend/my-react-ts-project/src/`)

| File | Route | Description |
|------|-------|-------------|
| `App.tsx` | — | Nav with 🏀 NBA / ⚾ MLB sport tabs + Players link; redirects `/` and `/player-props` to `/nba` |
| `PlayerProps.tsx` | `/nba`, `/mlb` | Props table; takes `sport` prop; Top Picks modal (Goblin/Demon/Std↑/Std↓ tabs); Long Shots modal; player headshots |
| `Players.tsx` | `/players` | Player search (NBA + MLB); auto-detects sport from API response; BBRef-style season stats; full game log |
| `api.ts` | — | Central API URL config — reads `VITE_API_URL`, falls back to localhost |

## Key Business Logic

### `last_percent` algorithm (`calculate_and_store_lastx.py:last_percent`)

Finds the best hit rate in an expanding window starting at game 0 (most recent). Rules:
- Skip windows of size 1 (1/1 is ignored)
- Skip 100% windows of ≤5 games **unless** followed by 2 consecutive misses
- Returns both the rate and a fraction string (e.g., `"24/25"`)

The game list is sorted **newest first** (`.order_by(game_date.desc())`), so index 0 = most recent game. DNP rows (min == 0 for NBA, `_is_mlb_active() == False` for MLB) are excluded.

### NBA `STAT_MAPPING`

Maps PrizePicks stat names to `PlayerGameLog` column names. Combined stats are lists; computed stats use special sentinel strings:

```python
"Pts+Rebs+Asts": ["pts", "reb", "ast"]    # summed
"Two Pointers Made": "2pm"                 # computed: fgm - fg3m
"Two Pointers Attempted": "2pa"            # computed: fga - fg3a
"Double-Double": "double_double"           # computed: 1 if ≥10 in 2+ of pts/reb/ast/blk/stl
"Fantasy Score": "fantasy_score"           # computed: pts + reb*1.2 + ast*1.5 + blk*3 + stl*3 - tov
```

### MLB `MLB_STAT_MAPPING` (`stat_collector/mlb_stat_mapping.py`)

Maps PrizePicks MLB stat names to `MLBPlayerGameLog` column names:

```python
"Hits": "h", "Home Runs": "hr", "RBIs": "rbi", "Runs": "r",
"Stolen Bases": "sb", "Hitter Strikeouts": "so", "Walks": "bb",
"Doubles": "doubles", "Triples": "triples",
"Singles": "singles",         # computed: h - doubles - triples - hr
"Total Bases": "total_bases", # computed: h + 2B + 2*3B + 3*HR (note: not standard TB formula — confirmed correct)
"Hits+Runs+RBIs": ["h", "r", "rbi"],
"Pitcher Strikeouts": "k", "Pitching Outs": "pitching_outs",  # computed: floor(ip)*3 + round((ip%1)*10)
"Earned Runs Allowed": "er", "Hits Allowed": "hits_allowed", "Walks Allowed": "bb_allowed"
```

MLB `_is_mlb_active()`: pitcher = `ip > 0`; batter = `ab > 0 or bb > 0 or hbp > 0`

### `UNSUPPORTED_STATS`

NBA props skipped (can't be computed from ESPN game logs):
- `Fantasy Score`, `Dunks`
- `Points/Assists/Rebounds - 1st 3 Minutes` — no per-period splits
- `Offensive Rebounds`, `Defensive Rebounds` — ESPN only provides total REB

MLB props skipped:
- `1st Inning Runs Allowed` — inning-level splits not in game logs

### `OddsType` enum

`standard` / `demon` / `goblin` — mirrors PrizePicks prop tiers.

### ESPN NBA stat labels order

ESPN returns stats as an ordered array matching `data["labels"]`:
`MIN, FG, FG%, 3PT, 3P%, FT, FT%, REB, AST, BLK, STL, PF, TO, PTS`

`FG`, `3PT`, `FT` are in `"made-attempted"` format (e.g., `"10-21"`). The fetcher always parses from `labels` dynamically, not by hardcoded index.

### ESPN MLB API specifics

- **Roster endpoint**: `site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_id}/roster`
  - Returns **nested** structure: `athletes = [{position: "Pitchers", items: [player, ...]}, ...]`
  - Unlike NBA (flat list), must iterate `group["items"]` to get individual players
- **Gamelog endpoint**: `site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes/{id}/gamelog?category=batting` (or `pitching`)
- **Pitcher detection**: position abbreviation in `{"SP", "RP", "CP", "P"}`
- **Pitching outs formula**: `floor(ip)*3 + round((ip%1)*10)` — e.g. 6.1 IP = 19 outs

### ESPN batting labels
`AB, R, H, 2B, 3B, HR, RBI, BB, HBP, SO, SB, CS, AVG, OBP, SLG, OPS`

### ESPN pitching labels
`IP, H, R, ER, HR, BB, K, GB, FB, P, TBF, GSC, Dec, Rel, ERA`

### Player headshots

ESPN CDN headshots are used for all players:
- NBA: `https://a.espncdn.com/i/headshots/nba/players/full/{espn_player_id}.png`
- MLB: `https://a.espncdn.com/i/headshots/mlb/players/full/{espn_player_id}.png`

The `player_id` stored in `PrizePicksProp` and `PlayerStatsCalculated` is the ESPN athlete ID, so it maps directly to these URLs. The `PlayerAvatar` component in `PlayerProps.tsx` falls back to initials if the image fails to load. Hotlinking ESPN's CDN is fine for small personal deployments; at larger scale, proxy through a backend endpoint to avoid rate limiting.

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

**2. Pipeline clears DB before refilling — downtime on refresh**
- File: `fetch_and_calculate_all.py` — `_clear_nba_data()` / `_clear_mlb_data()`
- Each sport's data is empty between the delete and the re-insert. Stories 10/11 in JIRA track the staging-table swap fix.

**3. MLB pipeline is slow (~3-4 min)**
- File: `fetch_and_calculate_all.py:run_mlb_pipeline`
- 400+ ESPN API calls with 0.3s sleep each. Fix: drop the sleep, batch DB writes, parallelize player fetches.

**4. `fetch_and_store_prop_data.py:store_prize_picks_props` is dead code with broken NBA API call**
- File: `fetch_and_store_prop_data.py:25`
- Not called by the active pipeline but would crash if invoked.

### Low Priority

**5. `calculate_and_store_stats_bulk` is unused but has a bug**
- File: `stat_collector/calculate_and_store_lastx.py`
- The bulk recalculation path is not called by the active pipeline.

**6. CORS defaults to `*` if `ALLOWED_ORIGINS` not set**
- File: `main.py`
- Fine locally, but remember to set `ALLOWED_ORIGINS` on Railway before going public.

---

## Important Notes

- **Always use `PYTHONIOENCODING=utf-8`** before `poetry run python` on Windows — print statements contain emoji that crash on cp1252.
- **`stats.nba.com` is unreachable** from this machine. The active pipeline uses ESPN. `fetch_and_store_player_stats.py` is kept for reference but non-functional.
- **ESPN API has no official docs** — NBA endpoints: `site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{id}/roster` and `site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{id}/gamelog`. MLB uses the same pattern with `baseball/mlb`.
- **ESPN MLB rosters are nested** — `athletes` is a list of position groups, each with an `items` list of players. NBA rosters are a flat list. Don't assume the same structure.
- **PrizePicks only shows active/upcoming games** — in the off-season or between series, `/api/props` may return 0 props even after a successful pipeline run.
- **`oreb` and `dreb` are always 0** in ESPN-sourced NBA data (ESPN only reports total rebounds). These prop types are in `UNSUPPORTED_STATS` and are skipped.
- `legacy_code/` and `Research/` are not part of the active app — ignore for debugging.
- **Local DB password** is `BigStink44` in the `database.py` fallback. This never runs in production — Railway injects `DATABASE_URL` automatically.
