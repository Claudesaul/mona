import { useCallback } from 'react';
import { motion } from 'framer-motion';
import { Download } from 'lucide-react';

interface DataTableProps {
  data: Record<string, unknown>[];
  title?: string;
}

function DataTable({ data, title }: DataTableProps) {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);

  const exportCsv = useCallback(() => {
    const header = columns.join(',');
    const rows = data.map((row) =>
      columns
        .map((col) => {
          const val = String(row[col] ?? '');
          // Escape commas and quotes
          return val.includes(',') || val.includes('"')
            ? `"${val.replace(/"/g, '""')}"`
            : val;
        })
        .join(',')
    );
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title || 'export'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, columns, title]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="my-3 rounded-xl border border-white/[0.08] bg-white/[0.03] overflow-hidden"
    >
      {/* Title bar */}
      {title && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.06]">
          <span className="text-xs font-medium text-mona-dark-300">{title}</span>
          <motion.button
            onClick={exportCsv}
            className="flex items-center gap-1.5 text-[11px] text-mona-dark-400 hover:text-mona-green-500 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Download size={12} />
            Export CSV
          </motion.button>
        </div>
      )}

      {/* No title - just show export */}
      {!title && (
        <div className="flex justify-end px-4 py-2 border-b border-white/[0.06]">
          <motion.button
            onClick={exportCsv}
            className="flex items-center gap-1.5 text-[11px] text-mona-dark-400 hover:text-mona-green-500 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Download size={12} />
            Export CSV
          </motion.button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-xs font-semibold text-mona-dark-300 bg-mona-green-500/[0.06] whitespace-nowrap border-b border-white/[0.06]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr
                key={i}
                className={`
                  border-b border-white/[0.04] hover:bg-white/[0.03] transition-colors
                  ${i % 2 === 0 ? 'bg-transparent' : 'bg-white/[0.015]'}
                `}
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-2 text-mona-dark-300 whitespace-nowrap max-w-[200px] truncate"
                  >
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

export default DataTable;
