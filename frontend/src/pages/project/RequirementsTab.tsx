import { useOutletContext } from 'react-router-dom';
import { CheckCircle2, List } from 'lucide-react';
import type { Project } from '../../api/client';

interface Context { project: Project | null; }

export default function RequirementsTab() {
  const { project } = useOutletContext<Context>();
  const reqs = (project as unknown as { requirements?: Record<string, unknown> })?.requirements ?? {};

  if (!reqs || Object.keys(reqs).length === 0) {
    return (
      <div className="card p-8 text-center max-w-md">
        <List className="w-10 h-10 text-text-muted mx-auto mb-3" />
        <p className="text-text-secondary">Requirements not yet analyzed. Run the pipeline.</p>
      </div>
    );
  }

  const r = reqs as {
    project_name?: string;
    problem_statement?: string;
    functional_requirements?: string[];
    non_functional_requirements?: string[];
    user_roles?: string[];
    acceptance_criteria?: string[];
    constraints?: string[];
    assumptions?: string[];
    estimated_complexity?: string;
    suggested_tech_stack?: string[];
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-2">
        <List className="w-5 h-5 text-accent-blue" />
        <h2 className="font-semibold text-text-primary">Requirements</h2>
        {r.estimated_complexity && <span className="badge-purple">{r.estimated_complexity}</span>}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-text-primary mb-1">{r.project_name ?? 'Project'}</h3>
        <p className="text-text-secondary text-sm leading-relaxed">{r.problem_statement}</p>
        {r.user_roles && r.user_roles.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {r.user_roles.map(role => <span key={role} className="badge-blue">{role}</span>)}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {r.functional_requirements && r.functional_requirements.length > 0 && (
          <Section title="Functional Requirements" items={r.functional_requirements} color="accent-green" />
        )}
        {r.non_functional_requirements && r.non_functional_requirements.length > 0 && (
          <Section title="Non-Functional Requirements" items={r.non_functional_requirements} color="accent-blue" />
        )}
        {r.acceptance_criteria && r.acceptance_criteria.length > 0 && (
          <Section title="Acceptance Criteria" items={r.acceptance_criteria} color="accent-yellow" />
        )}
        {r.constraints && r.constraints.length > 0 && (
          <Section title="Constraints" items={r.constraints} color="accent-red" />
        )}
        {r.assumptions && r.assumptions.length > 0 && (
          <Section title="Assumptions" items={r.assumptions} color="text-muted" />
        )}
        {r.suggested_tech_stack && r.suggested_tech_stack.length > 0 && (
          <div className="card p-5">
            <h4 className="text-sm font-medium text-text-primary mb-3">Suggested Tech Stack</h4>
            <div className="flex flex-wrap gap-2">
              {r.suggested_tech_stack.map(tech => <span key={tech} className="badge-purple">{tech}</span>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div className="card p-5">
      <h4 className="text-sm font-medium text-text-primary mb-3">{title}</h4>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
            <CheckCircle2 className={`w-3.5 h-3.5 text-${color} flex-shrink-0 mt-0.5`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
