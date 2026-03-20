import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import QueryDetails from './QueryDetails';
import type { ToolCall } from '@/hooks/useChat';
import type { Theme } from '@/hooks/useTheme';

const REMARK_PLUGINS = [remarkGfm];

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming: boolean;
  theme?: Theme;
  toolCalls?: ToolCall[];
}

function MessageBubble({ role, content, isStreaming, theme = 'dark', toolCalls }: MessageBubbleProps) {
  const isUser = role === 'user';
  const isDark = theme === 'dark';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`
          relative text-[15px] leading-[1.75] rounded-2xl px-5 py-3 border
          ${isUser
            ? `max-w-[85%] ${isDark
              ? 'bg-white/[0.08] border-white/[0.08] rounded-tr-lg text-white/85'
              : 'bg-gray-900 border-gray-900 rounded-tr-lg text-white'}`
            : `max-w-[95%] ${isDark
              ? 'bg-white/[0.03] border-white/[0.05] rounded-tl-lg text-white/80'
              : 'bg-white border-gray-200/80 rounded-tl-lg text-gray-700 shadow-[0_1px_3px_rgba(0,0,0,0.04)]'}`
          }
        `}
      >
        <div className={isUser ? '' : 'prose-mona'}>
          {content ? (
            isUser ? (
              <span>{content}</span>
            ) : (
              <ReactMarkdown remarkPlugins={REMARK_PLUGINS}>{content}</ReactMarkdown>
            )
          ) : isStreaming ? (
            <div className="flex items-center gap-1.5 py-1">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className={`w-2 h-2 rounded-full ${isDark ? 'bg-emerald-400/60' : 'bg-emerald-500/50'}`}
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
                />
              ))}
            </div>
          ) : (
            <span className={`italic text-sm ${isDark ? 'text-white/20' : 'text-gray-300'}`}>No response</span>
          )}
        </div>

        {isStreaming && content && (
          <motion.span
            className="inline-block w-[3px] h-[16px] bg-emerald-500 rounded-full ml-1 align-middle"
            animate={{ opacity: [1, 0.2, 1] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}

        {/* Query transparency: show which databases/queries were used */}
        {!isUser && !isStreaming && toolCalls && toolCalls.length > 0 && (
          <QueryDetails toolCalls={toolCalls} theme={theme} />
        )}
      </div>
    </motion.div>
  );
}

export default MessageBubble;
