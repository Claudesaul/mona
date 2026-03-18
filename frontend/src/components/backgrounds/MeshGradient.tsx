import { motion } from 'framer-motion';
import type { Theme } from '@/hooks/useTheme';

/** Style 2: Slow-morphing liquid blobs — macOS Sonoma wallpaper feel */
function MeshGradient({ theme }: { theme: Theme }) {
  const isDark = theme === 'dark';
  const base = isDark ? '#09090b' : '#fafafa';
  const mult = isDark ? 1 : 0.6;

  const blobs = [
    { color: `rgba(16,185,129,${0.18 * mult})`, size: 550, x: '15%', y: '10%', dur: 30,
      ax: [0, 120, -60, 80, 0], ay: [0, -100, 70, -40, 0], as: [1, 1.12, 0.88, 1.06, 1] },
    { color: `rgba(5,150,105,${0.14 * mult})`, size: 650, x: '60%', y: '20%', dur: 38,
      ax: [0, -80, 50, -100, 0], ay: [0, 60, -80, 30, 0], as: [1, 0.92, 1.1, 0.95, 1] },
    { color: `rgba(52,211,153,${0.1 * mult})`, size: 500, x: '40%', y: '55%', dur: 34,
      ax: [0, 70, -40, 90, 0], ay: [0, -50, 80, -60, 0], as: [1, 1.08, 0.9, 1.05, 1] },
    { color: `rgba(20,184,166,${0.08 * mult})`, size: 600, x: '75%', y: '65%', dur: 42,
      ax: [0, -60, 40, -30, 0], ay: [0, 40, -60, 50, 0], as: [1, 0.95, 1.08, 0.92, 1] },
    { color: `rgba(6,95,70,${0.15 * mult})`, size: 750, x: '25%', y: '70%', dur: 36,
      ax: [0, 50, -80, 60, 0], ay: [0, -30, 50, -40, 0], as: [1, 1.05, 0.93, 1.02, 1] },
  ];

  return (
    <div className="fixed inset-0 z-0 overflow-hidden" style={{ background: base }}>
      {blobs.map((b, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: b.size, height: b.size, left: b.x, top: b.y,
            background: `radial-gradient(circle, ${b.color}, transparent 70%)`,
            filter: 'blur(120px)',
          }}
          animate={{ x: b.ax, y: b.ay, scale: b.as }}
          transition={{ duration: b.dur, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
      <div className="absolute inset-0" style={{
        background: `radial-gradient(ellipse 65% 55% at 50% 45%, transparent 0%, ${base} 100%)`,
      }} />
      <div className="noise" />
    </div>
  );
}

export default MeshGradient;
