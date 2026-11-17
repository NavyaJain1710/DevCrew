import { useState, useEffect, useCallback } from 'react';
import { Outlet, useParams, useNavigate, NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, ChevronLeft, Play, X, Download,
  CheckCircle2, Shield, FileCode2, FlaskConical,
  BookOpen, Activity, BarChart3, List, Cpu, RefreshCw,
  Loader2, AlertCircle, Database
} from 'lucide-react';
import { projects as projectsApi, type Project } from '../../api/client';
import { useWebSocket, type WSEvent } from '../../hooks/useWebSocket';
import { StatusBadge } from '../../components/StatusBadge';
import HumanApprovalModal from '../../components/HumanApprovalModal';

const TABS = [
  { path: '', label: 'Overview',      icon: BarChart3 },
  { path: 'requirements', label: 'Requirements', icon: List },
  { path: 'architecture', label: 'Architecture', icon: Cpu },
  { path: 'agents',       label: 'Agents',       icon: Bot },
  { path: 'documents',    label: 'Documents & RAG', icon: Database },
  { path: 'files',        label: 'Files',        icon: FileCode2 },
  { path: 'tests',        label: 'Tests',        icon: FlaskConical },
  { path: 'security',     label: 'Security',     icon: Shield },
  { path: 'review',       label: 'Review',       icon: CheckCircle2 },
  { path: 'activity',     label: 'Activity',     icon: Activity },
  { path: 'reports',      label: 'Reports',      icon: BookOpen },
];

export default function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [wsEvents, setWsEvents] = useState<WSEvent[]>([]);
  const [approvalRequest, setApprovalRequest] = useState<{ id: string; action: string; description: string } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchProject = useCallback(() => {
    if (!projectId) return;
    projectsApi.get(projectId).then(setProject).catch(console.error);
  }, [projectId]);

  useEffect(() => { fetchProject(); }, [fetchProject]);

  // Poll project status when active
  useEffect(() => {
    if (!project) return;
    const ACTIVE = ['ANALYZING','ARCHITECTING','IMPLEMENTING','TESTING','FIXING','SECURITY_SCANNING','REVIEWING','DOCUMENTING'];
    if (!ACTIVE.includes(project.status)) return;
    const interval = setInterval(fetchProject, 5000);
    return () => clearInterval(interval);
  }, [project, fetchProject]);

  // If page loaded with a pending approval, show the modal
  useEffect(() => {
    if (project?.pending_approval && !approvalRequest) {
      setApprovalRequest({
        id: project.pending_approval.id,
        action: project.pending_approval.action,
        description: project.pending_approval.description,
      });
    }
  }, [project?.pending_approval]);

  // WebSocket for live updates
  const handleWsMessage = useCallback((event: WSEvent) => {
    setWsEvents(prev => [event, ...prev].slice(0, 200));
    if (event.event === 'human_approval_required') {
      setApprovalRequest({
        id: (event.data.approval_id as string) ?? '',
        action: (event.data.type as string) ?? 'Action',
        description: JSON.stringify(event.data.questions ?? event.data),
      });
    }
    if (['project_completed','error'].includes(event.event)) {
      fetchProject();
    }
  }, [fetchProject]);

  useWebSocket(projectId ?? null, handleWsMessage);

  async function handleRun() {
    if (!projectId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await projectsApi.run(projectId);
      fetchProject();
    } catch (err: unknown) {
      setActionError((err as Error).message ?? 'Failed to start pipeline');
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCancel() {
    if (!projectId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await projectsApi.cancel(projectId);
      fetchProject();
    } catch (err: unknown) {
      setActionError((err as Error).message ?? 'Failed to cancel pipeline');
    } finally {
      setActionLoading(false);
    }
  }

  const isActive = project && ['ANALYZING','ARCHITECTING','IMPLEMENTING','TESTING','FIXING','SECURITY_SCANNING','REVIEWING','DOCUMENTING'].includes(project.status);
  const canRun = project && ['CREATED','FAILED','PAUSED','WAITING_FOR_APPROVAL'].includes(project.status);

  return (
    <div className="min-h-screen bg-bg-base flex flex-col">
      {/* Top bar */}
      <header className="border-b border-bg-border glass-panel sticky top-0 z-40">
        <div className="px-6 py-3 flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost p-2">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 min-w-0">
            <Bot className="w-5 h-5 text-accent-blue flex-shrink-0" />
            <h1 className="font-semibold text-text-primary truncate">
              {project?.name ?? 'Loading…'}
            </h1>
            {project && <StatusBadge status={project.status} />}
          </div>
          <div className="ml-auto flex items-center gap-2">
            {project && (
              <span className="text-xs text-text-muted hidden md:block">
                Iter: {project.iteration_count} · ${(project.estimated_cost_usd || 0).toFixed(4)}
              </span>
            )}
            <button onClick={fetchProject} className="btn-ghost p-2" title="Refresh">
              <RefreshCw className="w-4 h-4" />
            </button>
            {canRun && (
              <button
                onClick={handleRun}
                className="btn-primary text-xs"
                id="run-pipeline-btn"
                disabled={actionLoading}
              >
                {actionLoading
                  ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  : <Play className="w-3.5 h-3.5" />}
                {actionLoading ? 'Starting…' : 'Run Pipeline'}
              </button>
            )}
            {isActive && (
              <button
                onClick={handleCancel}
                className="btn-danger text-xs"
                id="cancel-pipeline-btn"
                disabled={actionLoading}
              >
                {actionLoading
                  ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  : <X className="w-3.5 h-3.5" />}
                Cancel
              </button>
            )}
            {project?.status === 'COMPLETED' && (
              <button
                onClick={async () => {
                  try {
                    const { reports } = await import('../../api/client');
                    await reports.download(projectId!);
                  } catch (err: unknown) {
                    setActionError((err as Error).message ?? 'Download failed');
                  }
                }}
                className="btn-success text-xs"
              >
                <Download className="w-3.5 h-3.5" /> Download
              </button>
            )}
          </div>
        </div>

        {/* Error banner */}
        {actionError && (
          <div className="px-6 py-2 bg-accent-red/10 border-t border-accent-red/20 flex items-center gap-2 text-accent-red text-xs">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="flex-1">{actionError}</span>
            <button onClick={() => setActionError(null)} className="hover:opacity-70">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Progress bar for active status */}
        {isActive && (
          <div className="h-0.5 bg-bg-border">
            <div className="h-full progress-shimmer w-full" />
          </div>
        )}

        {/* Tab navigation */}
        <div className="px-6 flex gap-1 overflow-x-auto pb-px">
          {TABS.map(({ path, label, icon: Icon }) => {
            const to = `/projects/${projectId}${path ? `/${path}` : ''}`;
            return (
              <NavLink
                key={path}
                to={to}
                end={path === ''}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                    isActive
                      ? 'border-accent-blue text-accent-blue'
                      : 'border-transparent text-text-secondary hover:text-text-primary'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </NavLink>
            );
          })}
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Outlet context={{ project, wsEvents, refreshProject: fetchProject }} />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Human approval modal */}
      {approvalRequest && (
        <HumanApprovalModal
          request={approvalRequest}
          projectId={projectId!}
          onClose={() => setApprovalRequest(null)}
        />
      )}
    </div>
  );
}
