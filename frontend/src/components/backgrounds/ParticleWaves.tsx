import { useEffect, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import type { Theme } from '@/hooks/useTheme';

/** Combined: Particles across full viewport + wave ribbons anchored to the bottom */
function ParticleWaves({ theme }: { theme: Theme }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDark = theme === 'dark';
  const base = isDark ? '#09090b' : '#fafafa';

  // Use ref for theme so canvas effect doesn't restart on theme change
  const themeRef = useRef(isDark);
  themeRef.current = isDark;

  // ─── Particles (canvas) — runs ONCE, reads theme from ref ───
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let mouseX = -1000, mouseY = -1000;

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);
    const onMouse = (e: MouseEvent) => { mouseX = e.clientX; mouseY = e.clientY; };
    window.addEventListener('mousemove', onMouse);

    const count = 140;
    const colors = ['16,185,129', '52,211,153', '5,150,105', '20,184,166'];
    const particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      size: 1 + Math.random() * 1.8,
      opacity: 0.15 + Math.random() * 0.3,
      color: colors[Math.floor(Math.random() * colors.length)],
      pulsePhase: Math.random() * Math.PI * 2,
    }));

    const connectDist = 90;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const dark = themeRef.current;

      for (const p of particles) {
        const dx = p.x - mouseX;
        const dy = p.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150 && dist > 0) {
          const force = (150 - dist) / 150 * 0.015;
          p.vx += (dx / dist) * force;
          p.vy += (dy / dist) * force;
        }

        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.999;
        p.vy *= 0.999;

        if (p.x < -10) p.x = canvas.width + 10;
        if (p.x > canvas.width + 10) p.x = -10;
        if (p.y < -10) p.y = canvas.height + 10;
        if (p.y > canvas.height + 10) p.y = -10;

        p.pulsePhase += 0.008;
        const pulse = 0.7 + 0.3 * Math.sin(p.pulsePhase);
        const alpha = p.opacity * pulse * (dark ? 1 : 0.65);

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color},${alpha})`;
        ctx.fill();
      }

      const connAlpha = dark ? 0.035 : 0.04;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d = dx * dx + dy * dy;
          if (d < connectDist * connectDist) {
            const a = (1 - Math.sqrt(d) / connectDist) * connAlpha;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(16,185,129,${a})`;
            ctx.lineWidth = 0.7;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouse);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once — theme read from ref

  // ─── Wave ribbons (SVG, bottom-anchored) ───
  const ribbons = useMemo(() => {
    const w = 1600;
    const makeWave = (amp: number, freq: number, yOff: number, phase: number) => {
      const pts: string[] = [];
      for (let x = 0; x <= w; x += 8) {
        pts.push(`${x},${yOff + Math.sin((x / w) * Math.PI * 2 * freq + phase) * amp}`);
      }
      return pts;
    };
    const makePath = (amp: number, freq: number, yOff: number, phase: number, thick: number) => {
      const top = makeWave(amp, freq, yOff - thick / 2, phase);
      const bot = makeWave(amp, freq, yOff + thick / 2, phase + 0.3);
      return `M${top.join(' L')} L${bot.reverse().join(' L')} Z`;
    };
    const makePath2 = (amp: number, freq: number, yOff: number, phase: number, thick: number) => {
      const top = makeWave(amp, freq, yOff - thick / 2, phase + 1.5);
      const bot = makeWave(amp, freq, yOff + thick / 2, phase + 1.8);
      return `M${top.join(' L')} L${bot.reverse().join(' L')} Z`;
    };

    return [
      { d1: makePath(30, 1.5, 600, 0, 45), d2: makePath2(30, 1.5, 600, 0, 45),
        color: isDark ? 'rgba(16,185,129,0.14)' : 'rgba(16,185,129,0.09)', dur: 10, blur: 16 },
      { d1: makePath(22, 2, 660, 1, 35), d2: makePath2(22, 2, 660, 1, 35),
        color: isDark ? 'rgba(5,150,105,0.1)' : 'rgba(5,150,105,0.07)', dur: 14, blur: 12 },
      { d1: makePath(40, 1, 720, 2, 55), d2: makePath2(40, 1, 720, 2, 55),
        color: isDark ? 'rgba(52,211,153,0.08)' : 'rgba(52,211,153,0.06)', dur: 18, blur: 18 },
      { d1: makePath(18, 2.5, 640, 0.5, 28), d2: makePath2(18, 2.5, 640, 0.5, 28),
        color: isDark ? 'rgba(20,184,166,0.06)' : 'rgba(20,184,166,0.04)', dur: 12, blur: 10 },
    ];
  }, [isDark]);

  return (
    <div className="fixed inset-0 z-0 overflow-hidden transition-colors duration-500" style={{ background: base }}>
      {/* Particle canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }} />

      {/* Wave ribbons — bottom */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1600 800"
        preserveAspectRatio="xMidYMax slice"
        style={{ zIndex: 0 }}
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

      <div className="noise" style={{ zIndex: 2 }} />
    </div>
  );
}

export default ParticleWaves;
