from sqlalchemy.orm import Session
from alphabetter.nba_backend.database import get_db
from alphabetter.nba_backend.models import PlayerStats, PlayerGameLog, TeamInfo

# Create a new session
db: Session = next(get_db())

# Query all player stats
players = db.query(PlayerStats).all()

# Print player stats
for player in players:
    print(f"Player ID: {player.player_id}, Name: {player.name}, Team: {player.team}, "
          f"Games Played: {player.games_played}, Points Per Game: {player.points_per_game}, "
          f"Assists Per Game: {player.assists_per_game}, Rebounds Per Game: {player.rebounds_per_game}")

# Query all player game logs
player_game_logs = db.query(PlayerGameLog).all()

# Print player game logs
for game_log in player_game_logs:
    print(f"Player ID: {game_log.player_id}, Team ID: {game_log.team_id}, Game Date: {game_log.game_date}, "
          f"Matchup: {game_log.matchup}, WL: DNE, Minutes: {game_log.min}, Points: {game_log.pts}, "
          f"Offensive Rebounds: {game_log.oreb}, Defensive Rebounds: {game_log.dreb}, Rebounds: {game_log.reb}, "
          f"Assists: {game_log.ast}, Steals: {game_log.stl}, Blocks: {game_log.blk}, Turnovers: {game_log.tov}, "
          f"Field Goals Made: {game_log.fgm}, Field Goals Attempted: {game_log.fga}, Field Goal Percentage: {game_log.fg_pct}, "
          f"3-Point Field Goals Made: {game_log.fg3m}, 3-Point Field Goals Attempted: {game_log.fg3a}, 3-Point Field Goal Percentage: {game_log.fg3_pct}, "
          f"Free Throws Made: {game_log.ftm}, Free Throws Attempted: {game_log.fta}, Free Throw Percentage: {game_log.ft_pct}")

# Query all team game logs
team_game_logs = db.query(TeamInfo).all()

# Print team game logs
for team_log in team_game_logs:
    print(f"Team ID: {team_log.team_id}, Game ID: {team_log.game_id}, Game Date: {team_log.game_date}, "
          f"Matchup: {team_log.matchup}, WL: {team_log.wl}, Wins: {team_log.w}, Losses: {team_log.l}, "
          f"Win Percentage: {team_log.w_pct}, Minutes: {team_log.min}, Field Goals Made: {team_log.fgm}, "
          f"Field Goals Attempted: {team_log.fga}, Field Goal Percentage: {team_log.fg_pct}, "
          f"3-Point Field Goals Made: {team_log.fg3m}, 3-Point Field Goals Attempted: {team_log.fg3a}, "
          f"3-Point Field Goal Percentage: {team_log.fg3_pct}, Free Throws Made: {team_log.ftm}, "
          f"Free Throws Attempted: {team_log.fta}, Free Throw Percentage: {team_log.ft_pct}, "
          f"Offensive Rebounds: {team_log.oreb}, Defensive Rebounds: {team_log.dreb}, Rebounds: {team_log.reb}, "
          f"Assists: {team_log.ast}, Steals: {team_log.stl}, Blocks: {team_log.blk}, Turnovers: {team_log.tov}, "
          f"Personal Fouls: {team_log.pf}, Points: {team_log.pts}")

# Close the session
db.close()