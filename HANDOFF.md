# Claude Handoff Document

## Current State (as of 2026-05-27)

### What was running
- **Backend** (FastAPI): started with `PYTHONIOENCODING=utf-8 poetry run uvicorn alphabetter.nba_backend.main:app --host 127.0.0.1 --port 8000`
- **Frontend** (React/Vite): started with `npm run dev` in `alphabetter/nba_frontend/my-react-ts-project/`, running at http://localhost:5173
- **Data pipeline**: `PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.fetch_and_calculate_all` was launched as a background task and is **still running** (may or may not be complete)

### Pipeline status
- The pipeline cleared the DB (confirmed 0 props via `/api/props` mid-run)
- It was in the process of fetching fresh PrizePicks props + NBA player game logs and reinserting them
- Before the pipeline ran, the DB had **92 props / 92 calculated stats**, with game logs up to **March 31, 2025**
- To check if it's done: `curl http://127.0.0.1:8000/api/props` — if count > 0, it finished

### Known issue: emoji encoding on Windows
Running any pipeline script directly with `poetry run python` fails with a `UnicodeEncodeError` because Windows cp1252 can't encode emoji in print statements.
**Fix**: always prefix with `PYTHONIOENCODING=utf-8`
```bash
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.fetch_and_calculate_all
```

### Key URLs
- Frontend: http://localhost:5173
- Backend root: http://127.0.0.1:8000
- API docs (Swagger): http://127.0.0.1:8000/docs
- Props: http://127.0.0.1:8000/api/props
- Calculated stats: http://127.0.0.1:8000/api/player-stats-calculated

---

## Project Summary

**SportsPropAnalyzer** (`alphabetter` package) — NBA sports prop analysis tool. Fetches live PrizePicks props, pulls player game logs via the NBA API, and calculates historical hit rates to evaluate over/under bets.

### Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React 19 + TypeScript, Vite, React Router, Axios
- Dependency mgmt: Poetry (backend), npm (frontend)
- Must use `poetry run` — uvicorn/fastapi are NOT in system Python

### Database
- PostgreSQL, local DB: `nba_stats`
- Default connection: `postgresql://postgres:BigStink44@localhost/nba_stats`
- Override with `DATABASE_URL` env var
- Tables: `player_stats`, `player_game_log`, `team_info`, `prize_picks_props`, `player_stats_calculated`

### Commands
```bash
# Backend server
PYTHONIOENCODING=utf-8 poetry run uvicorn alphabetter.nba_backend.main:app --reload --host 127.0.0.1 --port 8000

# Full data refresh pipeline
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.fetch_and_calculate_all

# Init DB tables
PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.init_db

# Frontend
cd alphabetter/nba_frontend/my-react-ts-project && npm run dev
```

### Architecture (data flow)
1. `gen_prizepicks_json.py` hits PrizePicks API → writes `prizepicks_props.json`
2. `get_props.py` parses JSON into `Prop` objects
3. `fetch_and_store_player_stats.py` hits NBA API for each player's 2024-25 game logs
4. `calculate_and_store_lastx.py` computes L5/L10/L20 hit rates + `last_percent`
5. FastAPI serves results to the React frontend

### Key business logic
- **`last_percent`**: finds best hit rate from game 0 expanding outward; ignores 100% windows ≤5 games unless followed by 2 losses
- **`STAT_MAPPING`**: maps PrizePicks stat names → `PlayerGameLog` column names; combined stats (e.g. `"Pts+Rebs+Asts"`) are lists, summed at query time
- Season hardcoded to `'2024-25'` in `fetch_and_store_player_stats.py`
- `Fantasy Score` and `Dunks` props are skipped (unsupported)
- NBA API rate limits require `time.sleep(0.2–1.0)` between calls

### What was done this session
1. Created `CLAUDE.md` with architecture docs and commands
2. Confirmed backend works (`poetry run uvicorn`)
3. Started frontend dev server
4. Kicked off full data refresh pipeline (still running when handoff was made)
