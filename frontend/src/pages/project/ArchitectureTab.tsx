import { useOutletContext } from 'react-router-dom';
import {
  Cpu, Database, Globe, Layers, Shield, FolderTree,
  Server, ArrowRight, Code2
} from 'lucide-react';
import type { Project } from '../../api/client';

interface Context { project: Project | null; }

export default function ArchitectureTab() {
  const { project } = useOutletContext<Context>();
  const arch = (project as unknown as { architecture?: Record<string, unknown> })?.architecture ?? {};

  if (!arch || Object.keys(arch).length === 0) {
    return (
      <div className="card p-8 text-center max-w-md mx-auto my-12">
        <Cpu className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-text-primary mb-1">Architecture Not Generated Yet</h3>
        <p className="text-text-secondary text-xs">Run the autonomous development pipeline to generate technical architecture.</p>
      </div>
    );
  }

  const rawDecisions = (arch.technology_decisions as Array<{ technology: string; purpose: string; reason: string }>) || [];
  const rawTechStack = (arch.tech_stack as string[]) || [];
  
  // Normalize technology decisions
  const techDecisions = rawDecisions.length > 0 
    ? rawDecisions 
    : rawTechStack.map(t => ({
        technology: t,
        purpose: 'Core Application Component',
        reason: 'Selected for performance, modern standards, and asynchronous reliability.'
      }));

  const rawEndpoints = (arch.api_endpoints as Array<{ method: string; path: string; summary?: string; auth_required?: boolean }>) || [];
  const rawTables = (arch.database_tables as Array<{ name: string; purpose?: string; columns?: Array<{ name: string; type: string }> }>) 
    || (arch.database_models as Array<{ name: string; purpose?: string; columns?: Array<{ name: string; type: string }> }>) 
    || [];

  const folderStructure = (arch.folder_structure as string) || (arch.backend_structure as string) || '';
  const overviewText = (arch.architecture_overview as string) || 'Layered asynchronous service architecture with decoupled routing, domain modeling, and test isolation.';
  const securityArch = (arch.security_architecture as string) || 'Enforces JWT bearer authentication, Pydantic type validation on all request bodies, CORS domain restrictions, and isolated workspace filesystem containment.';

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title & Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 card">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-accent-blue/10 text-accent-blue">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-text-primary">System Architecture & Design</h2>
            <p className="text-xs text-text-secondary">
              Multi-tiered service layout synthesized by CrewAI Architect & Google ADK
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-xs font-mono font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            FastAPI + Pydantic v2
          </span>
        </div>
      </div>

      {/* Visual System Architecture Diagram */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-primary flex items-center gap-2">
            <Layers className="w-4 h-4 text-accent-blue" />
            Interactive System Flow Diagram
          </h3>
          <span className="text-[11px] text-text-muted">Data Flow Pipeline</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-center py-2">
          {/* Tier 1: Client */}
          <div className="p-3.5 bg-bg-raised border border-bg-border rounded-xl text-center space-y-1">
            <Globe className="w-5 h-5 text-accent-blue mx-auto" />
            <div className="text-xs font-semibold text-text-primary">Client Layer</div>
            <div className="text-[10px] text-text-muted">Web / Mobile / REST API</div>
          </div>

          <div className="hidden md:flex justify-center text-text-muted">
            <ArrowRight className="w-4 h-4" />
          </div>

          {/* Tier 2: Gateway */}
          <div className="p-3.5 bg-bg-raised border border-accent-blue/30 rounded-xl text-center space-y-1">
            <Server className="w-5 h-5 text-emerald-400 mx-auto" />
            <div className="text-xs font-semibold text-text-primary">FastAPI Gateway</div>
            <div className="text-[10px] text-text-muted">CORS · JWT · OpenAPI</div>
          </div>

          <div className="hidden md:flex justify-center text-text-muted">
            <ArrowRight className="w-4 h-4" />
          </div>

          {/* Tier 3: Business Logic & Models */}
          <div className="p-3.5 bg-bg-raised border border-bg-border rounded-xl text-center space-y-1">
            <Code2 className="w-5 h-5 text-accent-purple mx-auto" />
            <div className="text-xs font-semibold text-text-primary">Domain Routers</div>
            <div className="text-[10px] text-text-muted">Pydantic DTOs & Logic</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
          <div className="p-3 bg-bg-raised/60 border border-bg-border rounded-lg flex items-center gap-3">
            <Database className="w-4 h-4 text-accent-purple flex-shrink-0" />
            <div className="text-xs">
              <span className="font-semibold text-text-primary">Persistence Tier: </span>
              <span className="text-text-secondary">Relational DB / SQLite storage with parameterized ORM access</span>
            </div>
          </div>

          <div className="p-3 bg-bg-raised/60 border border-bg-border rounded-lg flex items-center gap-3">
            <Shield className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <div className="text-xs">
              <span className="font-semibold text-text-primary">Verification Tier: </span>
              <span className="text-text-secondary">Automated Pytest runner in isolated sandbox workspace</span>
            </div>
          </div>
        </div>
      </div>

      {/* Overview Card */}
      <div className="card p-5 space-y-2">
        <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
          Architecture Overview
        </h3>
        <p className="text-text-secondary text-xs sm:text-sm leading-relaxed">
          {overviewText}
        </p>
      </div>

      {/* Technology Decisions / Stack */}
      {techDecisions.length > 0 && (
        <div className="card p-5 space-y-4">
          <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-accent-blue" />
            Technology Stack & Architecture Choices ({techDecisions.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {techDecisions.map((td, i) => (
              <div key={i} className="p-3.5 bg-bg-raised rounded-xl border border-bg-border space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-text-primary">{td.technology}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-blue/10 text-accent-blue">
                    {td.purpose}
                  </span>
                </div>
                <p className="text-[11px] text-text-secondary leading-normal">{td.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Endpoints & Database Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Endpoints */}
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Globe className="w-4 h-4 text-accent-green" />
              API Endpoints ({rawEndpoints.length})
            </h3>
            <span className="text-[10px] text-text-muted">REST Interface</span>
          </div>

          {rawEndpoints.length === 0 ? (
            <div className="text-xs text-text-muted py-6 text-center border border-dashed border-bg-border rounded-lg">
              No custom endpoints exposed.
            </div>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {rawEndpoints.map((ep, i) => (
                <div key={i} className="p-2.5 bg-bg-raised border border-bg-border rounded-lg flex items-center gap-2 text-xs">
                  <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                    ep.method === 'GET' ? 'bg-emerald-500/10 text-emerald-400' :
                    ep.method === 'POST' ? 'bg-accent-blue/10 text-accent-blue' :
                    ep.method === 'PUT' || ep.method === 'PATCH' ? 'bg-yellow-500/10 text-yellow-400' :
                    'bg-red-500/10 text-red-400'
                  }`}>
                    {ep.method}
                  </span>
                  <span className="font-mono text-text-primary flex-1 truncate">{ep.path}</span>
                  {ep.auth_required && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-base text-text-muted flex items-center gap-1 font-mono">
                      🔒 Auth
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Database Models & Tables */}
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-accent-purple" />
              Domain Data Models ({rawTables.length})
            </h3>
            <span className="text-[10px] text-text-muted">Schemas</span>
          </div>

          {rawTables.length === 0 ? (
            <div className="text-xs text-text-muted py-6 text-center border border-dashed border-bg-border rounded-lg">
              No domain models specified.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {rawTables.map((table, i) => (
                <div key={i} className="p-3 bg-bg-raised border border-bg-border rounded-lg space-y-1.5 text-xs">
                  <div className="font-mono font-medium text-text-primary flex items-center justify-between">
                    <span>{table.name}</span>
                    <span className="text-[10px] text-text-muted font-normal">{table.purpose}</span>
                  </div>
                  {table.columns && table.columns.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {table.columns.slice(0, 6).map((col, j) => (
                        <span key={j} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-bg-base border border-bg-border text-text-secondary">
                          {col.name}: {col.type}
                        </span>
                      ))}
                      {table.columns.length > 6 && (
                        <span className="text-[10px] text-text-muted px-1">+{table.columns.length - 6} more</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Real Folder Structure Tree */}
      {folderStructure && (
        <div className="card p-5 space-y-3">
          <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <FolderTree className="w-4 h-4 text-accent-blue" />
            Project Directory Tree
          </h3>
          <pre className="text-xs font-mono text-text-secondary bg-bg-base p-4 rounded-xl border border-bg-border overflow-x-auto whitespace-pre max-h-64 overflow-y-auto">
            {folderStructure}
          </pre>
        </div>
      )}

      {/* Security Architecture */}
      <div className="card p-5 space-y-2 border-l-2 border-l-emerald-500">
        <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          Security Architecture & Protections
        </h3>
        <p className="text-text-secondary text-xs sm:text-sm leading-relaxed">
          {securityArch}
        </p>
      </div>
    </div>
  );
}
