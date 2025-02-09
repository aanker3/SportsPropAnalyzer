import time
import pandas as pd
from sqlalchemy.orm import Session
from nba_api.stats.endpoints import commonallplayers, playergamelog, commonplayerinfo, teamgamelog
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PlayerStats, PlayerGameLog, TeamInfo
from nba_api.stats.static import teams

# Function to fetch player stats
def fetch_player_stats(player_id: int) -> list:
    """Fetches all games for the current season for a player using the NBA API."""
    player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
    player_name = player_info["DISPLAY_FIRST_LAST"].iloc[0]
    team = player_info["TEAM_NAME"].iloc[0]
    team_id = player_info["TEAM_ID"].iloc[0]


    #TODO: Eventually read PlayerGameLog from the database instead of fetching it every time!
    # Fetch the player's game logs
    gamelog_df = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25').get_data_frames()[0]
    time.sleep(.2)
    # Fetch the team's schedule
    team_schedule_df = teamgamelog.TeamGameLog(team_id=team_id, season='2024-25').get_data_frames()[0]
    time.sleep(.2)
    # Merge game log with team schedule
    merged_df = pd.merge(
        team_schedule_df[["Game_ID", "GAME_DATE", "MATCHUP", "WL"]],
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

    # Fill NaN values with 0
    merged_df = merged_df.fillna(0)

    game_logs = []
    for _, row in merged_df.iterrows():
        game_log = {
            "player_id": int(player_id),
            "team_id": int(team_id),
            "game_date": row["GAME_DATE"],
            "matchup": row["MATCHUP"],
            "wl": row["WL"],
            "min": float(row["MIN"]),
            "pts": float(row["PTS"]),
            "oreb": float(row["OREB"]),
            "dreb": float(row["DREB"]),
            "reb": float(row["REB"]),
            "ast": float(row["AST"]),
            "stl": float(row["STL"]),
            "blk": float(row["BLK"]),
            "tov": float(row["TOV"]),
            "fgm": float(row["FGM"]),
            "fga": float(row["FGA"]),
            "fg_pct": float(row["FG_PCT"]),
            "fg3m": float(row["FG3M"]),
            "fg3a": float(row["FG3A"]),
            "fg3_pct": float(row["FG3_PCT"]),
            "ftm": float(row["FTM"]),
            "fta": float(row["FTA"]),
            "ft_pct": float(row["FT_PCT"]),
        }
        game_logs.append(game_log)

    return player_name, team, team_id, game_logs

# Function to store player stats in the database
def store_player_stats(db: Session, player_id: int, player_name: str, team: str, team_id: int, game_logs: list):
    """Stores player stats in the database."""
    # Store player summary stats
    games_played = len(game_logs)
    
    if games_played > 0:
        points_per_game = sum(float(log["pts"]) for log in game_logs) / games_played
        assists_per_game = sum(float(log["ast"]) for log in game_logs) / games_played
        rebounds_per_game = sum(float(log["reb"]) for log in game_logs) / games_played
    else:
        points_per_game = 0.0
        assists_per_game = 0.0
        rebounds_per_game = 0.0

    new_player_stats = PlayerStats(
        player_id=int(player_id),
        name=player_name,
        team=team,
        team_id=int(team_id),
        games_played=int(games_played),
        points_per_game=float(points_per_game),
        assists_per_game=float(assists_per_game),
        rebounds_per_game=float(rebounds_per_game),
    )
    db.add(new_player_stats)

    # Store individual game logs
    for log in game_logs:
        new_game_log = PlayerGameLog(
            player_id=int(log["player_id"]),
            team_id=int(log["team_id"]),
            game_date=log["game_date"],
            matchup=log["matchup"],
            wl=log["wl"],
            min=float(log["min"]),
            pts=float(log["pts"]),
            oreb=float(log["oreb"]),
            dreb=float(log["dreb"]),
            reb=float(log["reb"]),
            ast=float(log["ast"]),
            stl=float(log["stl"]),
            blk=float(log["blk"]),
            tov=float(log["tov"]),
            fgm=float(log["fgm"]),
            fga=float(log["fga"]),
            fg_pct=float(log["fg_pct"]),
            fg3m=float(log["fg3m"]),
            fg3a=float(log["fg3a"]),
            fg3_pct=float(log["fg3_pct"]),
            ftm=float(log["ftm"]),
            fta=float(log["fta"]),
            ft_pct=float(log["ft_pct"]),
        )
        db.add(new_game_log)

    db.commit()

def get_active_team_ids():
    """Fetches a list of team IDs for all active NBA teams."""
    active_teams = teams.get_teams()  # Gets all active teams
    team_ids = [team["id"] for team in active_teams]  # Extracts team IDs
    return team_ids

def fetch_team_gamelog(team_id: int) -> list:
    """Fetches all games for the current season for a team using the NBA API."""
    team_gamelog_df = teamgamelog.TeamGameLog(team_id=team_id, season='2024-25').get_data_frames()[0]

    team_logs = []
    for _, row in team_gamelog_df.iterrows():
        # Skip entries with NaN values
        if row.isnull().any():
            continue

        team_log = {
            "team_id": int(row["Team_ID"]),
            "game_id": int(row["Game_ID"]),
            "game_date": row["GAME_DATE"],
            "matchup": row["MATCHUP"],
            "wl": row["WL"],
            "w": int(row["W"]),
            "l": int(row["L"]),
            "w_pct": float(row["W_PCT"]),
            "min": float(row["MIN"]),
            "fgm": float(row["FGM"]),
            "fga": float(row["FGA"]),
            "fg_pct": float(row["FG_PCT"]),
            "fg3m": float(row["FG3M"]),
            "fg3a": float(row["FG3A"]),
            "fg3_pct": float(row["FG3_PCT"]),
            "ftm": float(row["FTM"]),
            "fta": float(row["FTA"]),
            "ft_pct": float(row["FT_PCT"]),
            "oreb": float(row["OREB"]),
            "dreb": float(row["DREB"]),
            "reb": float(row["REB"]),
            "ast": float(row["AST"]),
            "stl": float(row["STL"]),
            "blk": float(row["BLK"]),
            "tov": float(row["TOV"]),
            "pf": float(row["PF"]),
            "pts": float(row["PTS"]),
        }
        team_logs.append(team_log)

    return team_logs

def store_team_gamelog(db: Session, team_id: int, team_logs: list):
    """Stores team game logs in the database."""
    for log in team_logs:
        new_team_info = TeamInfo(
            team_id=log["team_id"],
            game_id=log["game_id"],
            game_date=log["game_date"],
            matchup=log["matchup"],
            wl=log["wl"],
            w=log["w"],
            l=log["l"],
            w_pct=log["w_pct"],
            min=log["min"],
            fgm=log["fgm"],
            fga=log["fga"],
            fg_pct=log["fg_pct"],
            fg3m=log["fg3m"],
            fg3a=log["fg3a"],
            fg3_pct=log["fg3_pct"],
            ftm=log["ftm"],
            fta=log["fta"],
            ft_pct=log["ft_pct"],
            oreb=log["oreb"],
            dreb=log["dreb"],
            reb=log["reb"],
            ast=log["ast"],
            stl=log["stl"],
            blk=log["blk"],
            tov=log["tov"],
            pf=log["pf"],
            pts=log["pts"],
        )
        db.add(new_team_info)
    db.commit()

def main():
    db: Session = next(get_db())

    # Fetch all current players
    players = commonallplayers.CommonAllPlayers(is_only_current_season=1).get_data_frames()[0]
    player_ids = players["PERSON_ID"].tolist()

    for player_id in player_ids[:10]:
        try:
            player_name, team, team_id, game_logs = fetch_player_stats(player_id)
            store_player_stats(db, player_id, player_name, team, team_id, game_logs)
            print(f"Stored stats for player ID: {player_id}")
            time.sleep(.5)  # To avoid hitting API rate limits
        except Exception as e:
            print(f"Error fetching/storing stats for player ID: {player_id} - {e}")

    # Fetch and store team game logs
    active_team_ids = get_active_team_ids()
    for team_id in active_team_ids:
        try:
            team_logs = fetch_team_gamelog(team_id)
            store_team_gamelog(db, team_id, team_logs)
            print(f"Stored game logs for team ID: {team_id}")
            time.sleep(.5)  # To avoid hitting API rate limits
        except Exception as e:
            print(f"Error fetching/storing game logs for team ID: {team_id} - {e}")

    print("Stored team information successfully!")

    db.close()

if __name__ == "__main__":
    main()