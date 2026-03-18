import { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { Theme } from '@/hooks/useTheme';

/** Style 5: Sinusoidal gradient wave ribbons flowing across the viewport */
function WaveRibbons({ theme }: { theme: Theme }) {
  const isDark = theme === 'dark';
  const base = isDark ? '#09090b' : '#fafafa';

  const ribbons = useMemo(() => {
    const w = 1600;
    const makeWave = (amp: number, freq: number, yOffset: number, phase: number) => {
      const points: string[] = [];
      for (let x = 0; x <= w; x += 8) {
        const y = yOffset + Math.sin((x / w) * Math.PI * 2 * freq + phase) * amp;
        points.push(`${x},${y}`);
      }
      return points;
    };

    const makePath = (amp: number, freq: number, yOffset: number, phase: number, thickness: number) => {
      const top = makeWave(amp, freq, yOffset - thickness / 2, phase);
      const bottom = makeWave(amp, freq, yOffset + thickness / 2, phase + 0.3);
      return `M${top.join(' L')} L${bottom.reverse().join(' L')} Z`;
    };

    const makePath2 = (amp: number, freq: number, yOffset: number, phase: number, thickness: number) => {
      const top = makeWave(amp, freq, yOffset - thickness / 2, phase + 1.5);
      const bottom = makeWave(amp, freq, yOffset + thickness / 2, phase + 1.8);
      return `M${top.join(' L')} L${bottom.reverse().join(' L')} Z`;
    };

    return [
      { d1: makePath(35, 1.5, 300, 0, 40), d2: makePath2(35, 1.5, 300, 0, 40),
        color: isDark ? 'rgba(16,185,129,0.12)' : 'rgba(16,185,129,0.08)', dur: 10, blur: 14 },
      { d1: makePath(25, 2, 380, 1, 35), d2: makePath2(25, 2, 380, 1, 35),
        color: isDark ? 'rgba(5,150,105,0.1)' : 'rgba(5,150,105,0.07)', dur: 14, blur: 12 },
      { d1: makePath(45, 1, 460, 2, 50), d2: makePath2(45, 1, 460, 2, 50),
        color: isDark ? 'rgba(52,211,153,0.08)' : 'rgba(52,211,153,0.06)', dur: 18, blur: 16 },
      { d1: makePath(20, 2.5, 340, 0.5, 30), d2: makePath2(20, 2.5, 340, 0.5, 30),
        color: isDark ? 'rgba(20,184,166,0.06)' : 'rgba(20,184,166,0.05)', dur: 12, blur: 10 },
    ];
  }, [isDark]);

  return (
    <div className="fixed inset-0 z-0 overflow-hidden" style={{ background: base }}>
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1600 800"
        preserveAspectRatio="xMidYMid slice"
      >
        {ribbons.map((r, i) => (
          <motion.path
            key={i}
            d={r.d1}
            fill={r.color}
            filter={`blur(${r.blur}px)`}
            animate={{ d: [r.d1, r.d2, r.d1] }}
            transition={{ duration: r.dur, repeat: Infinity, ease: 'easeInOut' }}
          />
        ))}
      </svg>

      {/* Subtle grid underneath */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: isDark
            ? `linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
               linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)`
            : `linear-gradient(rgba(0,0,0,0.02) 1px, transparent 1px),
               linear-gradient(90deg, rgba(0,0,0,0.02) 1px, transparent 1px)`,
          backgroundSize: '64px 64px',
        }}
      />

      <div className="absolute inset-0" style={{
        background: `radial-gradient(ellipse 65% 55% at 50% 45%, transparent 0%, ${base} 100%)`,
      }} />
      <div className="noise" />
    </div>
  );
}

export default WaveRibbons;
