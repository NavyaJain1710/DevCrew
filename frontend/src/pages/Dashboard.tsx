import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bot, Plus, FolderOpen, Activity, DollarSign, CheckCircle2,
  XCircle, Clock, LogOut
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { projects as projectsApi, type Project } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

export default function Dashboard() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [projectList, setProjectList] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewProject, setShowNewProject] = useState(false);

  useEffect(() => {
    projectsApi.list().then(setProjectList).catch(console.error).finally(() => setLoading(false));
  }, []);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const total = projectList.length;
  const completed = projectList.filter(p => p.status === 'COMPLETED').length;
  const active = projectList.filter(p => ['ANALYZING','IMPLEMENTING','TESTING','REVIEWING','SECURITY_SCANNING'].includes(p.status)).length;
  const failed = projectList.filter(p => p.status === 'FAILED').length;
  const totalCost = projectList.reduce((s, p) => s + p.estimated_cost_usd, 0);

  const statusData = [
    { name: 'Completed', value: completed, color: '#3fb950' },
    { name: 'Active', value: active, color: '#58a6ff' },
    { name: 'Failed', value: failed, color: '#f85149' },
    { name: 'Other', value: Math.max(0, total - completed - active - failed), color: '#6e7681' },
  ].filter(d => d.value > 0);

  return (
    <div className="min-h-screen bg-bg-base">
      {/* Header */}
      <header className="border-b border-bg-border sticky top-0 z-50 glass-panel">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center">
              <Bot className="w-5 h-5 text-accent-blue" />
            </div>
            <span className="font-bold text-text-primary text-lg">DevCrew</span>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            <Link to="/dashboard" className="nav-item-active">Dashboard</Link>
            <Link to="/projects" className="nav-item">Projects</Link>
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-text-secondary text-sm hidden md:block">{user?.full_name}</span>
            {user?.role === 'ADMIN' && (
              <span className="badge-purple">Admin</span>
            )}
            <button onClick={handleLogout} className="btn-ghost" title="Sign out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-2xl font-bold text-text-primary">
            Welcome back, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-text-secondary mt-1">
            Your AI development team is ready. What are we building today?
          </p>
        </motion.div>

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Projects', value: total, icon: FolderOpen, color: 'text-accent-blue' },
            { label: 'Completed', value: completed, icon: CheckCircle2, color: 'text-accent-green' },
            { label: 'Active Runs', value: active, icon: Activity, color: 'text-accent-yellow' },
            { label: 'Est. Total Cost', value: `$${totalCost.toFixed(4)}`, icon: DollarSign, color: 'text-accent-purple' },
          ].map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="metric-card"
            >
              <div className={`${m.color} mb-2`}>
                <m.icon className="w-5 h-5" />
              </div>
              <div className="text-2xl font-bold text-text-primary">{m.value}</div>
              <div className="text-xs text-text-muted">{m.label}</div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Projects list */}
          <div className="lg:col-span-2 card p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-text-primary">Recent Projects</h2>
              <button
                onClick={() => setShowNewProject(true)}
                className="btn-primary text-xs"
                id="new-project-btn"
              >
                <Plus className="w-3.5 h-3.5" />
                New Project
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12 text-text-muted">
                <Activity className="w-5 h-5 animate-spin mr-2" />
                Loading…
              </div>
            ) : projectList.length === 0 ? (
              <EmptyState onNew={() => setShowNewProject(true)} />
            ) : (
              <div className="space-y-3">
                {projectList.slice(0, 8).map((p) => (
                  <Link
                    key={p.id}
                    to={`/projects/${p.id}`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-raised transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-bg-raised border border-bg-border flex items-center justify-center flex-shrink-0 group-hover:border-accent-blue/40 transition-colors">
                        <Bot className="w-4 h-4 text-text-muted group-hover:text-accent-blue transition-colors" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-medium text-text-primary text-sm truncate">{p.name}</div>
                        <div className="text-xs text-text-muted truncate">{p.description || 'No description'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0 ml-3">
                      <StatusBadge status={p.status} />
                      <span className="text-xs text-text-muted hidden md:block">
                        {new Date(p.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </Link>
                ))}
                {projectList.length > 8 && (
                  <Link to="/projects" className="text-sm text-accent-blue hover:underline block text-center pt-2">
                    View all {projectList.length} projects →
                  </Link>
                )}
              </div>
            )}
          </div>

          {/* Sidebar stats */}
          <div className="space-y-4">
            {/* Status chart */}
            {statusData.length > 0 && (
              <div className="card p-5">
                <h3 className="font-medium text-text-primary text-sm mb-4">Project Status</h3>
                <ResponsiveContainer width="100%" height={120}>
                  <BarChart data={statusData} margin={{ left: -20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8b949e' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} />
                    <Tooltip
                      contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8 }}
                      labelStyle={{ color: '#e6edf3' }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {statusData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Quick actions */}
            <div className="card p-5">
              <h3 className="font-medium text-text-primary text-sm mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button onClick={() => setShowNewProject(true)}
                  className="w-full text-left flex items-center gap-2 p-2.5 rounded-lg hover:bg-bg-raised text-sm text-text-secondary hover:text-text-primary transition-colors">
                  <Plus className="w-4 h-4 text-accent-blue" />
                  New Project
                </button>
                <Link to="/projects" className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-bg-raised text-sm text-text-secondary hover:text-text-primary transition-colors">
                  <FolderOpen className="w-4 h-4 text-accent-purple" />
                  All Projects
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* New Project Modal */}
      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onCreate={(p) => {
            setProjectList(prev => [p, ...prev]);
            setShowNewProject(false);
            navigate(`/projects/${p.id}`);
          }}
        />
      )}
    </div>
  );
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="text-center py-12">
      <Bot className="w-12 h-12 text-text-muted mx-auto mb-3" />
      <p className="text-text-secondary font-medium">No projects yet</p>
      <p className="text-text-muted text-sm mt-1">Start by describing what you want to build.</p>
      <button onClick={onNew} className="btn-primary mt-4" id="empty-new-project">
        <Plus className="w-4 h-4" /> Create first project
      </button>
    </div>
  );
}

function NewProjectModal({ onClose, onCreate }: { onClose: () => void; onCreate: (p: Project) => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [requirement, setRequirement] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const p = await projectsApi.create({ name, description, raw_requirement: requirement });
      onCreate(p);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-bg-base/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass w-full max-w-lg p-8"
      >
        <h2 className="text-lg font-semibold text-text-primary mb-1">New Project</h2>
        <p className="text-text-secondary text-sm mb-6">Describe what you want DevCrew to build.</p>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-sm mb-4">
            <XCircle className="w-4 h-4 flex-shrink-0" /> {error}
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="label">Project name</label>
            <input className="input" placeholder="Task Manager App" value={name}
              onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Description (optional)</label>
            <input className="input" placeholder="Brief one-line description"
              value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">What should DevCrew build? <span className="text-accent-red">*</span></label>
            <textarea
              className="input resize-none"
              rows={5}
              placeholder="Build a task management application with authentication, projects, tasks with priorities and deadlines, and an admin dashboard."
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              required
            />
            <p className="text-xs text-text-muted mt-1">Be as detailed as possible. The more context, the better the output.</p>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" id="create-project-submit" className="btn-primary flex-1 justify-center" disabled={loading}>
              {loading ? <><Clock className="w-4 h-4 animate-spin" /> Creating…</> : '🚀 Build with DevCrew'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}


