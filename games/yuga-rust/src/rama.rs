//! Rama's native bow, step and ward on the same 20 Hz clock and receivers as Hanuman.
use crate::{combat::Receiver, world::World};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, VecDeque},
    sync::Arc,
};

type Point = [f32; 2];
// Original player.gd constants. The kit spends an arrow only after an accepted primary draw.
const MAGAZINE: u8 = 12;
const RELOAD_TICKS: u32 = 32;
const KIT: &str = include_str!("../../yuga-native/assets/design/rama-ability-kit.json");
const MUZZLES: &str = include_str!("../assets/rama-muzzles.json");
const STAGES: [(&str, &str, &str); 5] = [
    ("kodanda", "draw", "release"),
    ("piercing_dawn", "piercing_draw", "piercing_release"),
    ("measured_step", "dash", "dash_release"),
    ("guardian_circle", "circle_draw", "circle_release"),
    ("dawn_volley", "volley_draw", "volley_release"),
];
fn ticks(s: f64) -> u32 {
    (s * 20.0 - 1e-8).ceil().max(0.0) as u32
}
fn sub(a: Point, b: Point) -> Point {
    [a[0] - b[0], a[1] - b[1]]
}
fn add(a: Point, b: Point) -> Point {
    [a[0] + b[0], a[1] + b[1]]
}
fn scale(a: Point, v: f32) -> Point {
    [a[0] * v, a[1] * v]
}
fn len(a: Point) -> f32 {
    a[0].hypot(a[1])
}
fn norm(a: Point) -> Option<Point> {
    let l = len(a);
    (l.is_finite() && l > 1e-4).then(|| scale(a, 1. / l))
}
fn at(a: Point, b: Point, t: f32) -> Point {
    add(a, scale(sub(b, a), t))
}
fn rotate(dir: Point, radians: f32) -> Point {
    let (s, c) = radians.sin_cos();
    [dir[0] * c + dir[1] * s, dir[1] * c - dir[0] * s]
}
fn contact_fraction(start: Point, end: Point, center: Point, radius: f32) -> Option<f32> {
    let d = sub(end, start);
    let offset = sub(start, center);
    let dot = |a: Point, b: Point| a[0] * b[0] + a[1] * b[1];
    let c = dot(offset, offset) - radius * radius;
    if c <= 0.0 {
        return Some(0.0);
    }
    let a = dot(d, d);
    if a < 1e-12 {
        return None;
    }
    let b = dot(offset, d);
    let discr = b * b - a * c;
    if discr < 0.0 {
        return None;
    }
    let value = (-b - discr.sqrt()) / a;
    (0.0..=1.0).contains(&value).then_some(value)
}

#[derive(Deserialize)]
struct Kit {
    schema_version: u8,
    hero_id: String,
    max_casts: usize,
    history_capacity: usize,
    abilities: Vec<Rule>,
}
#[derive(Deserialize)]
struct Rule {
    id: String,
    label: String,
    description: String,
    color: String,
    windup_s: f64,
    recovery_s: f64,
    cooldown_s: f64,
    range_m: f32,
    #[serde(default)]
    radius_m: f32,
    #[serde(default)]
    speed_mps: f32,
    #[serde(default)]
    damage: f64,
    #[serde(default)]
    max_hits: usize,
    #[serde(default)]
    movement_s: f64,
    #[serde(default)]
    active_s: f64,
    #[serde(default)]
    shield: f64,
    #[serde(default)]
    heal_per_s: f64,
    #[serde(default)]
    yaw_offsets_rad: Vec<f32>,
    #[serde(default)]
    stagger_s: f64,
}
impl Rule {
    fn release(&self) -> u32 {
        ticks(self.windup_s)
    }
    fn unlock(&self) -> u32 {
        ticks(self.windup_s + self.recovery_s)
    }
    fn end(&self) -> u32 {
        let travel = if self.speed_mps > 0. {
            f64::from(self.range_m / self.speed_mps) + self.stagger_s * 2.
        } else {
            0.
        };
        ticks(self.windup_s + self.recovery_s.max(travel + 0.28).max(self.active_s + 0.30))
    }
}
struct Arrow {
    index: usize,
    direction: Point,
    origin: Point,
    pos: Point,
    y: f32,
    delay: u32,
    fired: bool,
    done: bool,
    hits: Vec<u32>,
}
struct Cast {
    id: u32,
    slot: usize,
    start: u32,
    origin: Point,
    aim: Point,
    target: Point,
    arrows: Vec<Arrow>,
    wards: BTreeMap<u32, (f64, u32, u32)>,
    step_from: Point,
}
impl Cast {
    fn state(&self, r: &Rule, now: u32) -> Value {
        let age = now.saturating_sub(self.start);
        let (phase, clip, p) = if age < r.release() {
            (
                "windup",
                STAGES[self.slot].1,
                age as f32 / r.release() as f32,
            )
        } else if age < r.unlock() {
            (
                "recovery",
                STAGES[self.slot].2,
                (age - r.release()) as f32 / (r.unlock() - r.release()).max(1) as f32,
            )
        } else {
            ("active", STAGES[self.slot].2, 1.)
        };
        json!({"cast_id":self.id,"slot":self.slot,"id":r.id,"phase":phase,"age_ticks":age,"motion":clip,
            "motion_phase_normalized":p,"origin":self.origin,"aim":self.aim,"target":self.target,"radius_m":r.radius_m,
            "release_tick":r.release(),"impact_tick":r.release(),"recovery_tick":r.unlock(),
            "field_end_tick":ticks(r.windup_s+r.active_s),"end_tick":r.end()})
    }
}

