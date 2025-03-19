import React, { useState } from 'react';

interface GameLog {
  game_date: string;
  matchup: string;
  game_minutes: number;
  stat_value: number;
}

interface PlayerStatsResponse {
  player_id: number;
  player_name: string;
  prop: {
    stat: string;
    target: number;
    over_under: string;
    odds_type: string;
  };
  game_logs: GameLog[];
}

const PlayerStats: React.FC = () => {
  const [propId, setPropId] = useState('');
  const [lastX, setLastX] = useState('');
  const [data, setData] = useState<PlayerStatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPlayerStats = async () => {
    if (!propId || !lastX) {
      setError('Please enter both Prop ID and Last X Games.');
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/last_x/${propId}/${lastX}`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      const result: PlayerStatsResponse = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
      setData(null);
    }
  };

  return (
    <div>
      <h1>Player Stats</h1>
      <div>
        <label>
          Prop ID:
          <input
            type="text"
            value={propId}
            onChange={(e) => setPropId(e.target.value)}
          />
        </label>
        <label>
          Last X Games:
          <input
            type="text"
            value={lastX}
            onChange={(e) => setLastX(e.target.value)}
          />
        </label>
        <button onClick={fetchPlayerStats}>Get Stats</button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {data && (
        <div>
          <h2>Prop Information</h2>
          <p><strong>Player Name:</strong> {data.player_name}</p>
          <p><strong>Stat:</strong> {data.prop.stat}</p>
          <p><strong>Target:</strong> {data.prop.target}</p>
          <p><strong>Over/Under:</strong> {data.prop.over_under}</p>
          <p><strong>Odds Type:</strong> {data.prop.odds_type}</p>

          <h2>Game Logs</h2>
          <table>
            <thead>
              <tr>
                <th>Game Date</th>
                <th>Matchup</th>
                <th>Minutes Played</th>
                <th>{data.prop.stat}</th>
              </tr>
            </thead>
            <tbody>
              {data.game_logs.map((log, index) => (
                <tr key={index}>
                  <td>{log.game_date}</td>
                  <td>{log.matchup}</td>
                  <td>{log.game_minutes}</td>
                  <td>{log.stat_value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PlayerStats;