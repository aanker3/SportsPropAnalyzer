import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import PlayerId from './PlayerId';
import PlayerProps from './PlayerProps';

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
          </ul>
        </nav>

        <Routes>
          <Route path="/player-id" element={<PlayerId />} />
          <Route path="/player-props" element={<PlayerProps />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;