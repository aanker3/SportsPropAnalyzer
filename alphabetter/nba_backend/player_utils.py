from sqlalchemy.orm import Session
from sqlalchemy import func
from alphabetter.nba_backend.models import PlayerStats, PrizePicksProp

def get_player_id(player_name: str, db: Session):
    # Query player ID for the player using case-insensitive match
    player = db.query(PlayerStats).filter(func.lower(PlayerStats.name) == player_name.lower()).first()
    if not player:
        # If player is not found, return all available props
        props = db.query(PrizePicksProp).all()
        props_list = [
            {
                "id": prop.id,
                "player_name": prop.player_name,
                "player_id": prop.player_id,
                "stat": prop.stat,
                "target": prop.target,
                "over_under": prop.over_under,
                "odds_type": prop.odds_type,
            }
            for prop in props
        ]
        return {"error": "Player not found", "props": props_list}

    return {"player_id": player.player_id}