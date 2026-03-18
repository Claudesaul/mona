import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTheme } from '@/hooks/useTheme';
import ParticleWaves from './components/backgrounds/ParticleWaves';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import AboutPage from './components/AboutPage';

type Page = 'chat' | 'about';

function generateSessionId(): string {
  return `s_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function App() {
  const [sessionId] = useState(() => generateSessionId());
  const [page, setPage] = useState<Page>('chat');
  const { theme, toggleTheme } = useTheme();
  const [transitioning, setTransitioning] = useState(false);
  const prevTheme = useRef(theme);

  const isDark = theme === 'dark';

  // Trigger a brief fade overlay on theme change
  useEffect(() => {
    if (prevTheme.current !== theme) {
      setTransitioning(true);
      const timer = setTimeout(() => setTransitioning(false), 350);
      prevTheme.current = theme;
      return () => clearTimeout(timer);
    }
  }, [theme]);

  return (
    <div className={`h-screen w-screen flex flex-col overflow-hidden ${isDark ? 'bg-[#09090b]' : 'bg-[#fafafa]'}`}>
      <ParticleWaves theme={theme} />
      <Header theme={theme} toggleTheme={toggleTheme} page={page} onNavigate={setPage} />
      <main className="relative z-10 flex-1 flex flex-col min-h-0">
        <AnimatePresence mode="wait">
          {page === 'chat' ? (
            <ChatWindow key="chat" sessionId={sessionId} theme={theme} />
          ) : (
            <AboutPage key="about" theme={theme} />
          )}
        </AnimatePresence>
      </main>

      {/* Theme transition overlay — quick fade to soften the switch */}
      <AnimatePresence>
        {transitioning && (
          <motion.div
            className="fixed inset-0 pointer-events-none z-50"
            style={{ background: isDark ? '#09090b' : '#fafafa' }}
            initial={{ opacity: 0.7 }}
            animate={{ opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
