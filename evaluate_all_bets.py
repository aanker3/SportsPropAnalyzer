import argparse
import pandas as pd
import sys
from nba_api.stats.endpoints import playergamelog, commonallplayers
from enum import Enum
from get_props import load_bets_json, create_props, Prop
import time
from typing import Dict, List
from dataclasses import dataclass, field
import statistics


# Define the PlayerData class
@dataclass
class PlayerData:
    player_name: str
    stats: Dict[str, List[float]] = field(default_factory=dict)
    team: str = ""
    position: str = ""
    num_games: int = 20


# Define the BetEvaluation class
@dataclass
class BetEvaluation:
    player_name: str
    stat_name: str
    bet_target: float
    over_under: str
    hits: int
    misses: int
    games_active: int
    games_missed: int
    hit_rate: float
    num_games: int
    median: float = 0.0
    mode: float = 0.0
    average: float = 0.0
    odds_type: str = "standard"


# Enum for Over/Under
class OverUnder(Enum):
    OVER = "over"
    UNDER = "under"


# Mapping of human-readable stat names to NBA API stat keys
STAT_MAPPING = {
    "Points": "PTS",
    "Rebounds": "REB",  # Total rebounds
    "Offensive Rebounds": "OREB",  # Offensive rebounds
    "Defensive Rebounds": "DREB",
    "Assists": "AST",
    "Steals": "STL",
    "Blocks": "BLK",
    "Turnovers": "TOV",  # Turnovers
    "3-PT Made": "FG3M",  # 3-Point field goals made
    "Free Throws Made": "FTM",  # Free throws made
    "FG Made": "FGM",  # Field goals made
    "FG Attempted": "FGA",  # Field goals attempted
    "3-PT Attempted": "FG3A",  # 3-Point field goals attempted
    # Derived stats
    "Rebs+Asts": "REB+AST",  # Rebounds + Assists
    "Pts+Rebs+Asts": "PTS+REB+AST",  # Points + Rebounds + Assists
    "Pts+Asts": "PTS+AST",  # Points + Assists
    "Pts+Rebs": "PTS+REB",  # Points + Rebounds
}


# Function to fetch player ID
def get_player_id(player_name: str) -> int:
    """Fetches the player ID for a given player name using the NBA API."""
    players = commonallplayers.CommonAllPlayers(is_only_current_season=0)
    players_df = players.get_data_frames()[0]
    matching_players = players_df[
        players_df["DISPLAY_FIRST_LAST"].str.contains(player_name, case=False, na=False)
    ]
    if not matching_players.empty:
        return matching_players["PERSON_ID"].iloc[0]
    else:
        print(f"No players found for name: {player_name}")
        return None


# Global ping counter
pings = 0


# Function to fetch the last x game stats
def get_last_x_game_stats(player_id: int, num_games: int = 20) -> pd.DataFrame:
    """Fetches the last `num_games` for a player using the NBA API."""
    global pings  # Declare `pings` as global to modify it
    pings += 1  # Increment the ping counter
    # print(f"PINGING NBA, PINGS = {pings}")  # Print the current ping count

    # Fetch the game log data
    gamelog = playergamelog.PlayerGameLog(player_id=player_id)
    gamelog_df = gamelog.get_data_frames()[0]
    return gamelog_df.head(num_games)


# Function to extract specific stats
def get_stat_from_last_x_games(gamelog_df: pd.DataFrame, stat: str) -> tuple:
    """Extracts a specific stat from a player's game log, including derived stats."""
    if "+" in stat:  # Handle derived stats
        stat_keys = stat.split("+")
        stat_dict = {}
        for _, row in gamelog_df.iterrows():
            stat_value = 0
            for key in stat_keys:
                stat_value += row.get(key, 0)  # Sum the relevant stats
            stat_dict[row["GAME_DATE"]] = stat_value
    else:  # Handle regular stats
        stat_dict = {
            row["GAME_DATE"]: row.get(stat, 0) for _, row in gamelog_df.iterrows()
        }

    num_games_missed = sum(1 for value in stat_dict.values() if pd.isna(value))
    return stat_dict, num_games_missed


