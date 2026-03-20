import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Database, Code } from 'lucide-react';
import type { ToolCall } from '@/hooks/useChat';
import type { Theme } from '@/hooks/useTheme';

interface QueryDetailsProps {
  toolCalls: ToolCall[];
  theme: Theme;
}

function QueryDetails({ toolCalls, theme }: QueryDetailsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const isDark = theme === 'dark';

  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className={`mt-3 rounded-lg border ${isDark ? 'border-white/[0.07]' : 'border-gray-200/80'}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full flex items-center gap-2 px-3 py-2 text-[12px] font-medium rounded-lg cursor-pointer
          transition-colors duration-150
          ${isDark
            ? 'text-white/40 hover:text-white/60 hover:bg-white/[0.03]'
            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
          }
        `}
      >
        <Database size={13} />
        <span>
          {toolCalls.length === 1
            ? `Queried ${toolCalls[0].database}`
            : `Queried ${toolCalls.length} databases`
          }
        </span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="ml-auto"
        >
          <ChevronDown size={13} />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className={`px-3 pb-3 space-y-2 ${isDark ? 'border-t border-white/[0.05]' : 'border-t border-gray-100'}`}>
              {toolCalls.map((tc, i) => (
                <div key={i} className="pt-2">
                  <div className={`flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider mb-1.5 ${isDark ? 'text-emerald-400/70' : 'text-emerald-600'}`}>
                    <Code size={11} />
                    {tc.database}
                  </div>
                  <pre
                    className={`
                      text-[11px] leading-relaxed p-2.5 rounded-md overflow-x-auto font-mono
                      ${isDark
                        ? 'bg-white/[0.03] text-white/50'
                        : 'bg-gray-50 text-gray-500'
                      }
                    `}
                  >
                    {tc.query || '(no query captured)'}
                  </pre>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default QueryDetails;
