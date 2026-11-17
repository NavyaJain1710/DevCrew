/**
 * DevCrew Typed API Client
 * All backend communication goes through this module.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

// ── Token management ────────────────────────────────────────────────────────

// Guard: only redirect to /login once even if many requests 401 simultaneously
let _redirectingToLogin = false;

export function getToken(): string | null {
  return localStorage.getItem('devcrew_token');
}

export function setToken(token: string): void {
  localStorage.setItem('devcrew_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('devcrew_token');
  localStorage.removeItem('devcrew_user');
  localStorage.removeItem('devcrew-auth');
}

// ── HTTP helpers ─────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    // Don't force redirect if we are actively trying to log in
    if (!_redirectingToLogin && !path.includes('/auth/login')) {
      _redirectingToLogin = true;
      window.location.href = '/login';
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Request failed');
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN';
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  iteration_count: number;
  estimated_cost_usd: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  created_at: string;
  completed_at: string | null;
  raw_requirement?: string;
  workspace_path?: string;
  error_message?: string;
  requirements?: Record<string, unknown>;
  architecture?: Record<string, unknown>;
  pending_approval?: {
    id: string;
    action: string;
    description: string;
  };
}

export interface AgentRun {
  id: string;
  agent: string;
  status: string;
  objective: string;
  iteration: number;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
}

export interface AgentMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  priority: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface TestResult {
  id: string;
  iteration: number;
  overall_status: string;
  passed: number;
  failed: number;
  skipped: number;
  coverage_percent: number;
  execution_time_ms: number;
  failures: Array<{
    test_name: string;
    file: string;
    line?: number;
    error: string;
    error_type: string;
    severity: string;
    suggested_area: string;
  }>;
  recommendations: string[];
  timestamp: string;
}

export interface SecurityResult {
  id?: string;
  scanner?: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  findings: Array<{
    title: string;
    severity: string;
    file: string;
    line?: string;
    description: string;
    impact: string;
    recommendation: string;
    scanner: string;
    status: string;
  }>;
  status: string;
  timestamp?: string;
}

export interface ReviewResult {
  id?: string;
  status: string;
  overall_score: number;
  code_quality_score: number;
  architecture_score: number;
  security_score: number;
  testing_score: number;
  documentation_score: number;
  strengths: string[];
  issues: Array<{
    category: string;
    severity: string;
    description: string;
    file?: string;
    recommendation: string;
  }>;
  recommendations: string[];
  timestamp?: string;
}

export interface FileInfo {
  files: string[];
  workspace_path: string;
}

export interface FileContent {
  path: string;
  content: string;
  size_bytes: number;
  language: string;
}

export interface SystemStats {
  total_users: number;
  total_projects: number;
  active_runs: number;
  completed_runs: number;
  failed_runs: number;
  total_model_calls: number;
  total_cost_usd: number;
  avg_test_coverage: number;
}

// ── Auth API ─────────────────────────────────────────────────────────────────

export const auth = {
  register: (email: string, password: string, full_name: string) =>
    request<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
  },

  me: () => request<User>('/auth/me'),
};

// ── Projects API ─────────────────────────────────────────────────────────────

export const projects = {
  list: () => request<Project[]>('/projects'),
  get: (id: string) => request<Project>(`/projects/${id}`),
  create: (data: { name: string; description: string; raw_requirement: string }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<void>(`/projects/${id}`, { method: 'DELETE' }),
  run: (id: string) =>
    request<{ project_id: string; status: string; message: string }>(
      `/projects/${id}/run`,
      { method: 'POST' },
    ),
  pause: (id: string) =>
    request<{ project_id: string; status: string; message: string }>(
      `/projects/${id}/pause`,
      { method: 'POST' },
    ),
  cancel: (id: string) =>
    request<{ project_id: string; status: string; message: string }>(
      `/projects/${id}/cancel`,
      { method: 'POST' },
    ),
  respondApproval: (projectId: string, approvalId: string, approved: boolean, rejection_reason?: string) =>
    request<{ approval_id: string; status: string }>(
      `/projects/${projectId}/approvals/${approvalId}`,
      { method: 'POST', body: JSON.stringify({ approved, rejection_reason }) },
    ),
};

// ── Agent API ────────────────────────────────────────────────────────────────

export const agents = {
  getRuns: (projectId: string) => request<AgentRun[]>(`/projects/${projectId}/agents`),
  getActivity: (projectId: string) => request<AgentMessage[]>(`/projects/${projectId}/activity`),
};

// ── Files API ────────────────────────────────────────────────────────────────

export const files = {
  list: (projectId: string) => request<FileInfo>(`/projects/${projectId}/files`),
  getContent: (projectId: string, filePath: string) =>
    request<FileContent>(`/projects/${projectId}/files/content?file_path=${encodeURIComponent(filePath)}`),
  getChanges: (projectId: string) =>
    request<Array<{
      file_path: string;
      change_type: string;
      before_content: string | null;
      after_content: string | null;
      reason: string | null;
      agent: string | null;
      timestamp: string;
    }>>(`/projects/${projectId}/files/changes`),
};

// ── Reports API ──────────────────────────────────────────────────────────────

export const reports = {
  getTests: (projectId: string) => request<TestResult[]>(`/projects/${projectId}/tests`),
  getSecurity: (projectId: string) => request<SecurityResult>(`/projects/${projectId}/security`),
  getReview: (projectId: string) => request<ReviewResult>(`/projects/${projectId}/review`),
  downloadUrl: (projectId: string) =>
    `${BASE_URL}/projects/${projectId}/reports/download`,
  download: async (projectId: string, type: string = 'zip') => {
    const token = getToken();
    const url = `${BASE_URL}/projects/${projectId}/reports/download${type === 'report' ? '?type=report' : ''}`;
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Download failed');
    
    const blob = await res.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    // Attempt to parse filename from Content-Disposition if available
    const disposition = res.headers.get('Content-Disposition');
    let filename = type === 'report' ? `${projectId}_report.pdf` : `${projectId}_source.zip`;
    if (disposition && disposition.includes('filename=')) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
    }
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(objectUrl);
  }
};

// ── Admin API ────────────────────────────────────────────────────────────────

export const admin = {
  getStats: () => request<SystemStats>('/admin/stats'),
  getUsers: () => request<User[]>('/admin/users'),
  getModelUsage: () => request<Array<Record<string, unknown>>>('/admin/model-usage'),
  getProjects: () => request<Project[]>('/admin/projects'),
};

// ── Documents & RAG API ──────────────────────────────────────────────────────

export interface DocumentItem {
  doc_id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  sha256: string;
}

export interface DocumentUploadResult {
  status: string;
  doc_id: string | null;
  filename: string;
  file_type: string;
  chunk_count: number;
  embedding_dimension?: number;
  character_count?: number;
  message?: string;
}

export interface DocumentSearchResult {
  document_id: string;
  title: string;
  source_type: string;
  content_snippet: string;
  score: number;
  metadata: Record<string, unknown>;
}

export const documents = {
  list: (projectId: string) => request<DocumentItem[]>(`/projects/${projectId}/documents`),
  delete: (projectId: string, docId: string) =>
    request<{ status: string; doc_id: string }>(`/projects/${projectId}/documents/${docId}`, {
      method: 'DELETE',
    }),
  query: (projectId: string, query: string, topK = 3) =>
    request<DocumentSearchResult[]>(`/projects/${projectId}/documents/query`, {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }),
  indexWorkspace: (projectId: string) =>
    request<{ status: string; total_files_indexed: number }>(`/projects/${projectId}/documents/index-workspace`, {
      method: 'POST',
    }),
  upload: async (projectId: string, files: FileList | File[]) => {
    const token = getToken();
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${BASE_URL}/projects/${projectId}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? 'Upload failed');
    }
    return res.json() as Promise<DocumentUploadResult[]>;
  },
};