# Function to evaluate a bet
def evaluate_bet(
    stat_results: tuple,
    bet_target: float,
    over_under: OverUnder,
    num_games: int,
    player_name: str,
    stat_name: str,
    odds_type: str,
) -> BetEvaluation:
    """Evaluates a bet and returns a BetEvaluation object."""
    stat_dict, num_games_missed = stat_results
    hits, misses, games_active = 0, 0, 0
    stat_values = []

    for stat in stat_dict.values():
        if pd.isna(stat):  # Skip if stat is NaN
            continue

        stat_values.append(stat)

        if over_under == OverUnder.OVER and stat > bet_target:
            hits += 1
        elif over_under == OverUnder.UNDER and stat < bet_target:
            hits += 1
        else:
            misses += 1
        games_active += 1

    hit_rate = hits / games_active if games_active > 0 else 0

    # Calculate median, mode, and average
    median = statistics.median(stat_values) if stat_values else 0
    try:
        mode = statistics.mode(stat_values) if stat_values else 0
    except statistics.StatisticsError:  # Handle no unique mode
        mode = None
    average = sum(stat_values) / len(stat_values) if stat_values else 0

    # Return the data as a BetEvaluation object
    return BetEvaluation(
        player_name=player_name,
        stat_name=stat_name,
        bet_target=bet_target,
        over_under=over_under.value,
        hits=hits,
        misses=misses,
        games_active=games_active,
        games_missed=num_games_missed,
        hit_rate=hit_rate,
        num_games=num_games,
        median=median,
        mode=mode,
        average=average,
        odds_type=odds_type,  # Include odds_type
    )


# Function to print bet evaluation results
def print_bet_evaluation(bet_info: BetEvaluation, print_stats: bool = False):
    """Prints the bet evaluation results in either a detailed or quick format."""
    player_name = bet_info.player_name
    stat_name = bet_info.stat_name
    over_under = bet_info.over_under.capitalize()
    bet_target = bet_info.bet_target
    hit_rate = bet_info.hit_rate
    num_games = bet_info.num_games
    median = bet_info.median
    mode = bet_info.mode
    average = bet_info.average
    odds_type = bet_info.odds_type  # Get odds_type

    # If the hit rate is high or print_stats is True, show detailed output
    if hit_rate > 0.75 or print_stats:
        display_player_stats_last_20_games(player_name)
        print("\n" + "=" * 50)
        print(f"Detailed Bet Evaluation for {player_name} - {stat_name}")
        print(f"Target: {over_under} {bet_target} over last {num_games} games")
        print(f"Hit Rate: {hit_rate:.2%}")
        print(f"Odds Type: {odds_type.capitalize()}")  # Include odds_type
        print("-" * 50)
        print(f"- Hits: {bet_info.hits}")
        print(f"- Misses: {bet_info.misses}")
        print(f"- Games Active: {bet_info.games_active}")
        print(f"- Games Missed (No Data): {bet_info.games_missed}")
        print(f"- Average {stat_name}: {average:.2f}")
        print(f"- Median {stat_name}: {median}")
        print(f"- Mode {stat_name}: {mode}")
        print("=" * 50 + "\n")
    else:
        # Quick summary for lower hit rates
        print(
            f"{player_name} - {stat_name}: {over_under} {bet_target} | "
            f"Hit Rate: {hit_rate:.2%} | Odds Type: {odds_type.capitalize()}"  # Include odds_type
        )


# Add a cache dictionary at the top of your script
player_stats_cache = {}


