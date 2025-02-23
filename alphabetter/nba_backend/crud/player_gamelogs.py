from sqlalchemy.orm import Session
from alphabetter.nba_backend.models import PlayerGameLog
from alphabetter.nba_backend.player_utils import get_player_id


def fetch_player_gamelogs(player_name: str, db: Session):
    """Fetch player game logs by converting player_name to player_id."""
    player_id_result = get_player_id(player_name, db)
    player_id = player_id_result.get("player_id") if player_id_result else None

    if not player_id:
        return None

    player_games = db.query(PlayerGameLog).filter(
        PlayerGameLog.player_id == player_id
    ).order_by(PlayerGameLog.game_date.desc()).all()

    game_logs = [
        {
            "game_date": game.game_date,
            "player_id": game.player_id,
            "team_id": game.team_id,
            "matchup": game.matchup,
            "min": game.min,
            "pts": game.pts,
            "oreb": game.oreb,
            "dreb": game.dreb,
            "reb": game.reb,
            "ast": game.ast,
            "stl": game.stl,
            "blk": game.blk,
            "tov": game.tov,
            "fgm": game.fgm,
            "fga": game.fga,
            "fg_pct": game.fg_pct,
            "fg3m": game.fg3m,
            "fg3a": game.fg3a,
            "fg3_pct": game.fg3_pct,
            "ftm": game.ftm,
            "fta": game.fta,
            "ft_pct": game.ft_pct
        }
        for game in player_games
    ]

    return game_logs
