import React, { useState } from 'react';
import { GitBranch, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { ingestRepo } from '../../api/ingest';

export default function RepoInput() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isValidUrl = (u: string) => {
    try {
      const parsed = new URL(u);
      return parsed.hostname.includes('github') || parsed.hostname.includes('gitlab') || parsed.hostname.includes('bitbucket') || u.endsWith('.git');
    } catch {
      return false;
    }
  };

  const handleSubmit = async () => {
    if (!isValidUrl(url)) {
      setError('Please enter a valid Git repository URL');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await ingestRepo(url);
      setResult(`Ingested ${res.chunk_count} chunks from repo`);
      setUrl('');
    } catch (err: any) {
      setError(err.message || 'Failed to ingest repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <GitBranch size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setError(null);
            }}
            placeholder="https://github.com/user/repo"
            className="input-field w-full pl-9 text-sm"
            disabled={loading}
            id="repo-url-input"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={loading || !url.trim()}
          className="btn-primary text-sm flex items-center gap-1.5"
          id="ingest-repo-button"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Clone'}
        </button>
      </div>

      {result && (
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <CheckCircle size={12} /> {result}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 text-xs text-red-400">
          <AlertCircle size={12} /> {error}
        </div>
      )}
    </div>
  );
}
