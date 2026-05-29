import time
from pathlib import Path
from sqlalchemy.orm import Session
from alphabetter.nba_backend.database import SessionLocal
from alphabetter.nba_backend.models import (
    PrizePicksProp, PlayerGameLog, PlayerStatsCalculated, PlayerStats, MLBPlayerGameLog
)
from alphabetter.nba_backend.get_props.gen_prizepicks_json import gen_prizepicks_json, gen_mlb_prizepicks_json
from alphabetter.nba_backend.get_props.get_props import load_bets_json, create_props
from alphabetter.nba_backend.fetch_and_store_player_stats import store_player_stats
from alphabetter.nba_backend.fetch_player_stats_espn import build_espn_player_map, fetch_player_stats_espn
from alphabetter.nba_backend.fetch_player_stats_espn_mlb import (
    build_mlb_player_map, fetch_mlb_player_stats, store_mlb_player_stats
)
from alphabetter.nba_backend.stat_collector.calculate_and_store_lastx import (
    store_calculated_stats, calculate_hit_rates, calculate_mlb_hit_rates
)
from alphabetter.nba_backend.stat_collector.mlb_stat_mapping import MLB_UNSUPPORTED_STATS

NBA_PROPS_FILE = Path(__file__).parent / "get_props" / "prizepicks_props.json"
MLB_PROPS_FILE = Path(__file__).parent / "get_props" / "prizepicks_props_mlb.json"

NBA_UNSUPPORTED_STATS = {
    "Fantasy Score",
    "Dunks",
    "Points - 1st 3 Minutes",
    "Assists - 1st 3 Minutes",
    "Rebounds - 1st 3 Minutes",
    "Offensive Rebounds",
    "Defensive Rebounds",
}


def _clear_nba_data(session: Session):
    print("Clearing NBA data...")
    session.query(PlayerStatsCalculated).filter(PlayerStatsCalculated.sport == "NBA").delete()
    session.query(PlayerGameLog).delete()
    session.query(PrizePicksProp).filter(PrizePicksProp.sport == "NBA").delete()
    session.query(PlayerStats).delete()
    session.commit()


def _clear_mlb_data(session: Session):
    print("Clearing MLB data...")
    session.query(PlayerStatsCalculated).filter(PlayerStatsCalculated.sport == "MLB").delete()
    session.query(MLBPlayerGameLog).delete()
    session.query(PrizePicksProp).filter(PrizePicksProp.sport == "MLB").delete()
    session.commit()


def run_nba_pipeline() -> int:
    start = time.time()
    db = SessionLocal()
    try:
        _clear_nba_data(db)
        gen_prizepicks_json()

        bet_data = load_bets_json(NBA_PROPS_FILE)
        props = create_props(bet_data)

        print("Building ESPN NBA player map...")
        espn_player_map = build_espn_player_map()

        fetched_players: set = set()
        stored_count = 0

        for index, prop in enumerate(props, start=1):
            if prop.stat in NBA_UNSUPPORTED_STATS:
                print(f"Skipping {prop.stat} for {prop.player_name}")
                continue

            espn_id = espn_player_map.get(prop.player_name)
            if not espn_id:
                print(f"ESPN ID not found for {prop.player_name}, skipping.")
                continue

            player_id = int(espn_id)

            if player_id not in fetched_players:
                try:
                    player_name, team, team_id, game_logs = fetch_player_stats_espn(espn_id, prop.player_name)
                    store_player_stats(db, player_id, player_name, team, team_id, game_logs)
                    fetched_players.add(player_id)
                    print(f"Stored {len(game_logs)} NBA logs for {player_name}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"Failed stats for {prop.player_name}: {e}")
                    continue

            new_prop = PrizePicksProp(
                player_name=prop.player_name,
                player_id=player_id,
                stat=prop.stat,
                target=prop.target,
                over_under=prop.over_under,
                odds_type=prop.odds_type.value,
                sport="NBA",
            )
            db.add(new_prop)
            db.commit()

            calculated = calculate_hit_rates(db, new_prop)
            if calculated:
                store_calculated_stats(db, calculated)
            else:
                print(f"No stats for {prop.player_name} / {prop.stat}")

            stored_count += 1
            print(f"NBA [{index}/{len(props)}]: {prop.player_name} {prop.stat}")

    finally:
        db.close()

    print(f"NBA pipeline done in {time.time()-start:.1f}s | Props: {stored_count}")
    return stored_count


def run_mlb_pipeline() -> int:
    start = time.time()
    db = SessionLocal()
    try:
        _clear_mlb_data(db)
        gen_mlb_prizepicks_json()

        bet_data = load_bets_json(MLB_PROPS_FILE)
        props = create_props(bet_data)

        print("Building ESPN MLB player map...")
        mlb_player_map = build_mlb_player_map()

        fetched_players: set = set()
        stored_count = 0

        for index, prop in enumerate(props, start=1):
            if prop.stat in MLB_UNSUPPORTED_STATS:
                print(f"Skipping {prop.stat} for {prop.player_name}")
                continue

            player_info = mlb_player_map.get(prop.player_name)
            if not player_info:
                print(f"MLB ESPN ID not found for {prop.player_name}, skipping.")
                continue

            espn_id = player_info["id"]
            is_pitcher = player_info["is_pitcher"]
            player_id = int(espn_id)

            if player_id not in fetched_players:
                try:
                    player_name, team, team_id, game_logs = fetch_mlb_player_stats(espn_id, prop.player_name, is_pitcher)
                    store_mlb_player_stats(db, player_id, player_name, team, team_id, game_logs)
                    fetched_players.add(player_id)
                    print(f"Stored {len(game_logs)} MLB logs for {player_name}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"Failed MLB stats for {prop.player_name}: {e}")
                    continue

            new_prop = PrizePicksProp(
                player_name=prop.player_name,
                player_id=player_id,
                stat=prop.stat,
                target=prop.target,
                over_under=prop.over_under,
                odds_type=prop.odds_type.value,
                sport="MLB",
            )
            db.add(new_prop)
            db.commit()

            calculated = calculate_mlb_hit_rates(db, new_prop)
            if calculated:
                store_calculated_stats(db, calculated)
            else:
                print(f"No MLB stats for {prop.player_name} / {prop.stat}")

            stored_count += 1
            print(f"MLB [{index}/{len(props)}]: {prop.player_name} {prop.stat}")

    finally:
        db.close()

    print(f"MLB pipeline done in {time.time()-start:.1f}s | Props: {stored_count}")
    return stored_count


def fetch_and_calculate_and_store() -> int:
    total = run_nba_pipeline()
    try:
        total += run_mlb_pipeline()
    except Exception as e:
        print(f"MLB pipeline failed (NBA data intact): {e}")
    return total


if __name__ == "__main__":
    fetch_and_calculate_and_store()
