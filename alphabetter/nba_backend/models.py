from sqlalchemy import Column, Integer, String, Float, Date
from alphabetter.nba_backend.database import Base

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
    __tablename__ = "player_game_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, index=True)
    team_id = Column(Integer)
    game_date = Column(Date)
    matchup = Column(String)
    wl = Column(String)
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

class TeamInfo(Base):
    __tablename__ = "team_info"

    team_id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, primary_key=True, index=True)
    # abbreviation = Column(String)
    # city = Column(String)
    # state = Column(String)
    # year_founded = Column(Integer)
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