import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Star } from 'lucide-react';
import { reports, type ReviewResult } from '../../api/client';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

export default function ReviewTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [review, setReview] = useState<ReviewResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    reports.getReview(projectId).then(setReview).catch(console.error).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="text-text-muted text-sm">Loading review…</div>;

  if (!review || review.status === 'not_run') {
    return (
      <div className="card p-8 text-center max-w-md">
        <Star className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">Code review not yet completed.</p>
      </div>
    );
  }

  const radarData = [
    { subject: 'Code Quality', value: review.code_quality_score },
    { subject: 'Architecture', value: review.architecture_score },
    { subject: 'Security', value: review.security_score },
    { subject: 'Testing', value: review.testing_score },
    { subject: 'Documentation', value: review.documentation_score },
  ];

  const isApproved = review.status === 'approved';

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-3">
        {isApproved
          ? <CheckCircle2 className="w-5 h-5 text-accent-green" />
          : <XCircle className="w-5 h-5 text-accent-red" />
        }
        <h2 className="font-semibold text-text-primary">Code Review</h2>
        <span className={isApproved ? 'badge-green' : 'badge-red'}>
          {isApproved ? 'Approved' : 'Changes Required'}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <Star className="w-4 h-4 text-accent-yellow" />
          <span className="text-xl font-bold text-text-primary">{review.overall_score.toFixed(1)}</span>
          <span className="text-text-muted text-sm">/100</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar chart */}
        <div className="card p-6">
          <h3 className="font-medium text-text-primary mb-4">Score Breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#30363d" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#8b949e', fontSize: 11 }} />
              <Radar dataKey="value" stroke="#58a6ff" fill="#58a6ff" fillOpacity={0.2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Score cards */}
        <div className="space-y-3">
          {radarData.map((d) => (
            <div key={d.subject} className="flex items-center gap-3">
              <span className="text-sm text-text-secondary w-32">{d.subject}</span>
              <div className="flex-1 bg-bg-raised rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${d.value}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className={`h-full rounded-full ${
                    d.value >= 80 ? 'bg-accent-green' :
                    d.value >= 60 ? 'bg-accent-yellow' :
                    'bg-accent-red'
                  }`}
                />
              </div>
              <span className={`text-sm font-medium w-12 text-right ${
                d.value >= 80 ? 'text-accent-green' :
                d.value >= 60 ? 'text-accent-yellow' :
                'text-accent-red'
              }`}>{d.value.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Strengths */}
      {review.strengths.length > 0 && (
        <div className="card p-6">
          <h3 className="font-medium text-accent-green mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> Strengths
          </h3>
          <ul className="space-y-2">
            {review.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                <span className="text-accent-green mt-0.5">✓</span>{s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues */}
      {review.issues.length > 0 && (
        <div className="card p-6">
          <h3 className="font-medium text-accent-red mb-3 flex items-center gap-2">
            <XCircle className="w-4 h-4" /> Issues
          </h3>
          <div className="space-y-3">
            {review.issues.map((issue, i) => (
              <div key={i} className="p-3 bg-bg-raised rounded-lg border border-bg-border">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`badge ${
                    issue.severity === 'critical' || issue.severity === 'high' ? 'badge-red' :
                    issue.severity === 'medium' ? 'badge-yellow' : 'badge-gray'
                  }`}>{issue.severity}</span>
                  <span className="text-xs text-text-muted">{issue.category}</span>
                  {issue.file && <span className="font-mono text-xs text-text-muted">{issue.file}</span>}
                </div>
                <p className="text-sm text-text-secondary">{issue.description}</p>
                {issue.recommendation && (
                  <p className="text-xs text-text-muted mt-1">→ {issue.recommendation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {review.recommendations.length > 0 && (
        <div className="card p-6">
          <h3 className="font-medium text-text-primary mb-3">Recommendations</h3>
          <ul className="space-y-2">
            {review.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                <span className="text-accent-blue mt-0.5">•</span>{r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
