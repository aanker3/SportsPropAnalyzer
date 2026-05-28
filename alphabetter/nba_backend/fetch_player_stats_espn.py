import time
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from alphabetter.nba_backend.models import PlayerStats, PlayerGameLog

ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=30"
ESPN_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
ESPN_GAMELOG_URL = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/gamelog"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def build_espn_player_map() -> dict[str, str]:
    """Fetches all 30 NBA team rosters and returns a name -> ESPN athlete ID map."""
    resp = requests.get(ESPN_TEAMS_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    teams = resp.json()["sports"][0]["leagues"][0]["teams"]
    team_ids = [t["team"]["id"] for t in teams]

    player_map = {}
    for team_id in team_ids:
        roster_resp = requests.get(ESPN_ROSTER_URL.format(team_id=team_id), headers=HEADERS, timeout=15)
        roster_resp.raise_for_status()
        for athlete in roster_resp.json().get("athletes", []):
            player_map[athlete["fullName"]] = athlete["id"]
        time.sleep(0.2)

    print(f"ESPN player map built: {len(player_map)} players across {len(team_ids)} teams")
    return player_map


def _parse_made_att(val: str) -> tuple[int, int]:
    """Parse '10-21' into (10, 21). Returns (0, 0) on failure."""
    try:
        made, att = str(val).split("-")
        return int(made), int(att)
    except Exception:
        return 0, 0


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def fetch_player_stats_espn(espn_id: str, player_name: str) -> tuple:
    """
    Fetches regular season + postseason game logs for a player from ESPN.
    Returns (player_name, team_name, team_id, game_logs).
    """
    url = ESPN_GAMELOG_URL.format(athlete_id=espn_id)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    labels = data.get("labels", [])
    label_idx = {label: i for i, label in enumerate(labels)}

    team_name = "Unknown"
    team_id = 0

    game_logs = []
    for season_type in data.get("seasonTypes", []):
        display = season_type.get("displayName", "")
        if "Preseason" in display:
            continue  # skip preseason games

        for category in season_type.get("categories", []):
            for evt in category.get("events", []):
                event_id = evt.get("eventId")
                stats = evt.get("stats", [])
                if not stats or not event_id:
                    continue

                game_info = data["events"].get(str(event_id)) or data["events"].get(event_id)
                if not game_info:
                    continue

                # Extract team info from first valid game
                if team_id == 0:
                    t = game_info.get("team", {})
                    team_name = t.get("displayName", "Unknown")
                    team_id = int(t.get("id", 0) or 0)

                # Skip if player didn't play (all stats would be 0 or DNP marker)
                pts_idx = label_idx.get("PTS")
                min_idx = label_idx.get("MIN")
                if min_idx is not None and min_idx < len(stats):
                    if stats[min_idx] in ("0", "0.0", 0):
                        continue  # DNP or 0 minutes

                def stat_val(label):
                    idx = label_idx.get(label)
                    if idx is None or idx >= len(stats):
                        return 0.0
                    return _safe_float(stats[idx])

                fgm, fga = _parse_made_att(stats[label_idx["FG"]] if "FG" in label_idx and label_idx["FG"] < len(stats) else "0-0")
                fg3m, fg3a = _parse_made_att(stats[label_idx["3PT"]] if "3PT" in label_idx and label_idx["3PT"] < len(stats) else "0-0")
                ftm, fta = _parse_made_att(stats[label_idx["FT"]] if "FT" in label_idx and label_idx["FT"] < len(stats) else "0-0")

                raw_date = game_info.get("gameDate", "")
                try:
                    game_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(timezone.utc).date()
                except Exception:
                    game_date = None

                at_vs = game_info.get("atVs", "vs")
                opp_abbr = game_info.get("opponent", {}).get("abbreviation", "UNK")
                my_abbr = game_info.get("team", {}).get("abbreviation", "UNK")
                if at_vs == "@":
                    matchup = f"{my_abbr} @ {opp_abbr}"
                else:
                    matchup = f"{my_abbr} vs. {opp_abbr}"

                game_logs.append({
                    "player_id": int(espn_id),
                    "team_id": int(game_info.get("team", {}).get("id", 0) or 0),
                    "game_date": game_date,
                    "matchup": matchup,
                    "min": stat_val("MIN"),
                    "pts": stat_val("PTS"),
                    "oreb": 0.0,
                    "dreb": 0.0,
                    "reb": stat_val("REB"),
                    "ast": stat_val("AST"),
                    "stl": stat_val("STL"),
                    "blk": stat_val("BLK"),
                    "tov": stat_val("TO"),
                    "fgm": float(fgm),
                    "fga": float(fga),
                    "fg_pct": stat_val("FG%"),
                    "fg3m": float(fg3m),
                    "fg3a": float(fg3a),
                    "fg3_pct": stat_val("3P%"),
                    "ftm": float(ftm),
                    "fta": float(fta),
                    "ft_pct": stat_val("FT%"),
                    "pf": stat_val("PF"),
                })

    return player_name, team_name, team_id, game_logs
