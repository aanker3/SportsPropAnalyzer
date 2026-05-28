import { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

interface GameLog {
  game_date: string;
  matchup: string;
  game_minutes: number;
  stat_value: number;
}

interface PropInfo {
  stat: string;
  target: number;
  over_under: string;
  odds_type: string;
}

interface ApiResponse {
  player_id: number;
  player_name: string;
  prop: PropInfo;
  game_logs: GameLog[];
}

export default function PlayerStats() {
  const [propId, setPropId] = useState('');
  const [lastX, setLastX] = useState('20');
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    if (!propId) return;
    setLoading(true);
    try {
      const res = await window.fetch(`http://127.0.0.1:8000/api/last_x/${propId}/${lastX || 20}`);
      if (!res.ok) throw new Error(res.statusText);
      const json = await res.json();
      if (json.message) throw new Error(json.message);
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const hits = data?.game_logs.filter(l => {
    const isOver = data.prop.over_under === 'over';
    return isOver ? l.stat_value >= data.prop.target : l.stat_value <= data.prop.target;
  }).length ?? 0;

  const chartData = data ? (() => {
    const isOver = data.prop.over_under === 'over';
    const colors = data.game_logs.map(l => {
      const hit = isOver ? l.stat_value >= data.prop.target : l.stat_value <= data.prop.target;
      return hit ? 'rgba(34,197,94,0.8)' : 'rgba(239,68,68,0.7)';
    });
    return {
      labels: data.game_logs.map(l => `${l.game_date}  ${l.matchup}`),
      datasets: [{
        label: data.prop.stat,
        data: data.game_logs.map(l => l.stat_value),
        backgroundColor: colors,
        borderRadius: 4,
        borderWidth: 0,
      }],
    };
  })() : null;

  const chartOptions: any = data ? {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      annotation: {
        annotations: {
          line: {
            type: 'line' as const, yMin: data.prop.target, yMax: data.prop.target,
            borderColor: 'rgba(251,191,36,0.9)', borderWidth: 2, borderDash: [6, 4],
            label: {
              content: `Line: ${data.prop.target}`, display: true, position: 'end',
              backgroundColor: 'rgba(251,191,36,0.15)', color: '#fbbf24', font: { size: 11 },
            },
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => {
            const log = data.game_logs[ctx.dataIndex];
            return [`${data.prop.stat}: ${ctx.raw}`, `Min: ${log.game_minutes}`];
          },
        },
      },
    },
    scales: {
      x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#1e293b' } },
      y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
    },
  } : {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Stat Lookup</h1>
        <p className="text-sm text-gray-500 mt-1">Analyze any prop by ID with custom game range</p>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="mb-1 block text-xs text-gray-500">Prop ID</label>
          <input
            type="number"
            value={propId}
            onChange={e => setPropId(e.target.value)}
            placeholder="e.g. 6925"
            className="h-10 w-32 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">Last X Games</label>
          <input
            type="number"
            value={lastX}
            onChange={e => setLastX(e.target.value)}
            min={1} max={82}
            className="h-10 w-24 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm text-white focus:border-blue-500 focus:outline-none"
          />
        </div>
        <button
          onClick={fetch}
          disabled={loading}
          className="h-10 rounded-lg bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : 'Analyze'}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {data && (
        <div className="space-y-4">
          {/* Prop info */}
          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
            <div className="flex flex-wrap gap-6 items-center">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Player</p>
                <p className="text-lg font-bold text-white">{data.player_name}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Stat</p>
                <p className="text-base font-semibold text-gray-200">{data.prop.stat}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Line</p>
                <p className="text-base font-mono text-white">
                  {data.prop.target}
                  <span className={`ml-1.5 text-sm ${data.prop.over_under === 'over' ? 'text-green-400' : 'text-red-400'}`}>
                    {data.prop.over_under.toUpperCase()}
                  </span>
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Hit Rate</p>
                <p className={`text-2xl font-bold ${hits / data.game_logs.length >= 0.6 ? 'text-green-400' : hits / data.game_logs.length >= 0.4 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {hits}/{data.game_logs.length} <span className="text-base">({Math.round(hits / data.game_logs.length * 100)}%)</span>
                </p>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
            <div className="h-64">
              {chartData && <Bar data={chartData} options={chartOptions} />}
            </div>
          </div>

          {/* Game log table */}
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-900/80 text-xs uppercase tracking-wide text-gray-500">
                  <th className="px-4 py-2.5 text-left">Date</th>
                  <th className="px-4 py-2.5 text-left">Matchup</th>
                  <th className="px-4 py-2.5 text-center">Min</th>
                  <th className="px-4 py-2.5 text-center">{data.prop.stat}</th>
                  <th className="px-4 py-2.5 text-center">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {data.game_logs.map((log, i) => {
                  const isOver = data.prop.over_under === 'over';
                  const hit = isOver ? log.stat_value >= data.prop.target : log.stat_value <= data.prop.target;
                  return (
                    <tr key={i} className="hover:bg-gray-800/40 transition-colors">
                      <td className="px-4 py-2 text-gray-400 text-xs">{log.game_date}</td>
                      <td className="px-4 py-2 text-gray-300 text-xs">{log.matchup}</td>
                      <td className="px-4 py-2 text-center text-gray-500 text-xs">{log.game_minutes}</td>
                      <td className="px-4 py-2 text-center font-mono font-medium text-white">{log.stat_value}</td>
                      <td className="px-4 py-2 text-center">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${hit ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {hit ? 'Hit' : 'Miss'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
