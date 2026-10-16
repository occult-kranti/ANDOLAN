import * as pc from 'playcanvas';

/** Original painted light field, convolved once for PBR gold/cloth; no downloaded HDR imagery. */
export function createOriginalEnvironment(app: pc.Application) {
  const canvas = document.createElement('canvas'); canvas.width = 256; canvas.height = 128;
  const context = canvas.getContext('2d'); if (!context) throw new Error('Environment canvas unavailable');
  const gradient = context.createLinearGradient(0, 0, 0, 128);
  gradient.addColorStop(0, '#819eb8'); gradient.addColorStop(.38, '#b5d2db');
  gradient.addColorStop(.53, '#f5dcbb'); gradient.addColorStop(.66, '#a5a08b'); gradient.addColorStop(1, '#5c706e');
  context.fillStyle = gradient; context.fillRect(0, 0, 256, 128);
  const glow = context.createRadialGradient(66, 40, 2, 66, 40, 37);
  glow.addColorStop(0, '#fff7df'); glow.addColorStop(.35, '#ffe9bc'); glow.addColorStop(1, 'rgba(255,225,180,0)');
  context.fillStyle = glow; context.fillRect(0, 0, 128, 90);
  context.fillStyle = '#d8e6e6'; context.fillRect(174, 33, 22, 18);
  const source = new pc.Texture(app.graphicsDevice, { name: 'original Sangam light field', width: 256, height: 128, projection: pc.TEXTUREPROJECTION_EQUIRECT, mipmaps: true });
  source.setSource(canvas);
  const lighting = pc.EnvLighting.generateLightingSource(source, { size: 64 });
  const atlas = pc.EnvLighting.generateAtlas(lighting, { size: 256, numReflectionSamples: 32, numAmbientSamples: 64 });
  app.scene.envAtlas = atlas;
  source.destroy(); lighting.destroy();
  let disposed = false;
  return { destroy() { if (disposed) return; disposed = true; app.scene.envAtlas = null; atlas.destroy(); } };
}
