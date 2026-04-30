import React from 'react';
import { UploadStatus } from '../../types';

interface IngestionProgressProps {
  uploads: UploadStatus[];
}

export default function IngestionProgress({ uploads }: IngestionProgressProps) {
  const total = uploads.length;
  const done = uploads.filter((u) => u.status === 'done').length;
  const errors = uploads.filter((u) => u.status === 'error').length;
  const inProgress = uploads.filter((u) => u.status === 'uploading').length;

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-gray-800/30 rounded-lg text-xs">
      <span className="text-gray-400">
        {total} file{total !== 1 ? 's' : ''}
      </span>
      {done > 0 && <span className="text-emerald-400">✓ {done} done</span>}
      {inProgress > 0 && <span className="text-brand-400">⟳ {inProgress} uploading</span>}
      {errors > 0 && <span className="text-red-400">✗ {errors} failed</span>}
    </div>
  );
}
