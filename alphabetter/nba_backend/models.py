from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from alphabetter.nba_backend.database import Base
from enum import Enum


class PlayerStats(Base):
    __tablename__ = "player_stats"

    player_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    team = Column(String)
    team_id = Column(Integer)
    games_played = Column(Integer)
    points_per_game = Column(Float)
    assists_per_game = Column(Float)
    rebounds_per_game = Column(Float)


class PlayerGameLog(Base):
    """NBA game log — one row per player per game."""
    __tablename__ = "player_game_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, index=True)
    team_id = Column(Integer)
    game_date = Column(Date)
    matchup = Column(String)
    min = Column(Float)
    pts = Column(Float)
    oreb = Column(Float)
    dreb = Column(Float)
    reb = Column(Float)
    ast = Column(Float)
    stl = Column(Float)
    blk = Column(Float)
    tov = Column(Float)
    fgm = Column(Float)
    fga = Column(Float)
    fg_pct = Column(Float)
    fg3m = Column(Float)
    fg3a = Column(Float)
    fg3_pct = Column(Float)
    ftm = Column(Float)
    fta = Column(Float)
    ft_pct = Column(Float)
    pf = Column(Float)


class MLBPlayerGameLog(Base):
    """MLB game log — one row per player per game. Batting and pitching stats in same row."""
    __tablename__ = "mlb_player_game_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, index=True)
    game_date = Column(Date)
    matchup = Column(String)
    is_pitcher = Column(Boolean, default=False)

    # Batting stats
    ab = Column(Float)
    r = Column(Float)
    h = Column(Float)
    doubles = Column(Float)
    triples = Column(Float)
    hr = Column(Float)
    rbi = Column(Float)
    bb = Column(Float)
    hbp = Column(Float)
    so = Column(Float)
    sb = Column(Float)
    cs = Column(Float)

    # Pitching stats
    ip = Column(Float)          # Decimal innings: 6.1 = 6⅓ innings (6*3+1=19 outs)
    hits_allowed = Column(Float)
    runs_allowed = Column(Float)
    er = Column(Float)
    hr_allowed = Column(Float)
    bb_allowed = Column(Float)
    k = Column(Float)           # Pitcher strikeouts


class TeamInfo(Base):
    __tablename__ = "team_info"

    team_id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, primary_key=True, index=True)
    game_date = Column(Date)
    matchup = Column(String)
    wl = Column(String)
    w = Column(Integer)
    l = Column(Integer)
    w_pct = Column(Float)
    min = Column(Float)
    fgm = Column(Float)
    fga = Column(Float)
    fg_pct = Column(Float)
    fg3m = Column(Float)
    fg3a = Column(Float)
    fg3_pct = Column(Float)
    ftm = Column(Float)
    fta = Column(Float)
    ft_pct = Column(Float)
    oreb = Column(Float)
    dreb = Column(Float)
    reb = Column(Float)
    ast = Column(Float)
    stl = Column(Float)
    blk = Column(Float)
    tov = Column(Float)
    pf = Column(Float)
    pts = Column(Float)


class OddsType(Enum):
    STANDARD = "standard"
    DEMON = "demon"
    GOBLIN = "goblin"

    @staticmethod
    def from_string(value: str) -> "OddsType":
        try:
            return OddsType(value.lower())
        except ValueError:
            return OddsType.STANDARD


class PrizePicksProp(Base):
    __tablename__ = "prize_picks_props"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_id = Column(Integer, index=True)
    stat = Column(String)
    target = Column(Float)
    over_under = Column(String)
    odds_type = Column(String)
    sport = Column(String, index=True, default="NBA")


class PlayerStatsCalculated(Base):
    __tablename__ = "player_stats_calculated"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, index=True)
    player_name = Column(String, index=True)
    prop_id = Column(Integer, index=True)
    sport = Column(String, index=True, default="NBA")
    l5_hit_rate = Column(Float)
    l10_hit_rate = Column(Float)
    l20_hit_rate = Column(Float)
    last_percent_total = Column(String)
    last_percent_rate = Column(Float)
    worst_percent_total = Column(String)
    worst_percent_rate = Column(Float)