# Modify the go_through_props_and_evaluate function
def go_through_props_and_evaluate(props: List[Prop], num_games: int = 20):
    """Evaluates a list of Prop objects and prints the results."""
    for prop in props:  # [:10]:
        time.sleep(0.5)  # Add a delay to avoid hitting API rate limits

        # Check if the player's stats are already in the cache
        if prop.player_name in player_stats_cache:
            gamelog_df = player_stats_cache[prop.player_name]
        else:
            # Fetch the player's stats and store them in the cache
            player_id = get_player_id(prop.player_name)
            if not player_id:
                print(f"Player {prop.player_name} not found. Skipping.")
                continue

            gamelog_df = get_last_x_game_stats(player_id, num_games)
            player_stats_cache[prop.player_name] = gamelog_df

        # Convert the human-readable stat name
        stat_key = STAT_MAPPING.get(prop.stat)
        if not stat_key:
            print(f"Statistic '{prop.stat}' not recognized. Skipping.")
            continue

        try:
            stat_results = get_stat_from_last_x_games(gamelog_df, stat_key)
            bet_info = evaluate_bet(
                stat_results,
                prop.target,
                OverUnder(prop.over_under),
                num_games,
                prop.player_name,
                prop.stat,
                prop.odds_type.value,  # Pass odds_type
            )
            # Now we simply pass bet_info to the printer
            print_bet_evaluation(bet_info)
        except KeyError:
            print(f"Statistic '{stat_key}' not found for {prop.player_name}. Skipping.")


# Function to display player stats for the last 20 games
def display_player_stats_last_20_games(player_name: str):
    """Displays a nicely formatted summary of a player's last 20 games using the NBA API."""
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"No player found for: {player_name}")
        return

    gamelog_df = get_last_x_game_stats(player_id, num_games=20)
    if gamelog_df.empty:
        print(f"No game logs found for: {player_name}")
        return

    columns_to_display = [
        "GAME_DATE",
        "MATCHUP",
        "WL",
        "MIN",
        "PTS",
        "REB",
        "AST",
        "STL",
        "BLK",
        "TOV",
        "FGM",
        "FGA",
        "FG_PCT",
        "FG3M",
        "FG3A",
        "FG3_PCT",
        "FTM",
        "FTA",
        "FT_PCT",
    ]

    columns_to_display = [
        col for col in columns_to_display if col in gamelog_df.columns
    ]
    display_df = gamelog_df[columns_to_display]
    print(f"\nLast 20 Games for {player_name}:\n")
    print(display_df.to_string(index=False))


# Main function for command-line usage
def main():
    parser = argparse.ArgumentParser(
        description="Evaluate NBA player stats for betting purposes."
    )
    parser.add_argument(
        "--player", type=str, help="Player's full name (e.g., 'Nikola Jokić')."
    )
    parser.add_argument(
        "--statistic", type=str, help="Statistic to evaluate (e.g., 'PTS', 'REB')."
    )
    parser.add_argument("--bet_target", type=float, help="Target value for the bet.")
    parser.add_argument(
        "--over_under",
        type=str,
        choices=["over", "under"],
        help="Specify 'over' or 'under'.",
    )
    parser.add_argument(
        "--num_games",
        type=int,
        default=20,
        help="Number of games to evaluate (default: 20).",
    )

    args = parser.parse_args()

    # Check if specific arguments are provided for single evaluation
    if args.player and args.statistic and args.bet_target and args.over_under:
        # Process a single player/statistic evaluation
        player_name = args.player
        statistic = args.statistic.upper()
        bet_target = args.bet_target
        over_under = args.over_under
        num_games = args.num_games

        # Fetch player ID
        player_id = get_player_id(player_name)
        if not player_id:
            print("Player not found. Exiting.")
            sys.exit(1)

        # Fetch game logs
        try:
            gamelog_df = get_last_x_game_stats(player_id, num_games)
        except Exception as e:
            print(f"Error fetching game logs: {e}")
            sys.exit(1)

        # Extract stats
        try:
            stat_results = get_stat_from_last_x_games(gamelog_df, statistic)
        except KeyError:
            print(f"Statistic '{statistic}' not found in game logs.")
            sys.exit(1)

        # Evaluate bet
        bet_info = evaluate_bet(
            stat_results,
            bet_target,
            OverUnder(over_under),
            num_games,
            player_name,
            statistic,
        )
        print_bet_evaluation(bet_info, print_stats=True)
    else:
        # Default to batch evaluation
        print("Running batch evaluation...")
        bet_data = load_bets_json()
        props = create_props(bet_data)
        go_through_props_and_evaluate(props)


if __name__ == "__main__":
    main()
    # print(f"player_stats_cache= {player_stats_cache}")
    # To get pts:
    # print(player_stats_cache["Amir Coffey"]["PTS"])
