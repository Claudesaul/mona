import { useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import QueryDetails from './QueryDetails';
import type { ToolCall } from '@/hooks/useChat';
import type { Theme } from '@/hooks/useTheme';

const REMARK_PLUGINS = [remarkGfm];

function extractTablesAsCsv(markdown: string): string | null {
  // Match markdown tables (header row | separator | data rows)
  const tableRegex = /\|(.+)\|\r?\n\|[-| :]+\|\r?\n((?:\|.+\|\r?\n?)+)/g;
  const tables: string[] = [];

  let match;
  while ((match = tableRegex.exec(markdown)) !== null) {
    const headerLine = match[1];
    const bodyBlock = match[2];

    const headers = headerLine.split('|').map(h => h.trim()).filter(Boolean);
    const rows = bodyBlock.trim().split('\n').map(row =>
      row.split('|').map(c => c.trim()).filter(Boolean)
    );

    const csvRows = [
      headers.map(h => `"${h.replace(/"/g, '""')}"`).join(','),
      ...rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')),
    ];
    tables.push(csvRows.join('\n'));
  }

  return tables.length > 0 ? tables.join('\n\n') : null;
}

function downloadCsv(csv: string) {
  // Add BOM for Excel UTF-8 compatibility
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mona_export_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming: boolean;
  theme?: Theme;
  toolCalls?: ToolCall[];
  status?: string;
}

function MessageBubble({ role, content, isStreaming, theme = 'dark', toolCalls, status }: MessageBubbleProps) {
  const isUser = role === 'user';
  const isDark = theme === 'dark';
  const csvData = !isUser && !isStreaming && content ? extractTablesAsCsv(content) : null;
  const handleExcelExport = useCallback(() => { if (csvData) downloadCsv(csvData); }, [csvData]);

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
              ? 'bg-white/[0.12] border-white/[0.12] rounded-tr-lg text-white'
              : 'bg-gray-900 border-gray-900 rounded-tr-lg text-white'}`
            : `max-w-[95%] ${isDark
              ? 'bg-white/[0.07] border-white/[0.09] rounded-tl-lg text-white/90'
              : 'bg-white border-gray-200 rounded-tl-lg text-gray-800 shadow-[0_1px_4px_rgba(0,0,0,0.06)]'}`
          }
        `}
      >
        <div className={isUser ? '' : 'prose-mona'}>
          {content ? (
            isUser ? (
              <span>{content}</span>
            ) : (
              <ReactMarkdown
                remarkPlugins={REMARK_PLUGINS}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
                  ),
                }}
              >{content}</ReactMarkdown>
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

        {isStreaming && status && (
          <div className={`flex items-center gap-2 mt-2 text-[13px] italic ${isDark ? 'text-emerald-400/60' : 'text-emerald-600/60'}`}>
            <motion.span
              className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-emerald-400/60' : 'bg-emerald-500/50'}`}
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
            />
            {status}
          </div>
        )}

        {isStreaming && content && !status && (
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

        {/* Open in Excel button for tabular data */}
        {csvData && (
          <button
            onClick={handleExcelExport}
            className={`
              mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium
              transition-colors duration-150 cursor-pointer border
              ${isDark
                ? 'text-white/50 hover:text-white/80 border-white/[0.1] hover:bg-white/[0.06]'
                : 'text-gray-500 hover:text-gray-700 border-gray-200 hover:bg-gray-50'
              }
            `}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="8" y1="13" x2="16" y2="13" />
              <line x1="8" y1="17" x2="16" y2="17" />
            </svg>
            Open in Excel
          </button>
        )}
      </div>
    </motion.div>
  );
}

export default MessageBubble;
