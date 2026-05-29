import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

import API_URL from './api';
const API = API_URL;

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

interface GameLog {
  game_date: string;
  matchup: string;
  game_minutes: number;
  stat_value: number;
}

const ODDS_STYLE: Record<string, string> = {
  demon:    'bg-orange-900/50 text-orange-300 border border-orange-700/50',
  goblin:   'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  standard: 'bg-slate-800 text-slate-300 border border-slate-600/50',
};

function RateBar({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const barColor = pct >= 60 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="h-1.5 flex-1 rounded-full bg-gray-700">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono w-8 text-right ${pct >= 60 ? 'text-green-400' : pct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
        {pct}%
      </span>
    </div>
  );
}

type SortKey = 'l5_hit_rate' | 'l10_hit_rate' | 'l20_hit_rate' | 'last_percent_rate';

export default function PlayerProps() {
  const [props, setProps] = useState<Prop[]>([]);
  const [stats, setStats] = useState<Record<number, Stat>>({});
  const [selectedProp, setSelectedProp] = useState<Prop | null>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [chartOptions, setChartOptions] = useState<any>(null);
  const [chartKey, setChartKey] = useState(0);
  const [seasonAvg, setSeasonAvg] = useState<number | null>(null);
  const [sliderValue, setSliderValue] = useState(10);
  const [sortKey, setSortKey] = useState<SortKey>('l10_hit_rate');
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');
  const [search, setSearch] = useState('');
  const [oddsFilter, setOddsFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');

  const loadData = () => {
    setLoading(true);
    return Promise.all([
      axios.get(`${API}/api/props`),
      axios.get(`${API}/api/player-stats-calculated`),
    ]).then(([propsRes, statsRes]) => {
      setProps(propsRes.data.props);
      const map: Record<number, Stat> = {};
      statsRes.data.stats.forEach((s: Stat) => { map[s.prop_id] = s; });
      setStats(map);
      setLoading(false);
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg('Fetching latest props and stats… (this takes ~30s)');
    try {
      await axios.post(`${API}/api/fetch_and_calculate_all`);
      setRefreshMsg('Done! Reloading data…');
      await loadData();
      setRefreshMsg('');
    } catch {
      setRefreshMsg('Refresh failed — check backend logs.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/props`),
      axios.get(`${API}/api/player-stats-calculated`),
    ]).then(([propsRes, statsRes]) => {
      setProps(propsRes.data.props);
      const map: Record<number, Stat> = {};
      statsRes.data.stats.forEach((s: Stat) => { map[s.prop_id] = s; });
      setStats(map);
      setLoading(false);
    });
  }, []);

  const fetchChart = async (prop: Prop, games: number, isNewProp = false) => {
    const res = await fetch(`${API}/api/last_x/${prop.id}/${games}`);
    const result = await res.json();
    if (!result.game_logs) return;

    // Compute season average from full dataset on first open
    if (isNewProp) {
      const allRes = await fetch(`${API}/api/last_x/${prop.id}/82`);
      const allResult = await allRes.json();
      if (allResult.game_logs?.length) {
        const active = allResult.game_logs.filter((l: GameLog) => l.game_minutes > 0);
        const avg = active.length ? active.reduce((s: number, l: GameLog) => s + l.stat_value, 0) / active.length : 0;
        setSeasonAvg(Math.round(avg * 10) / 10);
      }
    }

    const labels = result.game_logs.map((l: GameLog) => `${l.game_date}  ${l.matchup}`);
    const values = result.game_logs.map((l: GameLog) => l.stat_value);
    const target = result.prop.target;
    const isOver = result.prop.over_under === 'over';
    const colors = values.map((v: number) => {
      const hit = isOver ? v >= target : v <= target;
      return hit ? 'rgba(34,197,94,0.8)' : 'rgba(239,68,68,0.7)';
    });

    setChartKey(k => k + 1);
    setChartData({
      labels,
      datasets: [{ label: result.prop.stat, data: values, backgroundColor: colors, borderRadius: 4, borderWidth: 0 }],
    });
    setChartOptions({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        annotation: {
          annotations: {
            line: {
              type: 'line' as const, yMin: target, yMax: target,
              borderColor: 'rgba(251,191,36,0.9)', borderWidth: 2, borderDash: [6, 4],
              label: {
                content: `Line: ${target}`, display: true, position: 'end',
                backgroundColor: 'rgba(251,191,36,0.15)', color: '#fbbf24', font: { size: 11 },
              },
            },
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx: any) => {
              const log = result.game_logs[ctx.dataIndex];
              return [`${result.prop.stat}: ${ctx.raw}`, `Min: ${log.game_minutes}`];
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
      },
    });
  };

  const closeModal = () => { setSelectedProp(null); setSeasonAvg(null); };

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') closeModal(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const handleRowClick = (prop: Prop) => {
    setSelectedProp(prop);
    setSeasonAvg(null);
    fetchChart(prop, sliderValue, true);
  };

  const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.target.value);
    setSliderValue(v);
    if (selectedProp) fetchChart(selectedProp, v);
  };

  const filtered = useMemo(() => {
    return props
      .filter(p => {
        const s = search.toLowerCase();
        return (p.player_name.toLowerCase().includes(s) || p.stat.toLowerCase().includes(s)) &&
          (oddsFilter === 'all' || p.odds_type === oddsFilter);
      })
      .sort((a, b) => {
        const sa = stats[a.id]?.[sortKey] ?? 0;
        const sb = stats[b.id]?.[sortKey] ?? 0;
        return sortDir === 'desc' ? sb - sa : sa - sb;
      });
  }, [props, stats, search, oddsFilter, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const summaryStats = useMemo(() => {
    const vals = Object.values(stats);
    if (!vals.length) return null;
    const best = Math.max(...vals.map(s => s.l10_hit_rate));
    const avg = vals.reduce((a, s) => a + s.l10_hit_rate, 0) / vals.length;
    const hot = vals.filter(s => s.l10_hit_rate >= 0.7).length;
    return { total: props.length, best: Math.round(best * 100), avg: Math.round(avg * 100), hot };
  }, [props, stats]);

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      {summaryStats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: 'Total Props', value: summaryStats.total, color: 'text-blue-400' },
            { label: 'Avg L10 Hit Rate', value: `${summaryStats.avg}%`, color: 'text-slate-300' },
            { label: 'Best L10', value: `${summaryStats.best}%`, color: 'text-green-400' },
            { label: 'Hot (L10 ≥ 70%)', value: summaryStats.hot, color: 'text-orange-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl border border-gray-800 bg-gray-900/60 px-4 py-3">
              <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
              <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Refresh */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="h-8 rounded-lg bg-gray-800 px-4 text-xs font-medium text-gray-300 hover:bg-gray-700 hover:text-white disabled:opacity-50 transition-colors"
        >
          {refreshing ? '↻ Refreshing…' : '↻ Refresh Props'}
        </button>
        {refreshMsg && <span className="text-xs text-gray-400">{refreshMsg}</span>}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Search player or stat…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-9 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none w-56"
        />
        <select
          value={oddsFilter}
          onChange={e => setOddsFilter(e.target.value)}
          className="h-9 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white focus:border-blue-500 focus:outline-none"
        >
          <option value="all">All Odds Types</option>
          <option value="demon">Demon</option>
          <option value="goblin">Goblin</option>
          <option value="standard">Standard</option>
        </select>
      </div>

      {/* Props count */}
      <p className="text-xs text-gray-500">{filtered.length} props</p>

      {/* Table */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-gray-500">Loading props…</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3 text-left">Player</th>
                <th className="px-4 py-3 text-left">Stat</th>
                <th className="px-4 py-3 text-center">Line</th>
                <th className="px-4 py-3 text-center">Type</th>
                {([['l5_hit_rate','L5'],['l10_hit_rate','L10'],['l20_hit_rate','L20'],['last_percent_rate','Best %']] as [SortKey,string][]).map(([key, label]) => (
                  <th
                    key={key}
                    onClick={() => handleSort(key)}
                    className="px-4 py-3 text-left min-w-[110px] cursor-pointer select-none hover:text-white transition-colors"
                  >
                    <span className="flex items-center gap-1">
                      {label}
                      <span className="text-gray-600">
                        {sortKey === key ? (sortDir === 'desc' ? '▼' : '▲') : '⇅'}
                      </span>
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map(prop => {
                const s = stats[prop.id];
                return (
                  <tr
                    key={prop.id}
                    onClick={() => handleRowClick(prop)}
                    className="cursor-pointer bg-gray-900/30 transition-colors hover:bg-gray-800/60"
                  >
                    <td className="px-4 py-3 font-medium text-white">{prop.player_name}</td>
                    <td className="px-4 py-3 text-gray-300">{prop.stat}</td>
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
                      <td colSpan={4} className="px-4 py-3 text-gray-600 text-center text-xs">No data</td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {selectedProp && (
        <>
          <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm" onClick={closeModal} />
          <div className="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
            {/* Modal header */}
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">{selectedProp.player_name}</h2>
                <p className="text-sm text-gray-400">
                  {selectedProp.stat} &mdash; Line: <span className="font-mono text-white">{selectedProp.target}</span>
                  <span className={`ml-2 text-xs ${selectedProp.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedProp.over_under.toUpperCase()}
                  </span>
                  {seasonAvg !== null && (
                    <span className="ml-3 text-xs text-gray-500">
                      Season avg: <span className={`font-mono ${seasonAvg >= selectedProp.target ? 'text-green-400' : 'text-red-400'}`}>{seasonAvg}</span>
                    </span>
                  )}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-800 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Hit rate pills */}
            {stats[selectedProp.id] && (
              <div className="mb-4 flex gap-3">
                {(['l5', 'l10', 'l20'] as const).map(k => {
                  const rate = stats[selectedProp.id][`${k}_hit_rate` as SortKey];
                  const pct = Math.round(rate * 100);
                  const color = pct >= 60 ? 'text-green-400 bg-green-900/30 border-green-800' : pct >= 40 ? 'text-yellow-400 bg-yellow-900/30 border-yellow-800' : 'text-red-400 bg-red-900/30 border-red-800';
                  return (
                    <div key={k} className={`rounded-lg border px-3 py-1.5 text-center ${color}`}>
                      <p className="text-xs text-gray-500 uppercase">{k.toUpperCase()}</p>
                      <p className="text-lg font-bold">{pct}%</p>
                    </div>
                  );
                })}
                <div className="rounded-lg border border-gray-700 bg-gray-800/40 px-3 py-1.5 text-center">
                  <p className="text-xs text-gray-500 uppercase">Best %</p>
                  <p className="text-lg font-bold text-blue-400">{stats[selectedProp.id].last_percent_total}</p>
                </div>
              </div>
            )}

            {/* Chart — key forces full remount on every fetch so slider always reflects new data */}
            <div className="h-56">
              {chartData && chartOptions && <Bar key={chartKey} data={chartData} options={chartOptions} />}
            </div>

            {/* Slider */}
            <div className="mt-4">
              <label className="mb-1 flex justify-between text-xs text-gray-400">
                <span>Games shown</span>
                <span className="font-mono text-white">{sliderValue}</span>
              </label>
              <input
                type="range" min={5} max={82} value={sliderValue}
                onChange={handleSlider}
                className="w-full accent-blue-500"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
