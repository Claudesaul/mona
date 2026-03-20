import { useState, useCallback, useRef } from 'react';

export interface ToolCall {
  database: string;
  query: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
}

interface UseChatReturn {
  messages: Message[];
  sendMessage: (text: string) => void;
  isLoading: boolean;
  error: string | null;
}

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export function useChat(sessionId: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const assistantIdRef = useRef<string>('');
  const isLoadingRef = useRef(false);

  const fallbackFetch = useCallback(
    async (text: string, assistantId: string) => {
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const content = data.response || data.message || 'No response received.';

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content, isStreaming: false }
              : m
          )
        );
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: 'Something went wrong processing your request. Please try again.', isStreaming: false }
              : m
          )
        );
      } finally {
        setIsLoading(false);
        isLoadingRef.current = false;
      }
    },
    [sessionId]
  );

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isLoadingRef.current) return;

      setError(null);

      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
      };

      const assistantId = generateId();
      assistantIdRef.current = assistantId;
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
        toolCalls: [],
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);
      isLoadingRef.current = true;

      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const ws = new WebSocket(`${protocol}//${host}/ws/chat`);
        wsRef.current = ws;

        let opened = false;

        // Clear fallback timeout once WS is working
        const fallbackTimer = setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING) {
            ws.close();
            fallbackFetch(text.trim(), assistantId);
          }
        }, 3000);

        ws.onopen = () => {
          opened = true;
          clearTimeout(fallbackTimer);
          ws.send(
            JSON.stringify({
              session_id: sessionId,
              message: text.trim(),
            })
          );
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'chunk') {
              const chunk = data.content || '';
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, content: m.content + chunk }
                    : m
                )
              );
            } else if (data.type === 'status') {
              // Show status as italicized text during tool execution
              const statusText = `\n\n*${data.content}*\n\n`;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, content: m.content + statusText }
                    : m
                )
              );
            } else if (data.type === 'tool_use') {
              const toolCall: ToolCall = {
                database: data.database || 'Unknown',
                query: data.query || '',
              };
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, toolCalls: [...(m.toolCalls || []), toolCall] }
                    : m
                )
              );
            } else if (data.type === 'done' || data.done) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, isStreaming: false }
                    : m
                )
              );
              setIsLoading(false);
              isLoadingRef.current = false;
              ws.close();
            } else if (data.type === 'error' || data.error) {
              const errorMsg = data.error || data.content || data.message || 'Something went wrong. Please try again.';
              setError(errorMsg);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, content: errorMsg, isStreaming: false }
                    : m
                )
              );
              setIsLoading(false);
              isLoadingRef.current = false;
              ws.close();
            }
          } catch {
            // Plain text chunk
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantIdRef.current
                  ? { ...m, content: m.content + event.data }
                  : m
              )
            );
          }
        };

        ws.onerror = () => {
          clearTimeout(fallbackTimer);
          if (!opened) {
            fallbackFetch(text.trim(), assistantId);
          }
        };

        ws.onclose = (event) => {
          wsRef.current = null;
          clearTimeout(fallbackTimer);
          if (!event.wasClean && isLoadingRef.current) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantIdRef.current && m.isStreaming
                  ? { ...m, isStreaming: false }
                  : m
              )
            );
            setIsLoading(false);
            isLoadingRef.current = false;
          }
        };
      } catch {
        fallbackFetch(text.trim(), assistantId);
      }
    },
    [sessionId, fallbackFetch]
  );

  return { messages, sendMessage, isLoading, error };
}
