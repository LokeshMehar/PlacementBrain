import React, { useState } from 'react';
import { BookOpen } from 'lucide-react';
import { Message } from '../../types';
import SourceCard from './SourceCard';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  const hasSources = message.sources && message.sources.length > 0;
  const isTyping = !isUser && message.content === '';

  const timeStr = message.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 group`}>
      <div
        className={`max-w-[80%] ${
          isUser
            ? 'bg-gradient-to-br from-brand-500 to-brand-600 text-white rounded-2xl rounded-br-md shadow-lg shadow-brand-500/20'
            : 'bg-gray-800 text-gray-100 rounded-2xl rounded-bl-md border border-gray-700/50'
        } px-4 py-3`}
      >
        {/* Typing indicator */}
        {isTyping ? (
          <div className="flex items-center gap-1 py-1 px-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0s' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.2s' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: '0.4s' }} />
          </div>
        ) : (
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </div>
        )}

        {/* Sources toggle */}
        {hasSources && (
          <div className="mt-2 pt-2 border-t border-gray-700/30">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-300 transition-colors"
            >
              <BookOpen size={12} />
              {showSources ? 'Hide' : 'Show'} sources ({message.sources!.length})
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources!.map((source, idx) => (
                  <SourceCard key={idx} source={source} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-[10px] mt-1 ${
            isUser ? 'text-blue-200/60' : 'text-gray-500'
          } text-right`}
        >
          {timeStr}
        </div>
      </div>
    </div>
  );
}
