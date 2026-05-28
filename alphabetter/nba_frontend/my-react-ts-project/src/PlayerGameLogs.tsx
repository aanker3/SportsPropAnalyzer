import React, { useState } from 'react';
import axios from 'axios';

interface GameLog {
  game_date: string;
  player_id: number;
  matchup: string;
  min: number;
  pts: number;
  reb: number;
  ast: number;
  stl: number;
  blk: number;
  tov: number;
  fgm: number;
  fga: number;
  fg_pct: number;
  fg3m: number;
  fg3a: number;
  fg3_pct: number;
  ftm: number;
  fta: number;
  ft_pct: number;
}

const pct = (v: number) => v > 0 ? `${(v * 100).toFixed(1)}%` : '—';
const num = (v: number) => v > 0 ? v : '—';

export default function PlayerGameLogs() {
  const [playerName, setPlayerName] = useState('');
  const [gameLogs, setGameLogs] = useState<GameLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerName.trim()) return;
    setLoading(true);
    axios.get(`http://127.0.0.1:8000/api/player-gamelogs/${playerName.trim()}`)
      .then(res => {
        setGameLogs(res.data.game_logs ?? []);
        setFetched(playerName.trim());
        setError(null);
      })
      .catch(() => setError('Player not found or server error.'))
      .finally(() => setLoading(false));
  };

  const avg = (key: keyof GameLog) => {
    const active = gameLogs.filter(g => g.min > 0);
    if (!active.length) return 0;
    return active.reduce((s, g) => s + (g[key] as number), 0) / active.length;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Game Logs</h1>
        <p className="text-sm text-gray-500 mt-1">Look up any player's game-by-game stats</p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={playerName}
          onChange={e => setPlayerName(e.target.value)}
          placeholder="e.g. Shai Gilgeous-Alexander"
          className="h-10 w-72 rounded-lg border border-gray-700 bg-gray-900 px-4 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="h-10 rounded-lg bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : 'Search'}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {gameLogs.length > 0 && (
        <div className="space-y-4">
          {/* Season averages */}
          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
            <p className="text-xs uppercase text-gray-500 mb-3 tracking-wide">{fetched} — Season Averages ({gameLogs.filter(g => g.min > 0).length} games)</p>
            <div className="grid grid-cols-4 gap-4 sm:grid-cols-8">
              {[
                ['PTS', avg('pts').toFixed(1)],
                ['REB', avg('reb').toFixed(1)],
                ['AST', avg('ast').toFixed(1)],
                ['STL', avg('stl').toFixed(1)],
                ['BLK', avg('blk').toFixed(1)],
                ['TOV', avg('tov').toFixed(1)],
                ['FG%', pct(avg('fg_pct'))],
                ['3P%', pct(avg('fg3_pct'))],
              ].map(([label, value]) => (
                <div key={label} className="text-center">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-lg font-bold text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Game log table */}
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-900/80 text-gray-500 uppercase tracking-wide">
                  {['Date','Matchup','Min','PTS','REB','AST','STL','BLK','TOV','FGM/A','FG%','3PM/A','3P%','FTM/A','FT%'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-left whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {gameLogs.map((log, i) => (
                  <tr key={i} className={`transition-colors hover:bg-gray-800/40 ${log.min === 0 ? 'opacity-40' : ''}`}>
                    <td className="px-3 py-2 text-gray-400 whitespace-nowrap">{log.game_date}</td>
                    <td className="px-3 py-2 text-gray-300 whitespace-nowrap">{log.matchup}</td>
                    <td className="px-3 py-2 text-gray-400">{log.min}</td>
                    <td className="px-3 py-2 font-medium text-white">{log.pts}</td>
                    <td className="px-3 py-2 text-gray-300">{log.reb}</td>
                    <td className="px-3 py-2 text-gray-300">{log.ast}</td>
                    <td className="px-3 py-2 text-gray-300">{num(log.stl)}</td>
                    <td className="px-3 py-2 text-gray-300">{num(log.blk)}</td>
                    <td className="px-3 py-2 text-gray-300">{num(log.tov)}</td>
                    <td className="px-3 py-2 text-gray-400">{log.fgm}-{log.fga}</td>
                    <td className="px-3 py-2 text-gray-400">{pct(log.fg_pct)}</td>
                    <td className="px-3 py-2 text-gray-400">{log.fg3m}-{log.fg3a}</td>
                    <td className="px-3 py-2 text-gray-400">{pct(log.fg3_pct)}</td>
                    <td className="px-3 py-2 text-gray-400">{log.ftm}-{log.fta}</td>
                    <td className="px-3 py-2 text-gray-400">{pct(log.ft_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
