from sqlalchemy import Column, Integer, String, Float

from alphabetter.nba_backend.database import Base  # this does not work


class PlayerStats(Base):
    __tablename__ = "player_stats"

    player_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    team = Column(String)
    games_played = Column(Integer)
    points_per_game = Column(Float)
    assists_per_game = Column(Float)
    rebounds_per_game = Column(Float)


class Table2(Base):
    __tablename__ = "table2"

    player_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
