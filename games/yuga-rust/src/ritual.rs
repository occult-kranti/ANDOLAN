//! Isolated 20 Hz objective-rules experiment for the proposed Ember Rite mode.
//!
//! This module is not wired into the playable battle, browser, or room host.
//! An eventual server adapter must provide authoritative, post-damage actor
//! observations; clients must never submit positions or damage flags as truth.

use crate::army::Team;
use serde::Serialize;

pub const SEATS: usize = 10;
pub const HZ: u32 = 20;
pub const ROUND_TICKS: u32 = 100 * HZ;
pub const IGNITE_TICKS: u32 = 4 * HZ;
pub const QUENCH_TICKS: u32 = 7 * HZ / 2;
pub const BURN_TICKS: u32 = 40 * HZ;
pub const INTERACT_RANGE: f32 = 1.5;

type Point = [f32; 2];

fn other(team: Team) -> Team {
    match team {
        Team::Sun => Team::Moon,
        Team::Moon => Team::Sun,
    }
}

fn seat_team(seat: usize) -> Team {
    if seat % 2 == 0 {
        Team::Sun
    } else {
        Team::Moon
    }
}

fn finite(point: Point) -> bool {
    point.into_iter().all(f32::is_finite)
}

fn near(a: Point, b: Point, range: f32) -> bool {
    (a[0] - b[0]).hypot(a[1] - b[1]) <= range
}

/// A server-observed body at the end of a tick's movement and damage phase.
/// `damaged` means any accepted positive health or shield damage that tick,
/// even if healing subsequently restored the same amount. An adapter must
/// also check world collision, ground reachability and interaction visibility
/// before setting `reachable`. The client must never supply that flag directly.
#[derive(Clone, Copy, Debug)]
pub struct Actor {
    pub position: Point,
    pub alive: bool,
    pub connected: bool,
    pub grounded: bool,
    pub reachable: bool,
    pub damaged: bool,
    pub interact: bool,
}

impl Actor {
    fn available(self) -> bool {
        self.alive && self.connected
    }

