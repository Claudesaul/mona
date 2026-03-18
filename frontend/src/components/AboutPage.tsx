import { motion } from 'framer-motion';
import MonumentalLeaf from './MonumentalLeaf';
import type { Theme } from '@/hooks/useTheme';

interface AboutPageProps {
  theme: Theme;
}

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

function AboutPage({ theme }: AboutPageProps) {
  const isDark = theme === 'dark';
  const text = isDark ? 'text-white/55' : 'text-gray-500';
  const heading = isDark ? 'text-white' : 'text-gray-900';

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-xl mx-auto px-6 py-20 sm:py-28">
        {/* Header */}
        <motion.div className="mb-14" {...fadeUp} transition={{ duration: 0.6 }}>
          <div className="flex justify-center mb-6">
            <MonumentalLeaf size={40} />
          </div>
          <h1
            className={`text-3xl sm:text-4xl font-bold tracking-tight text-center mb-4 ${heading}`}
            style={{ letterSpacing: '-0.03em' }}
          >
            About Mona
          </h1>
          <p className={`text-[15px] leading-relaxed text-center max-w-md mx-auto ${text}`}>
            Mona is an AI assistant that answers questions about your business
            by querying your databases directly. No exports, no copy-pasting, no waiting.
          </p>
        </motion.div>

        {/* What it connects to */}
        <motion.section className="mb-12" {...fadeUp} transition={{ duration: 0.5, delay: 0.1 }}>
          <h2 className={`text-sm font-semibold uppercase tracking-wider mb-4 ${isDark ? 'text-emerald-400/70' : 'text-emerald-600'}`}>
            Connected to
          </h2>
          <ul className={`text-[15px] leading-relaxed space-y-2 ${text}`}>
            <li><strong className={heading}>LightSpeed/LEVEL</strong> — orders, fulfillment, warehouse inventory, and par levels</li>
            <li><strong className={heading}>OOS Database</strong> — fill rates and out-of-stock tracking</li>
            <li><strong className={heading}>Salesforce</strong> — accounts, contacts, tasks, cases, opportunities</li>
          </ul>
        </motion.section>

        {/* Tips */}
        <motion.section className="mb-12" {...fadeUp} transition={{ duration: 0.5, delay: 0.15 }}>
          <h2 className={`text-sm font-semibold uppercase tracking-wider mb-4 ${isDark ? 'text-emerald-400/70' : 'text-emerald-600'}`}>
            Tips
          </h2>
          <ul className={`text-[15px] leading-relaxed space-y-2 ${text}`}>
            <li>Be specific — "fill rate last Tuesday" beats "how are things"</li>
            <li>Follow up — Mona remembers context, so "now just top 5" works</li>
            <li>You can export any table result to CSV</li>
          </ul>
        </motion.section>

        {/* Footer */}
        <motion.div
          className="pt-8 border-t text-center"
          style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}
          {...fadeUp}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <p className={`text-[12px] ${isDark ? 'text-white/20' : 'text-gray-300'}`}>
            Built by the Data & Automation team at Monumental Markets
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export default AboutPage;
