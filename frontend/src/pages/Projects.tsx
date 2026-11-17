import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FolderOpen, Search, Filter, Plus, Activity } from 'lucide-react';
import { projects as projectsApi, type Project } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

export default function Projects() {
  const [projectList, setProjectList] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all'); // all, active, completed, failed

  useEffect(() => {
    projectsApi.list().then(setProjectList).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = projectList.filter((p) => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                       (p.description || '').toLowerCase().includes(search.toLowerCase());
    if (!matchSearch) return false;
    
    if (filter === 'all') return true;
    if (filter === 'completed') return p.status === 'COMPLETED';
    if (filter === 'failed') return p.status === 'FAILED';
    if (filter === 'active') return !['COMPLETED', 'FAILED', 'CREATED', 'PAUSED'].includes(p.status);
    return true;
  });

  return (
    <div className="min-h-screen bg-bg-base p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
              <FolderOpen className="w-6 h-6 text-accent-blue" />
              All Projects
            </h1>
            <p className="text-text-secondary mt-1">Manage and view all your generated applications.</p>
          </div>
          <Link to="/dashboard" className="btn-primary">
            <Plus className="w-4 h-4" /> New Project
          </Link>
        </div>

        {/* Filters */}
        <div className="card p-4 mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-text-muted" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input w-40 cursor-pointer"
            >
              <option value="all">All Projects</option>
              <option value="active">Active Runs</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* List */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-text-muted">
            <Activity className="w-8 h-8 animate-spin mb-4" />
            <p>Loading projects...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="card p-12 text-center">
            <FolderOpen className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-text-primary">No projects found</h3>
            <p className="text-text-secondary mt-1">Try adjusting your search or filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Link to={`/projects/${p.id}`} className="block h-full">
                  <div className="card p-5 h-full flex flex-col hover:border-accent-blue/40 transition-colors group">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-text-primary group-hover:text-accent-blue transition-colors truncate pr-4">
                        {p.name}
                      </h3>
                      <StatusBadge status={p.status} />
                    </div>
                    <p className="text-sm text-text-secondary line-clamp-2 mb-4 flex-1">
                      {p.description || 'No description provided.'}
                    </p>
                    <div className="flex items-center justify-between text-xs text-text-muted border-t border-bg-border pt-3">
                      <span>Iter: {p.iteration_count}</span>
                      <span>${p.estimated_cost_usd.toFixed(4)}</span>
                      <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
