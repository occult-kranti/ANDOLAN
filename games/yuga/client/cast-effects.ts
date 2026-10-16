import * as pc from 'playcanvas';
import type { ArenaSnapshot, Actor, AbilityMechanic } from '../shared/types';
import { heroById } from '../shared/heroes';
import { RenderKit, clamp, RAD } from './render-kit';

interface CastVisual { root: pc.Entity; progress: pc.Entity; detail: pc.Entity; key: string }

/** Telegraphs are drawn only from server-owned cast state, never from a pressed ability button. */
export class CastEffects {
  private readonly views = new Map<string, CastVisual>();
  constructor(private readonly kit: RenderKit, private readonly parent: pc.Entity) {}

  private create(actor: Actor, hostile: boolean): CastVisual {
    const cast = actor.cast!, ability = heroById(actor.heroId).abilities[cast.slot];
    const root = new pc.Entity(`windup ${cast.mechanic}`); this.parent.addChild(root);
    const team = this.kit.material('telegraph team', actor.team === 'sun' ? '#ffc36c' : '#6ce4f4', .7);
    const glow = this.kit.material(`cast ${cast.mechanic}`, ability.color, .8);
    const warning = this.kit.material('hostile telegraph', '#ff8b77', .7);
    const detail = new pc.Entity('cast silhouette'); root.addChild(detail);
    const radius = cast.mechanic === 'dawn-volley' ? 1.3 : ability.radius;
    this.kit.ring(root, team, radius, .09, .055, 48);
    const progress = this.kit.ring(root, glow, radius - .16, .065, .065, 48);
    // Triangles warn enemies; paired flat bars mark friendly support. Shape survives colour loss.
    for (let i = 0; i < 8; i++) {
      const a = i / 8 * Math.PI * 2, x = Math.sin(a) * radius, z = Math.cos(a) * radius;
      if (hostile) {
        const tip = this.kit.shape(root, 'cone', warning, x, .09, z, .38, .5, .03);
        tip.setLocalEulerAngles(90, a * RAD, 0);
      } else {
        const bar = this.kit.shape(root, 'box', team, x, .08, z, .32, .02, .09); bar.setLocalEulerAngles(0, a * RAD, 0);
      }
    }
    if (cast.mechanic === 'dawn-volley') {
      for (const angle of [-.12, 0, .12]) {
        const end = { x: Math.sin(angle) * 4, y: 1.2, z: Math.cos(angle) * 4 };
        this.kit.line(detail, glow, { x: 0, y: 1.2, z: .5 }, end, .025);
        const arrow = this.kit.shape(detail, 'cone', glow, end.x, end.y, end.z, .12, .4, .1);
        arrow.setLocalEulerAngles(90, angle * RAD, 0);
      }
    } else if (cast.mechanic === 'mountain-descent') {
      for (const angle of [0, Math.PI / 2]) {
        const slash = this.kit.shape(detail, 'box', glow, 0, .075, 0, 1.4, .025, .1); slash.setLocalEulerAngles(0, angle * RAD + 45, 0);
      }
      this.kit.line(detail, glow, { x: 0, y: .15, z: 0 }, { x: 0, y: 2.8, z: 0 }, .025);
      const diamond = this.kit.shape(detail, 'cone', glow, 0, 2.9, 0, .5, .7, .5); diamond.setLocalEulerAngles(180, 0, 0);
    } else {
      // An open petal canopy announces support without obscuring combat inside its footprint.
      for (let i = 0; i < 8; i++) {
        const a = i / 8 * Math.PI * 2;
        const leaf = this.kit.shape(detail, 'sphere', glow, Math.sin(a) * radius * .7, .065, Math.cos(a) * radius * .7, .22, .025, radius * .3);
        leaf.setLocalEulerAngles(0, a * RAD, 0);
      }
      this.kit.ring(detail, glow, radius * .5, .035, .065, 40);
    }
    return { root, progress, detail, key: `${cast.mechanic}/${actor.team}/${hostile}` };
  }

  update(snapshot: ArenaSnapshot, playerId: string | null, reducedMotion: boolean) {
    const localTeam = snapshot.actors.find(a => a.id === playerId)?.team;
    const live = new Set<string>();
    for (const actor of snapshot.actors) {
      const cast = actor.cast; if (!cast || actor.health <= 0) continue;
      live.add(actor.id);
      const hostile = !!localTeam && actor.team !== localTeam, key = `${cast.mechanic}/${actor.team}/${hostile}`;
      let v = this.views.get(actor.id);
      if (v?.key !== key) { v?.root.destroy(); v = this.create(actor, hostile); this.views.set(actor.id, v); }
      const center = cast.mechanic === 'mountain-descent' ? cast.target : cast.origin;
      v.root.setPosition(center.x, cast.mechanic === 'dawn-volley' ? actor.y : 0, center.z);
      v.root.setEulerAngles(0, cast.yaw * RAD, 0);
      const fraction = clamp((snapshot.time - cast.startedAt) / Math.max(.001, cast.releaseAt - cast.startedAt), 0, 1);
      // The outer boundary stays exact; the inner ring communicates preparation progress.
      const scale = .18 + .82 * fraction; v.progress.setLocalScale(scale, 1, scale);
      v.detail.setLocalPosition(0, reducedMotion || cast.mechanic !== 'mountain-descent' ? 0 : Math.sin(fraction * Math.PI) * .15, 0);
    }
    for (const [id, visual] of this.views) if (!live.has(id)) { visual.root.destroy(); this.views.delete(id); }
  }

  diagnostic(): { actorId: string; mechanic: AbilityMechanic }[] {
    return [...this.views].map(([actorId, view]) => ({ actorId, mechanic: view.key.split('/')[0] as AbilityMechanic }));
  }
  destroy() { for (const view of this.views.values()) view.root.destroy(); this.views.clear(); }
}
