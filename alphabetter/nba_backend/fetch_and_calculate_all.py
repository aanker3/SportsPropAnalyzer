import time
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from alphabetter.nba_backend.database import DATABASE_URL, Base
from alphabetter.nba_backend.models import PrizePicksProp, PlayerGameLog, PlayerStatsCalculated, PlayerStats
from alphabetter.nba_backend.fetch_and_store_prop_data import (
    generate_prize_picks_json,
    load_bets_json,
    create_props,
    store_prize_picks_props,
)
from alphabetter.nba_backend.fetch_and_store_player_stats import (
    fetch_player_stats,
    store_player_stats,
)
from alphabetter.nba_backend.stat_collector.calculate_and_store_lastx import (
    store_calculated_stats,
    calculate_hit_rates,
)
from alphabetter.nba_backend.database import get_db
from common.nba_api_common import get_player_id


# async_process_props.py

def delete_all_rows(session: Session):
    """Delete all rows from all tables."""
    print("🚨 Deleting all rows from all tables...")
    start_time = time.time()
    session.query(PlayerStatsCalculated).delete()
    session.query(PlayerGameLog).delete()
    session.query(PrizePicksProp).delete()
    session.query(PlayerStats).delete()
    session.commit()
    elapsed_time = time.time() - start_time
    print(f"✅ All rows deleted in {elapsed_time:.2f} seconds.")

def main():
    total_start_time = time.time()  # Start timing the entire process

    delete_all_rows(session=next(get_db()))
    # Load and create props
    generate_prize_picks_json()

    bet_data = load_bets_json()
    props = create_props(bet_data)

    db: Session = next(get_db())
    fetched_players = set()

    for prop in props:
        if prop.stat == "Fantasy Score" or prop.stat == "Dunks":  # Skip unsupported stats
            print(f"Skipping Fantasy Score for {prop.player_name}")
            continue

        # Get player_id
        try:
            player_id = get_player_id(prop.player_name)
        except ValueError as e:
            print(f"❌ {e} Skipping.")
            continue

        if player_id is None:
            print(f"Player ID not found for {prop.player_name}, skipping.")
            continue

        # Time processing for each player
        player_start_time = time.time()

        # Fetch & store player stats if not already done
        if player_id not in fetched_players:
            try:
                player_name, team, team_id, game_logs = fetch_player_stats(player_id)
                store_player_stats(db, player_id, player_name, team, team_id, game_logs)
                fetched_players.add(player_id)
                print(f"✅ Stored stats for {player_name}")
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Failed to fetch/store stats for {prop.player_name}: {e}")
                continue

        # Store prop in DB
        new_prop = PrizePicksProp(
            player_name=prop.player_name,
            player_id=player_id,
            stat=prop.stat,
            target=prop.target,
            over_under=prop.over_under,
            odds_type=prop.odds_type.value,
        )
        db.add(new_prop)
        db.commit()

        # Calculate and store lastX stats
        session = db  # reuse
        calculated_stats = calculate_hit_rates(session, new_prop.id)
        if calculated_stats:
            store_calculated_stats(session, calculated_stats)
            print(f"✅ Calculated and stored stats for prop_id {new_prop.id}")
        else:
            print(f"❌ Failed stats calc for prop_id {new_prop.id}")

        # Log time taken for this player
        player_elapsed_time = time.time() - player_start_time
        print(f"⏱️ Time taken for {prop.player_name}: {player_elapsed_time:.2f} seconds")
        print(f"# of players fetched: {len(fetched_players)}")
        print(f"# of props stored: {len(props)}")
    db.close()

    # Log total time taken
    total_elapsed_time = time.time() - total_start_time
    print(f"🎉 Total time taken for all players: {total_elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()