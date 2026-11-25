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
const HERO_ID_BASE: u32 = u32::MAX - 2;
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
    fn targets(&mut self, targets: Vec<Receiver>) {
        match self {
            Self::Gada(h) => h.set_receivers(targets),
            Self::Bow(r) => r.set_receivers(targets),
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
        fighter.targets(vec![]);
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

pub struct Battle {
    pub army: Army,
    players: Vec<Player>,
    winner: Option<&'static str>,
}

impl Battle {
    pub fn load(world: &World, sun: Hero, moon: Option<Hero>) -> Result<Self, String> {
        let mut army = Army::load()?;
        let mut players = vec![Player::new(sun, Team::Sun)?];
        if let Some(hero) = moon {
            players.push(Player::new(hero, Team::Moon)?);
        }
        // Enter the first clash through the ordinary simulation, keeping all shield clocks aligned.
        for _ in 0..ENTRY_TICKS {
            army.step(world);
            for player in &mut players {
                player.fighter.tick([0., 0.], world);
            }
        }
        for player in &mut players {
            player.fighter.body_mut().pos = army.frontline_spawn_for(world, player.team);
            player
                .fighter
                .aim([0., if player.team == Team::Sun { 1. } else { -1. }]);
        }
        let mut game = Self {
            army,
            players,
            winner: None,
        };
        for seat in 0..game.players.len() {
            game.refresh_targets(seat);
        }
        Ok(game)
    }

    fn refresh_targets(&mut self, seat: usize) {
        let mut targets = self.army.receivers();
        let other_seat = 1 - seat;
        if let Some(other) = self.players.get(other_seat) {
            let mut body = other.fighter.body().clone();
            body.id = HERO_ID_BASE + other_seat as u32;
            if body.hp > 0. {
                targets.push(body);
            }
        }
        self.players[seat].fighter.targets(targets);
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
        self.refresh_targets(seat);
        let fighter = &mut self.players[seat].fighter;
        fighter.aim(input.aim);
        fighter.cast(input.slot, input.ground, world)
    }

    pub fn step(&mut self, motion: &[Motion], world: &World) {
        if self.winner.is_some() {
            return;
        }
        let now = self.army.tick_index() + 1;
        let mut incoming = [0.0f64; 2];
        for offset in 0..self.players.len() {
            let seat = (now as usize + offset) % self.players.len();
            self.refresh_targets(seat);
            let opponent = 1 - seat;
            let other_before = self.players.get(opponent).map(|p| {
                let body = p.fighter.body();
                body.hp
                    + if body.shield_until > now {
                        body.shield
                    } else {
                        0.
                    }
            });
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
            self.army.apply_receivers_for(p.fighter.resolved(), p.team);
            if let Some(before) = other_before {
                if let Some(after) = p
                    .fighter
                    .resolved()
                    .iter()
                    .find(|t| t.id == HERO_ID_BASE + opponent as u32)
                {
                    incoming[opponent] = (before - after.hp - after.shield).max(0.);
                }
            }
        }
        // Both seats can finish an attack on the same tick.
        for (seat, damage) in incoming
            .iter()
            .copied()
            .enumerate()
            .take(self.players.len())
        {
            let p = &mut self.players[seat];
            let was_alive = p.fighter.body().hp > 0.;
            p.fighter.body_mut().damage(damage);
            if was_alive && p.fighter.body().hp <= 0. {
                self.refresh_targets(seat);
                let p = &mut self.players[seat];
                p.fighter.interrupt();
                self.army.apply_receivers_for(p.fighter.resolved(), p.team);
                p.defeats += 1;
                p.respawn_at = now + RESPAWN_TICKS;
            } else if p.respawn_at != 0 && now >= p.respawn_at {
                let actor = p.fighter.body_mut();
                actor.hp = actor.max_hp;
                actor.shield = 0.;
                actor.shield_until = 0;
                actor.pos = self.army.frontline_spawn_for(world, p.team);
                if let Fighter::Bow(rama) = &mut p.fighter {
                    rama.restore_after_respawn();
                }
                p.respawn_at = 0;
            }
        }
        self.army.step(world);
        self.winner = self.army.winner();
        if self.winner.is_none() && now >= LIMIT_TICKS {
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
    pub fn snapshot(&self, seat: usize) -> Option<Value> {
        let clock = self.army.tick_index();
        let mut state = self.players.get(seat)?.snapshot(clock);
        state["mode"] = json!("match");
        state["army"] = self.army.snapshot();
        state["winner"] = json!(self.winner);
        state["remaining_ticks"] = json!(LIMIT_TICKS.saturating_sub(clock));
        state["opponent"] = self
            .players
            .get(1 - seat)
            .map(|p| {
                let mut other = p.snapshot(clock);
                for k in ["abilities", "events"] {
                    other.as_object_mut().unwrap().remove(k);
                }
                other
            })
            .unwrap_or(Value::Null);
        Some(state)
    }
}
