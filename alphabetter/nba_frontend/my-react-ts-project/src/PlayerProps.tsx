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
  const [props, setProps] = useState([]); // Props data
  const [stats, setStats] = useState({}); // Stats data mapped by prop_id
  const [selectedProp, setSelectedProp] = useState(null); // For modal
  const [chartData, setChartData] = useState(null); // Chart data for the modal
  const [chartOptions, setChartOptions] = useState(null); // Chart options for the modal
  const [error, setError] = useState(null);
  const [selectedSort, setSelectedSort] = useState('l10_hit_rate'); // Default sorting criteria  
  const [sliderValue, setSliderValue] = useState(10); // Default slider value (number of games)

  // Fetch props and stats
  useEffect(() => {
    // Fetch props
    axios
      .get('http://127.0.0.1:8000/api/props')
      .then((response) => {
        setProps(response.data.props);
      })
      .catch((error) => {
        console.error('Error fetching props:', error);
      });

    // Fetch stats
    axios
      .get('http://127.0.0.1:8000/api/player-stats-calculated')
      .then((response) => {
        const statsMap = {};
        response.data.stats.forEach((stat) => {
          statsMap[stat.prop_id] = stat; // Map stats by prop_id for easy lookup
        });
        setStats(statsMap);
      })
      .catch((error) => {
        console.error('Error fetching stats:', error);
      });
  }, []);

  const handleRowClick = async (prop) => {
    setSelectedProp(prop); // Set the selected prop to display in the modal
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/last_x/${prop.id}/${sliderValue}`);
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


  // Sorting function
  const sortProps = (criteria) => {
    const sortedProps = [...props].sort((a, b) => {
      const statA = stats[a.id]?.[criteria] || 0;
      const statB = stats[b.id]?.[criteria] || 0;
      return statB - statA; // Sort descending by the selected criteria
    });
    setProps(sortedProps); // Update the props state with the sorted data
  };
  
    // Handle sorting criteria change
    const handleSortChange = (event) => {
      const criteria = event.target.value;
      setSelectedSort(criteria); // Update the selected sorting criteria
      sortProps(criteria); // Sort the props based on the new criteria
    };

  const handleSliderChange = async (event) => {
    const newValue = event.target.value;
    setSliderValue(newValue); // Update slider value

    // Fetch updated data based on the new slider value
    if (selectedProp) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/last_x/${selectedProp.id}/${newValue}`);
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }
        const result = await response.json();

        // Update chart data
        const labels = result.game_logs.map((log) => `${log.game_date}\n${log.matchup}`);
        const statValues = result.game_logs.map((log) => log.stat_value);
        const target = result.prop.target;

        const barColors = statValues.map((value) => {
          if (value > target) return 'rgba(75, 192, 75, 0.8)';
          if (value < target) return 'rgba(255, 99, 132, 0.8)';
          return 'rgba(128, 128, 128, 0.8)';
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
      } catch (err) {
        setError(err.message);
      }
    }
  };

  return (
    <div>
      <h1>PrizePicks Props</h1>

      {/* Sorting Dropdown */}
      <label htmlFor="sort-select" style={{ marginRight: '10px' }}>Sort By:</label>
      <select
        id="sort-select"
        value={selectedSort}
        onChange={handleSortChange}
        style={{ marginBottom: '10px', padding: '5px' }}
      >
        <option value="l5_hit_rate">L5 Hit Rate</option>
        <option value="l10_hit_rate">L10 Hit Rate</option>
        <option value="l20_hit_rate">L20 Hit Rate</option>
      </select>

      <table border="1">
        <thead>
          <tr>
            <th>ID</th>
            <th>Player Name</th>
            <th>Stat</th>
            <th>Target</th>
            <th>Over/Under</th>
            <th>Odds Type</th>
            <th>L5 Hit Rate</th>
            <th>L10 Hit Rate</th>
            <th>L20 Hit Rate</th>
            <th>Last %</th>
          </tr>
        </thead>
        <tbody>
          {props.map((prop) => {
            const stat = stats[prop.id] || {}; // Get stats for the current prop
            return (
              <tr
                key={prop.id}
                onClick={() => handleRowClick(prop)} // Open modal with chart
                style={{ cursor: 'pointer' }}
              >
                <td>{prop.id}</td>
                <td>{prop.player_name}</td>
                <td>{prop.stat}</td>
                <td>{prop.target}</td>
                <td>{prop.over_under}</td>
                <td>{prop.odds_type}</td>
                <td>{stat.l5_hit_rate != null ? `${(stat.l5_hit_rate * 100).toFixed(1)}%` : 'N/A'}</td>
                <td>{stat.l10_hit_rate != null ? `${(stat.l10_hit_rate * 100).toFixed(1)}%` : 'N/A'}</td>
                <td>{stat.l20_hit_rate != null ? `${(stat.l20_hit_rate * 100).toFixed(1)}%` : 'N/A'}</td>
                <td>{stat.last_percent_total ? `${stat.last_percent_total} (${(stat.last_percent_rate * 100).toFixed(2)}%)` : 'N/A'}</td>
              </tr>
            );
          })}
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
            width: '80vw', // Use viewport width
            height: '80vh', // Use viewport height
            maxWidth: '800px', // Optional: Limit max width
            maxHeight: '600px', // Optional: Limit max height
            overflow: 'hidden', // Prevent scrollbars
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <h2 style={{ textAlign: 'center' }}>{selectedProp.player_name} - {selectedProp.stat}</h2>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          {chartData && chartOptions && (
            <div style={{ flex: 1, width: '100%', height: '100%' }}>
              <Bar
                data={chartData}
                options={{
                  ...chartOptions,
                  responsive: true, // Make the chart responsive
                  maintainAspectRatio: false, // Allow the chart to fill the container
                }}
              />
            </div>
          )}
          <label htmlFor="game-slider" style={{ marginTop: '10px' }}>Number of Games: {sliderValue}</label>
          <input
            id="game-slider"
            type="range"
            min="5"
            max="30"  //TODO: Figure out Exact NUM GAMES
            value={sliderValue}
            onChange={handleSliderChange}
            style={{ width: '100%' }}
          />
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