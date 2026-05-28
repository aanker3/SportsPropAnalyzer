import React, { useState } from 'react';
import axios from 'axios';

function PlayerGameLogs() {
  const [playerName, setPlayerName] = useState('');
  const [gameLogs, setGameLogs] = useState([]);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPlayerName(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    axios.get(`http://127.0.0.1:8000/api/player-gamelogs/${playerName}`)
      .then(response => {
        console.log('Response data:', response.data);  // Add this line to log the response data
        setGameLogs(response.data.game_logs);
        setError(null);
      })
      .catch(error => {
        console.error('There was an error fetching the data!', error);
        setError('There was an error fetching the data!');
      });
  };

  return (
    <div>
      <h1>Player Game Logs</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" value={playerName} onChange={handleChange} placeholder="Enter player name" />
        <button type="submit">Get Game Logs</button>
      </form>
      {error && <p>{error}</p>}
      {gameLogs.length > 0 && (
        <table border="1">
          <thead>
            <tr>
              <th>Game Date</th>
              <th>Player ID</th>
              <th>Team ID</th>
              <th>Matchup</th>
              <th>Min</th>
              <th>Points</th>
              <th>OREB</th>
              <th>DREB</th>
              <th>REB</th>
              <th>AST</th>
              <th>STL</th>
              <th>BLK</th>
              <th>TOV</th>
              <th>FGM</th>
              <th>FGA</th>
              <th>FG%</th>
              <th>FG3M</th>
              <th>FG3A</th>
              <th>FG3%</th>
              <th>FTM</th>
              <th>FTA</th>
              <th>FT%</th>
            </tr>
          </thead>
          <tbody>
            {gameLogs.map((log, index) => (
              <tr key={index}>
                <td>{log.game_date}</td>
                <td>{log.player_id}</td>
                <td>{log.team_id}</td>
                <td>{log.matchup}</td>
                <td>{log.min}</td>
                <td>{log.pts}</td>
                <td>{log.oreb}</td>
                <td>{log.dreb}</td>
                <td>{log.reb}</td>
                <td>{log.ast}</td>
                <td>{log.stl}</td>
                <td>{log.blk}</td>
                <td>{log.tov}</td>
                <td>{log.fgm}</td>
                <td>{log.fga}</td>
                <td>{log.fg_pct}</td>
                <td>{log.fg3m}</td>
                <td>{log.fg3a}</td>
                <td>{log.fg3_pct}</td>
                <td>{log.ftm}</td>
                <td>{log.fta}</td>
                <td>{log.ft_pct}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default PlayerGameLogs;