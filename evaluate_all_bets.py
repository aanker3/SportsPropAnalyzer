import argparse
import pandas as pd
import sys
from nba_api.stats.endpoints import (
    playergamelog,
    commonallplayers,
    teamgamelog,
    commonplayerinfo,
)
from enum import Enum
from get_props import load_bets_json, create_props, Prop, OddsType
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import statistics
from collections import defaultdict
import subprocess

player_stats_cache = {}


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
    ties: int
    games_active: int
    games_missed: int
    hit_rate: float
    num_games: int
    median: float = 0.0
    mode: float = 0.0
    average: float = 0.0
    odds_type: OddsType = OddsType.STANDARD
    reasoning: List[str] = field(default_factory=list)


# Enum for Over/Under
class OverUnder(Enum):
    OVER = "over"
    UNDER = "under"


# Mapping of human-readable stat names to NBA API stat keys
# TODO Figure out exactly what this is a mapping to
STAT_MAPPING = {
    "Points": "PTS",
    "Rebounds": "REB",  # Total rebounds
    "Offensive Rebounds": "OREB",  # Offensive rebounds
    "Defensive Rebounds": "DREB",
    "Assists": "AST",
    "Steals": "STL",
    "Blocks": "BLK",
    "Blocked Shots": "BLK",  # Alias for Blocks
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
    "Blks+Stls": "BLK+STL",  # Blocks + Steals
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


# Function to fetch the season stats
def get_player_stats(player_name: str, num_games: int = 20) -> pd.DataFrame:
    """Fetches last num_games for a player using the NBA API and caches results."""
    global pings, player_stats_cache

    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Player {player_name} not found. Skipping.")
        return None

    if player_name in player_stats_cache:
        print(f"Using cached stats for {player_name}.")
        return player_stats_cache[player_name]

    pings += 3

    # Fetch player's team ID
    team_id = (
        commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        .get_data_frames()[0]["TEAM_ID"]
        .iloc[0]
    )
    time.sleep(0.4)

    # Fetch player's game log
    gamelog_df = playergamelog.PlayerGameLog(player_id=player_id).get_data_frames()[0]
    time.sleep(0.4)

    # Fetch team's schedule
    team_schedule = teamgamelog.TeamGameLog(
        team_id=team_id, season="2024"
    ).get_data_frames()[0]
    time.sleep(0.4)

    # Merge game log with team schedule
    merged_df = pd.merge(
        team_schedule[["Game_ID", "GAME_DATE", "MATCHUP", "WL"]],
        gamelog_df,
        on="Game_ID",
        how="left",
        suffixes=("_team", "_player"),
    ).rename(
        columns={
            "WL_team": "WL",
            "GAME_DATE_team": "GAME_DATE",
            "MATCHUP_team": "MATCHUP",
        }
    )

    print(f"PINGING NBA, PINGS = {pings}")

    # Drop games where there is no Win or Loss value (If game is in play)
    merged_df = merged_df.dropna(subset=["WL"])

    merged_df["PLAYED"] = merged_df["MIN"].notna()
    merged_df.fillna(0, inplace=True)
    merged_df["GAME_DATE"] = pd.to_datetime(merged_df["GAME_DATE"], format="%b %d, %Y")
    merged_df.sort_values("GAME_DATE", ascending=False, inplace=True)

    # Cache results
    player_stats_cache[player_name] = merged_df.head(num_games)
    print(f"Cached stats for {player_name}.")

    return player_stats_cache[player_name]


# Function to extract specific stats
def get_stat_from_last_x_games(
    gamelog_df: pd.DataFrame, stat: str, num_games: int = 20
) -> tuple:
    """Extracts a specific stat from a player's game log, including derived stats."""
    gamelog_df = gamelog_df.head(num_games)  # Select most recent X games

    stat_dict = {}
    num_games_missed = gamelog_df["PLAYED"].eq(False).sum()  # Count games not played

    if "+" in stat:  # Handle derived stats
        stat_keys = stat.split("+")
        for _, row in gamelog_df.iterrows():
            stat_value = sum(row.get(key, 0) for key in stat_keys)
            stat_dict[row["GAME_DATE"]] = stat_value
    else:  # Handle regular stats
        stat_dict = {
            row["GAME_DATE"]: row.get(stat, 0) for _, row in gamelog_df.iterrows()
        }

    return stat_dict, num_games_missed


# Function to evaluate a bet
def evaluate_bet(
    gamelog_df,
    stat_results: tuple,  # Can remove.
    bet_target: float,
    over_under: OverUnder,
    num_games: int,
    player_name: str,
    stat_name: str,
    odds_type: Optional[OddsType],
) -> BetEvaluation:
    """Evaluates a bet and returns a BetEvaluation object."""
    _, num_games_missed = stat_results
    hits = misses = ties = games_active = 0
    stat_values = []

    stat_key = STAT_MAPPING.get(stat_name)
    if not stat_key:
        print(f"Statistic '{stat_name}' not recognized")
        return None

    for _, row in gamelog_df.iterrows():
        if not row["PLAYED"]:  # Skip games where the player didn't play
            continue

        # Adjust evaluation based on minutes played (optional)
        minutes_played = row.get("MIN", 0)

        if minutes_played == 0:  # Example: Skip games with less than 10 minutes played
            # Missed game.
            continue

        # Handle multi-stat bets (e.g., "Pts+Rebs+Asts")
        if "+" in stat_key:
            stat_keys = stat_key.split(
                "+"
            )  # Split into individual stats (e.g., ["PTS", "REB", "AST"])
            stat_value = sum(row.get(key, 0) for key in stat_keys)  # Sum the values
        else:  # Handle single-stat bets
            stat_value = row.get(stat_key, 0)

        stat_values.append(stat_value)

        if over_under == OverUnder.OVER and stat_value > bet_target:
            hits += 1
        elif over_under == OverUnder.UNDER and stat_value < bet_target:
            hits += 1
        elif stat_value == bet_target:
            ties += 1
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

    # ANALYZE:
    reasoning = []
    # if stat_key == "FG3M":
    # ...

    # TODO REFACTOR
    if over_under == OverUnder.OVER:
        if median > 1.3 * bet_target:
            pct_difference = (median / bet_target) * 100
            reasoning.append(
                f"Median ({median}) {pct_difference}% larger than bet_target ({bet_target})"
            )
        if average > 1.3 * bet_target:
            pct_difference = (average / bet_target) * 100
            reasoning.append(
                f"Average ({average}) {pct_difference}% larger than bet_target ({bet_target})"
            )
    if over_under == OverUnder.UNDER:
        if median < 0.7 * bet_target:
            pct_difference = (median / bet_target) * 100
            reasoning.append(
                f"Median ({median}) {pct_difference}% smaller than bet_target ({bet_target})"
            )
        if average < 0.7 * bet_target:
            pct_difference = (average / bet_target) * 100
            reasoning.append(
                f"Average ({average}) {pct_difference}% smaller than bet_target ({bet_target})"
            )

    # Return the data as a BetEvaluation object
    return BetEvaluation(
        player_name=player_name,
        stat_name=stat_name,
        bet_target=bet_target,
        over_under=over_under.value,
        hits=hits,
        misses=misses,
        ties=ties,
        games_active=games_active,
        games_missed=num_games_missed,
        hit_rate=hit_rate,
        num_games=num_games,
        median=median,
        mode=mode,
        average=average,
        odds_type=odds_type,  # Include odds_type
        reasoning=reasoning,
    )


def print_detailed_bet_evaluation(bet_info: BetEvaluation):
    """Prints a detailed evaluation of a bet, including player stats and calculated metrics."""
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
    reasoning = bet_info.reasoning

    display_player_stats_last_x_games(player_name)
    print("\n" + "=" * 50)
    print(f"Detailed Bet Evaluation for {player_name} - {stat_name}")
    print(f"Target: {over_under} {bet_target} over last {num_games} games")
    print(f"Hit Rate: {hit_rate:.2%}")
    if odds_type is not None:
        print(f"Odds Type: {odds_type.name}")  # Include odds_type
    print("-" * 50)
    print(f"- Hits: {bet_info.hits}")
    print(f"- Misses: {bet_info.misses}")
    if bet_info.ties:
        print(f"- Ties: {bet_info.ties}")
    print(f"- Games Active: {bet_info.games_active}")
    print(f"- Games Missed: {bet_info.games_missed}")
    print(f"- Average {stat_name}: {average:.2f}")
    print(f"- Median {stat_name}: {median}")
    print(f"- Mode {stat_name}: {mode}")
    if reasoning:
        print(f"- Reasoning: {reasoning}")
    print("=" * 50 + "\n")


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
    # TODO: if hit rate < .15, swap over_under...
    if (
        (hit_rate >= 0.90 and odds_type == OddsType.GOBLIN)
        or (hit_rate >= 0.80 and odds_type == OddsType.STANDARD)
        or (hit_rate >= 0.55 and odds_type == OddsType.DEMON)
        or print_stats
    ):
        print_detailed_bet_evaluation(bet_info)
    else:
        # Quick summary for lower hit rates
        print(
            f"{player_name} - {stat_name}: {over_under} {bet_target} | "
            f"Hit Rate: {hit_rate:.2%} | Odds Type: {odds_type.name}"  # Include odds_type
        )


def go_through_player_props_and_evaluate(props: List[Prop], num_games: int = 20):
    """Evaluates a list of Prop objects and prints the results."""
    for prop in props:
        # Check if the player's stats are in the cache
        if prop.player_name not in player_stats_cache:
            print(f"Player {prop.player_name} not found in cache. Skipping.")
            continue

        # todo fix games missed.  This doesnt include games not played.
        gamelog_df = player_stats_cache[prop.player_name]

        # Convert the computer-readable stat name
        stat_key = STAT_MAPPING.get(prop.stat)
        if not stat_key:
            print(f"Statistic '{prop.stat}' not recognized. Skipping.")
            continue

        try:
            stat_results = get_stat_from_last_x_games(gamelog_df, stat_key)

            # Run over & under on standard bets.
            over_under_values = (
                [OverUnder.OVER, OverUnder.UNDER]
                if prop.odds_type == OddsType.STANDARD
                else [OverUnder(prop.over_under)]
            )

            for over_under in over_under_values:
                bet_info = evaluate_bet(
                    gamelog_df,
                    stat_results,
                    prop.target,
                    over_under,
                    num_games,
                    prop.player_name,
                    prop.stat,
                    prop.odds_type,
                )
                print_bet_evaluation(bet_info)

        except KeyError:
            print(f"Statistic '{stat_key}' not found for {prop.player_name}. Skipping.")


def update_props_file():
    try:
        print("Fetching props from PrizePicks...")
        subprocess.run(["get_props/get_props_prizepicks.exe"], check=True)
        print("Props successfully fetched.")
    except subprocess.CalledProcessError as e:
        print(f"Error running get_props_prizepicks.exe: {e}")
        sys.exit(1)


# Function to display player stats for the last 20 games
def display_player_stats_last_x_games(player_name: str, num_games: int = 20):
    """Displays a nicely formatted summary of a player's last 20 games using the NBA API."""
    # Check if the player's stats are in the cache
    if player_name not in player_stats_cache:
        print(
            f"No stats found in cache for: {player_name} player_stats_cache = {player_stats_cache}"
        )
        return

    gamelog_df = player_stats_cache[player_name]
    if gamelog_df.empty:
        print(f"No game logs found for: {player_name}")
        return

    # Select the last `num_games` rows
    gamelog_df = gamelog_df.head(num_games)

    columns_to_display = [
        "GAME_DATE",
        "MATCHUP",
        "WL",
        "MIN",
        "PTS",
        "OREB",
        "DREB",
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

    update_props_file()

    # Check if specific arguments are provided for single evaluation
    if args.player and args.statistic and args.bet_target and args.over_under:
        # Process a single player/statistic evaluation
        player_name = args.player
        statistic = args.statistic
        bet_target = args.bet_target
        over_under = args.over_under
        num_games = args.num_games

        # Fetch player ID

        # Fetch game logs
        gamelog_df = get_player_stats(player_name, num_games=20)
        player_stats_cache[player_name] = gamelog_df
        # print(gamelog_df)
        if gamelog_df is None or gamelog_df.empty:
            print(f"Error fetching game logs")
            sys.exit()
        # Extract stats
        try:
            stat_results = get_stat_from_last_x_games(gamelog_df, statistic)
        except KeyError:
            print(f"Statistic '{statistic}' not found in game logs.")
            sys.exit(1)

        # Evaluate bet
        bet_info = evaluate_bet(
            gamelog_df,
            stat_results,
            bet_target,
            OverUnder(over_under),
            num_games,
            player_name,
            statistic,
            None,
        )
        print_bet_evaluation(bet_info, print_stats=True)

    else:
        # Batch evaluation: Optimize by processing one player at a time
        print("Running batch evaluation...")
        bet_data = load_bets_json()
        props = create_props(bet_data)

        # Group props by player

        all_player_props = defaultdict(list)
        for prop in props:
            all_player_props[prop.player_name].append(prop)

        # Process each player separately
        for player_name, player_props in all_player_props.items():
            gamelog_df = get_player_stats(player_name, num_games=20)
            player_stats_cache[player_name] = gamelog_df
            # print(gamelog_df)
            if gamelog_df is None or gamelog_df.empty:
                continue

            # Evaluate props for this player
            go_through_player_props_and_evaluate(player_props)


if __name__ == "__main__":
    main()
