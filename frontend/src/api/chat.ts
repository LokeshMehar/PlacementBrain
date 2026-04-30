import { Source } from '../types';

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatMessage {
  role: 'human' | 'ai';
  content: string;
  created_at: string;
}

export interface InterviewStatus {
  status: 'active' | 'completed';
  question_index: number;
  current_question: string | null;
  feedback: string | null;
  final_assessment: string | null;
}

export async function listChats(): Promise<ChatSession[]> {
  const response = await fetch('/api/chat');
  if (!response.ok) throw new Error('Failed to fetch chats');
  return response.json();
}

export async function createChat(title: string = 'New Chat'): Promise<ChatSession> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) throw new Error('Failed to create chat');
  return response.json();
}

export async function deleteChat(chatId: string): Promise<void> {
  const response = await fetch(`/api/chat/${chatId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete chat');
}

export async function getMessages(chatId: string): Promise<ChatMessage[]> {
  const response = await fetch(`/api/chat/${chatId}/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  return response.json();
}

export async function startInterview(chatId: string, topic: string): Promise<InterviewStatus> {
  const response = await fetch('/api/interview/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, topic }),
  });
  if (!response.ok) throw new Error('Failed to start interview');
  return response.json();
}

export async function submitAnswer(chatId: string, answer: string): Promise<InterviewStatus> {
  const response = await fetch('/api/interview/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, answer }),
  });
  if (!response.ok) throw new Error('Failed to submit answer');
  return response.json();
}

export function streamChat(
  message: string,
  sessionId: string,
  onToken: (token: string) => void,
  onDone: (sources: Source[]) => void,
  onError: (err: Error) => void
): () => void {
  const params = new URLSearchParams({
    message,
    session_id: sessionId,
  });

  const eventSource = new EventSource(`/api/chat/stream?${params.toString()}`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'token') {
        onToken(data.data);
      } else if (data.type === 'done') {
        onDone(data.sources || []);
        eventSource.close();
      }
    } catch {
      // Raw text fallback
      onToken(event.data);
    }
  };

  eventSource.onerror = () => {
    onError(new Error('Connection lost'));
    eventSource.close();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
  };
}
