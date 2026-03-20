import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '@/hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import type { Theme } from '@/hooks/useTheme';

interface ChatWindowProps {
  sessionId: string;
  theme: Theme;
  pendingQuestion?: string;
  onPendingConsumed?: () => void;
}

// Pool of suggestion questions organized by source — real location/account names
// will be injected dynamically when fetched from /api/locations
const SUGGESTION_POOL = [
  // Snowflake — Revenue & Sales
  'What was total revenue last week?',
  'Top 10 locations by revenue this month',
  'Revenue by product category this week',
  'Which routes generated the most revenue yesterday?',
  'Show me gross margin by location this month',
  // LightSpeed — Orders & Picking
  "What's today's order status breakdown?",
  'How many orders are currently being picked?',
  'Which routes have the most orders today?',
  'Average pick time by route today',
  // OOS — Fill Rate & Stock Health
  'Which locations have the worst fill rate?',
  'Top spoilage items in the last 14 days',
  'What items have the highest shrinkage?',
  'Show me weekly OOS trends',
  'Which locations are predicted to have stock shortages?',
  'What are the fastest selling items right now?',
  // Level — Warehouse
  'What items are below reorder point?',
  'Show me current warehouse inventory levels',
  'Recent purchase orders this week',
  'Which items have the lowest days of supply?',
  // Salesforce — CRM
  'How many open tasks are there by account?',
  'Show me the sales pipeline',
  'Recent equipment installs this month',
  'How many customer vs prospect accounts do we have?',
];

// Templates that get real names injected
const LOCATION_TEMPLATES = [
  'How much revenue did {location} make this month?',
  "What's the fill rate at {location}?",
  'Show me orders for {location} today',
  'What items are out of stock at {location}?',
  'Spoilage report for {location}',
];

function pickRandom<T>(arr: T[], count: number): T[] {
  const shuffled = [...arr].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

function WelcomeState({
  onSuggestionClick,
  inputValue,
  onInputChange,
  onSend,
  isLoading,
  theme,
  suggestions,
}: {
  onSuggestionClick: (text: string) => void;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: (text: string) => void;
  isLoading: boolean;
  theme: Theme;
  suggestions: string[];
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
        <ChatInput
          value={inputValue}
          onChange={onInputChange}
          onSend={onSend}
          isLoading={isLoading}
          centered
          theme={theme}
        />
      </motion.div>

      {/* Suggestion pills — click pastes into input, doesn't send */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        className="flex flex-wrap justify-center gap-2.5 max-w-xl"
      >
        {suggestions.map((s, i) => (
          <motion.button
            key={s}
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

function ChatWindow({ sessionId, theme, pendingQuestion, onPendingConsumed }: ChatWindowProps) {
  const { messages, sendMessage, isLoading } = useChat(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);
  const [inputValue, setInputValue] = useState('');

  const [suggestions, setSuggestions] = useState(() => pickRandom(SUGGESTION_POOL, 5));

  // Handle pending question from Explore page
  useEffect(() => {
    if (pendingQuestion) {
      setInputValue(pendingQuestion);
      onPendingConsumed?.();
    }
  }, [pendingQuestion, onPendingConsumed]);

  // Fetch real location names and mix location-specific suggestions in
  useEffect(() => {
    fetch('/api/locations')
      .then((r) => r.json())
      .then((data) => {
        if (data.locations && data.locations.length > 0) {
          const locs = pickRandom(data.locations as string[], 3);
          const dynamic = pickRandom(LOCATION_TEMPLATES, 2).map((tpl, i) =>
            tpl.replace('{location}', locs[i % locs.length])
          );
          // Replace last 2 generic suggestions with location-specific ones
          setSuggestions((prev) => [...prev.slice(0, 3), ...dynamic]);
        }
      })
      .catch(() => {});
  }, []);

  // Only auto-scroll if user hasn't scrolled up
  useEffect(() => {
    if (!userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    userScrolledUp.current = !atBottom;
  };

  const handleSuggestionClick = (text: string) => {
    setInputValue(text);
  };

  const handleSend = (text: string) => {
    sendMessage(text);
    setInputValue('');
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <AnimatePresence mode="wait">
        {!hasMessages ? (
          <WelcomeState
            key="welcome"
            onSuggestionClick={handleSuggestionClick}
            inputValue={inputValue}
            onInputChange={setInputValue}
            onSend={handleSend}
            isLoading={isLoading}
            theme={theme}
            suggestions={suggestions}
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
                      toolCalls={message.toolCalls}
                    />
                  ))}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>
            </motion.div>
            <div className="px-4 sm:px-6 pb-5 pt-2">
              <div className="max-w-2xl mx-auto">
                <ChatInput
                  value={inputValue}
                  onChange={setInputValue}
                  onSend={handleSend}
                  isLoading={isLoading}
                  theme={theme}
                />
              </div>
            </div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ChatWindow;
