import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

interface InputBarProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function InputBar({ onSend, disabled }: InputBarProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 5 * 24; // ~5 lines
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-3 p-4 border-t border-gray-800 bg-gray-900/80 backdrop-blur-lg">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about your placement materials..."
        disabled={disabled}
        rows={1}
        className="flex-1 input-field resize-none min-h-[44px] max-h-[120px]"
        id="chat-input"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !text.trim()}
        className="btn-primary p-3 rounded-xl flex-shrink-0"
        id="send-button"
        aria-label="Send message"
      >
        <Send size={18} />
      </button>
    </div>
  );
}
