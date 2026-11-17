import { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bot, CheckCircle2, Clock, DollarSign, Repeat2, BarChart3,
  Cpu, ArrowRightLeft, Sparkles, Layers, FileCode2, Download
} from 'lucide-react';
import type { Project } from '../../api/client';
import { StatusBadge } from '../../components/StatusBadge';
import type { WSEvent } from '../../hooks/useWebSocket';

interface Context {
  project: Project | null;
  wsEvents: WSEvent[];
}

const PIPELINE_STAGES = [
  { key: 'manager',       label: 'Manager & Planning',     framework: 'CrewAI',       badgeColor: 'bg-accent-blue/10 text-accent-blue border-accent-blue/30' },
  { key: 'requirement',   label: 'Requirement Analysis',   framework: 'CrewAI',       badgeColor: 'bg-accent-purple/10 text-accent-purple border-accent-purple/30' },
  { key: 'architect',     label: 'System Architecture',    framework: 'CrewAI',       badgeColor: 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30' },
  { key: 'a2a_bridge',    label: 'A2A Protocol Handshake', framework: 'A2A Protocol', badgeColor: 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/30' },
  { key: 'developer',     label: 'Code Implementation',    framework: 'Google ADK',   badgeColor: 'bg-accent-green/10 text-accent-green border-accent-green/30' },
  { key: 'tester',        label: 'Sandbox Testing (Pytest)', framework: 'Google ADK', badgeColor: 'bg-accent-green/10 text-accent-green border-accent-green/30' },
  { key: 'security',      label: 'Security & Vulnerability', framework: 'CrewAI',     badgeColor: 'bg-accent-red/10 text-accent-red border-accent-red/30' },
  { key: 'reviewer',      label: 'Quality & Code Review',   framework: 'CrewAI',      badgeColor: 'bg-accent-blue/10 text-accent-blue border-accent-blue/30' },
];

const STATUS_TO_STAGE_INDEX: Record<string, number> = {
  CREATED: -1,
  ANALYZING: 1,
  ARCHITECTING: 2,
  IMPLEMENTING: 4,
  TESTING: 5,
  FIXING: 4,
  SECURITY_SCANNING: 6,
  REVIEWING: 7,
  DOCUMENTING: 7,
  COMPLETED: 8,
  FAILED: -1,
};

export default function Overview() {
  const navigate = useNavigate();
  const { project, wsEvents } = useOutletContext<Context>();
  const [selectedMode, setSelectedMode] = useState<'a2a_hybrid' | 'breakdown'>('a2a_hybrid');

  if (!project) return <div className="text-text-muted text-sm">Loading…</div>;

  const currentStageIndex = STATUS_TO_STAGE_INDEX[project.status] ?? -1;
  const isComplete = project.status === 'COMPLETED';
  const isFailed = project.status === 'FAILED';
  const recentEvents = wsEvents.slice(0, 10);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Framework Execution Architecture Mode Banner */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-5 border-l-4 border-l-accent-cyan bg-gradient-to-r from-bg-card to-bg-raised"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-accent-cyan" />
              <span className="text-xs font-semibold uppercase tracking-wider text-accent-cyan">
                Agentic Architecture Mode
              </span>
              <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                CrewAI + Google ADK via A2A
              </span>
            </div>
            <h2 className="text-base font-semibold text-text-primary">
              Multi-Agent Autonomous Pipeline (No LangGraph)
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              CrewAI coordinates requirements & architecture; delegates code synthesis via official A2A protocol to Google ADK; executes MCP tools.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={() => setSelectedMode('a2a_hybrid')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedMode === 'a2a_hybrid'
                  ? 'bg-accent-blue text-white shadow-sm'
                  : 'bg-bg-raised text-text-muted hover:text-text-primary'
              }`}
            >
              Hybrid Workflow
            </button>
            <button
              onClick={() => setSelectedMode('breakdown')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedMode === 'breakdown'
                  ? 'bg-accent-blue text-white shadow-sm'
                  : 'bg-bg-raised text-text-muted hover:text-text-primary'
              }`}
            >
              Framework Mapping
            </button>
          </div>
        </div>

        {selectedMode === 'breakdown' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 pt-3 border-t border-bg-border grid grid-cols-1 md:grid-cols-3 gap-3 text-xs"
          >
            <div className="p-2.5 rounded-lg bg-bg-base border border-bg-border">
              <span className="font-semibold text-accent-purple flex items-center gap-1.5 mb-1">
                <Bot className="w-3.5 h-3.5" /> CrewAI Core
              </span>
              <p className="text-text-muted">
                Drives Requirement Analysis, System Architecture, Engineering Task Planning, and Security Sentinel.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-bg-base border border-bg-border">
              <span className="font-semibold text-accent-yellow flex items-center gap-1.5 mb-1">
                <ArrowRightLeft className="w-3.5 h-3.5" /> A2A Protocol
              </span>
              <p className="text-text-muted">
                Official Agent-to-Agent standard with Agent Card at <code>/.well-known/agent.json</code> and validated payloads.
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-bg-base border border-bg-border">
              <span className="font-semibold text-accent-green flex items-center gap-1.5 mb-1">
                <Cpu className="w-3.5 h-3.5" /> Google ADK
              </span>
              <p className="text-text-muted">
                Implements production code, executes FastMCP workspace tools, and runs pytest sandbox validation.
              </p>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Project details card */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">{project.name}</h2>
            <p className="text-text-secondary text-sm mt-1">{project.description || 'No description provided'}</p>
          </div>
          <StatusBadge status={project.status} />
        </div>
        {project.raw_requirement && (
          <div className="mt-4 p-3 bg-bg-raised rounded-lg border border-bg-border">
            <p className="text-xs font-medium text-text-muted mb-1">Input Requirement</p>
            <p className="text-sm text-text-secondary leading-relaxed">{project.raw_requirement}</p>
          </div>
        )}
        {project.error_message && (
          <div className="mt-3 p-3 bg-accent-red/5 border border-accent-red/20 rounded-lg">
            <p className="text-xs text-accent-red">{project.error_message}</p>
          </div>
        )}
      </motion.div>

      {/* Generated Code & Deliverables Banner */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card p-5 border border-accent-green/30 bg-accent-green/5 space-y-3"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-accent-green/10 text-accent-green">
                <FileCode2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-text-primary text-sm">
                  Generated Source Code & Project Workspace Ready
                </h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  Full codebase, automated tests, requirements, and configuration are synthesized and stored in workspace.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                onClick={() => navigate(`/projects/${project.id}/files`)}
                className="btn-ghost text-xs border border-bg-border hover:bg-bg-raised text-text-primary flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              >
                <FileCode2 className="w-3.5 h-3.5 text-accent-blue" />
                <span>Browse Code</span>
              </button>
              <button
                onClick={async () => {
                  try {
                    const { reports } = await import('../../api/client');
                    await reports.download(project.id, 'zip');
                  } catch (e) {
                    console.error(e);
                  }
                }}
                className="btn-success text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg shadow-sm font-medium"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download ZIP</span>
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Iterations', value: project.iteration_count || 1, icon: Repeat2, color: 'text-accent-blue' },
          { label: 'Prompt Tokens', value: (project.total_prompt_tokens || 0).toLocaleString(), icon: BarChart3, color: 'text-accent-purple' },
          { label: 'Est. LLM Cost', value: `$${(project.estimated_cost_usd || 0).toFixed(4)}`, icon: DollarSign, color: 'text-accent-green' },
          { label: 'Status', value: project.status, icon: CheckCircle2, color: isComplete ? 'text-accent-green' : isFailed ? 'text-accent-red' : 'text-accent-yellow' },
        ].map((m) => (
          <div key={m.label} className="metric-card p-4 bg-bg-card rounded-xl border border-bg-border">
            <m.icon className={`w-4 h-4 ${m.color} mb-1`} />
            <div className="text-xl font-bold text-text-primary">{m.value}</div>
            <div className="text-xs text-text-muted">{m.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent pipeline with framework tags */}
        <div className="card p-6">
          <h3 className="font-medium text-text-primary mb-4 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent-blue" />
              Multi-Framework Pipeline
            </span>
            <span className="text-xs text-text-muted">CrewAI + Google ADK</span>
          </h3>
          <div className="space-y-3">
            {PIPELINE_STAGES.map((stage, idx) => {
              const isDone = isComplete || (currentStageIndex > idx);
              const isCurrent = currentStageIndex === idx && !isComplete;

              return (
                <div key={stage.key} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-bg-raised/40">
                  <div className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      isDone ? 'border-accent-green bg-accent-green/10' :
                      isCurrent ? 'border-accent-blue bg-accent-blue/10 animate-pulse' :
                      'border-bg-border bg-bg-raised'
                    }`}>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-accent-green" />
                      ) : isCurrent ? (
                        <div className="w-2 h-2 rounded-full bg-accent-blue animate-ping" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-bg-border" />
                      )}
                    </div>
                    <div>
                      <span className={`text-sm font-medium ${
                        isCurrent ? 'text-accent-blue font-semibold' : isDone ? 'text-text-primary' : 'text-text-muted'
                      }`}>
                        {stage.label}
                      </span>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${stage.badgeColor}`}>
                    {stage.framework}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Event Stream */}
        <div className="card p-6">
          <h3 className="font-medium text-text-primary mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-accent-blue" />
            Live Execution Stream
          </h3>
          {recentEvents.length === 0 ? (
            <p className="text-text-muted text-sm">No live events yet. Click &quot;Run Pipeline&quot; to begin.</p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {recentEvents.map((ev, i) => (
                <div key={i} className="flex items-start gap-2 text-xs p-2 rounded bg-bg-raised border border-bg-border/60">
                  <span className="text-text-muted font-mono whitespace-nowrap pt-0.5 text-[10px]">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`font-semibold ${
                    ev.event.includes('completed') ? 'text-accent-green' :
                    ev.event.includes('error') || ev.event.includes('fail') ? 'text-accent-red' :
                    'text-accent-blue'
                  }`}>
                    {ev.event}
                  </span>
                  <span className="text-text-muted truncate ml-auto">
                    {(ev.data as { stage?: string; current_framework?: string }).current_framework ?? ''}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
