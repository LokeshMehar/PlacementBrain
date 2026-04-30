import { useState, useCallback, useRef } from 'react';
import { Message, Source } from '../types';
import { streamChat } from '../api/chat';

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

export function useSSE() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const currentStreamIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(
    (text: string, sessionId: string) => {
      if (isStreaming) return;

      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };

      const assistantId = generateId();
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);
      currentStreamIdRef.current = assistantId;

      const cleanup = streamChat(
        text,
        sessionId,
        // onToken
        (token: string) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m
            )
          );
        },
        // onDone
        (sources: Source[]) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, sources } : m
            )
          );
          setIsStreaming(false);
          currentStreamIdRef.current = null;
        },
        // onError
        (err: Error) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `Error: ${err.message}` }
                : m
            )
          );
          setIsStreaming(false);
          currentStreamIdRef.current = null;
        }
      );

      cleanupRef.current = cleanup;
    },
    [isStreaming]
  );

  const clearMessages = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    setMessages([]);
    setIsStreaming(false);
    currentStreamIdRef.current = null;
  }, []);

  return { messages, setMessages, isStreaming, sendMessage, clearMessages };
}
