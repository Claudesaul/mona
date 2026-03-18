import type { Theme } from '@/hooks/useTheme';

/** Style 1: Soft flowing curtains of green light — northern lights effect */
function AuroraBorealis({ theme }: { theme: Theme }) {
  const isDark = theme === 'dark';
  const base = isDark ? '#09090b' : '#fafafa';

  return (
    <div className="fixed inset-0 z-0 overflow-hidden" style={{ background: base }}>
      {/* Aurora blob 1 — bright emerald, slow drift */}
      <div
        className="absolute w-[600px] h-[400px] rounded-full"
        style={{
          top: '-10%', left: '10%',
          background: `radial-gradient(circle, ${isDark ? 'rgba(16,185,129,0.25)' : 'rgba(16,185,129,0.15)'}, transparent 70%)`,
          filter: 'blur(80px)',
          animation: 'aurora1 18s ease-in-out infinite',
        }}
      />
      {/* Aurora blob 2 — deep green */}
      <div
        className="absolute w-[500px] h-[350px] rounded-full"
        style={{
          top: '5%', right: '5%',
          background: `radial-gradient(circle, ${isDark ? 'rgba(5,150,105,0.2)' : 'rgba(5,150,105,0.12)'}, transparent 70%)`,
          filter: 'blur(80px)',
          animation: 'aurora2 24s ease-in-out infinite',
        }}
      />
      {/* Aurora blob 3 — teal accent */}
      <div
        className="absolute w-[700px] h-[300px] rounded-full"
        style={{
          top: '-5%', left: '30%',
          background: `radial-gradient(circle, ${isDark ? 'rgba(52,211,153,0.15)' : 'rgba(52,211,153,0.1)'}, transparent 70%)`,
          filter: 'blur(100px)',
          animation: 'aurora3 20s ease-in-out infinite',
        }}
      />
      {/* Aurora blob 4 — deep teal, slow */}
      <div
        className="absolute w-[450px] h-[350px] rounded-full"
        style={{
          top: '10%', left: '50%',
          background: `radial-gradient(circle, ${isDark ? 'rgba(20,184,166,0.12)' : 'rgba(20,184,166,0.08)'}, transparent 70%)`,
          filter: 'blur(90px)',
          animation: 'aurora4 28s ease-in-out infinite',
        }}
      />

      {/* Vignette */}
      <div className="absolute inset-0" style={{
        background: `radial-gradient(ellipse 70% 60% at 50% 40%, transparent 0%, ${base} 100%)`,
      }} />
      <div className="noise" />

      <style>{`
        @keyframes aurora1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(15%, 10%) scale(1.15); }
          66% { transform: translate(-10%, 5%) scale(0.9); }
        }
        @keyframes aurora2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(-12%, 8%) scale(1.1); }
          66% { transform: translate(8%, -5%) scale(0.95); }
        }
        @keyframes aurora3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-8%, 12%) scale(1.1); }
        }
        @keyframes aurora4 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(10%, -8%) scale(1.08); }
          66% { transform: translate(-15%, 5%) scale(0.92); }
        }
      `}</style>
    </div>
  );
}

export default AuroraBorealis;
