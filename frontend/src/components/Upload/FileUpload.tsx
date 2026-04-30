import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { UploadStatus } from '../../types';
import { uploadFile } from '../../api/ingest';
import IngestionProgress from './IngestionProgress';

const ACCEPTED_EXTENSIONS = [
  '.pdf', '.xlsx', '.xls', '.py', '.js', '.ts', '.java', '.md', '.txt',
];

export default function FileUpload() {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(async (file: File) => {
    const uploadEntry: UploadStatus = {
      filename: file.name,
      status: 'uploading',
      progress: 50,
    };

    setUploads((prev) => [...prev, uploadEntry]);

    try {
      const result = await uploadFile(file);
      setUploads((prev) =>
        prev.map((u) =>
          u.filename === file.name
            ? { ...u, status: 'done', progress: 100, result }
            : u
        )
      );
    } catch (err: any) {
      setUploads((prev) =>
        prev.map((u) =>
          u.filename === file.name
            ? { ...u, status: 'error', progress: 0, error: err.message || 'Upload failed' }
            : u
        )
      );
    }
  }, []);

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      Array.from(files).forEach((file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        if (ACCEPTED_EXTENSIONS.includes(ext)) {
          processFile(file);
        }
      });
    },
    [processFile]
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'border-brand-400 bg-brand-500/10'
            : 'border-gray-700 hover:border-gray-600 hover:bg-gray-800/50'
        }`}
        id="file-drop-zone"
      >
        <Upload size={24} className="mx-auto text-gray-500 mb-2" />
        <p className="text-sm text-gray-400">
          Drop files here or <span className="text-brand-400">browse</span>
        </p>
        <p className="text-xs text-gray-600 mt-1">
          PDF, Excel, Python, JS, TS, Java, MD, TXT
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {/* Upload list */}
      {uploads.length > 0 && (
        <div className="space-y-2">
          <IngestionProgress uploads={uploads} />
          {uploads.map((upload, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 px-3 py-2 bg-gray-800/50 rounded-lg"
            >
              {upload.status === 'uploading' && (
                <Loader2 size={14} className="text-brand-400 animate-spin flex-shrink-0" />
              )}
              {upload.status === 'done' && (
                <CheckCircle size={14} className="text-emerald-400 flex-shrink-0" />
              )}
              {upload.status === 'error' && (
                <AlertCircle size={14} className="text-red-400 flex-shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <p className="text-xs text-gray-300 truncate">{upload.filename}</p>
                {upload.status === 'uploading' && (
                  <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                    <div
                      className="bg-brand-500 h-1 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}
                {upload.status === 'done' && upload.result && (
                  <p className="text-[10px] text-gray-500">
                    {upload.result.chunk_count} chunks
                  </p>
                )}
                {upload.status === 'error' && (
                  <p className="text-[10px] text-red-400">{upload.error}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
