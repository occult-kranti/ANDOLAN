//! The native Hanuman kit, evaluated at 20 Hz against the Rust practice world.
use crate::world::World;
use serde::Deserialize;
use serde_json::{json, Value};
use std::collections::VecDeque;

include!(concat!(env!("OUT_DIR"), "/motion_markers.rs"));

const KIT: &str = include_str!("../../yuga-native/assets/design/hanuman-ability-kit.json");
const HZ: u32 = 20;
const STEP: f32 = 1.0 / HZ as f32;
const WALK_SPEED: f32 = 5.0;
const SLOTS: [&str; 5] = ["primary", "ability_1", "ability_2", "ability_3", "ultimate"];
type Point = [f32; 2];

fn difference(a: Point, b: Point) -> Point {
    [a[0] - b[0], a[1] - b[1]]
}
fn add(a: Point, b: Point) -> Point {
    [a[0] + b[0], a[1] + b[1]]
}
fn scaled(a: Point, scale: f32) -> Point {
    [a[0] * scale, a[1] * scale]
}
fn length(a: Point) -> f32 {
    a[0].hypot(a[1])
}
fn finite(a: Point) -> bool {
    a.into_iter().all(f32::is_finite)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u32)]
pub enum GroundAim {
    Clear = 0,
    OutOfRange = 1,
    Obstructed = 2,
    InvalidOrigin = 3,
    Unavailable = 4,
}

impl GroundAim {
    fn message(self) -> &'static str {
        match self {
            Self::Clear => "",
            Self::OutOfRange => "Ground target is out of range",
            Self::Obstructed => "Cover blocks the ground target",
            Self::InvalidOrigin => "Cast origin is blocked or airborne",
            Self::Unavailable => "Choose a finite ground target",
        }
    }
}

#[derive(Deserialize)]
struct Kit {
    schema_version: u32,
    hero_id: String,
    abilities: Vec<Rule>,
}

#[derive(Deserialize)]
struct Rule {
    id: String,
    slot: String,
    label: String,
    description: String,
    motion: String,
    color: String,
    motion_phase: f32,
    #[serde(skip)]
    contact_phase: f32,
    cooldown_s: f64,
    timing: Timing,
    geometry: Geometry,
    effects: Vec<Effect>,
}

