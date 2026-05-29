"""
ESPN MLB stats fetcher.

Pitchers identified by position: SP, RP, CP, P.
Uses category=pitching for pitchers, category=batting for everyone else.
Pitching outs computed from IP: floor(ip)*3 + round((ip%1)*10).
"""
import time
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from alphabetter.nba_backend.models import MLBPlayerGameLog, PlayerStats

ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams?limit=30"
ESPN_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_id}/roster"
ESPN_GAMELOG_URL = "https://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes/{athlete_id}/gamelog"

PITCHER_POSITIONS = {"SP", "RP", "CP", "P"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def build_mlb_player_map() -> dict[str, dict]:
    """
    Fetches all 30 MLB team rosters.
    Returns name -> {"id": espn_id, "is_pitcher": bool}
    """
    resp = requests.get(ESPN_TEAMS_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    teams = resp.json()["sports"][0]["leagues"][0]["teams"]
    team_ids = [t["team"]["id"] for t in teams]

    player_map = {}
    for team_id in team_ids:
        roster_resp = requests.get(ESPN_ROSTER_URL.format(team_id=team_id), headers=HEADERS, timeout=15)
        roster_resp.raise_for_status()
        for athlete in roster_resp.json().get("athletes", []):
            position = athlete.get("position", {}).get("abbreviation", "")
            player_map[athlete["fullName"]] = {
                "id": athlete["id"],
                "is_pitcher": position in PITCHER_POSITIONS,
            }
        time.sleep(0.2)

    print(f"MLB ESPN player map built: {len(player_map)} players across {len(team_ids)} teams")
    return player_map


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _pitching_outs(ip: float) -> float:
    """Convert ESPN's decimal IP to total outs. 6.1 = 19 outs, 6.2 = 20 outs."""
    full_innings = int(ip)
    partial = round((ip - full_innings) * 10)
    return float(full_innings * 3 + partial)


def fetch_mlb_player_stats(espn_id: str, player_name: str, is_pitcher: bool) -> tuple:
    """
    Fetches regular season game logs for an MLB player.
    Returns (player_name, team_name, team_id, game_logs).
    """
    category = "pitching" if is_pitcher else "batting"
    url = ESPN_GAMELOG_URL.format(athlete_id=espn_id)
    resp = requests.get(url, headers=HEADERS, params={"category": category}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    labels = data.get("labels", [])
    label_idx = {label: i for i, label in enumerate(labels)}

    team_name = "Unknown"
    team_id = 0
    game_logs = []

    for season_type in data.get("seasonTypes", []):
        if "Preseason" in season_type.get("displayName", ""):
            continue

        for category_block in season_type.get("categories", []):
            for evt in category_block.get("events", []):
                event_id = evt.get("eventId")
                stats = evt.get("stats", [])
                if not stats or not event_id:
                    continue

                game_info = data["events"].get(str(event_id)) or data["events"].get(event_id)
                if not game_info:
                    continue

                if team_id == 0:
                    t = game_info.get("team", {})
                    team_name = t.get("displayName", "Unknown")
                    team_id = int(t.get("id", 0) or 0)

                def sv(label):
                    idx = label_idx.get(label)
                    if idx is None or idx >= len(stats):
                        return 0.0
                    return _safe_float(stats[idx])

                raw_date = game_info.get("gameDate", "")
                try:
                    game_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(timezone.utc).date()
                except Exception:
                    game_date = None

                at_vs = game_info.get("atVs", "vs")
                opp = game_info.get("opponent", {}).get("abbreviation", "UNK")
                my = game_info.get("team", {}).get("abbreviation", "UNK")
                matchup = f"{my} @ {opp}" if at_vs == "@" else f"{my} vs. {opp}"

                if is_pitcher:
                    ip = sv("IP")
                    if ip == 0.0:
                        continue  # didn't pitch
                    log = {
                        "player_id": int(espn_id),
                        "game_date": game_date,
                        "matchup": matchup,
                        "is_pitcher": True,
                        "ab": 0.0, "r": 0.0, "h": 0.0, "doubles": 0.0, "triples": 0.0,
                        "hr": 0.0, "rbi": 0.0, "bb": 0.0, "hbp": 0.0, "so": 0.0,
                        "sb": 0.0, "cs": 0.0,
                        "ip": ip,
                        "hits_allowed": sv("H"),
                        "runs_allowed": sv("R"),
                        "er": sv("ER"),
                        "hr_allowed": sv("HR"),
                        "bb_allowed": sv("BB"),
                        "k": sv("K"),
                    }
                else:
                    ab = sv("AB")
                    h = sv("H")
                    doubles = sv("2B")
                    triples = sv("3B")
                    hr = sv("HR")
                    log = {
                        "player_id": int(espn_id),
                        "game_date": game_date,
                        "matchup": matchup,
                        "is_pitcher": False,
                        "ab": ab,
                        "r": sv("R"),
                        "h": h,
                        "doubles": doubles,
                        "triples": triples,
                        "hr": hr,
                        "rbi": sv("RBI"),
                        "bb": sv("BB"),
                        "hbp": sv("HBP"),
                        "so": sv("SO"),
                        "sb": sv("SB"),
                        "cs": sv("CS"),
                        "ip": 0.0, "hits_allowed": 0.0, "runs_allowed": 0.0,
                        "er": 0.0, "hr_allowed": 0.0, "bb_allowed": 0.0, "k": 0.0,
                    }

                game_logs.append(log)

    return player_name, team_name, team_id, game_logs


def store_mlb_player_stats(db: Session, player_id: int, player_name: str,
                            team: str, team_id: int, game_logs: list):
    """Stores MLB game logs in the database."""
    for log in game_logs:
        db.add(MLBPlayerGameLog(
            player_id=player_id,
            game_date=log["game_date"],
            matchup=log["matchup"],
            is_pitcher=log["is_pitcher"],
            ab=log["ab"], r=log["r"], h=log["h"],
            doubles=log["doubles"], triples=log["triples"], hr=log["hr"],
            rbi=log["rbi"], bb=log["bb"], hbp=log["hbp"],
            so=log["so"], sb=log["sb"], cs=log["cs"],
            ip=log["ip"], hits_allowed=log["hits_allowed"],
            runs_allowed=log["runs_allowed"], er=log["er"],
            hr_allowed=log["hr_allowed"], bb_allowed=log["bb_allowed"],
            k=log["k"],
        ))
    db.commit()
