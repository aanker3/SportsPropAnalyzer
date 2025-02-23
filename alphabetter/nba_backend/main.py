from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PlayerGameLog, PrizePicksProp
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)