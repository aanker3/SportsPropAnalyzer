import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation'; // Import the annotation plugin

// Register Chart.js components and the annotation plugin
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

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

  const getChartData = () => {
    if (!data) return null;

    const labels = data.game_logs.map((log) => `${log.game_date}\n${log.matchup}`); // Game date and matchup as labels
    const statValues = data.game_logs.map((log) => log.stat_value); // Stat values
    const target = data.prop.target;

    // Determine bar colors based on comparison with the target
    const barColors = statValues.map((value) => {
      if (value > target) return 'rgba(75, 192, 75, 0.8)'; // Green for above target
      if (value < target) return 'rgba(255, 99, 132, 0.8)'; // Red for below target
      return 'rgba(128, 128, 128, 0.8)'; // Grey for equal to target
    });

    return {
      labels,
      datasets: [
        {
          label: `${data.prop.stat} (Actual)`,
          data: statValues,
          backgroundColor: barColors,
          borderColor: barColors.map((color) => color.replace('0.8', '1')), // Solid border
          borderWidth: 1,
        },
      ],
    };
  };

  const getChartOptions = () => {
    if (!data) return {};
  
    return {
      responsive: true,
      plugins: {
        legend: {
          display: false, // Hide legend for simplicity
        },
        title: {
          display: true,
          text: `${data.prop.stat} vs Target`,
        },
        annotation: {
          annotations: {
            targetLine: {
              type: 'line',
              yMin: data.prop.target,
              yMax: data.prop.target,
              borderColor: 'rgba(255, 99, 132, 1)', // Red line
              borderWidth: 2,
              borderDash: [5, 5], // Dashed line
              label: {
                content: 'Target',
                enabled: true,
                position: 'end',
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                color: 'white',
                font: {
                  size: 12,
                },
              },
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const index = context.dataIndex; // Get the index of the hovered bar
              const gameLog = data.game_logs[index]; // Get the corresponding game log
              const statValue = context.raw; // The stat value for the hovered bar
              return [
                `${data.prop.stat}: ${statValue}`,
                `Minutes Played: ${gameLog.game_minutes}`, // Add minutes played to the tooltip
              ];
            },
          },
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Game Date and Matchup',
          },
        },
        y: {
          title: {
            display: true,
            text: `${data.prop.stat} Value`,
          },
        },
      },
    };
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

          <h2>Graphical Representation</h2>
          <Bar
            data={getChartData()!}
            options={getChartOptions()}
          />
        </div>
      )}
    </div>
  );
};

export default PlayerStats;