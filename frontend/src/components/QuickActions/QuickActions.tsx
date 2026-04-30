import React from 'react';
import { BookCheck, Sparkles, Code, Search } from 'lucide-react';

interface QuickActionsProps {
  onAction: (action: string) => void;
  disabled: boolean;
}

const actions = [
  { id: 'quiz', label: 'Quiz me', icon: BookCheck, color: 'text-yellow-400' },
  { id: 'resume', label: 'Resume vs JD', icon: Sparkles, color: 'text-purple-400' },
  { id: 'explain', label: 'Explain code', icon: Code, color: 'text-blue-400' },
  { id: 'gaps', label: 'What am I missing?', icon: Search, color: 'text-emerald-400' },
];

export default function QuickActions({ onAction, disabled }: QuickActionsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto">
      {actions.map(({ id, label, icon: Icon, color }) => (
        <button
          key={id}
          onClick={() => onAction(id)}
          disabled={disabled}
          className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap"
        >
          <Icon size={14} className={color} />
          {label}
        </button>
      ))}
    </div>
  );
}
