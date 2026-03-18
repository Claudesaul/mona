import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '@/hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import MonumentalLeaf from './MonumentalLeaf';
import type { Theme } from '@/hooks/useTheme';

interface ChatWindowProps {
  sessionId: string;
  theme: Theme;
}

const suggestions = [
  'What locations had the worst fill rate?',
  'Show me today\'s order summary',
  'Which items are trending out of stock?',
  'Warehouse inventory status',
];

function WelcomeState({
  onSuggestionClick,
  onSend,
  isLoading,
  theme,
}: {
  onSuggestionClick: (text: string) => void;
  onSend: (text: string) => void;
  isLoading: boolean;
  theme: Theme;
}) {
  const isDark = theme === 'dark';

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      {/* Hero text */}
      <motion.h1
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-center mb-3 text-gradient-flow"
        style={{ letterSpacing: '-0.035em' }}
      >
        Hi, I'm Mona
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className={`text-[15px] sm:text-base text-center mb-10 max-w-md font-light leading-relaxed ${isDark ? 'text-white/35' : 'text-gray-400'}`}
      >
        Your AI assistant for Monumental Markets
      </motion.p>

      {/* Centered prompt box */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-[640px] mb-6"
      >
        <ChatInput onSend={onSend} isLoading={isLoading} centered theme={theme} />
      </motion.div>

      {/* Suggestion pills — invert colors on hover */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        className="flex flex-wrap justify-center gap-2.5 max-w-xl"
      >
        {suggestions.map((s, i) => (
          <motion.button
            key={i}
            onClick={() => onSuggestionClick(s)}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 + i * 0.06, duration: 0.3 }}
            whileTap={{ scale: 0.96 }}
            className={`
              suggestion-pill px-4 py-2.5 rounded-full text-[13px] font-medium border cursor-pointer
              transition-none
              ${isDark
                ? 'text-white/40 bg-transparent border-white/[0.08] hover:bg-white hover:text-[#09090b] hover:border-white'
                : 'text-gray-400 bg-transparent border-gray-200 hover:bg-gray-900 hover:text-white hover:border-gray-900'
              }
            `}
          >
            {s}
          </motion.button>
        ))}
      </motion.div>
    </div>
  );
}

function ChatWindow({ sessionId, theme }: ChatWindowProps) {
  const { messages, sendMessage, isLoading } = useChat(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // Only auto-scroll if user hasn't scrolled up
  useEffect(() => {
    if (!userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Detect if user scrolled away from bottom
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    userScrolledUp.current = !atBottom;
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <AnimatePresence mode="wait">
        {!hasMessages ? (
          <WelcomeState
            key="welcome"
            onSuggestionClick={sendMessage}
            onSend={sendMessage}
            isLoading={isLoading}
            theme={theme}
          />
        ) : (
          <>
            <motion.div
              key="messages"
              ref={containerRef}
              onScroll={handleScroll}
              className="flex-1 overflow-y-auto px-4 sm:px-6 py-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.25 }}
            >
              <div className="max-w-2xl mx-auto space-y-5">
                <AnimatePresence initial={false}>
                  {messages.map((message) => (
                    <MessageBubble
                      key={message.id}
                      role={message.role}
                      content={message.content}
                      isStreaming={message.isStreaming ?? false}
                      theme={theme}
                    />
                  ))}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>
            </motion.div>
            <div className="px-4 sm:px-6 pb-5 pt-2">
              <div className="max-w-2xl mx-auto">
                <ChatInput onSend={sendMessage} isLoading={isLoading} theme={theme} />
              </div>
            </div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ChatWindow;
