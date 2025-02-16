import React, { useEffect, useState } from 'react';
import axios from 'axios';

function Props() {
  const [props, setProps] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/api/props')
      .then(response => {
        setProps(response.data.props);
      })
      .catch(error => {
        console.error('There was an error fetching the data!', error);
      });
  }, []);

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
  );
}

export default Props;