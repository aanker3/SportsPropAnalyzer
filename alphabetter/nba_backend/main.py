from fastapi import FastAPI, Depends, BackgroundTasks
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

@app.post("/api/fetch_and_calculate_all_bg")
def run_pipeline_background(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_calculate_and_store)
    return {"status": "Task started in the background"}

@app.post("/api/fetch_and_calculate_all")
def run_pipeline_sync():
    prop_num = fetch_and_calculate_and_store()
    return {"prop_num": prop_num}

@app.get("/api/test_real_stats")
async def test_real_stats():
    url = "https://stats.nba.com/stats/playergamelog?PlayerID=1631105&Season=2023-24&SeasonType=Regular+Season"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nba.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.nba.com",
    }
    try:
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        return {"status": "success", "content": response.json()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

import pandas as pd

@app.get("/api/test_real_stats_bbref")
async def test_real_stats_bbref():
    try:
        url = "https://www.basketball-reference.com/players/g/garlada01/gamelog/2024"
        tables = pd.read_html(url)
        gamelog = tables[0].astype(object)  # Cast to avoid numpy float issues
        gamelog = gamelog.replace({float('inf'): None, float('-inf'): None})
        gamelog = gamelog.where(pd.notnull(gamelog), None)
        return {
            "status": "success",
            "games": gamelog.head(5).to_dict(orient="records")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/ping_stats_nba")
async def ping_stats_nba():
    """Ping stats.nba.com and return the result."""
    url = "https://stats.nba.com"
    try:
        response = requests.get(url, timeout=10)  # Set a timeout of 10 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors
        return {
            "status": "success",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:500],  # Return the first 500 characters of the response
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
        }

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
async def get_player_last_x(prop_id: int, num_games: int, db: Session = Depends(get_db)):

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