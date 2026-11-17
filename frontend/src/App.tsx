import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectLayout from './pages/project/ProjectLayout';
import Overview from './pages/project/Overview';
import RequirementsTab from './pages/project/RequirementsTab';
import ArchitectureTab from './pages/project/ArchitectureTab';
import AgentsTab from './pages/project/AgentsTab';
import FilesTab from './pages/project/FilesTab';
import TestsTab from './pages/project/TestsTab';
import SecurityTab from './pages/project/SecurityTab';
import ReviewTab from './pages/project/ReviewTab';
import ActivityTab from './pages/project/ActivityTab';
import ReportsTab from './pages/project/ReportsTab';
import DocumentsTab from './pages/project/DocumentsTab';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected */}
        <Route path="/" element={<RequireAuth><Navigate to="/dashboard" replace /></RequireAuth>} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/projects" element={<RequireAuth><Projects /></RequireAuth>} />

        {/* Project workspace */}
        <Route path="/projects/:projectId" element={<RequireAuth><ProjectLayout /></RequireAuth>}>
          <Route index element={<Overview />} />
          <Route path="requirements" element={<RequirementsTab />} />
          <Route path="architecture" element={<ArchitectureTab />} />
          <Route path="agents" element={<AgentsTab />} />
          <Route path="documents" element={<DocumentsTab />} />
          <Route path="files" element={<FilesTab />} />
          <Route path="tests" element={<TestsTab />} />
          <Route path="security" element={<SecurityTab />} />
          <Route path="review" element={<ReviewTab />} />
          <Route path="activity" element={<ActivityTab />} />
          <Route path="reports" element={<ReportsTab />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
