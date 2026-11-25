//! The same Confluence match runs inside WebAssembly and the native room host.
use crate::{
    army::{Army, Team},
    combat::{Combat, Receiver},
    rama::Rama,
    world::World,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const ENTRY_TICKS: u32 = 27 * 20;
pub const LIMIT_TICKS: u32 = 18 * 60 * 20;
const RESPAWN_TICKS: u32 = 3 * 20;
const MAX_SEATS: usize = 10;
const SMALL_TEAM_SEATS: usize = 6;

// The original duel reserved these first two receiver IDs. Both armies use small ascending IDs.
fn receiver_id(seat: usize) -> u32 {
    match seat {
        0 => u32::MAX - 2,
        1 => u32::MAX - 1,
        _ => u32::MAX - 1 - seat as u32,
    }
}
type Point = [f32; 2];

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Hero {
    Hanuman,
    Rama,
}

enum Fighter {
    Gada(Combat),
    Bow(Rama),
}

impl Fighter {
    fn load(hero: Hero) -> Result<Self, String> {
        match hero {
            Hero::Hanuman => Combat::load().map(Self::Gada),
            Hero::Rama => Rama::load().map(Self::Bow),
        }
    }
    fn body(&self) -> &Receiver {
        match self {
            Self::Gada(h) => h.actor(),
            Self::Bow(r) => r.actor(),
        }
    }
    fn body_mut(&mut self) -> &mut Receiver {
        match self {
            Self::Gada(h) => h.actor_mut(),
            Self::Bow(r) => r.actor_mut(),
        }
    }
    fn targets(&mut self, targets: Vec<Receiver>, elevations: &[(u32, f32)]) {
        match self {
            Self::Gada(h) => h.set_receivers_with_elevations(targets, elevations),
            Self::Bow(r) => r.set_receivers(targets),
        }
    }
    fn elevation(&self) -> f32 {
        match self {
            Self::Gada(h) => h.elevation(),
            Self::Bow(_) => 0.,
        }
    }
    fn resolved(&self) -> &[Receiver] {
        match self {
            Self::Gada(h) => h.receivers(),
            Self::Bow(r) => r.receivers(),
        }
    }
    fn aim(&mut self, aim: Point) {
        match self {
            Self::Gada(h) => h.set_aim(aim),
            Self::Bow(r) => r.set_aim(aim),
        }
    }
    fn cast(&mut self, slot: usize, ground: Point, world: &World) -> Result<(), String> {
        match self {
            Self::Gada(h) => h.cast(slot, ground, world),
            Self::Bow(r) => r.cast(slot, ground, world),
        }
    }
    fn tick(&mut self, movement: Point, world: &World) {
        match self {
            Self::Gada(h) => h.tick(movement, world),
            Self::Bow(r) => r.tick(movement, world),
        }
    }
    fn interrupt(&mut self) {
        match self {
            Self::Gada(h) => h.interrupt(),
            Self::Bow(r) => r.interrupt(),
        }
    }
    fn snapshot(&self) -> Value {
        match self {
            Self::Gada(h) => h.snapshot(),
            Self::Bow(r) => r.snapshot(),
        }
    }
}

struct Player {
    hero: Hero,
    team: Team,
    fighter: Fighter,
    respawn_at: u32,
    defeats: u32,
}

impl Player {
    fn new(hero: Hero, team: Team) -> Result<Self, String> {
        let mut fighter = Fighter::load(hero)?;
        fighter.targets(vec![], &[]);
        fighter.body_mut().team = if team == Team::Sun { "sun" } else { "moon" };
        fighter.body_mut().hp = fighter.body().max_hp;
        Ok(Self {
            hero,
            team,
            fighter,
            respawn_at: 0,
            defeats: 0,
        })
    }

    fn snapshot(&self, clock: u32) -> Value {
        let mut state = self.fighter.snapshot();
        // The match publishes soldiers once, including their up-to-date post-army positions.
        state.as_object_mut().unwrap().remove("targets");
        state["hero"] = json!(self.hero);
        state["respawn_ticks"] = json!(self.respawn_at.saturating_sub(clock));
        state["knockouts"] = json!(self.defeats);
        state
    }
}

#[derive(Clone, Copy, Default, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct Motion {
    pub movement: Point,
    pub aim: Point,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CastInput {
    pub slot: usize,
    pub ground: Point,
    pub aim: Point,
}

// Every fighter gets the same hero health at the start of a tick. Apply the effects after
// every fighter has acted so a lethal hit cannot cancel another actor's same-tick release.
#[derive(Default)]
struct Incoming {
    damage: f64,
    heal: f64,
    shield_grant: Option<(f64, u32)>,
    shield_restore: Option<(f64, u32)>,
}

impl Incoming {
    fn observe(&mut self, before: &Receiver, after: &Receiver, caster_team: &'static str) {
        if before.team != caster_team {
            self.damage += ((before.hp - after.hp) + (before.shield - after.shield)).max(0.);
            return;
        }
        self.heal += (after.hp - before.hp).max(0.);
        let shield = (after.shield, after.shield_until);
        if after.shield > before.shield
            || (after.shield == before.shield && after.shield_until > before.shield_until)
        {
            // Independently issued wards combine by maximum strength and duration, as in the kits.
            let (power, until) = self.shield_grant.unwrap_or((0., 0));
            self.shield_grant = Some((power.max(shield.0), until.max(shield.1)));
        } else if after.shield < before.shield || after.shield_until < before.shield_until {
            self.shield_restore = Some(shield);
        }
    }

    fn support(&self, body: &mut Receiver) {
        if body.hp <= 0. {
            return;
        }
        if let Some((power, until)) = self.shield_restore {
            body.shield = body.shield.min(power);
            body.shield_until = if body.shield > 0. { until } else { 0 };
        }
        if let Some((power, until)) = self.shield_grant {
            body.shield = body.shield.max(power);
            body.shield_until = body.shield_until.max(until);
        }
        body.hp = (body.hp + self.heal).min(body.max_hp);
    }
}

pub struct Battle {
    pub army: Army,
    players: Vec<Player>,
    winner: Option<&'static str>,
    hero_only: bool,
}

impl Battle {
    pub fn load(world: &World, sun: Hero, moon: Option<Hero>) -> Result<Self, String> {
        let mut heroes = vec![sun];
        heroes.extend(moon);
        Self::with_roster(world, &heroes)
    }

    pub fn with_roster(world: &World, roster: &[Hero]) -> Result<Self, String> {
        Self::build(world, roster, false)
    }

    /// Temporary hero-only mode; the existing army rules remain available to tests and tools.
    pub fn with_hero_roster(world: &World, roster: &[Hero]) -> Result<Self, String> {
        Self::build(world, roster, true)
    }

    pub fn load_hero_only(world: &World, hero: Hero) -> Result<Self, String> {
        Self::with_hero_roster(world, &[hero])
    }

    fn build(world: &World, roster: &[Hero], hero_only: bool) -> Result<Self, String> {
        if !matches!(roster.len(), 1 | 2 | SMALL_TEAM_SEATS | MAX_SEATS) {
            return Err(
                "Expected a solo hero, two duelists, six or ten alternating team seats".into(),
            );
        }
        let mut army = if hero_only {
            Army::load_without_waves()?
        } else {
            Army::load()?
        };
        let mut players = roster
            .iter()
            .enumerate()
            .map(|(seat, hero)| {
                Player::new(*hero, if seat % 2 == 0 { Team::Sun } else { Team::Moon })
            })
            .collect::<Result<Vec<_>, _>>()?;
        // Enter the first clash through the ordinary simulation, keeping all shield clocks aligned.
        for _ in 0..if hero_only { 0 } else { ENTRY_TICKS } {
            army.step(world);
            for player in &mut players {
                player.fighter.tick([0., 0.], world);
            }
        }
        let mut game = Self {
            army,
            players,
            winner: None,
            hero_only,
        };
        let mut placed = Vec::new();
        for seat in 0..game.players.len() {
            let position = game.spawn_position(seat, world, &placed);
            let player = &mut game.players[seat];
            player.fighter.body_mut().pos = position;
            player
                .fighter
                .aim([0., if player.team == Team::Sun { 1. } else { -1. }]);
            placed.push(position);
        }
        let bodies = game.receivers(game.army.tick_index());
        let elevations = game.elevations();
        for seat in 0..game.players.len() {
            game.refresh_targets(seat, &bodies, &elevations);
        }
        Ok(game)
    }

    fn spawn_position(&self, seat: usize, world: &World, occupied: &[Point]) -> Point {
        let team = self.players[seat].team;
        let base = if self.hero_only {
            self.army.skirmish_spawn_for(world, team)
        } else {
            self.army.frontline_spawn_for(world, team)
        };
        if self.players.len() <= 2 {
            return base;
        }
        let side = [0., -3., 3., -6., 6.][seat / 2];
        let back = if team == Team::Sun { -1. } else { 1. };
        for depth in [0., 2., 4., 6., 8.] {
            for lateral in [0., -1.5, 1.5, -3., 3.] {
                let point = [base[0] + side + lateral, base[1] + back * depth];
                if world.ground_target_allowed(point)
                    && world.clear_line(base, point)
                    && occupied
                        .iter()
                        .all(|p| (p[0] - point[0]).hypot(p[1] - point[1]) >= 1.3)
                    && self
                        .army
                        .targets()
                        .all(|u| (u.xz[0] - point[0]).hypot(u.xz[1] - point[1]) >= u.radius + 0.65)
                {
                    return point;
                }
            }
        }
        base
    }

    fn receivers(&self, now: u32) -> Vec<Receiver> {
        self.players
            .iter()
            .enumerate()
            .map(|(seat, p)| {
                let mut body = p.fighter.body().clone();
                body.id = receiver_id(seat);
                body.expire_shield(now);
                body
            })
            .collect()
    }

    fn elevations(&self) -> Vec<(u32, f32)> {
        self.players
            .iter()
            .enumerate()
            .map(|(seat, player)| (receiver_id(seat), player.fighter.elevation()))
            .collect()
    }

    fn refresh_targets(&mut self, seat: usize, bodies: &[Receiver], elevations: &[(u32, f32)]) {
        let mut targets = self.army.receivers();
        targets.extend(
            bodies
                .iter()
                .enumerate()
                .filter(|(i, b)| *i != seat && b.hp > 0.)
                .map(|(_, b)| b.clone()),
        );
        self.players[seat].fighter.targets(targets, elevations);
    }

    fn collect_effects(&mut self, seat: usize, before: &[Receiver], incoming: &mut [Incoming]) {
        let player = &self.players[seat];
        let resolved = player.fighter.resolved();
        self.army.apply_receivers_for(resolved, player.team);
        // Hero projections were appended after all army representatives, in seat order.
        let hero_receivers = resolved
            .iter()
            .rev()
            .take_while(|r| r.id >= receiver_id(MAX_SEATS - 1));
        for after in hero_receivers {
            if let Some(target) = before.iter().position(|b| b.id == after.id) {
                incoming[target].observe(&before[target], after, player.fighter.body().team);
            }
        }
    }

    pub fn reload(&mut self, seat: usize) -> bool {
        if self.winner.is_some() {
            return false;
        }
        let Some(player) = self.players.get_mut(seat) else {
            return false;
        };
        match &mut player.fighter {
            Fighter::Bow(r) if r.actor().hp > 0. => r.reload(),
            _ => false,
        }
    }

    pub fn cast(&mut self, seat: usize, input: CastInput, world: &World) -> Result<(), String> {
        if self.winner.is_some()
            || input.slot >= 5
            || !input.ground.iter().chain(&input.aim).all(|x| x.is_finite())
        {
            return Err("Invalid cast or match already finished".into());
        }
        if !self
            .players
            .get(seat)
            .is_some_and(|p| p.fighter.body().hp > 0.)
        {
            return Err("Hero unavailable".into());
        }
        let bodies = self.receivers(self.army.tick_index());
        let elevations = self.elevations();
        self.refresh_targets(seat, &bodies, &elevations);
        let fighter = &mut self.players[seat].fighter;
        fighter.aim(input.aim);
        fighter.cast(input.slot, input.ground, world)
    }

    pub fn step(&mut self, motion: &[Motion], world: &World) {
        if self.winner.is_some() {
            return;
        }
        let now = self.army.tick_index() + 1;
        let bodies = self.receivers(now);
        // Positions and elevations must share the same pre-tick snapshot for every seat.
        let elevations = self.elevations();
        let mut incoming: [Incoming; MAX_SEATS] = Default::default();
        for offset in 0..self.players.len() {
            let seat = (now as usize + offset) % self.players.len();
            self.refresh_targets(seat, &bodies, &elevations);
            let p = &mut self.players[seat];
            let input = motion.get(seat).copied().unwrap_or_default();
            let living = p.fighter.body().hp > 0.;
            let moving = input.movement.iter().all(|v| v.is_finite());
            if living {
                p.fighter.aim(input.aim);
            }
            p.fighter.tick(
                if living && moving {
                    input.movement
                } else {
                    [0., 0.]
                },
                world,
            );
            self.collect_effects(seat, &bodies, &mut incoming);
        }
        let team_mode = self.players.len() > 2;
        for (i, p) in self.players.iter_mut().enumerate() {
            let body = p.fighter.body_mut();
            if team_mode {
                // Settle all damage against shields already present when the tick began.
                // Then apply support to survivors. A ward shared in the same frame must not
                // retroactively absorb already-lethal damage, even when the caster is its target.
                incoming[i].observe(&bodies[i], body, body.team);
                body.hp = bodies[i].hp;
                body.shield = bodies[i].shield;
                body.shield_until = bodies[i].shield_until;
            }
            body.damage(incoming[i].damage);
            incoming[i].support(body);
        }
        for seat in 0..self.players.len() {
            if bodies[seat].hp > 0. && self.players[seat].fighter.body().hp <= 0. {
                // An interrupted Guardian Circle also releases wards on other surviving heroes.
                let at_death = self.receivers(now);
                let elevations_at_death = self.elevations();
                self.refresh_targets(seat, &at_death, &elevations_at_death);
                let p = &mut self.players[seat];
                p.fighter.interrupt();
                p.defeats += 1;
                p.respawn_at = now + RESPAWN_TICKS;
                let mut cleanup: [Incoming; MAX_SEATS] = Default::default();
                self.collect_effects(seat, &at_death, &mut cleanup);
                for (i, p) in self.players.iter_mut().enumerate() {
                    cleanup[i].support(p.fighter.body_mut());
                }
            } else if self.players[seat].respawn_at != 0 && now >= self.players[seat].respawn_at {
                let occupied: Vec<_> = self
                    .players
                    .iter()
                    .map(|p| p.fighter.body())
                    .filter(|b| b.hp > 0.)
                    .map(|b| b.pos)
                    .collect();
                let spawn = self.spawn_position(seat, world, &occupied);
                let p = &mut self.players[seat];
                let actor = p.fighter.body_mut();
                actor.hp = actor.max_hp;
                actor.shield = 0.;
                actor.shield_until = 0;
                actor.pos = spawn;
                if let Fighter::Bow(rama) = &mut p.fighter {
                    rama.restore_after_respawn();
                }
                p.respawn_at = 0;
            }
        }
        self.army.step(world);
        if self.hero_only {
            let [sun, moon] = self.hero_score();
            let target = self.score_target();
            if (self.players.len() > 1 && sun.max(moon) >= target && sun != moon)
                || now >= LIMIT_TICKS
            {
                self.winner = Some(if sun > moon {
                    "sun"
                } else if moon > sun {
                    "moon"
                } else {
                    "draw"
                });
            }
        } else {
            self.winner = self.army.winner();
        }
        if !self.hero_only && self.winner.is_none() && now >= LIMIT_TICKS {
            let cores = &self.army.snapshot()["cores"];
            let sun = cores["sun"].as_f64().unwrap();
            let moon = cores["moon"].as_f64().unwrap();
            self.winner = Some(if sun > moon {
                "sun"
            } else if moon > sun {
                "moon"
            } else {
                "draw"
            });
        }
    }

    pub fn winner(&self) -> Option<&'static str> {
        self.winner
    }

    fn hero_score(&self) -> [u32; 2] {
        let mut score = [0u32; 2];
        for player in &self.players {
            // A team's defeats count for its opponent. Friendly fire is disabled.
            let opponent = usize::from(player.team == Team::Sun);
            score[opponent] = score[opponent].saturating_add(player.defeats);
        }
        score
    }

    fn score_target(&self) -> u32 {
        match self.players.len() {
            MAX_SEATS => 25,
            SMALL_TEAM_SEATS => 20,
            _ => 10,
        }
    }

    pub fn snapshot(&self, seat: usize) -> Option<Value> {
        let clock = self.army.tick_index();
        self.players.get(seat)?;
        let team_mode = self.players.len() > 2;
        let player_view = |index: usize| {
            let p = &self.players[index];
            let mut s = p.snapshot(clock);
            if team_mode {
                s["seat"] = json!(index);
                s["team"] = json!(p.team);
                s["actor"]["id"] = json!(receiver_id(index));
                // Kits use receiver zero as the caster inside their own simulation.
                for e in s["events"].as_array_mut().into_iter().flatten() {
                    for r in e["receipts"].as_array_mut().into_iter().flatten() {
                        for field in ["unit", "unit_id"] {
                            if r[field].as_u64() == Some(0) {
                                r[field] = json!(receiver_id(index));
                            }
                        }
                    }
                }
            }
            s
        };
        let mut state = player_view(seat);
        state["mode"] = json!("match");
        state["army"] = self.army.snapshot();
        state["winner"] = json!(self.winner);
        state["remaining_ticks"] = json!(LIMIT_TICKS.saturating_sub(clock));
        if self.hero_only {
            let [sun, moon] = self.hero_score();
            state["ruleset"] = json!("hero_skirmish");
            state["score"] = json!({"sun": sun, "moon": moon, "target": self.score_target()});
            state["solo_exploration"] = json!(self.players.len() == 1);
        }
        if team_mode {
            let remote: Vec<Value> = (0..self.players.len())
                .filter(|i| *i != seat)
                .map(player_view)
                .collect();
            state["opponent"] = remote
                .iter()
                .find(|p| p["team"] != state["team"])
                .cloned()
                .map(compact)
                .unwrap_or(Value::Null);
            state["roster"] = Value::Array(remote);
        } else {
            state["opponent"] = self
                .players
                .get(1 - seat)
                .map(|p| compact(p.snapshot(clock)))
                .unwrap_or(Value::Null);
        }
        Some(state)
    }
}

fn compact(mut state: Value) -> Value {
    if let Some(fields) = state.as_object_mut() {
        fields.remove("abilities");
        fields.remove("events");
    }
    state
}
