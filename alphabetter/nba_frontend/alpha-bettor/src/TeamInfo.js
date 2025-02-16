import React, { useEffect, useState } from 'react';
import axios from 'axios';

function TeamInfo() {
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/api/teams')
      .then(response => {
        setTeams(response.data.teams);
      })
      .catch(error => {
        console.error('There was an error fetching the data!', error);
      });
  }, []);

  return (
    <div>
      <h1>Team Info</h1>
      <table border="1">
        <thead>
          <tr>
            <th>Team ID</th>
            <th>Game ID</th>
            <th>Game Date</th>
            <th>Matchup</th>
            <th>WL</th>
            <th>W</th>
            <th>L</th>
            <th>W PCT</th>
            <th>MIN</th>
            <th>FGM</th>
            <th>FGA</th>
            <th>FG PCT</th>
            <th>FG3M</th>
            <th>FG3A</th>
            <th>FG3 PCT</th>
            <th>FTM</th>
            <th>FTA</th>
            <th>FT PCT</th>
            <th>OREB</th>
            <th>DREB</th>
            <th>REB</th>
            <th>AST</th>
            <th>STL</th>
            <th>BLK</th>
            <th>TOV</th>
            <th>PF</th>
            <th>PTS</th>
          </tr>
        </thead>
        <tbody>
          {teams.map(team => (
            <tr key={team.team_id}>
              <td>{team.team_id}</td>
              <td>{team.game_id}</td>
              <td>{team.game_date}</td>
              <td>{team.matchup}</td>
              <td>{team.wl}</td>
              <td>{team.w}</td>
              <td>{team.l}</td>
              <td>{team.w_pct}</td>
              <td>{team.min}</td>
              <td>{team.fgm}</td>
              <td>{team.fga}</td>
              <td>{team.fg_pct}</td>
              <td>{team.fg3m}</td>
              <td>{team.fg3a}</td>
              <td>{team.fg3_pct}</td>
              <td>{team.ftm}</td>
              <td>{team.fta}</td>
              <td>{team.ft_pct}</td>
              <td>{team.oreb}</td>
              <td>{team.dreb}</td>
              <td>{team.reb}</td>
              <td>{team.ast}</td>
              <td>{team.stl}</td>
              <td>{team.blk}</td>
              <td>{team.tov}</td>
              <td>{team.pf}</td>
              <td>{team.pts}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TeamInfo;