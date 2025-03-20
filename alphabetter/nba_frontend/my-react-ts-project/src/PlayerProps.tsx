import React, { useEffect, useState } from 'react';
import axios from 'axios';
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
import annotationPlugin from 'chartjs-plugin-annotation';

// Register Chart.js components and the annotation plugin
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

function PlayerProps() {
  const [props, setProps] = useState([]);
  const [selectedProp, setSelectedProp] = useState(null); // For modal
  const [chartData, setChartData] = useState(null); // Chart data for the modal
  const [chartOptions, setChartOptions] = useState(null); // Chart options for the modal
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/api/props')
      .then((response) => {
        setProps(response.data.props);
      })
      .catch((error) => {
        console.error('There was an error fetching the data!', error);
      });
  }, []);

  const handleRowClick = async (prop) => {
    setSelectedProp(prop); // Set the selected prop to display in the modal
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/last_x/${prop.id}/10`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      const result = await response.json();
      setError(null);

      // Prepare chart data
      const labels = result.game_logs.map((log) => `${log.game_date}\n${log.matchup}`);
      const statValues = result.game_logs.map((log) => log.stat_value);
      const target = result.prop.target;

      const barColors = statValues.map((value) => {
        if (value > target) return 'rgba(75, 192, 75, 0.8)'; // Green for above target
        if (value < target) return 'rgba(255, 99, 132, 0.8)'; // Red for below target
        return 'rgba(128, 128, 128, 0.8)'; // Grey for equal to target
      });

      setChartData({
        labels,
        datasets: [
          {
            label: `${result.prop.stat} (Actual)`,
            data: statValues,
            backgroundColor: barColors,
            borderColor: barColors.map((color) => color.replace('0.8', '1')),
            borderWidth: 1,
          },
        ],
      });

      setChartOptions({
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: `${result.prop.stat} vs Target` },
          annotation: {
            annotations: {
              targetLine: {
                type: 'line',
                yMin: target,
                yMax: target,
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                  content: 'Target',
                  enabled: true,
                  position: 'end',
                  backgroundColor: 'rgba(255, 99, 132, 0.8)',
                  color: 'white',
                  font: { size: 12 },
                },
              },
            },
          },
        },
        scales: {
          x: { title: { display: true, text: 'Game Date and Matchup' } },
          y: { title: { display: true, text: `${result.prop.stat} Value` } },
        },
      });
    } catch (err) {
      setError(err.message);
      setChartData(null);
      setChartOptions(null);
    }
  };

  return (
    <div>
      <h1>PrizePicks Props</h1>
      <table border="1">
        <thead>
          <tr>
            <th>ID</th>
            <th>Player Name</th>
            <th>Player ID</th>
            <th>Stat</th>
            <th>Target</th>
            <th>Over/Under</th>
            <th>Odds Type</th>
          </tr>
        </thead>
        <tbody>
          {props.map((prop) => (
            <tr
              key={prop.id}
              onClick={() => handleRowClick(prop)} // Open modal with chart
              style={{ cursor: 'pointer' }}
            >
              <td>{prop.id}</td>
              <td>{prop.player_name}</td>
              <td>{prop.player_id}</td>
              <td>{prop.stat}</td>
              <td>{prop.target}</td>
              <td>{prop.over_under}</td>
              <td>{prop.odds_type}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal for displaying chart */}
      {selectedProp && (
        <div
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            padding: '20px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
            zIndex: 1000,
            width: '80%',
            maxHeight: '80%',
            overflowY: 'auto',
          }}
        >
          <h2>{selectedProp.player_name} - {selectedProp.stat}</h2>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          {chartData && chartOptions && (
            <Bar data={chartData} options={chartOptions} />
          )}
          <button onClick={() => setSelectedProp(null)} style={{ marginTop: '20px' }}>
            Close
          </button>
        </div>
      )}

      {/* Modal overlay */}
      {selectedProp && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
          }}
          onClick={() => setSelectedProp(null)} // Close modal on overlay click
        ></div>
      )}
    </div>
  );
}

export default PlayerProps;