from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphabetter.nba_backend.database import DATABASE_URL, Base
from alphabetter.nba_backend.models import PlayerGameLog, PlayerStatsCalculated, PrizePicksProp
import argparse

STAT_MAPPING = {
    "Points": "pts",
    "Rebounds": "reb",
    "Offensive Rebounds": "oreb",
    "Defensive Rebounds": "dreb",
    "Assists": "ast",
    "Steals": "stl",
    "Blocks": "blk",
    "Blocked Shots": "blk",
    "Turnovers": "tov",
    "3-PT Made": "fg3m",
    "Free Throws Made": "ftm",
    "FG Made": "fgm",
    "FG Attempted": "fga",
    "3-PT Attempted": "fg3a",
    # Combined stats
    "Rebs+Asts": ["reb", "ast"],
    "Pts+Rebs+Asts": ["pts", "reb", "ast"],
    "Pts+Asts": ["pts", "ast"],
    "Pts+Rebs": ["pts", "reb"],
    "Blks+Stls": ["blk", "stl"],
}


def _calc_hit_rate(games, target, over_under, stat):
    """Calculate hit rate for given games list and specified stat."""
    if not games:
        return 0

    def get_stat_value(game):
        # Handle single or combined stats
        if isinstance(stat, list):
            return sum(getattr(game, s, 0) for s in stat)
        return getattr(game, stat, 0)

    hits = sum(
        1 for game in games
        if (get_stat_value(game) >= target if over_under == 'over' else get_stat_value(game) < target)
    )
    return hits / len(games)


def last_percent(hits: list[bool]) -> tuple[float, str]:
    # Initialize best values
    max_percent = 0.0
    best_hit_count = 0
    best_total = 0
    start = 0  # window always starts at index 0

    # Expand the window one element at a time
    for end in range(start, len(hits)):
        window = hits[start:end + 1]
        total = end - start + 1
        hit_count = sum(window)
        percent = hit_count / total

        if total == 1:
            continue  # Don't allow 1/1

        # Handle 100% hit rate exceptions
        is_hundred = percent == 1.0
        if is_hundred and total <= 5:
            # Skip unless followed by 2 losses
            if not (len(hits) > end + 2 and not hits[end + 1] and not hits[end + 2]):
                continue  # skip this perfect short window

        # Update max if current window is better
        if percent >= max_percent:
            max_percent = percent
            best_hit_count = hit_count
            best_total = total

    # Return the best percentage and its fraction string
    return round(max_percent * 100, 2), f"{best_hit_count}/{best_total}"


def calculate_best_streak_until_last_miss(games, target, over_under):
    """
    Calculate the longest consecutive hit streak until the first miss.
    - The streak resets at the first miss.
    - Counts from the most recent game backward.
    """
    current_streak = 0

    for game in games:
        hit = game.pts >= target if over_under == 'over' else game.pts < target
        if hit:
            current_streak += 1
        else:
            break  # Stop at the first miss

    return current_streak

def calculate_hit_rates(session: Session, prop_id: int):
    prop = session.query(PrizePicksProp).filter(PrizePicksProp.id == prop_id).first()
    if not prop:
        print(f"No prop found for prop_id: {prop_id}")
        return None

    player_id = prop.player_id
    player_name = prop.player_name
    target = prop.target
    over_under = prop.over_under
    odds_type = prop.odds_type
    stat = STAT_MAPPING.get(prop.stat, "pts")

    print(f"Calculating hit rates for {player_name} on {prop.stat} with odds_type: {odds_type}")

    player_games = session.query(PlayerGameLog).filter(
        PlayerGameLog.player_id == player_id
    ).order_by(PlayerGameLog.game_date.desc()).all()

    if not player_games:
        print("No games found for the player")
        return None

    l5_hit_rate = _calc_hit_rate(player_games[:5], target, over_under, stat)
    l10_hit_rate = _calc_hit_rate(player_games[:10], target, over_under, stat)
    l20_hit_rate = _calc_hit_rate(player_games[:20], target, over_under, stat)

    # Build hit list for last_percent
    def get_stat_value(game):
        if isinstance(stat, list):
            return sum(getattr(game, s, 0) for s in stat)
        return getattr(game, stat, 0)

    games = [
        (get_stat_value(game) >= target if over_under == 'over' else get_stat_value(game) < target)
        for game in player_games
        if game.min and game.min > 0
    ]
    print(f"games= {games}")  # Debugging line to check the games list
    last_percent_rate, last_percent_total = last_percent(games)

    return {
        "player_id": player_id,
        "player_name": player_name,
        "prop_id": prop_id,
        "l5_hit_rate": l5_hit_rate,
        "l10_hit_rate": l10_hit_rate,
        "l20_hit_rate": l20_hit_rate,
        "last_percent_total": last_percent_total,
        "last_percent_rate": last_percent_rate / 100,  # store as 0.882 not 88.2
    }


