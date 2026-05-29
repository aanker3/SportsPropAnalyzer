# Claude Handoff Document

## Current Date: 2026-05-29
## Branch: `frontend-redesign`

All active work is on this branch. It's ahead of master with the full redesign, bug fixes, security hardening, and MLB foundation.

---

## Servers

```bash
# Backend (if not running)
PYTHONIOENCODING=utf-8 poetry run uvicorn alphabetter.nba_backend.main:app --host 127.0.0.1 --port 8000

# Frontend (if not running)
cd alphabetter/nba_frontend/my-react-ts-project && npm run dev
```

---

## MLB Feature — Mid-Implementation (PICK UP HERE)

MLB support was started and partially committed. Pick up from step 4.

### ✅ Already done and committed

1. **`models.py`** — `MLBPlayerGameLog` table added; `sport` column added to `PrizePicksProp` and `PlayerStatsCalculated`
2. **`fetch_player_stats_espn_mlb.py`** — Full ESPN MLB fetcher: roster map, batting/pitching game logs, `store_mlb_player_stats()`
3. **`stat_collector/mlb_stat_mapping.py`** — `MLB_STAT_MAPPING`, `MLB_UNSUPPORTED_STATS`, `_get_mlb_stat_value()`, `_is_mlb_active()`

### ❌ Still to do

**4. DB migration** — Run these against the local `nba_stats` database, then run `init_db.py`:
```sql
ALTER TABLE prize_picks_props ADD COLUMN IF NOT EXISTS sport VARCHAR DEFAULT 'NBA';
ALTER TABLE player_stats_calculated ADD COLUMN IF NOT EXISTS sport VARCHAR DEFAULT 'NBA';
```
Then: `PYTHONIOENCODING=utf-8 poetry run python -m alphabetter.nba_backend.init_db`
(This creates `mlb_player_game_log` since `create_all` picks up the new model.)

**5. `gen_prizepicks_json.py`** — Add `league_id` parameter. Create `gen_mlb_prizepicks_json()` using `league_id=2`.

**6. `calculate_and_store_lastx.py`** — Add `calculate_mlb_hit_rates(session, prop)` that queries `MLBPlayerGameLog` and uses `_get_mlb_stat_value()` / `_is_mlb_active()` from `mlb_stat_mapping.py`. Mirrors existing `calculate_hit_rates()`.

**7. `fetch_and_calculate_all.py`** — Add `run_mlb_pipeline()` function:
- Fetch props with `league_id=2`, store with `sport="MLB"`
- Build MLB ESPN player map, fetch/store game logs
- Calculate hit rates with `calculate_mlb_hit_rates()`
- Keep NBA pipeline (`run_nba_pipeline()`) independent — run each separately

**8. `main.py`** — 
- Add `?sport=` query param to `GET /api/props` for filtering
- Update `GET /api/last_x/{prop_id}/{num_games}` to query `MLBPlayerGameLog` when `prop.sport == "MLB"`
- Add `POST /api/run_mlb_pipeline` endpoint

**9. Frontend** — Add sport tabs to Props page and Players page:
- Tabs: `All | NBA | MLB` (show only tabs that have data)
- Filter props by `prop.sport` when a tab is selected
- Autocomplete on Players page should respect the selected sport tab

---

## Key MLB Facts (Researched This Session)

| Item | Value |
|------|-------|
| PrizePicks league_id | `2` |
| ESPN URL pattern | Same as NBA — replace `basketball/nba` with `baseball/mlb` |
| Category param | `?category=batting` or `?category=pitching` |
| Pitcher detection | Position abbreviation in `{"SP", "RP", "CP", "P"}` |
| Pitching outs formula | `floor(ip)*3 + round((ip%1)*10)` e.g. 6.1 IP = 19 outs |

**ESPN batting labels:** `AB, R, H, 2B, 3B, HR, RBI, BB, HBP, SO, SB, CS, AVG, OBP, SLG, OPS`

**ESPN pitching labels:** `IP, H, R, ER, HR, BB, K, GB, FB, P, TBF, GSC, Dec, Rel, ERA`

**All MLB PrizePicks stat types:**
Hits, Home Runs, RBIs, Runs, Stolen Bases, Hitter Strikeouts, Walks, Doubles, Triples, Singles, Total Bases, Hits+Runs+RBIs, Pitcher Strikeouts, Pitching Outs, Earned Runs Allowed, Hits Allowed, Walks Allowed, 1st Inning Runs Allowed (unsupported)

**Other live PrizePicks leagues found:** PGA(1), WNBA(3), NASCAR(4), Tennis(5), NHL(8), NFL(9), UFC(12)

---

## What Was Completed This Session

- Replaced broken NBA API with ESPN undocumented API
- Full dark-theme frontend redesign (Tailwind CSS)
- Props page: hit rate bars, search/filter, clickable sort headers, season avg in modal, refresh button
- Players page: autocomplete search, active props + game log combined view
- Fixed 10+ bugs (stat mapping, double-double, bar colors, DNP rows, etc.)
- Security audit fixes: CORS, removed hardcoded credentials, removed debug endpoints, input validation
- Deployment config: `Procfile`, `railway.json`, `vercel.json`, `runtime.txt`
- `VITE_API_URL` env var wired through all frontend components
- CLAUDE.md fully rewritten to reflect current state