    fn can_interact(self) -> bool {
        self.available() && self.grounded && self.reachable && self.interact && !self.damaged
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Site {
    pub center: Point,
    pub radius: f32,
}

#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Vessel {
    Carried {
        seat: usize,
        last_ground: Point,
    },
    Dropped {
        at: Point,
    },
    Burning {
        site: usize,
        at: Point,
        remaining: u32,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChannelKind {
    Ignite,
    Quench,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub struct Channel {
    pub kind: ChannelKind,
    pub seat: usize,
    pub site: usize,
    pub progress: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Reason {
    AttackersEliminated,
    DefendersEliminated,
    TimeExpired,
    FireCompleted,
    Quenched,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub struct RoundOutcome {
    pub winner: Team,
    pub reason: Reason,
}

/// One round. The caller starts it after its separate preparation phase and
/// supplies ten fixed alternating-team seats (even = Sun, odd = Moon).
pub struct RitualRound {
    attackers: Team,
    sites: [Site; 2],
    tick: u32,
    vessel: Vessel,
    channel: Option<Channel>,
    outcome: Option<RoundOutcome>,
}

impl RitualRound {
    pub fn new(
        attackers: Team,
        sites: [Site; 2],
        carrier: usize,
        carrier_ground: Point,
    ) -> Result<Self, &'static str> {
        if carrier >= SEATS || seat_team(carrier) != attackers || !finite(carrier_ground) {
            return Err("invalid carrier or ground point");
        }
        if sites
            .iter()
            .any(|s| !finite(s.center) || !s.radius.is_finite() || s.radius <= 0.)
            || near(
                sites[0].center,
                sites[1].center,
                sites[0].radius + sites[1].radius,
            )
        {
            return Err("invalid or overlapping sites");
        }
        Ok(Self {
            attackers,
            sites,
            tick: 0,
            vessel: Vessel::Carried {
                seat: carrier,
                last_ground: carrier_ground,
            },
            channel: None,
            outcome: None,
        })
    }

    pub fn tick(&self) -> u32 {
        self.tick
    }
    pub fn vessel(&self) -> &Vessel {
        &self.vessel
    }
    pub fn channel(&self) -> Option<Channel> {
        self.channel
    }
    pub fn outcome(&self) -> Option<RoundOutcome> {
        self.outcome
    }

    fn finish(&mut self, winner: Team, reason: Reason) {
        self.channel = None;
        self.outcome = Some(RoundOutcome { winner, reason });
    }

    /// Consume one complete, trusted post-damage observation. On a tick shared
    /// by completion and expiry, successful ignite/quench wins the tie; lethal
    /// damage and elimination are resolved first. A finished round is frozen.
    pub fn step(&mut self, actors: &[Actor; SEATS]) -> Result<(), &'static str> {
        if self.outcome.is_some() {
            return Err("round already resolved");
        }
        if actors.iter().any(|a| !finite(a.position)) {
            return Err("non-finite position");
        }

        self.tick += 1;
        let attack_alive = actors
            .iter()
            .enumerate()
            .any(|(i, a)| seat_team(i) == self.attackers && a.available());
        let defend_alive = actors
            .iter()
            .enumerate()
            .any(|(i, a)| seat_team(i) != self.attackers && a.available());
        let burning = matches!(self.vessel, Vessel::Burning { .. });
        if !burning && !attack_alive {
            self.finish(other(self.attackers), Reason::AttackersEliminated);
            return Ok(());
        }
        if !defend_alive {
            self.finish(self.attackers, Reason::DefendersEliminated);
            return Ok(());
        }

        match self.vessel.clone() {
            Vessel::Carried { seat, last_ground } => {
                let actor = actors[seat];
                if !actor.available() {
                    self.vessel = Vessel::Dropped { at: last_ground };
                    self.channel = None;
                } else {
                    let ground = if actor.grounded {
                        actor.position
                    } else {
                        last_ground
                    };
                    self.vessel = Vessel::Carried {
                        seat,
                        last_ground: ground,
                    };
                    let site = self
                        .sites
                        .iter()
                        .position(|s| near(actor.position, s.center, s.radius));
                    if actor.can_interact() {
                        if let Some(site) = site {
                            let previous = self
                                .channel
                                .filter(|c| {
                                    c.kind == ChannelKind::Ignite
                                        && c.seat == seat
                                        && c.site == site
                                })
                                .map_or(0, |c| c.progress);
                            let progress = previous + 1;
                            if progress >= IGNITE_TICKS {
                                self.vessel = Vessel::Burning {
                                    site,
                                    at: actor.position,
                                    remaining: BURN_TICKS,
                                };
                                self.channel = None;
                            } else {
                                self.channel = Some(Channel {
                                    kind: ChannelKind::Ignite,
                                    seat,
                                    site,
                                    progress,
                                });
                            }
                        } else {
                            self.channel = None;
                        }
                    } else {
                        self.channel = None;
                    }
                }
            }
            Vessel::Dropped { at } => {
                self.channel = None;
                if let Some(seat) = actors.iter().enumerate().find_map(|(i, a)| {
                    (seat_team(i) == self.attackers
                        && a.can_interact()
                        && near(a.position, at, INTERACT_RANGE))
                    .then_some(i)
                }) {
                    self.vessel = Vessel::Carried {
                        seat,
                        last_ground: actors[seat].position,
                    };
                }
            }
            Vessel::Burning {
                site,
                at,
                remaining,
            } => {
                let valid = |i: usize| {
                    seat_team(i) != self.attackers
                        && actors[i].can_interact()
                        && near(actors[i].position, at, INTERACT_RANGE)
                };
                let prior = self
                    .channel
                    .filter(|c| c.kind == ChannelKind::Quench && c.site == site && valid(c.seat));
                let candidate = prior
                    .map(|c| c.seat)
                    .or_else(|| (0..SEATS).find(|&i| valid(i)));
                if let Some(seat) = candidate {
                    let progress = prior.map_or(0, |c| c.progress) + 1;
                    if progress >= QUENCH_TICKS {
                        self.finish(other(self.attackers), Reason::Quenched);
                        return Ok(());
                    }
                    self.channel = Some(Channel {
                        kind: ChannelKind::Quench,
                        seat,
                        site,
                        progress,
                    });
                } else {
                    self.channel = None;
                }
                let remaining = remaining.saturating_sub(1);
                self.vessel = Vessel::Burning {
                    site,
                    at,
                    remaining,
                };
                if remaining == 0 {
                    self.finish(self.attackers, Reason::FireCompleted);
                }
            }
        }

        if self.outcome.is_none()
            && self.tick >= ROUND_TICKS
            && !matches!(self.vessel, Vessel::Burning { .. })
        {
            self.finish(other(self.attackers), Reason::TimeExpired);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SeriesOutcome {
    Winner(Team),
    Draw,
}

/// First to 13 in regulation. At 12–12, play up to three two-round
/// overtime pairs, swapping attack side each round; a tied third pair is a draw.
#[derive(Default)]
pub struct Series {
    score: [u8; 2],
    played: u8,
    outcome: Option<SeriesOutcome>,
}

impl Series {
    pub fn score(&self) -> [u8; 2] {
        self.score
    }
    pub fn played(&self) -> u8 {
        self.played
    }
    pub fn outcome(&self) -> Option<SeriesOutcome> {
        self.outcome
    }

    pub fn attackers(&self) -> Option<Team> {
        if self.outcome.is_some() {
            return None;
        }
        Some(
            if self.played < 12 || (self.played >= 24 && self.played % 2 == 0) {
                Team::Sun
            } else {
                Team::Moon
            },
        )
    }

    pub fn record(&mut self, winner: Team) -> Result<(), &'static str> {
        if self.outcome.is_some() {
            return Err("series already resolved");
        }
        let index = usize::from(winner == Team::Moon);
        self.score[index] += 1;
        self.played += 1;
        if self.played <= 24 && self.score[index] >= 13 {
            self.outcome = Some(SeriesOutcome::Winner(winner));
        } else if self.played > 24 && self.played % 2 == 0 {
            if self.score[0] != self.score[1] {
                self.outcome = Some(SeriesOutcome::Winner(if self.score[0] > self.score[1] {
                    Team::Sun
                } else {
                    Team::Moon
                }));
            } else if self.played >= 30 {
                self.outcome = Some(SeriesOutcome::Draw);
            }
        }
        Ok(())
    }
}
