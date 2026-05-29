import { BrowserRouter as Router, Route, Routes, Link, Navigate, useLocation } from 'react-router-dom';
import PlayerProps from './PlayerProps';
import Players from './Players';

const SPORT_LINKS = [
  { to: '/nba', label: 'NBA', icon: '🏀' },
  { to: '/mlb', label: 'MLB', icon: '⚾' },
];

const PAGE_LINKS = [
  { to: '/players', label: 'Players' },
];

function NavBar() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center gap-6 px-4">
        <Link to="/nba" className="flex items-center gap-2 text-white font-bold text-lg tracking-tight shrink-0">
          <span className="text-blue-400">●</span> AlphaBetter
        </Link>

        {/* Sport tabs */}
        <div className="flex gap-1 rounded-lg border border-gray-800 bg-gray-900/60 p-1">
          {SPORT_LINKS.map(({ to, label, icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                pathname.startsWith(to)
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <span>{icon}</span>
              {label}
            </Link>
          ))}
        </div>

        {/* Page nav */}
        <nav className="flex gap-1 ml-2">
          {PAGE_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pathname === to
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#0a0d14]">
        <NavBar />
        <main className="mx-auto max-w-screen-xl px-4 py-6">
          <Routes>
            <Route path="/" element={<Navigate to="/nba" replace />} />
            <Route path="/player-props" element={<Navigate to="/nba" replace />} />
            <Route path="/nba" element={<PlayerProps sport="NBA" />} />
            <Route path="/mlb" element={<PlayerProps sport="MLB" />} />
            <Route path="/players" element={<Players />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
