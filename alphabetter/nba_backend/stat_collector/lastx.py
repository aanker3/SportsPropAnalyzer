from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphabetter.nba_backend.database import DATABASE_URL, Base
from alphabetter.nba_backend.models import PlayerGameLog, PlayerStatsCalculated, PrizePicksProp
import argparse

def calculate_hit_rates(session: Session, prop_id: int):
    # Fetch the PrizePicksProp record using the prop_id
    prop = session.query(PrizePicksProp).filter(PrizePicksProp.id == prop_id).first()
    if not prop:
        print(f"No prop found for prop_id: {prop_id}")
        return None

    player_id = prop.player_id
    player_name = prop.player_name
    target = prop.target
    over_under = prop.over_under

    # Print the player_id being queried
    print(f"Calculating hit rates for player_id: {player_id}")

    # Check if there are records in PlayerGameLog for the given player_id
    player_games = session.query(PlayerGameLog).filter(PlayerGameLog.player_id == player_id).order_by(PlayerGameLog.game_date.desc()).limit(20).all()
    
    # Print the player games in a readable format
    formatted_games = [format_game(game) for game in player_games]
    print("Player games:", formatted_games)

    if not player_games:
        print("No games found for the player")
        return None

    l5_games = player_games[:5]
    l10_games = player_games[:10]
    l20_games = player_games

    if over_under == 'over':
        l5_hit_rate = sum(1 for game in l5_games if game.pts >= target) / len(l5_games) if l5_games else 0
        l10_hit_rate = sum(1 for game in l10_games if game.pts >= target) / len(l10_games) if l10_games else 0
        l20_hit_rate = sum(1 for game in l20_games if game.pts >= target) / len(l20_games) if l20_games else 0
    else:
        l5_hit_rate = sum(1 for game in l5_games if game.pts < target) / len(l5_games) if l5_games else 0
        l10_hit_rate = sum(1 for game in l10_games if game.pts < target) / len(l10_games) if l10_games else 0
        l20_hit_rate = sum(1 for game in l20_games if game.pts < target) / len(l20_games) if l20_games else 0

    return {
        "player_id": player_id,
        "player_name": player_name,
        "prop_id": prop_id,  # Add this line
        "l5_hit_rate": l5_hit_rate,
        "l10_hit_rate": l10_hit_rate,
        "l20_hit_rate": l20_hit_rate
    }

def store_calculated_stats(session: Session, stats: dict):
    player_stats_calculated = PlayerStatsCalculated(
        player_id=stats["player_id"],
        player_name=stats["player_name"],
        prop_id=stats["prop_id"],  # Add this line
        l5_hit_rate=stats["l5_hit_rate"],
        l10_hit_rate=stats["l10_hit_rate"],
        l20_hit_rate=stats["l20_hit_rate"]
    )
    session.add(player_stats_calculated)
    session.commit()
    print("stats committed to database")

def format_game(game):
    return {
        "game_date": game.game_date,
        "pts": game.pts,
        "reb": game.reb,
        "ast": game.ast,
        # Add other relevant attributes here
    }

def main():
    parser = argparse.ArgumentParser(description="Calculate hit rates for a given prop_id")
    parser.add_argument("prop_id", type=int, help="The ID of the prop to calculate hit rates for")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    stats = calculate_hit_rates(session, args.prop_id)
    if stats:
        store_calculated_stats(session, stats)
        print("Hit rates calculated and stored successfully")
    else:
        print("Failed to calculate hit rates")

if __name__ == "__main__":
    main()