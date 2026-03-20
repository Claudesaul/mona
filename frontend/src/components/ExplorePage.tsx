import { motion } from 'framer-motion';
import { Database, TrendingUp, Package, Warehouse, Users } from 'lucide-react';
import type { Theme } from '@/hooks/useTheme';

interface ExplorePageProps {
  theme: Theme;
  onAskQuestion: (question: string) => void;
}

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

interface Section {
  title: string;
  source: string;
  icon: React.ReactNode;
  questions: string[];
}

const sections: Section[] = [
  {
    title: 'Revenue & Sales',
    source: 'Snowflake',
    icon: <TrendingUp size={16} />,
    questions: [
      'What was total revenue last week?',
      'Top 10 locations by revenue this month',
      'Revenue and gross margin by product category',
      'Which routes generated the most revenue yesterday?',
      'Compare this week vs last week revenue',
      'What are our highest revenue items?',
    ],
  },
  {
    title: 'Orders & Picking',
    source: 'LightSpeed',
    icon: <Package size={16} />,
    questions: [
      "What's today's order status breakdown?",
      'How many orders are currently being picked?',
      'Which routes have the most orders today?',
      'Average pick time by route today',
      'How many items were staged today?',
      'Show me order volume by route this week',
    ],
  },
  {
    title: 'Fill Rate & Stock Health',
    source: 'OOS Database',
    icon: <Database size={16} />,
    questions: [
      'Which locations have the worst fill rate?',
      'Top spoilage items in the last 14 days',
      'What items have the highest shrinkage?',
      'Show me weekly OOS trends',
      'Which locations are predicted to have stock shortages?',
      'What are the fastest selling items right now?',
      'Sell-through percentage by category',
      'Which coils have the highest demand per day?',
    ],
  },
  {
    title: 'Warehouse Inventory',
    source: 'Level',
    icon: <Warehouse size={16} />,
    questions: [
      'What items are below reorder point?',
      'Show me current warehouse inventory levels',
      'Recent purchase orders this week',
      'Which items have the lowest days of supply?',
      'What did we receive from vendors this week?',
      'Items with zero quantity on hand',
    ],
  },
  {
    title: 'CRM & Accounts',
    source: 'Salesforce',
    icon: <Users size={16} />,
    questions: [
      'How many open tasks are there by account?',
      'Show me the sales pipeline',
      'Recent equipment installs this month',
      'How many customer vs prospect accounts do we have?',
      'Open opportunities by stage',
      'Tasks due this week',
    ],
  },
];

function ExplorePage({ theme, onAskQuestion }: ExplorePageProps) {
  const isDark = theme === 'dark';
  const text = isDark ? 'text-white/55' : 'text-gray-500';
  const heading = isDark ? 'text-white' : 'text-gray-900';

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-16 sm:py-20">
        {/* Header */}
        <motion.div className="mb-12" {...fadeUp} transition={{ duration: 0.6 }}>
          <h1
            className={`text-3xl sm:text-4xl font-bold tracking-tight text-center mb-3 ${heading}`}
            style={{ letterSpacing: '-0.03em' }}
          >
            What can you ask?
          </h1>
          <p className={`text-[15px] leading-relaxed text-center max-w-lg mx-auto ${text}`}>
            Mona connects to 5 databases. Click any question to try it, or use these as inspiration for your own.
          </p>
        </motion.div>

        {/* Sections */}
        <div className="space-y-10">
          {sections.map((section, si) => (
            <motion.section
              key={section.title}
              {...fadeUp}
              transition={{ duration: 0.5, delay: 0.05 * si }}
            >
              {/* Section header */}
              <div className="flex items-center gap-2.5 mb-4">
                <div className={`${isDark ? 'text-emerald-400/70' : 'text-emerald-600'}`}>
                  {section.icon}
                </div>
                <h2 className={`text-sm font-semibold uppercase tracking-wider ${isDark ? 'text-emerald-400/70' : 'text-emerald-600'}`}>
                  {section.title}
                </h2>
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${isDark ? 'bg-white/[0.05] text-white/30' : 'bg-gray-100 text-gray-400'}`}>
                  {section.source}
                </span>
              </div>

              {/* Question grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {section.questions.map((q) => (
                  <button
                    key={q}
                    onClick={() => onAskQuestion(q)}
                    className={`
                      text-left px-4 py-3 rounded-xl text-[14px] leading-snug border cursor-pointer
                      transition-all duration-150
                      ${isDark
                        ? 'text-white/50 bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.06] hover:text-white/80 hover:border-white/[0.12]'
                        : 'text-gray-500 bg-white border-gray-150 hover:bg-gray-50 hover:text-gray-800 hover:border-gray-300'
                      }
                    `}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </motion.section>
          ))}
        </div>

        {/* Footer hint */}
        <motion.p
          className={`text-center text-[12px] mt-14 ${isDark ? 'text-white/20' : 'text-gray-300'}`}
          {...fadeUp}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          These are just examples. Ask anything about your business data in plain English.
        </motion.p>
      </div>
    </div>
  );
}

export default ExplorePage;
