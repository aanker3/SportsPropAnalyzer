import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Props from './Props';
import TeamInfo from './TeamInfo';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav>
          <ul>
            <li>
              <Link to="/props">Props</Link>
            </li>
            <li>
              <Link to="/team-info">Team Info</Link>
            </li>
          </ul>
        </nav>
        <Routes>
          <Route path="/props" element={<Props />} />
          <Route path="/team-info" element={<TeamInfo />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;