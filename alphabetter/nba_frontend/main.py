from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from alphabetter.nba_backend.database import Base, get_db, DATABASE_URL
from alphabetter.nba_backend.models import PrizePicksProp, TeamInfo

app = FastAPI()

# Set up the database engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/props")
async def get_props():
    # Query all PrizePicks props
    props = session.query(PrizePicksProp).all()
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
    return {"props": props_list}

@app.get("/api/teams")
async def get_teams():
    # Query all TeamInfo
    teams = session.query(TeamInfo).all()
    teams_list = [
        {
            "team_id": team.team_id,
            "game_id": team.game_id,
            "game_date": team.game_date,
            "matchup": team.matchup,
            "wl": team.wl,
            "w": team.w,
            "l": team.l,
            "w_pct": team.w_pct,
            "min": team.min,
            "fgm": team.fgm,
            "fga": team.fga,
            "fg_pct": team.fg_pct,
            "fg3m": team.fg3m,
            "fg3a": team.fg3a,
            "fg3_pct": team.fg3_pct,
            "ftm": team.ftm,
            "fta": team.fta,
            "ft_pct": team.ft_pct,
            "oreb": team.oreb,
            "dreb": team.dreb,
            "reb": team.reb,
            "ast": team.ast,
            "stl": team.stl,
            "blk": team.blk,
            "tov": team.tov,
            "pf": team.pf,
            "pts": team.pts,
        }
        for team in teams
    ]
    return {"teams": teams_list}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)