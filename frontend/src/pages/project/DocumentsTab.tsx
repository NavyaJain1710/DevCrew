import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileText, Upload, Trash2, Search, RefreshCw, Loader2,
  CheckCircle2, AlertCircle, Database, FileCode2
} from 'lucide-react';
import {
  documents as docApi,
  type DocumentItem,
  type DocumentSearchResult,
  type DocumentUploadResult,
} from '../../api/client';

export default function DocumentsTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [docList, setDocList] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    if (!projectId) return;
    try {
      let docs = await docApi.list(projectId);
      if (docs.length === 0) {
        try {
          const res = await docApi.indexWorkspace(projectId);
          if (res && res.total_files_indexed > 0) {
            docs = await docApi.list(projectId);
          }
        } catch {
          // No workspace files yet
        }
      }
      setDocList(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [projectId]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!projectId || !e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    setUploadMessage(null);
    setUploadError(null);

    try {
      const res: DocumentUploadResult[] = await docApi.upload(projectId, e.target.files);
      const indexedCount = res.filter((r) => r.status === 'indexed').length;
      const skippedCount = res.filter((r) => r.status === 'skipped').length;
      setUploadMessage(`Uploaded: ${indexedCount} indexed, ${skippedCount} up to date.`);
      fetchDocuments();
    } catch (err: unknown) {
      setUploadError((err as Error).message || 'File upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docId: string) => {
    if (!projectId) return;
    try {
      await docApi.delete(projectId, docId);
      fetchDocuments();
    } catch (err: unknown) {
      alert((err as Error).message || 'Failed to delete document');
    }
  };

  const handleIndexWorkspace = async () => {
    if (!projectId) return;
    setUploading(true);
    setUploadMessage(null);
    setUploadError(null);
    try {
      const res = await docApi.indexWorkspace(projectId);
      setUploadMessage(`Indexed workspace files: ${res.total_files_indexed} total files.`);
      fetchDocuments();
    } catch (err: unknown) {
      setUploadError((err as Error).message || 'Failed to index workspace');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !searchQuery.trim()) return;
    setSearching(true);
    try {
      const results = await docApi.query(projectId, searchQuery, 4);
      setSearchResults(results);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Upload actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 card">
        <div>
          <h2 className="text-base font-semibold text-text-primary flex items-center gap-2">
            <Database className="w-5 h-5 text-accent-blue" />
            Dynamic RAG Knowledge Base
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Upload PDFs, DOCX specifications, Markdown guidelines, or source-code files to ground agent execution with dense vector search (all-MiniLM-L6-v2).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            multiple
            accept=".pdf,.docx,.txt,.md,.py,.js,.ts,.tsx,.jsx,.html,.css,.json,.yaml,.yml,.sql"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="btn-primary text-xs"
          >
            {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
            Upload Documents
          </button>
          <button
            onClick={handleIndexWorkspace}
            disabled={uploading}
            className="btn-secondary text-xs"
            title="Index workspace files"
          >
            <FileCode2 className="w-3.5 h-3.5" />
            Index Workspace
          </button>
          <button onClick={fetchDocuments} className="btn-ghost p-2" title="Refresh">
            <RefreshCw className="w-4 h-4 text-text-secondary" />
          </button>
        </div>
      </div>

      {uploadMessage && (
        <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs rounded-lg">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          {uploadMessage}
        </div>
      )}

      {uploadError && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded-lg">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {uploadError}
        </div>
      )}

      {/* Main Grid: Document List & Semantic Query Sandbox */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document List */}
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
              Indexed Documents ({docList.length})
            </span>
          </div>

          {loading ? (
            <div className="flex items-center gap-2 text-xs text-text-muted py-6 justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-accent-blue" />
              Loading vector index…
            </div>
          ) : docList.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-bg-border rounded-lg text-text-muted text-xs">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-40" />
              No documents indexed yet. Upload a PDF, Word doc, or codebase file to enable context retrieval.
            </div>
          ) : (
            <div className="divide-y divide-bg-border max-h-[400px] overflow-y-auto">
              {docList.map((doc) => (
                <div key={doc.doc_id} className="py-2.5 flex items-center justify-between text-xs">
                  <div className="min-w-0 pr-3">
                    <div className="font-medium text-text-primary truncate flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-accent-blue/10 text-accent-blue uppercase">
                        {doc.file_type.replace('.', '') || 'TXT'}
                      </span>
                      {doc.filename}
                    </div>
                    <div className="text-[11px] text-text-muted mt-0.5">
                      {doc.chunk_count} vector chunks · SHA: {doc.sha256.slice(0, 10)}…
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.doc_id)}
                    className="btn-ghost p-1.5 text-text-muted hover:text-red-400"
                    title="Delete document and remove vectors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Semantic Search Tester */}
        <div className="card p-4 space-y-3">
          <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
            Semantic Vector Search Tester
          </span>

          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Test query: e.g. 'How is authentication implemented?'"
              className="input-field text-xs flex-1"
            />
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="btn-primary text-xs"
            >
              {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              Search
            </button>
          </form>

          {/* Results display */}
          <div className="space-y-2 max-h-[350px] overflow-y-auto">
            {searching ? (
              <div className="flex items-center gap-2 text-xs text-text-muted py-6 justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-accent-blue" />
                Computing cosine similarity…
              </div>
            ) : searchResults.length === 0 ? (
              <div className="text-center py-8 text-text-muted text-xs">
                Enter a query above to see dynamically retrieved vector chunks and relevance scores.
              </div>
            ) : (
              searchResults.map((r, i) => (
                <div key={i} className="p-3 bg-bg-surface border border-bg-border rounded-lg text-xs space-y-1.5">
                  <div className="flex items-center justify-between font-medium">
                    <span className="text-accent-blue truncate">{r.title}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                      Score: {(r.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <pre className="text-[11px] text-text-secondary bg-bg-base/70 p-2 rounded whitespace-pre-wrap font-mono max-h-24 overflow-y-auto">
                    {r.content_snippet}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
