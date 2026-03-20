import { useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowUp } from 'lucide-react';
import type { Theme } from '@/hooks/useTheme';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string) => void;
  isLoading: boolean;
  centered?: boolean;
  theme?: Theme;
}

function ChatInput({ value, onChange, onSend, isLoading, centered = false, theme = 'dark' }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isDark = theme === 'dark';

  const canSend = value.trim().length > 0 && !isLoading;

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, centered ? 180 : 120)}px`;
    }
  }, [centered]);

  useEffect(() => { adjustHeight(); }, [value, adjustHeight]);

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(value.trim());
    onChange('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [canSend, value, onSend, onChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    },
    [handleSend]
  );

  const btnSize = centered ? 'h-9 px-4' : 'h-8 px-3';

  return (
    <div className="w-full">
      <div
        className={`
          relative overflow-hidden transition-all duration-300
          ${centered ? 'rounded-2xl' : 'rounded-xl'}
          border
          ${isDark
            ? value
              ? 'bg-[#111113] border-white/[0.12] shadow-[0_0_0_1px_rgba(16,185,129,0.05),0_8px_50px_rgba(0,0,0,0.5)]'
              : 'bg-[#111113] border-white/[0.07] shadow-[0_4px_30px_rgba(0,0,0,0.35)]'
            : value
              ? 'bg-white border-gray-300/80 shadow-[0_0_0_1px_rgba(16,185,129,0.06),0_8px_40px_rgba(0,0,0,0.08)]'
              : 'bg-white border-gray-200/80 shadow-[0_4px_24px_rgba(0,0,0,0.05)]'
          }
        `}
      >
        {/* Textarea */}
        <div className={centered ? 'px-5 pt-5 pb-3' : 'px-4 pt-4 pb-2'}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            rows={centered ? 2 : 1}
            className={`
              w-full resize-none bg-transparent outline-none leading-relaxed
              ${centered ? 'text-[15px] min-h-[56px]' : 'text-[14px]'}
              ${isDark
                ? 'text-white/85 placeholder-white/20'
                : 'text-gray-800 placeholder-gray-300'
              }
            `}
            style={{ maxHeight: centered ? '180px' : '120px' }}
          />
        </div>

        {/* Bottom bar */}
        <div className={`flex items-center justify-end ${centered ? 'px-5 pb-4 pt-1' : 'px-4 pb-3 pt-0'}`}>
          <motion.button
            onClick={handleSend}
            disabled={!canSend}
            whileTap={canSend ? { scale: 0.95 } : {}}
            className={`
              relative flex items-center justify-center gap-2 rounded-full
              ${btnSize}
              text-[13px] font-medium
              overflow-hidden
              transition-none
              ${canSend
                ? 'cursor-pointer'
                : 'cursor-not-allowed'
              }
              ${canSend
                ? isDark
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.25)]'
                  : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-[0_2px_12px_rgba(16,185,129,0.3)]'
                : isDark
                  ? 'bg-white/[0.04] text-white/15'
                  : 'bg-gray-100 text-gray-300'
              }
            `}
          >
            {/* Shimmer overlay on active */}
            {canSend && (
              <div
                className="absolute inset-0 opacity-0 hover:opacity-100"
                style={{
                  background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.12) 50%, transparent 100%)',
                  backgroundSize: '200% 100%',
                  animation: 'none',
                  transition: 'opacity 0.15s',
                }}
              />
            )}
            <ArrowUp size={15} strokeWidth={2.5} className="relative z-10" />
          </motion.button>
        </div>
      </div>

      {centered && (
        <p className={`text-[11px] text-center mt-4 ${isDark ? 'text-white/15' : 'text-gray-300'}`}>
          Mona can make mistakes. Always verify important business data.
        </p>
      )}
    </div>
  );
}

export default ChatInput;
