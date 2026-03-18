import { useEffect, useRef } from 'react';
import type { Theme } from '@/hooks/useTheme';

/** Style 3: Subtle grid with glowing energy traces traveling along lines */
function GridTraces({ theme }: { theme: Theme }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const cellSize = 60;
    const traces: { x: number; y: number; dx: number; dy: number; life: number; maxLife: number }[] = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const spawnTrace = () => {
      const horizontal = Math.random() > 0.5;
      const x = horizontal ? 0 : Math.floor(Math.random() * (canvas.width / cellSize)) * cellSize;
      const y = horizontal ? Math.floor(Math.random() * (canvas.height / cellSize)) * cellSize : 0;
      traces.push({
        x, y,
        dx: horizontal ? 2 + Math.random() * 2 : 0,
        dy: horizontal ? 0 : 2 + Math.random() * 2,
        life: 0,
        maxLife: 200 + Math.random() * 200,
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw grid
      const gridAlpha = isDark ? 0.04 : 0.06;
      ctx.strokeStyle = isDark ? `rgba(16,185,129,${gridAlpha})` : `rgba(16,185,129,${gridAlpha})`;
      ctx.lineWidth = 1;
      for (let x = 0; x <= canvas.width; x += cellSize) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = 0; y <= canvas.height; y += cellSize) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }

      // Radial mask — fade edges
      const grad = ctx.createRadialGradient(
        canvas.width / 2, canvas.height / 2, 0,
        canvas.width / 2, canvas.height / 2, canvas.width * 0.5
      );
      const base = isDark ? '9,9,11' : '250,250,250';
      grad.addColorStop(0, `rgba(${base},0)`);
      grad.addColorStop(0.7, `rgba(${base},0)`);
      grad.addColorStop(1, `rgba(${base},1)`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw traces
      for (let i = traces.length - 1; i >= 0; i--) {
        const t = traces[i];
        t.x += t.dx;
        t.y += t.dy;
        t.life++;

        const alpha = Math.max(0, 1 - t.life / t.maxLife);
        const trailLen = 80;

        ctx.save();
        const lineGrad = ctx.createLinearGradient(
          t.x - t.dx * trailLen, t.y - t.dy * trailLen, t.x, t.y
        );
        lineGrad.addColorStop(0, 'rgba(52,211,153,0)');
        lineGrad.addColorStop(1, `rgba(52,211,153,${0.6 * alpha})`);
        ctx.strokeStyle = lineGrad;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(16,185,129,0.5)';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(t.x - t.dx * trailLen, t.y - t.dy * trailLen);
        ctx.lineTo(t.x, t.y);
        ctx.stroke();
        ctx.restore();

        if (t.life > t.maxLife || t.x > canvas.width + 10 || t.y > canvas.height + 10) {
          traces.splice(i, 1);
        }
      }

      if (Math.random() < 0.015 && traces.length < 6) spawnTrace();
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, [isDark]);

  return (
    <div className="fixed inset-0 z-0" style={{ background: isDark ? '#09090b' : '#fafafa' }}>
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
      <div className="noise" />
    </div>
  );
}

export default GridTraces;
