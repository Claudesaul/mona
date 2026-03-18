import { useState, useCallback, useRef } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
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
              ? { ...m, content: `Sorry, I encountered an error: ${errorMsg}`, isStreaming: false }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isLoading) return;

      setError(null);

      // Add user message
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
      };

      // Add placeholder assistant message
      const assistantId = generateId();
      assistantIdRef.current = assistantId;
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      // Try WebSocket first
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const ws = new WebSocket(`${protocol}//${host}/ws/chat`);
        wsRef.current = ws;

        let opened = false;

        ws.onopen = () => {
          opened = true;
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

            if (data.type === 'chunk' || data.chunk) {
              const chunk = data.chunk || data.content || data.text || '';
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, content: m.content + chunk }
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
              ws.close();
            } else if (data.type === 'error' || data.error) {
              const errorMsg = data.error || data.message || 'Unknown error';
              setError(errorMsg);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? {
                        ...m,
                        content: `Sorry, I encountered an error: ${errorMsg}`,
                        isStreaming: false,
                      }
                    : m
                )
              );
              setIsLoading(false);
              ws.close();
            } else if (data.type === 'message' || data.response) {
              // Full message response (non-streaming)
              const content = data.response || data.content || data.message || '';
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantIdRef.current
                    ? { ...m, content, isStreaming: false }
                    : m
                )
              );
              setIsLoading(false);
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
          if (!opened) {
            // WebSocket failed to connect -- fall back to HTTP
            fallbackFetch(text.trim(), assistantId);
          }
        };

        ws.onclose = (event) => {
          wsRef.current = null;
          if (!event.wasClean && isLoading) {
            // Abnormal close while still loading -- finalize
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantIdRef.current && m.isStreaming
                  ? { ...m, isStreaming: false }
                  : m
              )
            );
            setIsLoading(false);
          }
        };

        // Timeout: if WS doesn't open in 3s, fall back
        setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING) {
            ws.close();
            fallbackFetch(text.trim(), assistantId);
          }
        }, 3000);
      } catch {
        // WebSocket constructor failed -- fall back
        fallbackFetch(text.trim(), assistantId);
      }
    },
    [isLoading, sessionId, fallbackFetch]
  );

  return { messages, sendMessage, isLoading, error };
}
