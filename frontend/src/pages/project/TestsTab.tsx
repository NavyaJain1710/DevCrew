import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FlaskConical, CheckCircle2, XCircle, Clock, TrendingUp } from 'lucide-react';
import { reports, type TestResult } from '../../api/client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

export default function TestsTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [testRuns, setTestRuns] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    reports.getTests(projectId).then(setTestRuns).catch(console.error).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="text-text-muted text-sm">Loading test results…</div>;

  const latest = testRuns[0];

  const pieData = latest ? [
    { name: 'Passed', value: latest.passed, color: '#3fb950' },
    { name: 'Failed', value: latest.failed, color: '#f85149' },
    { name: 'Skipped', value: latest.skipped, color: '#6e7681' },
  ].filter(d => d.value > 0) : [];

  const historyData = [...testRuns].reverse().map((r, i) => ({
    iter: `Iter ${r.iteration || i + 1}`,
    passed: r.passed,
    failed: r.failed,
    coverage: r.coverage_percent,
  }));

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-2">
        <FlaskConical className="w-5 h-5 text-accent-yellow" />
        <h2 className="font-semibold text-text-primary">Test Results</h2>
        {testRuns.length > 0 && (
          <span className="badge-gray">{testRuns.length} run{testRuns.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {!latest ? (
        <div className="card p-8 text-center">
          <FlaskConical className="w-10 h-10 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary">No test runs yet. Run the pipeline to generate tests.</p>
        </div>
      ) : (
        <>
          {/* Summary metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Passed', value: latest.passed, icon: CheckCircle2, color: 'text-accent-green' },
              { label: 'Failed', value: latest.failed, icon: XCircle, color: 'text-accent-red' },
              { label: 'Coverage', value: `${latest.coverage_percent.toFixed(1)}%`, icon: TrendingUp, color: 'text-accent-blue' },
              { label: 'Time', value: `${(latest.execution_time_ms / 1000).toFixed(1)}s`, icon: Clock, color: 'text-text-secondary' },
            ].map((m) => (
              <div key={m.label} className="metric-card">
                <m.icon className={`w-4 h-4 ${m.color} mb-1`} />
                <div className="text-2xl font-bold text-text-primary">{m.value}</div>
                <div className="text-xs text-text-muted">{m.label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie chart */}
            {pieData.length > 0 && (
              <div className="card p-6">
                <h3 className="font-medium text-text-primary mb-4">Pass/Fail Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" label={({ name, percent }) => `${name} ${(((percent as number) ?? 0) * 100).toFixed(0)}%`} labelLine={false}>
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Coverage history */}
            {historyData.length > 1 && (
              <div className="card p-6">
                <h3 className="font-medium text-text-primary mb-4">Coverage Over Iterations</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={historyData}>
                    <XAxis dataKey="iter" tick={{ fontSize: 10, fill: '#8b949e' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#8b949e' }} unit="%" />
                    <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d' }} />
                    <Bar dataKey="coverage" fill="#58a6ff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Failures */}
          {latest.failures.length > 0 && (
            <div className="card p-6">
              <h3 className="font-medium text-text-primary mb-4 flex items-center gap-2">
                <XCircle className="w-4 h-4 text-accent-red" />
                Test Failures ({latest.failures.length})
              </h3>
              <div className="space-y-3">
                {latest.failures.map((f, i) => (
                  <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                    className="p-4 bg-bg-raised rounded-lg border border-accent-red/20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-sm text-accent-red">{f.test_name}</span>
                      <span className={`badge ${f.severity === 'critical' || f.severity === 'high' ? 'badge-red' : f.severity === 'medium' ? 'badge-yellow' : 'badge-gray'}`}>
                        {f.severity}
                      </span>
                    </div>
                    <div className="text-xs text-text-muted mb-1">{f.file}{f.line ? `:${f.line}` : ''}</div>
                    <pre className="text-xs text-text-secondary bg-bg-base p-2 rounded overflow-x-auto whitespace-pre-wrap">{f.error}</pre>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {latest.recommendations.length > 0 && (
            <div className="card p-6">
              <h3 className="font-medium text-text-primary mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {latest.recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                    <span className="text-accent-blue mt-0.5">•</span>{r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
