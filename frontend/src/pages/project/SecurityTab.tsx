import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { reports, type SecurityResult } from '../../api/client';

const SEV_CONFIG: Record<string, { color: string; badge: string; icon: typeof Shield }> = {
  critical: { color: 'text-accent-red border-accent-red/30 bg-accent-red/5', badge: 'badge-red', icon: AlertCircle },
  high:     { color: 'text-accent-red border-accent-red/20 bg-accent-red/5', badge: 'badge-red', icon: AlertTriangle },
  medium:   { color: 'text-accent-yellow border-accent-yellow/20 bg-accent-yellow/5', badge: 'badge-yellow', icon: AlertTriangle },
  low:      { color: 'text-text-secondary border-bg-border bg-bg-raised', badge: 'badge-gray', icon: Info },
  info:     { color: 'text-text-muted border-bg-border bg-bg-raised', badge: 'badge-gray', icon: Info },
};

export default function SecurityTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [result, setResult] = useState<SecurityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (!projectId) return;
    reports.getSecurity(projectId).then(setResult).catch(console.error).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="text-text-muted text-sm">Loading security results…</div>;

  if (!result || result.status === 'not_run') {
    return (
      <div className="card p-8 text-center max-w-md">
        <Shield className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">Security scan not yet run. Execute the pipeline first.</p>
      </div>
    );
  }

  const filtered = filter === 'all'
    ? result.findings
    : result.findings.filter(f => f.severity === filter);

  const isClean = result.critical_count === 0 && result.high_count === 0;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-2">
        <Shield className={`w-5 h-5 ${isClean ? 'text-accent-green' : 'text-accent-red'}`} />
        <h2 className="font-semibold text-text-primary">Security Analysis</h2>
        {isClean
          ? <span className="badge-green"><CheckCircle2 className="w-3 h-3" /> Cleared</span>
          : <span className="badge-red"><AlertTriangle className="w-3 h-3" /> Issues Found</span>
        }
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Critical', value: result.critical_count, cls: result.critical_count > 0 ? 'text-accent-red' : 'text-text-muted' },
          { label: 'High', value: result.high_count, cls: result.high_count > 0 ? 'text-accent-red' : 'text-text-muted' },
          { label: 'Medium', value: result.medium_count, cls: result.medium_count > 0 ? 'text-accent-yellow' : 'text-text-muted' },
          { label: 'Low', value: result.low_count, cls: 'text-text-muted' },
        ].map((s) => (
          <div key={s.label} className="metric-card">
            <div className={`text-2xl font-bold ${s.cls}`}>{s.value}</div>
            <div className="text-xs text-text-muted">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Severity filter */}
      {result.findings.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilter(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                filter === sev ? 'bg-accent-blue/10 text-accent-blue border border-accent-blue/30' : 'bg-bg-raised text-text-muted border border-bg-border hover:text-text-primary'
              }`}
            >
              {sev} {sev !== 'all' && `(${result.findings.filter(f => f.severity === sev).length})`}
            </button>
          ))}
        </div>
      )}

      {/* Findings */}
      {filtered.length === 0 ? (
        <div className="card p-8 text-center">
          <CheckCircle2 className="w-10 h-10 text-accent-green mx-auto mb-3" />
          <p className="text-text-secondary">
            {result.findings.length === 0 ? 'No security issues found.' : 'No findings match the current filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((f, i) => {
            const cfg = SEV_CONFIG[f.severity] ?? SEV_CONFIG.info;
            const Icon = cfg.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`p-4 rounded-lg border ${cfg.color}`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className="font-medium text-sm">{f.title}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={cfg.badge}>{f.severity}</span>
                    {f.status === 'fixed' && <span className="badge-green">Fixed ✓</span>}
                    <span className="badge-gray text-xs">{f.scanner}</span>
                  </div>
                </div>
                {f.file && (
                  <div className="font-mono text-xs text-text-muted mb-2">
                    {f.file}{f.line ? `:${f.line}` : ''}
                  </div>
                )}
                <p className="text-xs text-text-secondary mb-2">{f.description}</p>
                {f.impact && <p className="text-xs text-text-muted mb-2"><strong>Impact:</strong> {f.impact}</p>}
                {f.recommendation && (
                  <div className="bg-bg-base/50 p-2 rounded text-xs text-text-secondary">
                    <strong>Fix:</strong> {f.recommendation}
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
