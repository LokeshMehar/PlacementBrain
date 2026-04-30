import React, { useState } from 'react';
import { Trash2, FileText, Code, FileSpreadsheet, GitBranch, FileType, File } from 'lucide-react';
import { SourceItem } from '../../types';

interface SourceRowProps {
  source: SourceItem;
  onDelete: (id: string) => void;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  pdf: <FileText size={16} className="text-red-400" />,
  code: <Code size={16} className="text-blue-400" />,
  excel: <FileSpreadsheet size={16} className="text-emerald-400" />,
  repo: <GitBranch size={16} className="text-purple-400" />,
  markdown: <FileType size={16} className="text-yellow-400" />,
  text: <File size={16} className="text-gray-400" />,
  jd: <FileText size={16} className="text-teal-400" />,
};

const BADGE_CLASSES: Record<string, string> = {
  pdf: 'badge-pdf',
  code: 'badge-code',
  excel: 'badge-excel',
  repo: 'badge-repo',
  markdown: 'badge-markdown',
  text: 'badge-text',
  jd: 'badge-jd',
};

export default function SourceRow({ source, onDelete }: SourceRowProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const icon = TYPE_ICONS[source.source_type] || TYPE_ICONS.text;
  const badgeClass = BADGE_CLASSES[source.source_type] || 'badge-text';

  const handleDelete = () => {
    if (confirmDelete) {
      onDelete(source.source_id);
      setConfirmDelete(false);
    } else {
      setConfirmDelete(true);
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          {icon}
          <span className="text-sm text-gray-200 truncate max-w-[200px]">
            {source.filename}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={`badge ${badgeClass}`}>{source.source_type}</span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400 text-center">
        {source.chunk_count}
      </td>
      <td className="px-4 py-3 text-right">
        <button
          onClick={handleDelete}
          className={`text-xs px-2 py-1 rounded-md transition-all duration-200 ${
            confirmDelete
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'text-gray-500 hover:text-red-400 hover:bg-red-500/10'
          }`}
        >
          {confirmDelete ? (
            'Confirm?'
          ) : (
            <Trash2 size={14} />
          )}
        </button>
      </td>
    </tr>
  );
}
