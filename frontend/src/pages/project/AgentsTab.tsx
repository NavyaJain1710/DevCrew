import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bot, CheckCircle2, Clock, Loader2, AlertCircle, ArrowRightLeft,
  Layers, ExternalLink
} from 'lucide-react';
import { agents as agentsApi, type AgentRun } from '../../api/client';

interface AgentConfig {
  framework: 'CrewAI' | 'Google ADK';
  badgeStyle: string;
  role: string;
}

const AGENT_META: Record<string, AgentConfig> = {
  manager: {
    framework: 'CrewAI',
    badgeStyle: 'text-accent-blue border-accent-blue/30 bg-accent-blue/10',
    role: 'Orchestrator & Delivery Lead',
  },
  requirement: {
    framework: 'CrewAI',
    badgeStyle: 'text-accent-purple border-accent-purple/30 bg-accent-purple/10',
    role: 'Senior Requirement Analyst',
  },
  architect: {
    framework: 'CrewAI',
    badgeStyle: 'text-accent-cyan border-accent-cyan/30 bg-accent-cyan/10',
    role: 'Principal Software Architect',
  },
  developer: {
    framework: 'Google ADK',
    badgeStyle: 'text-accent-green border-accent-green/30 bg-accent-green/10',
    role: 'Autonomous Software Engineer (via A2A)',
  },
  tester: {
    framework: 'Google ADK',
    badgeStyle: 'text-accent-yellow border-accent-yellow/30 bg-accent-yellow/10',
    role: 'QA & Sandbox Test Engineer',
  },
  security: {
    framework: 'CrewAI',
    badgeStyle: 'text-accent-red border-accent-red/30 bg-accent-red/10',
    role: 'Security & Vulnerability Sentinel',
  },
  reviewer: {
    framework: 'CrewAI',
    badgeStyle: 'text-accent-blue border-accent-blue/30 bg-accent-blue/10',
    role: 'Code Quality & Standard Reviewer',
  },
  documentation: {
    framework: 'CrewAI',
    badgeStyle: 'text-text-secondary border-bg-border bg-bg-raised',
    role: 'Technical Writer',
  },
};

export default function AgentsTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    agentsApi
      .getRuns(projectId)
      .then(setAgentRuns)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div className="text-text-muted text-sm">Loading agent runs…</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Framework Summary Header */}
      <div className="card p-5 bg-bg-card border border-bg-border">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-accent-blue/10 border border-accent-blue/20">
              <Layers className="w-5 h-5 text-accent-blue" />
            </div>
            <div>
              <h2 className="font-semibold text-text-primary text-base">Multi-Agent Roster</h2>
              <p className="text-xs text-text-secondary">
                Collaborative team orchestrated across CrewAI and Google Agent Development Kit (ADK).
              </p>
            </div>
          </div>
          <a
            href="http://localhost:8000/.well-known/agent.json"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium bg-bg-raised border border-bg-border text-accent-cyan hover:text-white transition-colors"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            A2A Agent Card
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Agent Runs List */}
      <div className="space-y-3">
        {agentRuns.length === 0 ? (
          <div className="card p-8 text-center">
            <Bot className="w-10 h-10 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary">No agent runs recorded yet.</p>
            <p className="text-xs text-text-muted mt-1">Run the project pipeline to start the agents.</p>
          </div>
        ) : (
          agentRuns.map((run, i) => {
            const cleanKey = run.agent.toLowerCase().replace(/[^a-z]/g, '');
            const meta = AGENT_META[cleanKey] ?? (
              cleanKey.includes('adk') || cleanKey.includes('developer')
                ? AGENT_META.developer
                : AGENT_META.requirement
            );
            const StatusIcon =
              run.status === 'completed'
                ? CheckCircle2
                : run.status === 'failed'
                ? AlertCircle
                : Loader2;

            return (
              <motion.div
                key={run.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="card p-4 flex items-start gap-4 hover:border-accent-blue/40 transition-colors"
              >
                <div className="flex items-center justify-center w-9 h-9 rounded-full bg-bg-raised border border-bg-border flex-shrink-0 mt-0.5">
                  <StatusIcon
                    className={`w-4 h-4 ${
                      run.status === 'completed'
                        ? 'text-accent-green'
                        : run.status === 'failed'
                        ? 'text-accent-red'
                        : 'text-accent-blue animate-spin'
                    }`}
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-semibold text-sm text-text-primary">
                      {meta.role}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${meta.badgeStyle}`}>
                      {meta.framework}
                    </span>
                    <span className="badge-gray text-[11px]">iter {run.iteration}</span>
                    <span
                      className={`text-xs font-medium ml-auto ${
                        run.status === 'completed'
                          ? 'text-accent-green'
                          : run.status === 'failed'
                          ? 'text-accent-red'
                          : 'text-accent-blue'
                      }`}
                    >
                      {run.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-xs text-text-secondary leading-relaxed">{run.objective}</p>

                  {run.duration_ms && (
                    <div className="flex items-center gap-1 mt-2 text-[11px] text-text-muted">
                      <Clock className="w-3 h-3" />
                      <span>Execution Time: {(run.duration_ms / 1000).toFixed(2)}s</span>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
