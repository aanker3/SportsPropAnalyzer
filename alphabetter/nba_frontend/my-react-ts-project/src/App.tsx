import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import PlayerId from './PlayerId';
import PlayerProps from './PlayerProps';
import PlayerGameLogs from './PlayerGameLogs';
import PlayerStats from './PlayerStats';

function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li>
              <Link to="/player-id">Player ID</Link>
            </li>
            <li>
              <Link to="/player-props">Player Props</Link>
            </li>
            <li>
              <Link to="/player-gamelogs">Player Game Logs</Link>
            </li>
            <li>
              <Link to="/player-stats">Player Stats</Link>
            </li>
          </ul>
        </nav>

        <Routes>
          <Route path="/player-id" element={<PlayerId />} />
          <Route path="/player-props" element={<PlayerProps />} />
          <Route path="/player-gamelogs" element={<PlayerGameLogs />} />
          <Route path="/player-stats" element={<PlayerStats />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;