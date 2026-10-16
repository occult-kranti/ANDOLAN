export interface Building { id: string; x: number; z: number; width: number; depth: number; height: number; color: string; style?: string }
export interface Landmark { id: string; name: string; x: number; z: number; radius: number }
export const WORLD = {
  bounds: 100, roadWidth: 13, roads: [-48, 0, 48], spawn: { x: -52, z: 48 },
  landmarks: [
    { id: 'garage', name: 'Yusuf’s Garage', x: -60, z: 48, radius: 8 },
    { id: 'board', name: 'The Newsroom', x: -68, z: 43, radius: 6 },
    { id: 'clinic', name: 'Night Clinic', x: 52, z: -48, radius: 9 },
    { id: 'archive', name: 'City Records', x: 48, z: -66, radius: 8 },
    { id: 'mill', name: 'Mill Ward', x: -48, z: -68, radius: 8 },
    { id: 'radio', name: 'Open Frequency', x: 65, z: 0, radius: 8 },
    { id: 'square', name: 'Assembly Square', x: 0, z: 66, radius: 8 },
    { id: 'civic', name: 'Public Hearing', x: 0, z: 82, radius: 8 },
    { id: 'river', name: 'River Steps', x: 82, z: 48, radius: 8 },
  ] satisfies Landmark[],
  buildings: [
    { id: 'market-a', x: -24, z: 23, width: 25, depth: 24, height: 13, color: '#b67d55' },
    { id: 'market-b', x: 24, z: 22, width: 24, depth: 24, height: 16, color: '#c9a36b' },
    { id: 'market-c', x: -24, z: -24, width: 24, depth: 24, height: 18, color: '#8b9b8c' },
    { id: 'market-d', x: 24, z: -24, width: 24, depth: 24, height: 12, color: '#b67b62' },
    { id: 'northwest-a', x: -74, z: -22, width: 25, depth: 23, height: 20, color: '#9c8d79' },
    { id: 'northwest-b', x: -74, z: -75, width: 24, depth: 24, height: 16, color: '#8f8073' },
    { id: 'northeast-a', x: 73, z: -24, width: 25, depth: 23, height: 20, color: '#b3b4a0' },
    { id: 'northeast-b', x: 74, z: -77, width: 24, depth: 20, height: 24, color: '#bc946c' },
    { id: 'southwest-a', x: -24, z: 75, width: 24, depth: 23, height: 18, color: '#b78e7b' },
    { id: 'southeast-a', x: 24, z: 75, width: 24, depth: 23, height: 18, color: '#a1b3a8' },
    { id: 'southwest-b', x: -73, z: 77, width: 24, depth: 20, height: 12, color: '#c4b187' },
    { id: 'southeast-b', x: 74, z: 76, width: 24, depth: 22, height: 21, color: '#b1a28c' },
    { id: 'north-mid-a', x: -24, z: -75, width: 24, depth: 22, height: 18, color: '#adb49b' },
    { id: 'north-mid-b', x: 24, z: -75, width: 24, depth: 22, height: 16, color: '#9ea6ae' },
  ] satisfies Building[],
  obstacles: [
    { id: 'garage-back', x: -80, z: 48, width: 0.5, depth: 23, height: 7.6 },
    { id: 'garage-north', x: -69.5, z: 36.7, width: 21, depth: 0.4, height: 7.6 },
    { id: 'garage-south', x: -69.5, z: 59.3, width: 21, depth: 0.4, height: 7.6 },
    { id: 'clinic-back', x: 79, z: -48, width: 0.5, depth: 17, height: 7 },
    { id: 'clinic-wing', x: 70, z: -58, width: 18, depth: 3, height: 7 },
    { id: 'civic-back', x: 0, z: 96, width: 29, depth: 5, height: 11 },
  ],
};
export const landmark = (id: string) => WORLD.landmarks.find(p => p.id === id);
export const isBlocked = (x: number, z: number, radius = 0.5) => Math.abs(x) + radius > WORLD.bounds || Math.abs(z) + radius > WORLD.bounds || [...WORLD.buildings, ...WORLD.obstacles].some(b => Math.abs(x - b.x) < b.width / 2 + radius && Math.abs(z - b.z) < b.depth / 2 + radius);
