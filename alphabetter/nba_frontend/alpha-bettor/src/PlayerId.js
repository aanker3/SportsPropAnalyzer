import React, { useState } from 'react';
import axios from 'axios';

function PlayerId() {
  const [playerName, setPlayerName] = useState('');
  const [playerId, setPlayerId] = useState(null);
  const [props, setProps] = useState([]);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setPlayerName(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.get(`http://127.0.0.1:8000/api/player/${playerName}`)
      .then(response => {
        if (response.data.error) {
          setError(response.data.error);
          setProps(response.data.props);
          setPlayerId(null);
        } else {
          setPlayerId(response.data.player_id);
          setError(null);
          setProps([]);
        }
      })
      .catch(error => {
        setPlayerId(null);
        setError('An error occurred');
        setProps([]);
      });
  };

  return (
    <div>
      <h1>Player ID</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Enter a player name:
          <input type="text" value={playerName} onChange={handleChange} />
        </label>
        <button type="submit">Submit</button>
      </form>
      {error && <div>{error}</div>}
      {playerId && (
        <div>
          <h2>Player ID: {playerId}</h2>
        </div>
      )}
      {props.length > 0 && (
        <div>
          <h2>Available Props</h2>
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
              {props.map(prop => (
                <tr key={prop.id}>
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
        </div>
      )}
    </div>
  );
}

export default PlayerId;