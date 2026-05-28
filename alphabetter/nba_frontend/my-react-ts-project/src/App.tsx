import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import PlayerProps from './PlayerProps';
import PlayerGameLogs from './PlayerGameLogs';
import PlayerStats from './PlayerStats';

const NAV_LINKS = [
  { to: '/player-props', label: 'Props' },
  { to: '/player-gamelogs', label: 'Game Logs' },
  { to: '/player-stats', label: 'Stat Lookup' },
];

function NavBar() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-screen-xl items-center gap-8 px-4">
        <Link to="/player-props" className="flex items-center gap-2 text-white font-bold text-lg tracking-tight">
          <span className="text-blue-400">●</span> AlphaBetter
        </Link>
        <nav className="flex gap-1">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pathname === to
                  ? 'bg-blue-600 text-white'
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
            <Route path="/" element={<PlayerProps />} />
            <Route path="/player-props" element={<PlayerProps />} />
            <Route path="/player-gamelogs" element={<PlayerGameLogs />} />
            <Route path="/player-stats" element={<PlayerStats />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
