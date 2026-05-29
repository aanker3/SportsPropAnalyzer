import React, { useState } from 'react';
import axios from 'axios';
import API_URL from './api';

function PlayerId() {
  const [playerName, setPlayerName] = useState('');
  const [playerId, setPlayerId] = useState<number | null>(null);
  const [props, setProps] = useState([]);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPlayerName(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    axios.get(`${API_URL}/api/player/${playerName}`)
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
        console.error('There was an error fetching the data!', error);
        setError('There was an error fetching the data!');
      });
  };

  return (
    <div>
      <h1>Player ID</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" value={playerName} onChange={handleChange} placeholder="Enter player name" />
        <button type="submit">Get Player ID</button>
      </form>
      {error && <p>{error}</p>}
      {playerId && <p>Player ID: {playerId}</p>}
      {props.length > 0 && (
        <div>
          <h2>Props</h2>
          <ul>
            {props.map((prop: any, index: number) => (
              <li key={index}>{prop}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default PlayerId;