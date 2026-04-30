import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Source } from '../../types';

interface SourceCardProps {
  source: Source;
}

const BADGE_CLASSES: Record<string, string> = {
  pdf: 'badge-pdf',
  code: 'badge-code',
  excel: 'badge-excel',
  repo: 'badge-repo',
  markdown: 'badge-markdown',
  text: 'badge-text',
  jd: 'badge-jd',
};

export default function SourceCard({ source }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);
  const badgeClass = BADGE_CLASSES[source.source_type] || 'badge-text';
  const scorePercent = Math.round((source.score || 0) * 100);

  return (
    <div className="glass-card p-3 hover:border-gray-600 transition-all duration-200">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className={`badge ${badgeClass}`}>{source.source_type}</span>
          <span className="text-sm text-gray-300 truncate">{source.filename}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-gray-500">{scorePercent}%</span>
          {expanded ? (
            <ChevronUp size={14} className="text-gray-500" />
          ) : (
            <ChevronDown size={14} className="text-gray-500" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-2 pt-2 border-t border-gray-700/50">
          <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed max-h-40 overflow-y-auto">
            {source.text}
          </pre>
        </div>
      )}
    </div>
  );
}
