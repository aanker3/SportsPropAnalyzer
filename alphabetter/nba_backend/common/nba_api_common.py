from nba_api.stats.static import players

def get_player_id(player_name: str) -> int:
    """Converts a player name to an nba_api player ID."""
    player = players.find_players_by_full_name(player_name)
    if player:
        return player[0]['id']
    else:
        raise ValueError(f"Player with name '{player_name}' not found.")