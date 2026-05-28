import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000';

interface GameLog {
  game_date: string;
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

interface Prop {
  id: number;
  player_name: string;
  stat: string;
  target: number;
  over_under: string;
  odds_type: string;
}

interface Stat {
  prop_id: number;
  l5_hit_rate: number;
  l10_hit_rate: number;
  l20_hit_rate: number;
  last_percent_rate: number;
  last_percent_total: string;
}

const pct = (v: number) => v > 0 ? `${v.toFixed(1)}%` : '—';
const num = (v: number) => v > 0 ? v : '—';

const ODDS_STYLE: Record<string, string> = {
  demon:    'bg-orange-900/50 text-orange-300 border border-orange-700/50',
  goblin:   'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  standard: 'bg-slate-800 text-slate-300 border border-slate-600/50',
};

function RateBar({ rate }: { rate: number }) {
  const p = Math.round(rate * 100);
  const color = p >= 60 ? 'bg-green-500' : p >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  const textColor = p >= 60 ? 'text-green-400' : p >= 40 ? 'text-yellow-400' : 'text-red-400';
  return (
    <div className="flex items-center gap-2 min-w-[90px]">
      <div className="h-1.5 flex-1 rounded-full bg-gray-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${p}%` }} />
      </div>
      <span className={`text-xs font-mono w-8 text-right ${textColor}`}>{p}%</span>
    </div>
  );
}

export default function Players() {
  const [playerName, setPlayerName] = useState('');
  const [gameLogs, setGameLogs] = useState<GameLog[]>([]);
  const [playerProps, setPlayerProps] = useState<Prop[]>([]);
  const [statsMap, setStatsMap] = useState<Record<number, Stat>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState('');

  type SortKey = 'l5_hit_rate' | 'l10_hit_rate' | 'l20_hit_rate' | 'last_percent_rate';
  const [propSort, setPropSort] = useState<SortKey | null>(null);
  const [propSortDir, setPropSortDir] = useState<'desc' | 'asc'>('desc');

  const [allPlayers, setAllPlayers] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    axios.get(`${API}/api/props`).then(res => {
      const names: string[] = Array.from(
        new Set((res.data.props as Prop[]).map(p => p.player_name))
      ).sort();
      setAllPlayers(names);
    });
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setPlayerName(val);
    setActiveSuggestion(-1);
    if (val.trim().length >= 2) {
      const q = val.toLowerCase();
      const matches = allPlayers.filter(n => n.toLowerCase().includes(q)).slice(0, 8);
      setSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveSuggestion(i => Math.min(i + 1, suggestions.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveSuggestion(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter' && activeSuggestion >= 0) { e.preventDefault(); selectSuggestion(suggestions[activeSuggestion]); }
    else if (e.key === 'Escape') setShowSuggestions(false);
  };

  const selectSuggestion = (name: string) => {
    setPlayerName(name);
    setSuggestions([]);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
    doFetch(name);
  };

  const doFetch = async (name: string) => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const [logsRes, propsRes, statsRes] = await Promise.all([
        axios.get(`${API}/api/player-gamelogs/${name.trim()}`),
        axios.get(`${API}/api/props`),
        axios.get(`${API}/api/player-stats-calculated`),
      ]);

      const logs: GameLog[] = logsRes.data.game_logs ?? [];
      const allProps: Prop[] = propsRes.data.props ?? [];
      const allStats: Stat[] = statsRes.data.stats ?? [];

      const filteredProps = allProps.filter(
        p => p.player_name.toLowerCase() === name.trim().toLowerCase()
      );

      const map: Record<number, Stat> = {};
      allStats.forEach(s => { map[s.prop_id] = s; });

      setGameLogs(logs);
      setPlayerProps(filteredProps);
      setStatsMap(map);
      setFetched(name.trim());

      if (!logs.length && !filteredProps.length) setError('Player not found.');
    } catch {
      setError('Player not found or server error.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    doFetch(playerName);
  };

  const handlePropSort = (key: SortKey) => {
    if (propSort === key) {
      setPropSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setPropSort(key);
      setPropSortDir('desc');
    }
  };

  const sortedProps = propSort
    ? [...playerProps].sort((a, b) => {
        const va = statsMap[a.id]?.[propSort] ?? 0;
        const vb = statsMap[b.id]?.[propSort] ?? 0;
        return propSortDir === 'desc' ? vb - va : va - vb;
      })
    : playerProps;

  const avg = (key: keyof GameLog) => {
    const active = gameLogs.filter(g => g.min > 0);
    if (!active.length) return 0;
    return active.reduce((s, g) => s + (g[key] as number), 0) / active.length;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Players</h1>
        <p className="text-sm text-gray-500 mt-1">View a player's active props and full game log</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={playerName}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="e.g. Shai Gilgeous-Alexander"
            autoComplete="off"
            className="h-10 w-80 rounded-lg border border-gray-700 bg-gray-900 px-4 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
          {showSuggestions && (
            <ul className="absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-lg border border-gray-700 bg-gray-900 shadow-xl">
              {suggestions.map((name, i) => (
                <li
                  key={name}
                  onMouseDown={() => selectSuggestion(name)}
                  className={`cursor-pointer px-4 py-2 text-sm transition-colors ${
                    i === activeSuggestion ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  {name}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="h-10 rounded-lg bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : 'Search'}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {fetched && !loading && (
        <div className="space-y-6">

          {/* Season averages */}
          {gameLogs.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
              <p className="text-xs uppercase text-gray-500 mb-3 tracking-wide">
                {fetched} — Season Averages ({gameLogs.filter(g => g.min > 0).length} games)
              </p>
              <div className="grid grid-cols-4 gap-4 sm:grid-cols-8">
                {([
                  ['PTS', avg('pts').toFixed(1)],
                  ['REB', avg('reb').toFixed(1)],
                  ['AST', avg('ast').toFixed(1)],
                  ['STL', avg('stl').toFixed(1)],
                  ['BLK', avg('blk').toFixed(1)],
                  ['TOV', avg('tov').toFixed(1)],
                  ['FG%', pct(avg('fg_pct'))],
                  ['3P%', pct(avg('fg3_pct'))],
                ] as [string, string][]).map(([label, value]) => (
                  <div key={label} className="text-center">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-lg font-bold text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active props */}
          {playerProps.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">
                Active Props ({playerProps.length})
              </h2>
              <div className="overflow-x-auto rounded-xl border border-gray-800">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
                      <th className="px-4 py-3 text-left">Stat</th>
                      <th className="px-4 py-3 text-center">Line</th>
                      <th className="px-4 py-3 text-center">Type</th>
                      {([ ['l5_hit_rate','L5'], ['l10_hit_rate','L10'], ['l20_hit_rate','L20'], ['last_percent_rate','Best %'] ] as [SortKey, string][]).map(([key, label]) => (
                        <th
                          key={key}
                          onClick={() => handlePropSort(key)}
                          className="px-4 py-3 text-left min-w-[110px] cursor-pointer select-none hover:text-white transition-colors"
                        >
                          <span className="flex items-center gap-1">
                            {label}
                            <span className="text-gray-600">
                              {propSort === key ? (propSortDir === 'desc' ? '▼' : '▲') : '⇅'}
                            </span>
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60">
                    {sortedProps.map(prop => {
                      const s = statsMap[prop.id];
                      return (
                        <tr key={prop.id} className="bg-gray-900/30 hover:bg-gray-800/50 transition-colors">
                          <td className="px-4 py-3 font-medium text-white">{prop.stat}</td>
                          <td className="px-4 py-3 text-center">
                            <span className="font-mono text-white">{prop.target}</span>
                            <span className={`ml-1.5 text-xs ${prop.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                              {prop.over_under === 'over' ? '▲' : '▼'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${ODDS_STYLE[prop.odds_type] ?? ODDS_STYLE.standard}`}>
                              {prop.odds_type}
                            </span>
                          </td>
                          {s ? (
                            <>
                              <td className="px-4 py-3"><RateBar rate={s.l5_hit_rate} /></td>
                              <td className="px-4 py-3"><RateBar rate={s.l10_hit_rate} /></td>
                              <td className="px-4 py-3"><RateBar rate={s.l20_hit_rate} /></td>
                              <td className="px-4 py-3">
                                <span className="font-mono text-xs text-gray-300">{s.last_percent_total}</span>
                                <span className="ml-1 text-xs text-gray-500">({Math.round(s.last_percent_rate * 100)}%)</span>
                              </td>
                            </>
                          ) : (
                            <td colSpan={4} className="px-4 py-3 text-xs text-gray-600 text-center">No data</td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Game log */}
          {gameLogs.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">
                Game Log
              </h2>
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
      )}
    </div>
  );
}
