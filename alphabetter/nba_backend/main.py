from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PlayerGameLog, PrizePicksProp, PlayerStatsCalculated
from alphabetter.nba_backend.stat_collector.lastx import calculate_hit_rates, store_calculated_stats
from alphabetter.nba_backend.player_utils import get_player_id
from alphabetter.nba_backend.crud.player_gamelogs import fetch_player_gamelogs


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/player-gamelogs/{player_name}")
async def get_player_gamelogs(player_name: str, db: Session = Depends(get_db)):
    game_logs = fetch_player_gamelogs(player_name, db)
    if game_logs is None:
        return {"message": f"Player '{player_name}' not found."}
    return {"game_logs": game_logs}



@app.get("/api/props")
async def get_props(db: Session = Depends(get_db)):
    props = db.query(PrizePicksProp).all()
    return {"props": props}

@app.get("/api/player-stats-calculated")
async def get_player_stats_calculated(db: Session = Depends(get_db)):
    stats = db.query(PlayerStatsCalculated).all()
    return {"stats": stats}

@app.post("/api/calculate-stats/{prop_id}")
async def calculate_stats(prop_id: int, db: Session = Depends(get_db)):
    stats = calculate_hit_rates(db, prop_id)
    if stats:
        store_calculated_stats(db, stats)
        return {"message": "Stats calculated and stored successfully"}
    else:
        return {"message": "No games found for the player"}

@app.get("/api/player/{player_name}")
async def get_player_id_endpoint(player_name: str, db: Session = Depends(get_db)):
    return get_player_id(player_name, db)

@app.get("/api/last_x/{prop_id}/{num_games}")
async def get_player_last_x(prop_id: int, num_games: int, db: Session = Depends(get_db)):

    prop = db.query(PrizePicksProp).filter(PrizePicksProp.id == prop_id).first()
    if not prop:
        return {"message": f"Prop with id '{prop_id}' not found."}

    player_id = prop.player_id

    # Mapping of stat names from PrizePicksProp to PlayerGameLog
    #TODO most of the right side is wrong...
    stat_mapping = {
        "Points": "pts",  # Points scored
        "Rebounds": "reb",  # Total rebounds
        "Offensive Rebounds": "oreb",  # Offensive rebounds
        "Defensive Rebounds": "dreb",  # Defensive rebounds
        "Assists": "ast",  # Assists
        "Steals": "stl",  # Steals
        "Blocks": "blk",  # Blocks
        "Blocked Shots": "blk",  # Alias for Blocks
        "Turnovers": "tov",  # Turnovers
        "3-PT Made": "fg3m",  # 3-Point field goals made
        "Free Throws Made": "ftm",  # Free throws made
        "FG Made": "fgm",  # Field goals made
        "FG Attempted": "fga",  # Field goals attempted
        "3-PT Attempted": "fg3a",  # 3-Point field goals attempted
        # Derived stats
        "Rebs+Asts": ["reb", "ast"],  # Rebounds + Assists
        "Pts+Rebs+Asts": ["pts", "reb", "ast"],  # Points + Rebounds + Assists
        "Pts+Asts": ["pts", "ast"],  # Points + Assists
        "Pts+Rebs": ["pts", "reb"],  # Points + Rebounds
        "Blks+Stls": ["blk", "stl"], 
    }


    stat_type = stat_mapping.get(prop.stat)
    if not stat_type:
        return {"message": f"Stat '{prop.stat}' not found in PlayerGameLog."}

    game_logs = db.query(PlayerGameLog).filter(
        PlayerGameLog.player_id == player_id
    ).order_by(PlayerGameLog.game_date.desc()).limit(num_games).all()

    if not game_logs:
        return {"message": "No game logs found for the player."}

    result_info = []
    for game_log in game_logs:
        if isinstance(stat_type, list):  # Handle compound stats
            game_stat = sum(getattr(game_log, stat) for stat in stat_type)
        else:  # Handle single stats
            game_stat = getattr(game_log, stat_type)

        game_minutes = getattr(game_log, "min")
        game_date = getattr(game_log, "game_date")
        game_matchup = getattr(game_log, "matchup")

        result_info.append({
            "game_date": game_date,
            "matchup": game_matchup,
            "game_minutes": game_minutes,
            "stat_value": game_stat
        })

    return {
        "player_id": player_id,
        "player_name": prop.player_name,
        "prop": {
            "stat": prop.stat,
            "target": prop.target,
            "over_under": prop.over_under,
            "odds_type": prop.odds_type
        },
        "game_logs": result_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)