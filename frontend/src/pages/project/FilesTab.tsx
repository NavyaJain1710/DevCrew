import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileCode2, File, Loader2, Download } from 'lucide-react';
import { files as filesApi, reports } from '../../api/client';
import Editor from '@monaco-editor/react';

export default function FilesTab() {
  const { projectId } = useParams<{ projectId: string }>();
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [language, setLanguage] = useState('plaintext');
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    filesApi.list(projectId).then((r) => {
      setFileList(r.files);
      if (r.files && r.files.length > 0) {
        // Auto-select main code entry point or first file
        const preferred = r.files.find(f => 
          f.endsWith('main.py') || 
          f.endsWith('app.py') || 
          f.endsWith('index.html') || 
          f.endsWith('App.tsx') || 
          f.endsWith('README.md') ||
          f.endsWith('requirements.txt')
        ) || r.files[0];
        openFile(preferred);
      }
    }).catch(console.error).finally(() => setLoading(false));
  }, [projectId]);

  async function openFile(path: string) {
    if (!projectId) return;
    setSelectedFile(path);
    setContentLoading(true);
    try {
      const r = await filesApi.getContent(projectId, path);
      setFileContent(r.content);
      setLanguage(r.language);
    } catch (e) {
      setFileContent('// Error loading file');
    } finally {
      setContentLoading(false);
    }
  }

  async function handleDownloadZip() {
    if (!projectId) return;
    setDownloadingZip(true);
    try {
      await reports.download(projectId, 'zip');
    } catch (e) {
      console.error(e);
    } finally {
      setDownloadingZip(false);
    }
  }

  if (loading) return <div className="text-text-muted text-sm">Loading files…</div>;

  return (
    <div className="flex gap-4 h-[calc(100vh-14rem)]">
      {/* File tree */}
      <div className="w-64 flex-shrink-0 card p-3 overflow-y-auto flex flex-col">
        <div className="flex items-center justify-between mb-2 px-2">
          <div className="section-title">Workspace ({fileList.length})</div>
          {fileList.length > 0 && (
            <button
              onClick={handleDownloadZip}
              disabled={downloadingZip}
              className="text-xs text-accent-green hover:underline flex items-center gap-1 font-medium"
              title="Download ZIP"
            >
              {downloadingZip ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
              <span>ZIP</span>
            </button>
          )}
        </div>
        {fileList.length === 0 ? (
          <p className="text-text-muted text-xs px-2">No files yet. Run the pipeline.</p>
        ) : (
          <div className="space-y-0.5 overflow-y-auto flex-1">
            {fileList.map((f) => (
              <button
                key={f}
                onClick={() => openFile(f)}
                className={`w-full text-left flex items-center gap-2 px-2 py-1.5 rounded text-xs font-mono transition-colors ${
                  selectedFile === f
                    ? 'bg-accent-blue/10 text-accent-blue font-semibold'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-raised'
                }`}
              >
                <File className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{f}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Editor panel */}
      <div className="flex-1 card overflow-hidden flex flex-col">
        {selectedFile ? (
          <>
            <div className="flex items-center gap-2 px-4 py-2 border-b border-bg-border bg-bg-raised">
              <FileCode2 className="w-4 h-4 text-accent-blue" />
              <span className="font-mono text-sm text-text-primary">{selectedFile}</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-bg-base text-text-muted border border-bg-border ml-2">
                {language}
              </span>
              {contentLoading && <Loader2 className="w-3.5 h-3.5 animate-spin text-text-muted ml-auto" />}
            </div>
            <div className="flex-1">
              {contentLoading ? (
                <div className="flex items-center justify-center h-full text-text-muted">
                  <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
                </div>
              ) : (
                <Editor
                  height="100%"
                  language={language}
                  value={fileContent}
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: 'JetBrains Mono, Fira Code, monospace',
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    automaticLayout: true,
                  }}
                />
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-text-muted gap-3">
            <FileCode2 className="w-12 h-12 opacity-30" />
            <p className="text-sm">Select a file to view its content</p>
          </div>
        )}
      </div>
    </div>
  );
}