#[derive(Deserialize)]
struct Timing {
    windup_s: f64,
    travel_s: f64,
    active_s: f64,
    recovery_s: f64,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum Geometry {
    Sector {
        range_m: f32,
        half_angle_cos: f32,
        height_m: f32,
        direction: Option<String>,
    },
    Disk {
        target_range_m: f32,
        radius_m: f32,
        height_m: f32,
    },
    Movement {
        target_range_m: f32,
        clearance_m: f32,
    },
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum Effect {
    Damage {
        amount: f64,
        team: String,
    },
    DamageRate {
        amount_per_s: f64,
        team: String,
    },
    Heal {
        amount: f64,
        team: String,
        include_caster: bool,
    },
    Shield {
        amount: f64,
        duration_s: f64,
        team: String,
        include_caster: bool,
    },
}

fn ticks(seconds: f64) -> u32 {
    (seconds * HZ as f64).round() as u32
}

#[derive(Clone, Copy)]
struct Beats {
    release: u32,
    impact: u32,
    recovery: u32,
    field_end: u32,
}

impl Rule {
    fn beats(&self) -> Beats {
        let t = &self.timing;
        let release = ticks(t.windup_s);
        let impact = release + ticks(t.travel_s);
        Beats {
            release,
            impact,
            recovery: impact + ticks(t.recovery_s),
            field_end: impact + ticks(t.active_s),
        }
    }
}

impl Geometry {
    fn contains(
        &self,
        center: Point,
        aim: Point,
        position: Point,
        feet_y: f32,
        body_height: f32,
    ) -> bool {
        let offset = difference(position, center);
        let distance = length(offset);
        match self {
            Self::Sector {
                range_m,
                half_angle_cos,
                height_m,
                direction,
            } => {
                let dot = offset[0] * aim[0] + offset[1] * aim[1];
                let dot = if direction.as_deref() == Some("rear") {
                    -dot
                } else {
                    dot
                };
                feet_y <= *height_m
                    && feet_y + body_height >= -*height_m
                    && distance <= *range_m + 1e-6
                    && (distance < 1e-6 || dot >= (*half_angle_cos - 1e-6) * distance)
            }
            Self::Disk {
                radius_m, height_m, ..
            } => {
                feet_y <= *height_m
                    && feet_y + body_height >= -*height_m
                    && distance <= *radius_m + 1e-6
            }
            Self::Movement { .. } => false,
        }
    }
}

#[derive(Clone, Debug)]
pub struct Receiver {
    pub id: u32,
    pub team: &'static str,
    pub pos: Point,
    pub hp: f64,
    pub max_hp: f64,
    pub shield: f64,
    pub shield_until: u32,
    pub radius: f32,
    pub height: f32,
}

impl Receiver {
    pub fn new(id: u32, team: &'static str, pos: Point, hp: f64, max_hp: f64) -> Self {
        Self {
            id,
            team,
            pos,
            hp,
            max_hp,
            shield: 0.0,
            shield_until: 0,
            radius: 0.45,
            height: 1.8,
        }
    }
    pub fn state(&self) -> Value {
        json!({"id":self.id,"team":self.team,"pos":self.pos,"hp":self.hp,
            "max_hp":self.max_hp,"shield":self.shield,"alive":self.hp>0.0})
    }
    pub fn expire_shield(&mut self, now: u32) {
        if now >= self.shield_until {
            self.shield = 0.0;
        }
    }
    pub fn damage(&mut self, amount: f64) {
        let absorbed = self.shield.min(amount);
        self.shield -= absorbed;
        self.hp = (self.hp - (amount - absorbed)).max(0.);
    }
}

struct Cast {
    id: u32,
    slot: usize,
    start: u32,
    origin: Point,
    aim: Point,
    target: Point,
    landed_age: Option<u32>,
}

impl Cast {
    fn state(&self, rule: &Rule, now: u32) -> Value {
        let age = now - self.start;
        let beats = rule.beats();
        let contact = self.landed_age.unwrap_or(beats.impact);
        let release_pose = rule.motion_phase;
        let contact_pose = rule.contact_phase;
        let (phase, pose) = if age < beats.release {
            let fraction = age as f32 / beats.release as f32;
            ("windup", release_pose * fraction.min(0.999))
        } else if age < contact {
            let fraction = (age - beats.release) as f32 / (beats.impact - beats.release) as f32;
            (
                "travel",
                release_pose + (contact_pose - release_pose) * fraction.min(0.999),
            )
        } else if age < beats.recovery {
            let fraction = (age - contact) as f32 / (beats.recovery - beats.impact).max(1) as f32;
            (
                "recovery",
                contact_pose + (1. - contact_pose) * fraction.min(1.),
            )
        } else {
            ("active", 1.)
        };
        json!({"cast_id":self.id,"slot":self.slot,"id":rule.id,"phase":phase,"age_ticks":age,
            "motion":rule.motion,"motion_phase_normalized":pose,"landed_age_ticks":self.landed_age,"origin":self.origin,"aim":self.aim,"target":self.target,
            "release_tick":beats.release,"impact_tick":beats.impact,"recovery_tick":beats.recovery,
            "end_tick":beats.recovery.max(beats.field_end)})
    }
}

pub struct Combat {
    kit: Kit,
    now: u32,
    generation: u32,
    next_cast: u32,
    seq: u32,
    actor: Receiver,
    targets: Vec<Receiver>,
    target_elevations: Vec<(u32, f32)>,
    aim: Point,
    height: f32,
    cooldowns: [u32; 5],
    casts: Vec<Cast>,
    events: VecDeque<Value>,
}

impl Combat {
    pub fn load() -> Result<Self, String> {
        let mut kit: Kit = serde_json::from_str(KIT).map_err(|e| e.to_string())?;
        if kit.schema_version != 1 || kit.hero_id != "hanuman" || kit.abilities.len() != SLOTS.len()
        {
            return Err("Unsupported Hanuman kit".into());
        }
        for (rule, expected_slot) in kit.abilities.iter_mut().zip(SLOTS) {
            let (_, release, impact) = MOTION_MARKERS
                .iter()
                .find(|(name, _, _)| *name == rule.motion)
                .ok_or_else(|| format!("Missing animation markers for {}", rule.motion))?;
            if (rule.motion_phase - release).abs() > 1e-6
                || (rule.timing.travel_s > 0.0) != impact.is_some()
            {
                return Err(format!(
                    "Ability and animation markers disagree for {}",
                    rule.motion
                ));
            }
            rule.contact_phase = impact.unwrap_or(*release);
            let t = &rule.timing;
            if rule.slot != expected_slot
                || [
                    t.windup_s,
                    t.travel_s,
                    t.active_s,
                    t.recovery_s,
                    rule.cooldown_s,
                ]
                .into_iter()
                .any(|v| {
                    !v.is_finite()
                        || v < 0.0
                        || (v * f64::from(HZ) - (v * f64::from(HZ)).round()).abs() > 1e-6
                })
            {
                return Err(format!(
                    "Unsupported slot or off-grid authored timing for {}",
                    rule.id
                ));
            }
        }
        let mut s = Self {
            kit,
            now: 0,
            generation: 0,
            next_cast: 0,
            seq: 0,
            actor: Receiver::new(0, "sun", [0., -55.], 275., 300.),
            targets: Vec::new(),
            target_elevations: Vec::new(),
            aim: [0., 1.],
            height: 0.,
            cooldowns: [0; 5],
            casts: Vec::new(),
            events: VecDeque::new(),
        };
        s.reset();
        Ok(s)
    }

    pub fn reset(&mut self) {
        self.now = 0;
        self.generation = self.generation.wrapping_add(1);
        self.next_cast = 0;
        self.seq = 0;
        self.actor = Receiver::new(0, "sun", [0., -55.], 275., 300.);
        self.targets = vec![
            Receiver::new(1, "moon", [0., -52.5], 90., 90.),
            Receiver::new(2, "moon", [0., -58.], 90., 90.),
            Receiver::new(3, "moon", [2., -48.], 90., 90.),
            Receiver::new(4, "sun", [1., -51.5], 90., 90.),
        ];
        self.aim = [0., 1.];
        self.height = 0.0;
        self.target_elevations.clear();
        self.cooldowns = [0; 5];
        self.casts.clear();
        self.events.clear();
    }

    pub fn set_receivers(&mut self, targets: Vec<Receiver>) {
        self.targets = targets;
        self.target_elevations.clear();
    }

    pub(crate) fn set_receivers_with_elevations(
        &mut self,
        targets: Vec<Receiver>,
        elevations: &[(u32, f32)],
    ) {
        self.set_receivers(targets);
        self.target_elevations.extend_from_slice(elevations);
    }

    pub(crate) fn elevation(&self) -> f32 {
        self.height
    }

    pub fn receivers(&self) -> &[Receiver] {
        &self.targets
    }

    pub fn actor(&self) -> &Receiver {
        &self.actor
    }

    pub fn actor_mut(&mut self) -> &mut Receiver {
        &mut self.actor
    }

    pub fn interrupt(&mut self) {
        self.casts.clear();
        self.height = 0.;
    }

    pub fn set_position(&mut self, point: [f32; 2]) {
        self.actor.pos = point;
    }

    pub fn set_aim(&mut self, aim: Point) {
        let n = length(aim);
        if n.is_finite() && n > 0.0001 {
            self.aim = scaled(aim, 1. / n);
        }
    }

    fn locked(&self) -> Option<&Cast> {
        self.casts
            .iter()
            .find(|c| self.now - c.start < self.kit.abilities[c.slot].beats().recovery)
    }

    /// Checks spatial eligibility only. The server checks action locks and cooldowns on commit.
    pub fn ground_aim(
        &self,
        slot: usize,
        origin: Point,
        height: f32,
        ground: Point,
        world: &World,
    ) -> GroundAim {
        let Some(Geometry::Disk { target_range_m, .. }) =
            self.kit.abilities.get(slot).map(|r| &r.geometry)
        else {
            return GroundAim::Unavailable;
        };
        if !finite(ground) {
            return GroundAim::Unavailable;
        }
        if !height.is_finite() || height.abs() > 0.35 || !world.ground_target_allowed(origin) {
            return GroundAim::InvalidOrigin;
        }
        if length(difference(ground, origin)) > target_range_m + 1e-6 {
            return GroundAim::OutOfRange;
        }
        if !world.ground_target_allowed(ground) || !world.clear_line(origin, ground) {
            return GroundAim::Obstructed;
        }
        GroundAim::Clear
    }

    pub fn cast(&mut self, slot: usize, ground: Point, world: &World) -> Result<(), String> {
        let rule = self.kit.abilities.get(slot).ok_or("Unknown ability")?;
        if self.locked().is_some() || self.casts.len() >= 3 {
            return Err("Finish the current action".into());
        }
        if self.now < self.cooldowns[slot] {
            return Err("Ability is cooling down".into());
        }
        if !finite(ground) {
            return Err("Choose a finite ground target".into());
        }
        let origin = self.actor.pos;
        if !matches!(rule.geometry, Geometry::Disk { .. })
            && (!world.ground_target_allowed(origin) || self.height.abs() > 0.35)
        {
            return Err("Cast origin is blocked or airborne".into());
        }
        let target = match rule.geometry {
            Geometry::Disk { .. } => {
                let aim = self.ground_aim(slot, origin, self.height, ground, world);
                if aim != GroundAim::Clear {
                    return Err(aim.message().into());
                }
                ground
            }
            Geometry::Movement {
                target_range_m,
                clearance_m,
            } => world
                .vault_endpoint(origin, self.aim, target_range_m, clearance_m)
                .ok_or("There is no room to vault")?,
            Geometry::Sector { .. } => origin,
        };
        self.cooldowns[slot] = self.now + ticks(rule.cooldown_s);
        self.next_cast += 1;
        let cast = Cast {
            id: self.next_cast,
            slot,
            start: self.now,
            origin,
            aim: self.aim,
            target,
            landed_age: None,
        };
        self.record("begin", &cast, Vec::new());
        self.casts.push(cast);
        Ok(())
    }

    fn record(&mut self, kind: &str, c: &Cast, receipts: Vec<Value>) {
        self.seq += 1;
        if self.events.len() == 64 {
            self.events.pop_front();
        }
        self.events.push_back(
            json!({"generation":self.generation,"seq":self.seq,"kind":kind,
            "cast_id":c.id,"id":self.kit.abilities[c.slot].id,"slot":c.slot,"tick":self.now,
            "origin":c.origin,"target":c.target,"aim":c.aim,"receipts":receipts}),
        );
    }

    fn payload(&mut self, c: &Cast, world: &World, ongoing: bool) -> Vec<Value> {
        let rule = &self.kit.abilities[c.slot];
        let mut receipts = Vec::new();
        let faction = self.actor.team;
        let elevations = &self.target_elevations;
        let caster_height = self.height;
        for unit in self
            .targets
            .iter_mut()
            .chain(std::iter::once(&mut self.actor))
        {
            let is_caster = unit.id == 0;
            let y = if is_caster {
                caster_height
            } else {
                elevations
                    .iter()
                    .find(|(id, _)| *id == unit.id)
                    .map_or(0., |(_, height)| *height)
            };
            if unit.hp <= 0.
                || !rule
                    .geometry
                    .contains(c.target, c.aim, unit.pos, y, unit.height)
                || !world.clear_line(c.target, unit.pos)
            {
                continue;
            }
            let before = unit.hp;
            let shield_before = unit.shield;
            let mut accepted = false;
            for e in &rule.effects {
                match e {
                    Effect::Damage { amount, team }
                        if !ongoing && team == "enemy" && unit.team != faction =>
                    {
                        unit.damage(*amount);
                        accepted = true;
                    }
                    Effect::DamageRate { amount_per_s, team }
                        if ongoing && team == "enemy" && unit.team != faction =>
                    {
                        unit.damage(amount_per_s / f64::from(HZ));
                        accepted = true;
                    }
                    Effect::Heal {
                        amount,
                        team,
                        include_caster,
                    } if !ongoing
                        && team == "ally"
                        && unit.team == faction
                        && (!is_caster || *include_caster) =>
                    {
                        unit.hp = (unit.hp + amount).min(unit.max_hp);
                        accepted |= unit.hp > before;
                    }
                    Effect::Shield {
                        amount,
                        team,
                        include_caster,
                        duration_s,
                    } if !ongoing
                        && team == "ally"
                        && unit.team == faction
                        && (!is_caster || *include_caster) =>
                    {
                        unit.shield = unit.shield.max(*amount);
                        unit.shield_until = unit.shield_until.max(self.now + ticks(*duration_s));
                        accepted = true;
                    }
                    _ => {}
                }
            }
            if accepted {
                receipts.push(json!({"unit":unit.id,"damage":(before+shield_before-unit.hp-unit.shield).max(0.),
                "heal":(unit.hp-before).max(0.),"hp_after":unit.hp,"shield_after":unit.shield}));
            }
        }
        receipts
    }

    pub fn tick(&mut self, movement: Point, world: &World) {
        if self.locked().is_none() && finite(movement) {
            let magnitude = length(movement);
            if magnitude.is_finite() && magnitude > 0. {
                self.actor.pos = world.move_actor(
                    self.actor.pos,
                    scaled(movement, WALK_SPEED * STEP / magnitude.max(1.)),
                );
            }
        }
        self.now += 1;
        self.actor.expire_shield(self.now);
        for target in &mut self.targets {
            target.expire_shield(self.now);
        }
        let mut live = std::mem::take(&mut self.casts);
        live.retain_mut(|c| {
            let b = self.kit.abilities[c.slot].beats();
            let age = self.now - c.start;
            let vault = matches!(
                self.kit.abilities[c.slot].geometry,
                Geometry::Movement { .. }
            );
            if age == b.release {
                if let Geometry::Movement { clearance_m, .. } = self.kit.abilities[c.slot].geometry
                {
                    if !world.clear_line_with_margin(c.origin, c.target, clearance_m)
                        || length(difference(self.actor.pos, c.origin)) > 0.6
                    {
                        self.record("cancel", c, Vec::new());
                        return false;
                    }
                }
                self.record("release", c, Vec::new());
                if vault {
                    self.record("impact", c, Vec::new());
                }
            }
            if vault && c.landed_age.is_none() && (b.release..=b.impact).contains(&age) {
                let t = (age - b.release) as f32 / (b.impact - b.release) as f32;
                let next = add(c.origin, scaled(difference(c.target, c.origin), t));
                self.actor.pos = world.move_actor(self.actor.pos, difference(next, self.actor.pos));
                let arc_height = (length(difference(c.target, c.origin)) * 0.19).clamp(0.35, 1.55);
                if length(difference(self.actor.pos, next)) > 0.001 || age == b.impact {
                    c.landed_age = Some(age);
                    self.height = 0.;
                } else {
                    self.height = arc_height * 4.0 * t * (1. - t);
                }
            }
            if age == b.impact && !vault {
                let hits = self.payload(c, world, false);
                self.record("impact", c, hits);
            }
            if age > b.impact && age <= b.field_end {
                let hits = self.payload(c, world, true);
                self.record("tick", c, hits);
            }
            if age == b.recovery {
                self.record("recovery", c, Vec::new());
            }
            if age == b.recovery.max(b.field_end) {
                self.record("end", c, Vec::new());
                return false;
            }
            true
        });
        self.casts = live;
    }

    pub fn snapshot(&self) -> Value {
        let mut actor = self.actor.state();
        actor["aim"] = json!(self.aim);
        actor["y"] = json!(self.height);
        let phase = |c: &Cast| c.state(&self.kit.abilities[c.slot], self.now);
        let abilities: Vec<_> = self.kit.abilities.iter().enumerate().map(|(i,r)|json!({
            "id":r.id,"slot":i,"label":r.label,"description":r.description,"motion":r.motion,"motion_phase":r.motion_phase,
            "color":r.color,"cooldown_ticks":self.cooldowns[i].saturating_sub(self.now),"full_cooldown_ticks":ticks(r.cooldown_s)
        })).collect();
        let enemies = self
            .targets
            .iter()
            .filter(|t| t.team != self.actor.team)
            .count();
        let defeated = self
            .targets
            .iter()
            .filter(|t| t.team != self.actor.team && t.hp <= 0.)
            .count();
        json!({"generation":self.generation,"tick":self.now,"actor":actor,"targets":self.targets.iter().map(Receiver::state).collect::<Vec<_>>(),
            "active":self.locked().map(phase),"casts":self.casts.iter().map(phase).collect::<Vec<_>>(),
            "events":self.events,"abilities":abilities,"enemies":enemies,"defeated":defeated})
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    const NATIVE_CAPTURE: &str = include_str!(
        "../../yuga-native/docs/research/hanuman-ability-production/QA-integration.json"
    );
    fn setup() -> (Combat, World) {
        (Combat::load().unwrap(), World::load().unwrap())
    }
    fn advance(s: &mut Combat, w: &World, ticks: u32) {
        for _ in 0..ticks {
            s.tick([0., 0.], w);
        }
    }

    #[test]
    fn authored_height_bands_include_touching_capsules() {
        let (combat, _) = setup();
        let gada = &combat.kit.abilities[0].geometry;
        let center = [0., 0.];
        let aim = [0., 1.];
        let target = [0., 1.];
        assert!(gada.contains(center, aim, target, 1.4, 1.8));
        assert!(!gada.contains(center, aim, target, 1.4001, 1.8));

        let symmetric_band = Geometry::Disk {
            radius_m: 2.,
            height_m: 1.,
            target_range_m: 2.,
        };
        assert!(symmetric_band.contains(center, aim, target, -3., 2.));
        assert!(!symmetric_band.contains(center, aim, target, -3.0001, 2.));
    }

    #[test]
    fn replacing_receivers_defaults_their_elevation_to_ground() {
        let (mut combat, world) = setup();
        let target = Receiver::new(42, "moon", [0., -52.5], 100., 100.);
        combat.set_receivers_with_elevations(vec![target.clone()], &[(42, 2.)]);
        combat.set_receivers(vec![target]);
        combat.cast(0, [0., -55.], &world).unwrap();
        advance(&mut combat, &world, 5);
        assert_eq!(combat.receivers()[0].hp, 66.);
    }
    #[test]
    fn five_native_action_timelines_match_all_recorded_beats() {
        let native: Value = serde_json::from_str(NATIVE_CAPTURE).unwrap();
        for slot in 0..5 {
            let (mut s, w) = setup();
            let rule_id = s.kit.abilities[slot].id.clone();
            s.cast(slot, [0., -53.], &w).unwrap();
            assert!(s.cast(slot, [0., -53.], &w).is_err());
            advance(&mut s, &w, 60);
            let timeline: Vec<_> = s
                .events
                .iter()
                .map(|e| json!([e["kind"], e["tick"].as_u64().unwrap() * 50]))
                .collect();
            let scenarios = native["scenarios"].as_array().unwrap();
            let mut matched = 0;
            for row in scenarios.iter().filter(|row| row["id"] == rule_id) {
                assert_eq!(
                    Value::Array(timeline.clone()),
                    row["timeline_ms"],
                    "{rule_id}"
                );
                matched += 1;
            }
            assert_eq!(matched, 2);
            match slot {
                0 => assert_eq!(s.targets[0].hp, 56.),
                1 => {
                    assert_eq!(s.actor.shield, 48.);
                    assert_eq!(s.targets[3].shield, 48.);
                }
                2 => {
                    assert_eq!(s.height, 0.);
                    assert!((s.actor.pos[1] + 46.5).abs() < 1e-4);
                }
                3 => {
                    assert!((s.targets[1].hp - 46.).abs() < 1e-8);
                    assert_eq!(s.targets[0].hp, 90.);
                }
                4 => {
                    assert_eq!(s.targets[0].hp, 25.);
                    assert_eq!(s.actor.hp, 300.);
                }
                _ => unreachable!(),
            }
        }
    }
    #[test]
    fn active_field_releases_action_lock_and_preserves_one_impact() {
        let (mut s, w) = setup();
        s.cast(3, [0., -55.], &w).unwrap();
        advance(&mut s, &w, 17);
        assert!(s.locked().is_none());
        assert_eq!(s.casts.len(), 1);
        s.cast(0, [0., -55.], &w).unwrap();
        advance(&mut s, &w, 32);
        assert!(s.casts.is_empty());
        assert_eq!(s.events.iter().filter(|e| e["kind"] == "impact").count(), 2);
        assert_eq!(s.events.iter().filter(|e| e["kind"] == "tick").count(), 40);
    }
    #[test]
    fn rejection_cooldown_reset_and_bounded_history() {
        let (mut s, w) = setup();
        s.set_aim([f32::NAN, 1.]);
        assert_eq!(s.aim, [0., 1.]);
        s.tick([f32::NAN, 0.], &w);
        assert_eq!(s.actor.pos, [0., -55.]);
        assert!(s.cast(99, s.actor.pos, &w).is_err());
        assert!(s.cast(4, [f32::NAN, 0.], &w).is_err());
        assert!(s.cast(4, [0., 100.], &w).is_err());
        s.cast(0, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 11);
        assert!(s.cast(0, s.actor.pos, &w).is_err());
        advance(&mut s, &w, 1);
        for _ in 0..32 {
            s.cast(0, s.actor.pos, &w).unwrap();
            advance(&mut s, &w, 12);
        }
        assert_eq!(s.events.len(), 64);
        let generation = s.generation;
        s.reset();
        assert_eq!(s.generation, generation + 1);
        assert!(s.events.is_empty());
        assert_eq!(s.targets[0].hp, 90.);
        s.cast(4, [0., -55.], &w).unwrap();
        advance(&mut s, &w, 15);
        s.reset();
        advance(&mut s, &w, 30);
        assert!(s.events.is_empty());
        assert_eq!(s.targets[0].hp, 90.);
    }
    #[test]
    fn shield_expires_on_authority_tick_and_vault_has_visible_apex() {
        let (mut s, w) = setup();
        s.cast(1, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 66);
        assert_eq!(s.actor.shield, 48.);
        advance(&mut s, &w, 1);
        assert_eq!(s.actor.shield, 0.);
        assert_eq!(s.targets[3].shield, 0.);
        s.cast(2, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 8);
        assert!(s.height > 1.45 && s.height <= 1.55);
        let mid = s.actor.pos;
        s.tick([1., 0.], &w);
        assert_eq!(s.actor.pos[0], mid[0]);
        advance(&mut s, &w, 8);
        assert!(s.locked().is_none());
        assert_eq!(s.height, 0.);
    }

    #[test]
    fn interrupted_vault_clears_height_but_keeps_its_cooldown_and_history() {
        let (mut combat, world) = setup();
        combat.set_aim([1., 0.]);
        combat.cast(2, [0., -55.], &world).unwrap();
        advance(&mut combat, &world, 8);
        let airborne = combat.snapshot();
        assert!(airborne["actor"]["y"].as_f64().unwrap() > 0.35);
        let cooldown = airborne["abilities"][2]["cooldown_ticks"].clone();
        let events = airborne["events"].clone();

        combat.interrupt();
        combat.interrupt();
        let stopped = combat.snapshot();
        assert_eq!(stopped["actor"]["y"], 0.);
        assert!(stopped["active"].is_null());
        assert!(stopped["casts"].as_array().unwrap().is_empty());
        assert_eq!(stopped["abilities"][2]["cooldown_ticks"], cooldown);
        assert_eq!(stopped["events"], events);
        assert_eq!(
            combat.cast(2, [0., -55.], &world).unwrap_err(),
            "Ability is cooling down"
        );
        combat.cast(0, [0., -55.], &world).unwrap();
        advance(&mut combat, &world, 5);
        assert_eq!(combat.snapshot()["actor"]["y"], 0.);
    }
    #[test]
    fn motion_uses_authoritative_clip_markers_and_pause_does_not_advance() {
        for (slot, release, travel, release_pose, contact_pose) in [
            (0, 5, 0, 0.26, 0.26),
            (1, 7, 0, 0.5, 0.5),
            (2, 4, 9, 0.08, 0.72),
            (3, 9, 0, 0.5, 0.5),
            (4, 14, 9, 0.55, 0.78),
        ] {
            let (mut s, w) = setup();
            s.cast(slot, s.actor.pos, &w).unwrap();
            let pose = |s: &Combat| {
                s.snapshot()["active"]["motion_phase_normalized"]
                    .as_f64()
                    .unwrap()
            };
            assert_eq!(pose(&s), 0.);
            advance(&mut s, &w, release);
            assert!((pose(&s) - release_pose).abs() < 1e-6);
            let paused = s.snapshot();
            for _ in 0..12 {
                assert_eq!(s.snapshot(), paused);
            }
            advance(&mut s, &w, travel);
            assert!((pose(&s) - contact_pose).abs() < 1e-6);
            assert_eq!(s.snapshot()["active"]["phase"], "recovery");
        }
    }

    #[test]
    fn mountain_preview_matches_commit_at_range_cover_and_landing_edges() {
        for (origin, height, point, expected) in [
            ([0., -55.], 0., [0., -41.], GroundAim::Clear),
            ([0., -55.], 0., [0., -40.99], GroundAim::OutOfRange),
            ([-13., -18.], 0., [-10., -21.], GroundAim::Obstructed),
            ([0., -55.], 0.351, [0., -53.], GroundAim::InvalidOrigin),
            ([0., -55.], 0.35, [0., -53.], GroundAim::Clear),
            ([0., -55.], 0., [f32::NAN, 0.], GroundAim::Unavailable),
        ] {
            let (mut s, w) = setup();
            s.actor.pos = origin;
            s.height = height;
            let before = s.snapshot();
            assert_eq!(s.ground_aim(4, origin, height, point, &w), expected);
            assert_eq!(
                s.ground_aim(99, origin, height, point, &w),
                GroundAim::Unavailable
            );
            assert_eq!(s.snapshot(), before);
            assert_eq!(s.cast(4, point, &w).is_ok(), expected == GroundAim::Clear);
            if expected != GroundAim::Clear {
                assert_eq!(s.snapshot(), before);
            }
        }
    }

    #[test]
    fn occluded_ward_and_receivers_leaving_or_entering_a_delayed_disk() {
        let (mut s, w) = setup();
        s.actor.pos = [-13., -18.];
        s.targets[3].pos = [-10., -21.];
        s.set_aim([1., -1.]);
        assert!(w.ground_target_allowed(s.targets[3].pos));
        assert!(!w.clear_line(s.actor.pos, s.targets[3].pos));
        s.cast(1, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 7);
        assert_eq!(s.actor.shield, 48.);
        assert_eq!(s.targets[3].shield, 0.);
        assert!(s.cast(4, s.targets[3].pos, &w).is_err());
        advance(&mut s, &w, 5);
        assert!(s.cast(4, s.targets[3].pos, &w).is_err());
        assert_eq!(s.cooldowns[4], 0);
        s.reset();
        s.targets[1].pos = [0., -66.]; // The second receiver starts outside the marked disk.
        s.cast(4, [0., -53.], &w).unwrap();
        advance(&mut s, &w, 14);
        s.targets[0].pos = [0., -66.]; // Leaves the mark during the visible flight.
        s.targets[1].pos = [0., -53.];
        s.targets[1].shield = 48.;
        s.targets[1].shield_until = 40;
        advance(&mut s, &w, 9);
        assert_eq!(s.targets[0].hp, 90.);
        assert_eq!(s.targets[1].hp, 73.);
        assert_eq!(s.targets[1].shield, 0.);
        assert_eq!(s.events.back().unwrap()["kind"], "impact");
        let receipt = s.events.back().unwrap()["receipts"]
            .as_array()
            .unwrap()
            .iter()
            .find(|hit| hit["unit"] == 2)
            .unwrap();
        assert_eq!(receipt["damage"], 65.);
    }

    #[test]
    fn floor_limits_prevent_outside_marks_and_bound_the_actual_vault_endpoint() {
        let (mut s, w) = setup();
        s.cast(2, s.actor.pos, &w).unwrap();
        // Simulate another controller displacing Hanuman during the windup.
        s.actor.pos[0] += 1.;
        advance(&mut s, &w, 4);
        assert!(s.casts.is_empty());
        assert_eq!(s.events.back().unwrap()["kind"], "cancel");
        assert_eq!(s.height, 0.);
        s.reset();
        s.actor.pos = [0., 126.9];
        assert!(s.cast(4, [0., 128.01], &w).is_err());
        assert_eq!(s.cooldowns[4], 0);
        s.cast(2, [0., 126.9], &w).unwrap();
        let target = s.casts[0].target;
        assert!((target[1] - 127.52).abs() < 0.001);
        advance(&mut s, &w, 13);
        let snapshot = s.snapshot();
        let landed = snapshot["active"]["landed_age_ticks"].as_u64().unwrap();
        assert!((4..13).contains(&landed));
        assert_eq!(snapshot["active"]["phase"], "recovery");
        assert_eq!(s.height, 0.);
        assert!((s.actor.pos[1] - 127.35).abs() < 0.002);
        assert!(s.actor.pos[1] < target[1]);
        assert_eq!(s.events.iter().filter(|e| e["kind"] == "impact").count(), 1);
        advance(&mut s, &w, 4);
        assert!(s.locked().is_none());
        assert!(s.cast(2, s.actor.pos, &w).is_err());
    }

    #[test]
    fn full_drill_can_finish_by_aiming_selective_attacks() {
        let (mut s, w) = setup();
        s.cast(4, [0., -53.], &w).unwrap();
        advance(&mut s, &w, 33);
        s.cast(0, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 12);
        s.cast(3, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 49);
        assert_eq!(s.snapshot()["defeated"], 2);
        for _ in 0..18 {
            s.tick([0., 1.], &w);
        }
        s.set_aim(difference(s.targets[2].pos, s.actor.pos));
        s.cast(0, s.actor.pos, &w).unwrap();
        advance(&mut s, &w, 11);
        assert_eq!(s.snapshot()["defeated"], 3);
        assert_eq!(s.targets[3].hp, 90.);
    }
}
