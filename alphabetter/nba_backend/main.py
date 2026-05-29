from fastapi import FastAPI, Depends, BackgroundTasks, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PlayerGameLog, PrizePicksProp, PlayerStatsCalculated
from alphabetter.nba_backend.stat_collector.calculate_and_store_lastx import calculate_hit_rates, store_calculated_stats, STAT_MAPPING, _get_stat_value
from alphabetter.nba_backend.player_utils import get_player_id
from alphabetter.nba_backend.crud.player_gamelogs import fetch_player_gamelogs
from alphabetter.nba_backend.fetch_and_calculate_all import fetch_and_calculate_and_store
import requests
import os

app = FastAPI()

# In production set ALLOWED_ORIGINS="https://your-vercel-app.vercel.app"
# Multiple origins: comma-separated list
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/api/player-gamelogs/{player_name}")
async def get_player_gamelogs(
    player_name: str = Path(..., max_length=100),
    db: Session = Depends(get_db)
):
    game_logs = fetch_player_gamelogs(player_name, db)
    if game_logs is None:
        return {"message": f"Player '{player_name}' not found."}
    return {"game_logs": game_logs}

@app.post("/api/fetch_and_calculate_all_bg")
def run_pipeline_background(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_calculate_and_store)
    return {"status": "Task started in the background"}

@app.post("/api/fetch_and_calculate_all")
def run_pipeline_sync():
    prop_num = fetch_and_calculate_and_store()
    return {"prop_num": prop_num}

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/api/props")
async def get_props(db: Session = Depends(get_db)):
    props = db.query(PrizePicksProp).all()
    return {"props": props}

@app.get("/api/player-stats-calculated")
async def get_player_stats_calculated(db: Session = Depends(get_db)):
    stats = db.query(PlayerStatsCalculated).all()
    return {"stats": stats}

@app.get("/api/player/{player_name}")
async def get_player_id_endpoint(player_name: str, db: Session = Depends(get_db)):
    return get_player_id(player_name, db)

@app.get("/api/last_x/{prop_id}/{num_games}")
async def get_player_last_x(
    prop_id: int = Path(..., gt=0),
    num_games: int = Path(..., gt=0, le=200),
    db: Session = Depends(get_db)
):

    prop = db.query(PrizePicksProp).filter(PrizePicksProp.id == prop_id).first()
    if not prop:
        return {"message": f"Prop with id '{prop_id}' not found."}

    player_id = prop.player_id

    stat_type = STAT_MAPPING.get(prop.stat)
    if not stat_type or stat_type == "fantasy_score":
        return {"message": f"Stat '{prop.stat}' not supported in game log view."}

    game_logs = db.query(PlayerGameLog).filter(
        PlayerGameLog.player_id == player_id
    ).order_by(PlayerGameLog.game_date.desc()).limit(num_games).all()

    if not game_logs:
        return {"message": "No game logs found for the player."}

    result_info = []
    for game_log in game_logs:
        game_stat = _get_stat_value(game_log, stat_type)

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