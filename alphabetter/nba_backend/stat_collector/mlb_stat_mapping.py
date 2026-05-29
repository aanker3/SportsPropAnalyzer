"""
MLB stat mapping and hit rate calculation.

Column names reference MLBPlayerGameLog fields.
Computed stats use sentinel strings handled in _get_mlb_stat_value().
"""
from alphabetter.nba_backend.fetch_player_stats_espn_mlb import _pitching_outs

MLB_STAT_MAPPING = {
    # Batting
    "Hits": "h",
    "Home Runs": "hr",
    "RBIs": "rbi",
    "Runs": "r",
    "Stolen Bases": "sb",
    "Hitter Strikeouts": "so",
    "Walks": "bb",
    "Doubles": "doubles",
    "Triples": "triples",
    "Singles": "singles",           # computed: h - doubles - triples - hr
    "Total Bases": "total_bases",   # computed: h + doubles + 2*triples + 3*hr
    "Hits+Runs+RBIs": ["h", "r", "rbi"],

    # Pitching
    "Pitcher Strikeouts": "k",
    "Pitching Outs": "pitching_outs",   # computed from ip
    "Earned Runs Allowed": "er",
    "Hits Allowed": "hits_allowed",
    "Walks Allowed": "bb_allowed",
}

MLB_UNSUPPORTED_STATS = {
    "1st Inning Runs Allowed",  # inning-level split not available in game logs
}


def _get_mlb_stat_value(game, stat) -> float:
    """Extract or compute the relevant MLB stat value from a game log row."""
    if stat == "singles":
        return max(0.0, getattr(game, "h", 0) - getattr(game, "doubles", 0)
                   - getattr(game, "triples", 0) - getattr(game, "hr", 0))
    if stat == "total_bases":
        # 1B*1 + 2B*2 + 3B*3 + HR*4 = H + 2B + 2*3B + 3*HR
        h = getattr(game, "h", 0)
        d = getattr(game, "doubles", 0)
        t = getattr(game, "triples", 0)
        hr = getattr(game, "hr", 0)
        singles = max(0.0, h - d - t - hr)
        return singles + d * 2 + t * 3 + hr * 4
    if stat == "pitching_outs":
        return _pitching_outs(getattr(game, "ip", 0.0))
    if isinstance(stat, list):
        return sum(getattr(game, s, 0) for s in stat)
    return getattr(game, stat, 0.0)


def _is_mlb_active(game) -> bool:
    """Return True if the player actually participated in this game."""
    if game.is_pitcher:
        return (game.ip or 0) > 0
    return (game.ab or 0) > 0 or (game.bb or 0) > 0 or (game.hbp or 0) > 0
