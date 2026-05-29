from sqlalchemy.orm import Session
from sqlalchemy import func
from alphabetter.nba_backend.models import PlayerGameLog, MLBPlayerGameLog, PrizePicksProp


def fetch_player_gamelogs(player_name: str, db: Session):
    """Fetch game logs for a player, routing to the correct table based on sport."""
    prop = db.query(PrizePicksProp).filter(
        func.lower(PrizePicksProp.player_name) == player_name.strip().lower()
    ).first()

    if not prop:
        return None

    player_id = prop.player_id
    sport = prop.sport or "NBA"

    if sport == "MLB":
        games = db.query(MLBPlayerGameLog).filter(
            MLBPlayerGameLog.player_id == player_id
        ).order_by(MLBPlayerGameLog.game_date.desc()).all()

        game_logs = [
            {
                "game_date": g.game_date,
                "matchup": g.matchup,
                "is_pitcher": g.is_pitcher,
                "ab": g.ab, "r": g.r, "h": g.h,
                "doubles": g.doubles, "triples": g.triples, "hr": g.hr,
                "rbi": g.rbi, "bb": g.bb, "hbp": g.hbp, "so": g.so,
                "sb": g.sb, "cs": g.cs,
                "ip": g.ip, "hits_allowed": g.hits_allowed,
                "runs_allowed": g.runs_allowed, "er": g.er,
                "hr_allowed": g.hr_allowed,
                "bb_allowed": g.bb_allowed, "k": g.k,
            }
            for g in games
        ]
        return {"sport": "MLB", "player_id": player_id, "game_logs": game_logs}

    # NBA
    games = db.query(PlayerGameLog).filter(
        PlayerGameLog.player_id == player_id
    ).order_by(PlayerGameLog.game_date.desc()).all()

    game_logs = [
        {
            "game_date": g.game_date,
            "matchup": g.matchup,
            "min": g.min, "pts": g.pts, "reb": g.reb, "ast": g.ast,
            "stl": g.stl, "blk": g.blk, "tov": g.tov,
            "fgm": g.fgm, "fga": g.fga, "fg_pct": g.fg_pct,
            "fg3m": g.fg3m, "fg3a": g.fg3a, "fg3_pct": g.fg3_pct,
            "ftm": g.ftm, "fta": g.fta, "ft_pct": g.ft_pct,
        }
        for g in games
    ]
    return {"sport": "NBA", "player_id": player_id, "game_logs": game_logs}
