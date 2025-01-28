import argparse
import pandas as pd
import sys
from nba_api.stats.endpoints import playergamelog, commonallplayers
from enum import Enum
from get_props import get_prop_info
import time

# Enum for Over/Under
class OverUnder(Enum):
    OVER = "over"
    UNDER = "under"

STAT_MAPPING = {
    "Points": "PTS",
    "Rebounds": "REB",              # Total rebounds
    "Offensive Rebounds": "OREB",   # Offensive rebounds
    "Assists": "AST",
    "Steals": "STL",
    "Blocks": "BLK",
    "Turnovers": "TOV",             # Turnovers
    "3-Point Made": "FG3M"          # 3-Point field goals made
}

# Function to fetch player ID
def get_player_id(player_name):
    """
    Fetches the player ID for a given player name using the NBA API.
    """
    players = commonallplayers.CommonAllPlayers(is_only_current_season=0)
    players_df = players.get_data_frames()[0]
    matching_players = players_df[players_df['DISPLAY_FIRST_LAST'].str.contains(player_name, case=False, na=False)]
    if not matching_players.empty:
        # print(matching_players[['PERSON_ID', 'DISPLAY_FIRST_LAST']])
        return matching_players['PERSON_ID'].iloc[0]
    else:
        print(f"No players found for name: {player_name}")
        return None

# Function to fetch the last x game stats
def get_last_x_game_stats(player_id, num_games=20):
    """
    Fetches the last `num_games` for a player using the NBA API.
    """
    gamelog = playergamelog.PlayerGameLog(player_id=player_id)
    gamelog_df = gamelog.get_data_frames()[0]
    return gamelog_df.head(num_games)

# Function to extract specific stats
def get_stat_from_last_x_games(gamelog_df, stat):
    """
    Extracts a specific stat from a player's game log.
    """
    stat_dict = {row['GAME_DATE']: row[stat] for _, row in gamelog_df.iterrows()}
    num_games_missed = sum(1 for value in stat_dict.values() if pd.isna(value))
    return stat_dict, num_games_missed

# Function to evaluate bets
def evaluate_bet(stat_results, bet_target, over_under, num_games, player_name, stat_name):
    """
    Evaluates a bet based on recent stats and provides dynamic output based on hit rate.

    Args:
        stat_results (tuple): Tuple of (stat_dict, num_games_missed).
        bet_target (float): Target value for the bet.
        over_under (OverUnder): Enum indicating 'over' or 'under'.
        num_games (int): Number of games considered.
        player_name (str): Name of the player.
        stat_name (str): Name of the statistic being evaluated.

    Returns:
        float: The hit rate percentage.
    """
    stat_dict, num_games_missed = stat_results
    hits, misses, games_active = 0, 0, 0

    for stat in stat_dict.values():
        if pd.isna(stat):  # Skip if stat is NaN
            continue

        if over_under == OverUnder.OVER and stat > bet_target:
            hits += 1
        elif over_under == OverUnder.UNDER and stat < bet_target:
            hits += 1
        else:
            misses += 1
        games_active += 1

    hit_rate = hits / games_active if games_active > 0 else 0

    if hit_rate > 0.65:
        # Detailed output for high hit rate
        print("\n" + "=" * 50)
        print(f"Detailed Bet Evaluation for {player_name} - {stat_name}")
        print(f"Target: {over_under.value.capitalize()} {bet_target} over last {num_games} games")
        print("-" * 50)
        print(f"Results:")
        print(f"- Hits: {hits}")
        print(f"- Misses: {misses}")
        print(f"- Games Active: {games_active}")
        print(f"- Games Missed (No Data): {num_games_missed}")
        print(f"- Hit Rate: {hit_rate:.2%}")
        print("=" * 50 + "\n")
    else:
        # Quick line summary for low hit rate
        print(f"{player_name} - {stat_name}: {over_under.value.capitalize()} {bet_target} | Hit Rate: {hit_rate:.2%}")

    return hit_rate


# Function to evaluate multiple player props
# Function to evaluate multiple player props
def go_through_props_and_evaluate(props, num_games=20):
    """
    Evaluates a dictionary of player props with multiple stats.
    """
    for player_name, stats in props.items():
        time.sleep(.5)
        # Fetch player ID
        player_id = get_player_id(player_name)
        if not player_id:
            print(f"Player {player_name} not found. Skipping.")
            continue

        try:
            # Fetch game logs
            gamelog_df = get_last_x_game_stats(player_id, num_games)

            # Loop through stats for the player
            for stat, bet_target in stats.items():
                # Map human-readable stat name to NBA API column name
                stat_key = STAT_MAPPING.get(stat)
                if not stat_key:
                    print(f"Statistic '{stat}' not recognized. Skipping.")
                    continue

                try:
                    stat_results = get_stat_from_last_x_games(gamelog_df, stat_key)
                    hit_rate = evaluate_bet(stat_results, bet_target, OverUnder.OVER, num_games, player_name, stat)


                    if hit_rate > 0.65:
                        print(f"GOOD Hit rate ({hit_rate:.2%}) for {stat} of {player_name}. Target = {bet_target}")
                except KeyError:
                    print(f"Statistic '{stat_key}' not found in game logs for {player_name}. Skipping.")
        except Exception as e:
            print(f"Error evaluating {player_name}: {e}")


# Main function for command-line usage
def main():
    parser = argparse.ArgumentParser(description="Evaluate NBA player stats for betting purposes.")
    parser.add_argument("player", type=str, help="Player's full name (e.g., 'Nikola Jokić').")
    parser.add_argument("statistic", type=str, help="Statistic to evaluate (e.g., 'PTS', 'REB').")
    parser.add_argument("bet_target", type=float, help="Target value for the bet.")
    parser.add_argument("over_under", type=str, choices=[e.value for e in OverUnder], help="Specify 'over' or 'under'.")
    parser.add_argument("--num_games", type=int, default=20, help="Number of games to evaluate (default: 20).")

    args = parser.parse_args()
    player_name = args.player
    statistic = args.statistic.upper()
    bet_target = args.bet_target
    over_under = OverUnder(args.over_under)
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
    evaluate_bet(stat_results, bet_target, over_under, num_games)

if __name__ == "__main__":
    # Example props for batch evaluation
    props = get_prop_info()  # Returns the dictionary with multiple stats
    print(props)
    go_through_props_and_evaluate(props)
