import React, { useState } from 'react';
import { Database, Loader2 } from 'lucide-react';
import { useSourcesList, useDeleteSource } from '../../hooks/useSources';
import SourceRow from './SourceRow';

const SOURCE_TYPES = ['all', 'pdf', 'code', 'excel', 'repo', 'markdown', 'text', 'jd'];

export default function KnowledgeBase() {
  const { sources, isLoading, refetch } = useSourcesList();
  const deleteMutation = useDeleteSource();
  const [filter, setFilter] = useState('all');

  const filteredSources =
    filter === 'all'
      ? sources
      : sources.filter((s) => s.source_type === filter);

  const totalChunks = sources.reduce((sum, s) => sum + s.chunk_count, 0);

  const handleDelete = async (sourceId: string) => {
    await deleteMutation.mutateAsync(sourceId);
    refetch();
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
            <Database size={20} className="text-brand-400" />
            Knowledge Base
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {sources.length} source{sources.length !== 1 ? 's' : ''} · {totalChunks} chunks
          </p>
        </div>
      </div>

      {/* Filter buttons */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        {SOURCE_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap ${
              filter === type
                ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
            }`}
          >
            {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto glass-card">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 size={24} className="text-brand-400 animate-spin" />
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-center">
            <Database size={32} className="text-gray-600 mb-3" />
            <p className="text-gray-500 text-sm">
              {filter === 'all'
                ? 'No sources ingested yet. Upload files to get started.'
                : `No ${filter} sources found.`}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  File
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Chunks
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredSources.map((source) => (
                <SourceRow
                  key={source.source_id}
                  source={source}
                  onDelete={handleDelete}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
