import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Download, BookOpen, FileText, Loader2, AlertCircle, X } from 'lucide-react';
import { reports } from '../../api/client';

export default function ReportsTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [downloading, setDownloading] = useState<'zip' | 'report' | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  async function handleDownload(type: 'zip' | 'report') {
    if (!projectId) return;
    setDownloading(type);
    setDownloadError(null);
    try {
      await reports.download(projectId, type);
    } catch (err: unknown) {
      const msg = (err as Error).message ?? 'Download failed';
      // Friendly message when pipeline hasn't run yet
      setDownloadError(
        msg.includes('Download failed') || msg.includes('404')
          ? 'No files to download yet — run the pipeline first to generate project files.'
          : msg,
      );
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-accent-blue" />
        <h2 className="font-semibold text-text-primary">Project Reports</h2>
      </div>

      {/* Error banner */}
      {downloadError && (
        <div className="flex items-start gap-3 p-4 bg-accent-red/10 border border-accent-red/20 rounded-lg text-accent-red text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span className="flex-1">{downloadError}</span>
          <button onClick={() => setDownloadError(null)} className="hover:opacity-70 flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="card p-6 space-y-4">
        <div className="flex items-start gap-4 p-4 bg-bg-raised rounded-lg border border-bg-border">
          <FileText className="w-8 h-8 text-accent-green flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-text-primary">Project ZIP Archive</h3>
            <p className="text-sm text-text-secondary mt-1">
              Complete generated project as a ZIP file, including all source code,
              tests, documentation, and Docker configuration.
            </p>
          </div>
          <button
            onClick={() => handleDownload('zip')}
            className="btn-primary text-sm flex-shrink-0"
            id="download-zip-btn"
            disabled={downloading !== null}
          >
            {downloading === 'zip'
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Download className="w-4 h-4" />}
            {downloading === 'zip' ? 'Downloading…' : 'Download ZIP'}
          </button>
        </div>

        <div className="flex items-start gap-4 p-4 bg-bg-raised rounded-lg border border-bg-border">
          <FileText className="w-8 h-8 text-accent-blue flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-text-primary">Project Report</h3>
            <p className="text-sm text-text-secondary mt-1">
              Comprehensive project report covering requirements, architecture decisions,
              test results, security findings, and review scores.
            </p>
          </div>
          <button
            onClick={() => handleDownload('report')}
            className="btn-secondary text-sm flex-shrink-0"
            id="download-report-btn"
            disabled={downloading !== null}
          >
            {downloading === 'report'
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Download className="w-4 h-4" />}
            {downloading === 'report' ? 'Downloading…' : 'Download Report'}
          </button>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-medium text-text-primary mb-3">Available Documentation</h3>
        <ul className="space-y-2 text-sm text-text-secondary">
          {['README.md', 'docs/architecture.md', 'docs/api.md', 'docs/database.md', 'docs/testing.md', 'docs/security.md', 'docs/deployment.md'].map(doc => (
            <li key={doc} className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-text-muted" />
              <span className="font-mono">{doc}</span>
            </li>
          ))}
        </ul>
        <p className="text-xs text-text-muted mt-3">All docs are included in the ZIP download above.</p>
      </div>
    </div>
  );
}