def store_calculated_stats(session: Session, stats: dict):
    # Check if a record for the given prop_id already exists
    existing_record = session.query(PlayerStatsCalculated).filter(
        PlayerStatsCalculated.prop_id == stats["prop_id"]
    ).first()

    if existing_record:
        # Update the existing record
        existing_record.l5_hit_rate = stats["l5_hit_rate"]
        existing_record.l10_hit_rate = stats["l10_hit_rate"]
        existing_record.l20_hit_rate = stats["l20_hit_rate"]
        existing_record.last_percent_total = stats["last_percent_total"]
        existing_record.last_percent_rate = stats["last_percent_rate"]
        print(f"""🔄 Updating existing record:
        Player ID: {existing_record.player_id}
        Name: {existing_record.player_name}
        Prop ID: {existing_record.prop_id}
        L5: {existing_record.l5_hit_rate}
        L10: {existing_record.l10_hit_rate}
        L20: {existing_record.l20_hit_rate}
        Last %: {existing_record.last_percent_total} ({existing_record.last_percent_rate})
        """)
    else:
        # Create a new record
        player_stats_calculated = PlayerStatsCalculated(
            player_id=stats["player_id"],
            player_name=stats["player_name"],
            prop_id=stats["prop_id"],
            l5_hit_rate=stats["l5_hit_rate"],
            l10_hit_rate=stats["l10_hit_rate"],
            l20_hit_rate=stats["l20_hit_rate"],
            last_percent_total=stats["last_percent_total"],
            last_percent_rate=stats["last_percent_rate"]
        )
        session.add(player_stats_calculated)
        print(f"""➡️ Adding new record:
        Player ID: {player_stats_calculated.player_id}
        Name: {player_stats_calculated.player_name}
        Prop ID: {player_stats_calculated.prop_id}
        L5: {player_stats_calculated.l5_hit_rate}
        L10: {player_stats_calculated.l10_hit_rate}
        L20: {player_stats_calculated.l20_hit_rate}
        Last %: {player_stats_calculated.last_percent_total} ({player_stats_calculated.last_percent_rate})
        """)

    # Commit the changes to the database
    session.commit()
    print("✅ Stats committed to database.")

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
    parser.add_argument("prop_id", type=int, nargs="?", help="The ID of the prop to calculate hit rates for")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    if args.prop_id is not None:
        # Run for one specific prop_id
        prop_id = args.prop_id
        stats = calculate_hit_rates(session, prop_id)
        if stats:
            print(f"""🎯 Stats for prop_id {prop_id}:
        Player ID: {stats['player_id']}
        Name: {stats['player_name']}
        Prop ID: {stats['prop_id']}
        L5: {stats['l5_hit_rate']}
        L10: {stats['l10_hit_rate']}
        L20: {stats['l20_hit_rate']}
        Last %: {stats['last_percent_total']} ({stats['last_percent_rate']})
        """)
        else:
            print("❌ Failed to calculate stats for the given prop_id")
    else:
        # Batch mode — full stats including last% stored in DB
        props = session.query(PrizePicksProp).all()
        for prop in props:
            print(f"Processing prop_id: {prop.id} for player: {prop.player_name}")
            stats = calculate_hit_rates(session, prop.id)
            if stats:
                store_calculated_stats(session, stats)
                print(f"✅ Hit rates calculated and stored for prop_id: {prop.id}")
            else:
                print(f"❌ Failed to calculate hit rates for prop_id: {prop.id}")


if __name__ == "__main__":
    main()
