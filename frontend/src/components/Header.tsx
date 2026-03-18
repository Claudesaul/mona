import { useState } from 'react';
import { motion } from 'framer-motion';
import MonumentalLeaf from './MonumentalLeaf';
import ThemeToggle from './ThemeToggle';
import type { Theme } from '@/hooks/useTheme';

interface HeaderProps {
  theme: Theme;
  toggleTheme: () => void;
  page: 'chat' | 'about';
  onNavigate: (page: 'chat' | 'about') => void;
}

function Header({ theme, toggleTheme, page, onNavigate }: HeaderProps) {
  const isDark = theme === 'dark';
  const [logoHover, setLogoHover] = useState(false);

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="relative z-20 w-full px-6 sm:px-10 h-16 flex items-center"
    >
      <div className="w-full max-w-4xl mx-auto flex items-center justify-between">
        {/* Left: Logo — hover shows gradient text + leaf glow */}
        <motion.button
          onClick={() => onNavigate('chat')}
          onMouseEnter={() => setLogoHover(true)}
          onMouseLeave={() => setLogoHover(false)}
          className="flex items-center gap-3 cursor-pointer group relative"
          whileTap={{ scale: 0.95 }}
        >
          <div className="relative z-10">
            <MonumentalLeaf size={16} animated={logoHover} />
          </div>
          <span
            className={`relative z-10 text-2xl font-bold tracking-tight transition-none ${logoHover ? 'text-gradient-flow' : isDark ? 'text-white' : 'text-gray-900'}`}
            style={{ letterSpacing: '-0.03em', fontFamily: "'Inter', sans-serif" }}
          >
            Mona
          </span>
        </motion.button>

        {/* Center: Nav links */}
        <nav className="flex items-center gap-1">
          {(['chat', 'about'] as const).map((p) => (
            <button
              key={p}
              onClick={() => onNavigate(p)}
              className={`
                px-4 py-1.5 rounded-full text-[13px] font-medium transition-all duration-200 cursor-pointer capitalize
                ${page === p
                  ? isDark ? 'bg-white/[0.1] text-white' : 'bg-black/[0.06] text-gray-900'
                  : isDark ? 'text-white/40 hover:text-white/70 hover:bg-white/[0.05]' : 'text-gray-400 hover:text-gray-700 hover:bg-black/[0.03]'
                }
              `}
            >
              {p}
            </button>
          ))}
        </nav>

        {/* Right: Theme toggle + Status */}
        <div className="flex items-center gap-2">
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />

          <div className={`
            hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-md border
            ${isDark ? 'bg-white/[0.05] border-white/[0.07]' : 'bg-white/80 border-gray-200/60'}
          `}>
            <div className="relative">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping opacity-40" />
            </div>
            <span className={`text-[11px] font-medium ${isDark ? 'text-white/45' : 'text-gray-400'}`}>Online</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
}

export default Header;