pub struct Rama {
    rules: Vec<Arc<Rule>>,
    muzzles: BTreeMap<String, [f32; 3]>,
    max_casts: usize,
    history: usize,
    now: u32,
    generation: u32,
    next: u32,
    seq: u32,
    actor: Receiver,
    receivers: Vec<Receiver>,
    aim: Point,
    movement: Point,
    cooldowns: [u32; 5],
    ammo: u8,
    reload_at: Option<u32>,
    casts: Vec<Cast>,
    events: VecDeque<Value>,
}
impl Rama {
    pub fn load() -> Result<Self, String> {
        let kit: Kit = serde_json::from_str(KIT).map_err(|e| e.to_string())?;
        let muzzles: BTreeMap<String, [f32; 3]> =
            serde_json::from_str(MUZZLES).map_err(|e| e.to_string())?;
        if kit.schema_version != 1
            || kit.hero_id != "rama"
            || kit.abilities.len() != STAGES.len()
            || kit.max_casts == 0
            || kit.history_capacity == 0
        {
            return Err("Invalid native Rama kit".into());
        }
        for (index, r) in kit.abilities.iter().enumerate() {
            if r.id != STAGES[index].0
                || r.release() == 0
                || r.unlock() <= r.release()
                || r.range_m <= 0.
                || (r.speed_mps > 0. && (r.max_hits == 0 || !muzzles.contains_key(&r.id)))
            {
                return Err(format!("Invalid Rama action {}", r.id));
            }
        }
        let mut s = Self {
            rules: kit.abilities.into_iter().map(Arc::new).collect(),
            muzzles,
            max_casts: kit.max_casts,
            history: kit.history_capacity,
            now: 0,
            generation: 0,
            next: 0,
            seq: 0,
            actor: Receiver::new(0, "sun", [0., -55.], 300., 300.),
            receivers: vec![],
            aim: [0., 1.],
            movement: [0., 0.],
            cooldowns: [0; 5],
            ammo: MAGAZINE,
            reload_at: None,
            casts: vec![],
            events: VecDeque::new(),
        };
        s.reset();
        Ok(s)
    }
    pub fn reset(&mut self) {
        self.interrupt();
        self.generation = self.generation.wrapping_add(1);
        self.now = 0;
        self.next = 0;
        self.seq = 0;
        self.actor = Receiver::new(0, "sun", [0., -55.], 300., 300.);
        self.receivers.clear();
        self.aim = [0., 1.];
        self.movement = [0., 0.];
        self.restore_after_respawn();
        self.events.clear();
    }
    pub fn restore_after_respawn(&mut self) {
        self.ammo = MAGAZINE;
        self.reload_at = None;
        self.cooldowns = [0; 5];
    }
    pub fn reload(&mut self) -> bool {
        if self.actor.hp <= 0.
            || self.ammo == MAGAZINE
            || self.reload_at.is_some()
            || self.locked().is_some()
        {
            return false;
        }
        self.reload_at = Some(self.now + RELOAD_TICKS);
        true
    }
    pub fn actor(&self) -> &Receiver {
        &self.actor
    }
    pub fn actor_mut(&mut self) -> &mut Receiver {
        &mut self.actor
    }
    pub fn set_receivers(&mut self, units: Vec<Receiver>) {
        self.receivers = units;
    }
    pub fn receivers(&self) -> &[Receiver] {
        &self.receivers
    }
    pub fn set_aim(&mut self, aim: Point) {
        if let Some(d) = norm(aim) {
            self.aim = d
        }
    }
    pub fn set_position(&mut self, position: Point) {
        if position.iter().all(|v| v.is_finite()) {
            self.actor.pos = position;
        }
    }
    fn locked(&self) -> Option<&Cast> {
        self.casts
            .iter()
            .find(|c| self.now - c.start < self.rules[c.slot].unlock())
    }
    pub fn cast(&mut self, slot: usize, ground: Point, w: &World) -> Result<(), String> {
        if slot == 0 && self.ammo == 0 && ground.iter().all(|x| x.is_finite()) {
            self.reload();
            return Err("Reload the bow".into());
        }
        let r = self.rules.get(slot).ok_or("Unknown Rama action")?;
        if self.actor.hp <= 0.
            || self.locked().is_some()
            || self.reload_at.is_some()
            || self.casts.len() >= self.max_casts
            || self.cooldowns[slot] > self.now
        {
            return Err("Action unavailable".into());
        }
        let origin = self.actor.pos;
        if !w.ground_target_allowed(origin) || !ground.iter().all(|x| x.is_finite()) {
            return Err("Invalid ground or origin".into());
        }
        let target = match slot {
            2 => w
                .step_endpoint(origin, norm(self.movement).unwrap_or(self.aim), r.range_m)
                .ok_or("No room to step")?,
            3 => {
                if !w.ground_target_allowed(ground)
                    || len(sub(ground, origin)) > r.range_m + 1e-6
                    || !w.clear_line(origin, ground)
                {
                    return Err("Choose visible ground in range".into());
                }
                ground
            }
            _ => add(origin, scale(self.aim, r.range_m)),
        };
        let mut arrows = Vec::new();
        if r.speed_mps > 0. {
            let offsets: &[f32] = if r.yaw_offsets_rad.is_empty() {
                &[0.]
            } else {
                &r.yaw_offsets_rad
            };
            for (index, &angle) in offsets.iter().enumerate() {
                arrows.push(Arrow {
                    index,
                    direction: rotate(self.aim, angle),
                    origin,
                    pos: origin,
                    y: 1.25,
                    delay: ticks(index as f64 * r.stagger_s),
                    fired: false,
                    done: false,
                    hits: Vec::new(),
                });
            }
        }
        if slot == 0 {
            self.ammo -= 1;
        }
        self.next += 1;
        let cast = Cast {
            id: self.next,
            slot,
            start: self.now,
            origin,
            aim: self.aim,
            target,
            arrows,
            wards: BTreeMap::new(),
            step_from: origin,
        };
        self.cooldowns[slot] = self.now + ticks(r.cooldown_s);
        self.record("begin", &cast, vec![], Value::Null);
        self.casts.push(cast);
        Ok(())
    }
    fn record(&mut self, kind: &str, c: &Cast, receipts: Vec<Value>, detail: Value) {
        self.seq += 1;
        let mut e = json!({"generation":self.generation,"seq":self.seq,"tick":self.now,"kind":kind,"cast_id":c.id,
            "id":self.rules[c.slot].id,"slot":c.slot,"origin":c.origin,"target":c.target,"aim":c.aim,"receipts":receipts});
        if let Some(fields) = detail.as_object() {
            e.as_object_mut().unwrap().extend(fields.clone())
        }
        if self.events.len() == self.history {
            self.events.pop_front();
        }
        self.events.push_back(e);
    }
    pub fn cancel_windup(&mut self) -> bool {
        if let Some(i) = self
            .casts
            .iter()
            .position(|c| self.now - c.start < self.rules[c.slot].release())
        {
            let c = self.casts.remove(i);
            self.record("cancel", &c, vec![], json!({"reason":"interrupt"}));
            return true;
        }
        false
    }
    pub fn interrupt(&mut self) {
        for mut c in std::mem::take(&mut self.casts) {
            self.clear_ward(&mut c);
            self.record("cancel", &c, vec![], json!({"reason":"interrupt"}));
        }
    }
    fn clear_ward(&mut self, c: &mut Cast) {
        for u in std::iter::once(&mut self.actor).chain(self.receivers.iter_mut()) {
            if let Some(&(before, until, owned)) = c.wards.get(&u.id) {
                if u.shield_until == owned && u.shield <= self.rules[c.slot].shield {
                    u.shield = if until > self.now {
                        u.shield.min(before)
                    } else {
                        0.
                    };
                    u.shield_until = if u.shield > 0. { until } else { 0 };
                }
            }
        }
        c.wards.clear();
    }
    fn ward(&mut self, c: &mut Cast, r: &Rule, w: &World, heal: f64) -> Vec<Value> {
        let mut receipts = vec![];
        let team = self.actor.team;
        let expiry = c.start + ticks(r.windup_s + r.active_s);
        for u in std::iter::once(&mut self.actor).chain(self.receivers.iter_mut()) {
            if u.team != team
                || u.hp <= 0.
                || len(sub(u.pos, c.target)) > r.radius_m
                || !w.clear_line(c.target, u.pos)
            {
                continue;
            }
            let (before, shield) = (u.hp, u.shield);
            if !c.wards.contains_key(&u.id) && u.shield < r.shield {
                c.wards
                    .insert(u.id, (u.shield, u.shield_until, expiry.max(u.shield_until)));
                u.shield = r.shield;
                u.shield_until = expiry.max(u.shield_until);
            }
            u.hp = (u.hp + heal).min(u.max_hp);
            if u.hp > before || u.shield > shield {
                receipts.push(json!({"unit_id":u.id,"kind":"guardian","health_before":before,"health_after":u.hp,
                    "shield_before":shield,"shield_after":u.shield,"healing_applied":u.hp-before}));
            }
        }
        receipts
    }
    fn release(&mut self, c: &mut Cast, r: &Rule, w: &World) -> bool {
        if c.slot == 0 {
            if len(sub(self.actor.pos, c.origin)) > 4.0
                || !w.clear_line_with_margin(c.origin, self.actor.pos, 0.05)
            {
                return false;
            }
            c.origin = self.actor.pos;
        }
        if !c.arrows.is_empty() {
            let [x, y, z] = self.muzzles[&r.id];
            let muzzle = add(
                c.origin,
                add(scale([c.aim[1], -c.aim[0]], x), scale(c.aim, z)),
            );
            if !w.clear_line_with_margin(c.origin, muzzle, 0.05) {
                return false;
            }
            for arrow in &mut c.arrows {
                arrow.origin = muzzle;
                arrow.pos = muzzle;
                arrow.y = y;
            }
        }
        self.record("release", c, vec![], Value::Null);
        if c.slot == 2 {
            let Some(target) = w.step_endpoint(
                self.actor.pos,
                sub(c.target, c.origin),
                len(sub(c.target, c.origin)),
            ) else {
                return false;
            };
            c.step_from = self.actor.pos;
            c.target = target;
            self.record(
                "impact",
                c,
                vec![],
                json!({"reason":"movement_accepted","position":target}),
            );
        } else if c.slot == 3 {
            let receipts = self.ward(c, r, w, 0.);
            self.record(
                "impact",
                c,
                receipts,
                json!({"reason":"field","position":c.target}),
            );
        }
        true
    }
    fn projectiles(&mut self, c: &mut Cast, r: &Rule, w: &World, flight: u32) {
        for index in 0..c.arrows.len() {
            let a = &mut c.arrows[index];
            if a.done || flight < a.delay {
                continue;
            }
            a.fired = true;
            let traveled = (flight - a.delay) as f32 * 0.05 * r.speed_mps;
            let start = a.pos;
            let end = add(a.origin, scale(a.direction, traveled.min(r.range_m)));
            let wall = w.segment_wall_fraction(start, end, r.radius_m);
            let mut contacts = vec![];
            for (j, u) in self.receivers.iter().enumerate() {
                if u.team == self.actor.team
                    || u.hp <= 0.
                    || a.hits.contains(&u.id)
                    || a.y > u.height + 2.7
                {
                    continue;
                }
                if let Some(f) = contact_fraction(start, end, u.pos, u.radius + r.radius_m) {
                    if f < wall.unwrap_or(f32::INFINITY) {
                        contacts.push((f, u.id, j))
                    }
                }
            }
            contacts.sort_by(|a, b| a.0.total_cmp(&b.0).then(a.1.cmp(&b.1)));
            let mut impacts = vec![];
            for (f, id, j) in contacts {
                let u = &mut self.receivers[j];
                let (before, shield) = (u.hp, u.shield);
                u.damage(r.damage);
                a.hits.push(id);
                a.done = a.hits.len() >= r.max_hits;
                let pos = at(start, end, f);
                impacts.push((vec![json!({"unit_id":id,"kind":"damage","health_before":before,"health_after":u.hp,
                    "shield_before":shield,"shield_after":u.shield,"damage_applied":before+shield-u.hp-u.shield})],
                    json!({"projectile_index":index,"position":pos,"reason":"unit","terminal":a.done})));
                if a.done {
                    a.pos = pos;
                    break;
                }
            }
            if !a.done {
                a.pos = at(start, end, wall.unwrap_or(1.));
                if wall.is_some() || traveled + 1e-6 >= r.range_m {
                    a.done = true;
                    impacts.push((
                        vec![],
                        json!({"projectile_index":index,"position":a.pos,
                        "reason": if wall.is_some(){"wall"}else{"range"},"terminal":true}),
                    ));
                }
            }
            for (receipts, detail) in impacts {
                self.record("impact", c, receipts, detail);
            }
        }
    }
    pub fn tick(&mut self, movement: Point, w: &World) {
        self.movement = if movement.iter().all(|v| v.is_finite()) {
            movement
        } else {
            [0., 0.]
        };
        let movable = self.locked().is_none_or(|c| c.slot == 0);
        if self.actor.hp > 0. && movable {
            if let Some(dir) = norm(self.movement) {
                self.actor.pos = w.move_actor(
                    self.actor.pos,
                    scale(dir, 0.25 * len(self.movement).min(1.)),
                );
            }
        }
        self.now += 1;
        if self.reload_at.is_some_and(|deadline| self.now >= deadline) {
            self.ammo = MAGAZINE;
            self.reload_at = None;
        }
        self.actor.expire_shield(self.now);
        for u in &mut self.receivers {
            u.expire_shield(self.now);
        }
        if self.actor.hp <= 0. {
            self.interrupt();
            return;
        }
        let mut casts = std::mem::take(&mut self.casts);
        casts.retain_mut(|c| {
            let r = Arc::clone(&self.rules[c.slot]);
            let age = self.now - c.start;
            if age == r.release() && !self.release(c, &r, w) {
                self.record("cancel", c, vec![], json!({"reason":"blocked_at_release"}));
                return false;
            }
            if age >= r.release() {
                let flight = age - r.release();
                self.projectiles(c, &r, w, flight);
                if c.slot == 2 && flight > 0 && flight <= ticks(r.movement_s) {
                    let next = at(
                        c.step_from,
                        c.target,
                        (flight as f64 * 0.05 / r.movement_s).min(1.) as f32,
                    );
                    self.actor.pos = w.move_actor(self.actor.pos, sub(next, self.actor.pos));
                } else if c.slot == 3 && flight > 0 && age <= ticks(r.windup_s + r.active_s) {
                    let receipts = self.ward(c, &r, w, r.heal_per_s * 0.05);
                    if !receipts.is_empty() {
                        self.record("tick", c, receipts, Value::Null)
                    }
                    if age == ticks(r.windup_s + r.active_s) {
                        self.clear_ward(c);
                    }
                }
            }
            if age == r.unlock() {
                self.record("recovery", c, vec![], Value::Null)
            }
            if age >= r.end() {
                self.clear_ward(c);
                self.record("end", c, vec![], Value::Null);
                return false;
            }
            true
        });
        self.casts = casts;
    }
    pub fn snapshot(&self) -> Value {
        let mut actor = self.actor.state();
        actor["aim"] = json!(self.aim);
        actor["y"] = json!(0.);
        let abilities:Vec<_>=self.rules.iter().enumerate().map(|(i,r)|json!({"slot":i,"id":r.id,"label":r.label,
            "description":r.description,"motion":STAGES[i].1,"motion_phase":1.0,"color":r.color,
            "cooldown_ticks":self.cooldowns[i].saturating_sub(self.now),"full_cooldown_ticks":ticks(r.cooldown_s)})).collect();
        let projectiles:Vec<_>=self.casts.iter().flat_map(|c|c.arrows.iter().filter(|a|a.fired&&!a.done).map(|a|
            json!({"id":self.rules[c.slot].id,"cast_id":c.id,"index":a.index,"pos":a.pos,"origin":a.origin,
                "y":a.y,"forward":a.direction,"color":self.rules[c.slot].color,"age_ticks":self.now-c.start-self.rules[c.slot].release()-a.delay}))).collect();
        let state = |c: &Cast| c.state(&self.rules[c.slot], self.now);
        json!({"hero_id":"rama","ammo":self.ammo,"max_ammo":MAGAZINE,
            "reload_ticks":self.reload_at.unwrap_or(0).saturating_sub(self.now),"generation":self.generation,"tick":self.now,"actor":actor,"abilities":abilities,
            "active":self.locked().map(state),"casts":self.casts.iter().map(state).collect::<Vec<_>>(),"events":self.events,
            "targets":self.receivers.iter().map(Receiver::state).collect::<Vec<_>>(),"projectiles":projectiles,
            "enemies":self.receivers.iter().filter(|u|u.team!=self.actor.team).count(),
            "defeated":self.receivers.iter().filter(|u|u.team!=self.actor.team&&u.hp<=0.).count()})
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn setup() -> (Rama, World) {
        let mut rama = Rama::load().unwrap();
        rama.set_position([0., 0.]);
        (rama, World::load().unwrap())
    }
    fn advance(r: &mut Rama, w: &World, n: u32) {
        for _ in 0..n {
            r.tick([0., 0.], w);
        }
    }
    fn unit(id: u32, team: &'static str, p: Point) -> Receiver {
        Receiver::new(id, team, p, 150., 150.)
    }
    #[test]
    fn moving_draw_uses_native_release_tick_and_sampled_muzzle() {
        let (mut r, w) = setup();
        r.set_receivers(vec![unit(1, "moon", [1., 5.])]);
        r.cast(0, [0., 0.], &w).unwrap();
        for _ in 0..3 {
            r.tick([1., 0.], &w);
        }
        assert!(r.events.iter().all(|v| v["kind"] != "release"));
        r.tick([1., 0.], &w);
        assert_eq!(r.actor().pos, [1., 0.]);
        let p = r.snapshot()["projectiles"][0].clone();
        assert_eq!(p["age_ticks"], 0);
        assert!((p["y"].as_f64().unwrap() - 1.561).abs() < 0.001);
        assert!(p["origin"][0].as_f64().unwrap() > 0.90);
        advance(&mut r, &w, 4);
        assert_eq!(r.receivers[0].hp, 122.);
        assert!(r.cast(0, [0., 0.], &w).is_ok());
    }
    #[test]
    fn piercing_sorts_contacts_hits_six_unique_enemies_and_skips_allies_on_both_teams() {
        for (team, enemy) in [("sun", "moon"), ("moon", "sun")] {
            let (mut r, w) = setup();
            r.actor_mut().team = team;
            let mut units: Vec<_> = (1..=7)
                .rev()
                .map(|i| unit(i, enemy, [0., 1. + 2. * i as f32]))
                .collect();
            units.push(unit(42, team, [0., 4.]));
            r.set_receivers(units);
            r.cast(1, [0., 0.], &w).unwrap();
            advance(&mut r, &w, 32);
            for u in r.receivers() {
                assert_eq!(u.hp, if u.id <= 6 { 80. } else { 150. });
            }
            assert!(r.cast(1, [0., 0.], &w).is_err());
            assert!(r.cast(0, [0., 0.], &w).is_ok());
            let hit_ids: Vec<_> = r
                .events
                .iter()
                .filter_map(|e| e["receipts"].get(0).map(|v| v["unit_id"].as_u64().unwrap()))
                .collect();
            assert_eq!(hit_ids, vec![1, 2, 3, 4, 5, 6]);
        }
    }
    #[test]
    fn solid_cover_wins_and_missed_arrows_retire_at_range() {
        let (mut r, w) = setup();
        r.set_position([0., -28.]);
        r.set_aim([-1., 0.]);
        r.set_receivers(vec![unit(7, "moon", [-26., -28.])]);
        r.cast(1, [0., -28.], &w).unwrap();
        advance(&mut r, &w, 35);
        assert_eq!(r.receivers[0].hp, 150.);
        assert!(r.events.iter().any(|e| e["reason"] == "wall"));
        r.reset();
        r.cast(0, [0., 0.], &w).unwrap();
        advance(&mut r, &w, 30);
        assert!(r.events.iter().any(|e| e["reason"] == "range"));
        assert!(r.casts.is_empty());
    }
    #[test]
    fn guardian_heals_for_exactly_90_ticks_and_restores_previous_ward() {
        let (mut r, w) = setup();
        r.actor_mut().hp = 220.;
        let mut ally = unit(8, "sun", [1., 1.]);
        ally.hp = 90.;
        ally.shield = 20.;
        ally.shield_until = 160;
        r.set_receivers(vec![ally, unit(9, "moon", [1., 2.])]);
        r.cast(3, [0., 0.], &w).unwrap();
        advance(&mut r, &w, 11);
        assert_eq!(r.actor().shield, 55.);
        assert_eq!(r.receivers[0].shield, 55.);
        advance(&mut r, &w, 20);
        assert_eq!(r.actor().hp, 230.);
        assert_eq!(r.receivers[0].hp, 100.);
        advance(&mut r, &w, 70);
        assert_eq!(r.actor().shield, 0.);
        assert_eq!(r.receivers[0].shield, 20.);
        assert_eq!(r.receivers[0].shield_until, 160);
        assert_eq!(r.receivers[0].hp, 135.);
        assert_eq!(r.receivers[1].shield, 0.);
        advance(&mut r, &w, 20);
        assert_eq!(r.receivers[0].hp, 135.);
    }
    #[test]
    fn step_preserves_heading_and_volley_has_three_staggered_live_arrows() {
        let (mut r, w) = setup();
        r.tick([1., 0.], &w);
        let x = r.actor().pos[0];
        r.cast(2, [0., 0.], &w).unwrap();
        advance(&mut r, &w, 1);
        assert_eq!(r.actor().pos[0], x);
        advance(&mut r, &w, 9);
        assert!((r.actor().pos[0] - x - 4.5).abs() < 1e-5);
        assert_eq!(r.aim, [0., 1.]);
        r.cast(4, [0., 0.], &w).unwrap();
        advance(&mut r, &w, 18);
        assert_eq!(r.snapshot()["projectiles"], json!([]));
        for count in 1..=3 {
            advance(&mut r, &w, if count == 1 { 1 } else { 2 });
            assert_eq!(r.snapshot()["projectiles"].as_array().unwrap().len(), count);
        }
        advance(&mut r, &w, 32);
        assert!(r.casts.is_empty());
    }
    #[test]
    fn interrupt_cleans_fields_and_arrows_and_rejected_input_preserves_cooldowns() {
        let (mut r, w) = setup();
        assert!(r.cast(3, [600., 0.], &w).is_err());
        assert!(r.cast(1, [f32::NAN, 0.], &w).is_err());
        assert_eq!(r.cooldowns, [0; 5]);
        r.cast(3, [0., 0.], &w).unwrap();
        advance(&mut r, &w, 18);
        r.cast(1, [0., 0.], &w).unwrap();
        assert!(r.cancel_windup());
        assert_eq!(r.casts.len(), 1);
        assert_eq!(r.actor().shield, 55.);
        r.interrupt();
        assert!(r.casts.is_empty());
        assert_eq!(r.actor().shield, 0.);
        assert!(r.cooldowns[1] > r.now);
        r.reset();
        assert_eq!(r.cooldowns, [0; 5]);
        assert_eq!(r.seq, 0);
    }
    #[test]
    fn magazine_pays_on_accept_and_reload_blocks_all_casts_for_32_ticks() {
        let (mut r, w) = setup();
        assert!(!r.reload());
        for remaining in (0..12).rev() {
            r.cast(0, [0., 0.], &w).unwrap();
            assert_eq!(r.ammo, remaining);
            assert!(r.cast(0, [0., 0.], &w).is_err());
            assert_eq!(r.ammo, remaining);
            assert!(!r.reload());
            advance(&mut r, &w, 8);
        }
        assert!(r.cast(0, [0., 0.], &w).is_err());
        assert_eq!(r.snapshot()["reload_ticks"], 32);
        advance(&mut r, &w, 31);
        assert!(r.cast(1, [0., 0.], &w).is_err());
        assert_eq!(r.ammo, 0);
        advance(&mut r, &w, 1);
        assert_eq!(r.ammo, 12);
        r.cast(0, [0., 0.], &w).unwrap();
        assert!(r.cancel_windup());
        assert!(r.reload());
        r.restore_after_respawn();
        assert_eq!(r.ammo, 12);
        assert!(r.reload_at.is_none());
    }

    #[test]
    fn projectile_damage_reaches_a_live_receiver_in_the_match() {
        use crate::battle::{Battle, CastInput, Hero};
        let world = World::load().unwrap();
        let mut battle = Battle::load(&world, Hero::Rama, None).unwrap();
        let start = battle.snapshot(0).unwrap();
        let pos: Point = serde_json::from_value(start["actor"]["pos"].clone()).unwrap();
        let target = battle
            .army
            .receivers()
            .into_iter()
            .filter(|u| u.team == "moon" && world.clear_line(pos, u.pos))
            .min_by(|a, b| len(sub(a.pos, pos)).total_cmp(&len(sub(b.pos, pos))))
            .unwrap();
        battle
            .cast(
                0,
                CastInput {
                    slot: 1,
                    ground: target.pos,
                    aim: sub(target.pos, pos),
                },
                &world,
            )
            .unwrap();
        for _ in 0..40 {
            battle.step(&[], &world);
            let state = battle.snapshot(0).unwrap();
            if let Some(receipt) = state["events"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|e| e["id"] == "piercing_dawn")
                .flat_map(|e| e["receipts"].as_array().unwrap())
                .find(|r| r["kind"] == "damage")
            {
                let id = receipt["unit_id"].as_u64().unwrap() as u32;
                let hit = state["army"]["units"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .find(|u| u["id"] == id)
                    .unwrap();
                assert!(
                    hit["hp"].as_f64().unwrap() <= receipt["health_after"].as_f64().unwrap() + 1e-4
                );
                let available = receipt["health_before"].as_f64().unwrap()
                    + receipt["shield_before"].as_f64().unwrap();
                assert!(available > 0.);
                assert_eq!(receipt["damage_applied"], available.min(70.));
                return;
            }
        }
        panic!("No authoritative army hit for the frontline shot");
    }

    #[test]
    fn replay_3600_ticks_preserves_bounds_and_order() {
        let (wmut, w) = setup();
        let mut a = wmut;
        let (mut b, _) = setup();
        for r in [&mut a, &mut b] {
            r.set_receivers(
                (1..=64)
                    .map(|i| {
                        unit(
                            i,
                            if i % 3 == 0 { "sun" } else { "moon" },
                            [(i % 8) as f32 - 4., (i / 8) as f32 * 2.],
                        )
                    })
                    .collect(),
            );
            for n in 0..3600 {
                if n % 5 == 0 {
                    let _ = r.cast((n / 5) % 5, r.actor().pos, &w);
                }
                r.tick([0., 0.], &w);
                assert!(
                    r.casts.len() <= 12
                        && r.events.len() <= 96
                        && r.receivers.iter().all(|u| (0.0..=u.max_hp).contains(&u.hp))
                );
            }
            assert!(r.next > 50 && r.seq as usize > r.history * 4);
            assert_eq!(r.events.len(), r.history);
            println!(
                "3600 ticks, {} accepted casts, {} recorded events",
                r.next, r.seq
            );
        }
        assert_eq!(a.snapshot(), b.snapshot());
    }
}
