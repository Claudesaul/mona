import type { Theme } from '@/hooks/useTheme';
import AuroraBorealis from './backgrounds/AuroraBorealis';
import MeshGradient from './backgrounds/MeshGradient';
import GridTraces from './backgrounds/GridTraces';
import ParticleField from './backgrounds/ParticleField';
import WaveRibbons from './backgrounds/WaveRibbons';
import ParticleWaves from './backgrounds/ParticleWaves';

export type BgStyle = 'aurora' | 'mesh' | 'grid' | 'particles' | 'waves' | 'particle-waves';

export const BG_OPTIONS: { id: BgStyle; label: string }[] = [
  { id: 'particle-waves', label: 'Particle Waves' },
  { id: 'aurora', label: 'Aurora' },
  { id: 'mesh', label: 'Mesh' },
  { id: 'grid', label: 'Grid' },
  { id: 'particles', label: 'Particles' },
  { id: 'waves', label: 'Waves' },
];

function BackgroundEffects({ theme, style }: { theme: Theme; style: BgStyle }) {
  switch (style) {
    case 'aurora': return <AuroraBorealis theme={theme} />;
    case 'mesh': return <MeshGradient theme={theme} />;
    case 'grid': return <GridTraces theme={theme} />;
    case 'particles': return <ParticleField theme={theme} />;
    case 'waves': return <WaveRibbons theme={theme} />;
    case 'particle-waves': return <ParticleWaves theme={theme} />;
    default: return <ParticleWaves theme={theme} />;
  }
}

export default BackgroundEffects;
