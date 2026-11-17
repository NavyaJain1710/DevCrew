import { useOutletContext } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import type { Project } from '../../api/client';
import type { WSEvent } from '../../hooks/useWebSocket';

interface Context { project: Project | null; wsEvents: WSEvent[]; }

const EVENT_COLORS: Record<string, string> = {
  agent_started:          'bg-accent-blue',
  agent_completed:        'bg-accent-green',
  test_started:           'bg-accent-yellow',
  test_completed:         'bg-accent-yellow',
  security_scan_started:  'bg-accent-purple',
  security_scan_completed:'bg-accent-purple',
  review_started:         'bg-accent-blue',
  project_completed:      'bg-accent-green',
  human_approval_required:'bg-accent-yellow',
  error:                  'bg-accent-red',
};

export default function ActivityTab() {
  const { wsEvents } = useOutletContext<Context>();

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center gap-2">
        <Activity className="w-5 h-5 text-accent-blue" />
        <h2 className="font-semibold text-text-primary">Live Activity</h2>
        <span className="badge-gray">{wsEvents.length} events</span>
      </div>

      {wsEvents.length === 0 ? (
        <div className="card p-8 text-center">
          <Activity className="w-10 h-10 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary">No activity yet. Run the pipeline and events will appear here in real-time.</p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-2 bottom-2 w-px bg-bg-border" />
          <div className="space-y-3 pl-12">
            {wsEvents.map((event, i) => {
              const dotColor = EVENT_COLORS[event.event] ?? 'bg-text-muted';
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                  className="relative"
                >
                  {/* Dot */}
                  <div className={`absolute -left-[2.25rem] top-2 w-3 h-3 rounded-full border-2 border-bg-base ${dotColor}`} />

                  <div className="card p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm text-text-primary">{event.event}</span>
                      <span className="text-xs text-text-muted font-mono">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    {Object.keys(event.data).length > 0 && (
                      <pre className="text-xs text-text-muted overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(event.data, null, 2).slice(0, 200)}
                      </pre>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
