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
    calculate_and_store_stats_bulk
)
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.common.nba_api_common import get_player_id


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

def fetch_and_calculate_and_store():
    total_start_time = time.time()  # Start timing the entire process

    delete_all_rows(session=next(get_db()))
    # Load and create props
    generate_prize_picks_json()

    bet_data = load_bets_json()
    props = create_props(bet_data)

    db: Session = next(get_db())
    fetched_players = set()
    new_props = []  # Collect new props to batch commit

    total_props = len(props)  # Get the total number of props

    for index, prop in enumerate(props, start=1):  # Add a counter to the loop
        print(f"Processing prop {index}/{total_props} for {prop.player_name}...")  # Display progress

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

        # Store prop in memory for batch commit
        new_prop = PrizePicksProp(
            player_name=prop.player_name,
            player_id=player_id,
            stat=prop.stat,
            target=prop.target,
            over_under=prop.over_under,
            odds_type=prop.odds_type.value,
        )
        new_props.append(new_prop)

    # Batch commit all new props
    db.add_all(new_props)  # Add all props to the session
    db.commit()

    # Refresh the props to get their IDs
    for new_prop in new_props:
        db.refresh(new_prop)  # Refresh to populate the `id` field

    # Batch calculate and store stats
    calculate_and_store_stats_bulk(db, new_props)

    db.close()

    # Debug information
    print(f"\n=== Debug Information ===")
    print(f"🎉 Total time taken: {time.time() - total_start_time:.2f} seconds")
    print(f"✅ Total props stored: {len(new_props)}")
    print(f"✅ Total players fetched: {len(fetched_players)}")
    print(f"=========================\n")


if __name__ == "__main__":
    fetch_and_calculate_and_store()