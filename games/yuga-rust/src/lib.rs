//! The Rust authority owns the Confluence drill. Both desktop tests and the
//! browser call the same fixed-step simulation.
pub mod army;
pub mod battle;
pub mod combat;
#[cfg(not(target_arch = "wasm32"))]
pub mod hero;
pub mod mix;
pub mod rama;
pub mod world;

#[cfg(target_arch = "wasm32")]
mod browser {
    use super::{
        battle::{Battle, CastInput, Hero, Motion},
        combat::Combat,
        world::World,
    };
    use std::cell::RefCell;

    struct Trial {
        world: World,
        combat: Combat,
        battle: Option<(Battle, Hero)>,
        snapshot: Vec<u8>,
    }

    thread_local! { static TRIAL: RefCell<Option<Trial>> = const { RefCell::new(None) }; }

    #[no_mangle]
    pub extern "C" fn trial_start() -> i32 {
        let (Ok(world), Ok(combat)) = (World::load(), Combat::load()) else {
            return 0;
        };
        TRIAL.with(|cell| {
            *cell.borrow_mut() = Some(Trial {
                world,
                combat,
                battle: None,
                snapshot: Vec::new(),
            })
        });
        1
    }

    #[no_mangle]
    pub extern "C" fn trial_select(mode: u32) -> i32 {
        TRIAL.with_borrow_mut(|trial| {
            let Some(t) = trial else {
                return 0;
            };
            match mode {
                0 => {
                    t.battle = None;
                    t.combat.reset();
                }
                1 | 2 => {
                    let hero = if mode == 1 { Hero::Hanuman } else { Hero::Rama };
                    let Ok(game) = Battle::load(&t.world, hero, None) else {
                        return 0;
                    };
                    t.battle = Some((game, hero));
                }
                _ => return 0,
            }
            1
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_tick(dx: f32, dz: f32, aim_x: f32, aim_z: f32) {
        if ![dx, dz, aim_x, aim_z].iter().all(|v| v.is_finite()) {
            return;
        }
        TRIAL.with_borrow_mut(|trial| {
            if let Some(t) = trial {
                if let Some((game, _)) = &mut t.battle {
                    game.step(
                        &[Motion {
                            movement: [dx, dz],
                            aim: [aim_x, aim_z],
                        }],
                        &t.world,
                    );
                } else {
                    t.combat.set_aim([aim_x, aim_z]);
                    t.combat.tick([dx, dz], &t.world);
                }
            }
        });
    }

    #[no_mangle]
    pub extern "C" fn trial_cast(slot: u32, gx: f32, gz: f32, aim_x: f32, aim_z: f32) -> i32 {
        if ![gx, gz, aim_x, aim_z].iter().all(|v| v.is_finite()) {
            return 0;
        }
        TRIAL.with_borrow_mut(|trial| {
            let Some(t) = trial else { return 0 };
            if let Some((game, _)) = &mut t.battle {
                return i32::from(
                    game.cast(
                        0,
                        CastInput {
                            slot: slot as usize,
                            ground: [gx, gz],
                            aim: [aim_x, aim_z],
                        },
                        &t.world,
                    )
                    .is_ok(),
                );
            }
            t.combat.set_aim([aim_x, aim_z]);
            i32::from(t.combat.cast(slot as usize, [gx, gz], &t.world).is_ok())
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_reload() -> i32 {
        TRIAL.with_borrow_mut(|trial| {
            let Some((game, _)) = trial.as_mut().and_then(|t| t.battle.as_mut()) else {
                return 0;
            };
            i32::from(game.reload(0))
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_reset() {
        TRIAL.with_borrow_mut(|trial| {
            if let Some(t) = trial {
                if let Some((game, hero)) = &mut t.battle {
                    *game = Battle::load(&t.world, *hero, None).expect("validated match data");
                } else {
                    t.combat.reset();
                }
            }
        });
    }

    // Caller reads UTF-8 bytes immediately, before another snapshot or reset.
    #[no_mangle]
    pub extern "C" fn trial_snapshot() -> *const u8 {
        TRIAL.with_borrow_mut(|trial| {
            let Some(t) = trial else {
                return std::ptr::null();
            };
            let state = if let Some((game, _)) = &t.battle {
                game.snapshot(0).expect("Sun seat always exists")
            } else {
                t.combat.snapshot()
            };
            t.snapshot = serde_json::to_vec(&state).expect("finite combat state");
            t.snapshot.as_ptr()
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_snapshot_len() -> usize {
        TRIAL.with_borrow(|trial| trial.as_ref().map_or(0, |t| t.snapshot.len()))
    }
}

// Portable room workers each instantiate an independent match authority.
#[cfg(target_arch = "wasm32")]
mod room_worker {
    use crate::{
        battle::{Battle, CastInput, Hero, Motion},
        world::World,
    };
    use std::cell::RefCell;

    struct Room {
        world: World,
        battle: Battle,
        bytes: Vec<u8>,
    }
    thread_local! {static ROOM: RefCell<Option<Room>>=const {RefCell::new(None)};}

    fn choice(index: u32) -> Option<Hero> {
        match index {
            0 => Some(Hero::Hanuman),
            1 => Some(Hero::Rama),
            _ => None,
        }
    }

    #[no_mangle]
    pub extern "C" fn duel_start(sun: u32, moon: u32) -> i32 {
        let (Some(sun), Some(moon)) = (choice(sun), choice(moon)) else {
            return 0;
        };
        let Ok(world) = World::load() else {
            return 0;
        };
        let Ok(battle) = Battle::load(&world, sun, Some(moon)) else {
            return 0;
        };
        ROOM.with_borrow_mut(|r| {
            *r = Some(Room {
                world,
                battle,
                bytes: Vec::new(),
            })
        });
        1
    }

    #[no_mangle]
    pub extern "C" fn duel_cast(seat: u32, slot: u32, gx: f32, gz: f32, ax: f32, az: f32) -> i32 {
        ROOM.with_borrow_mut(|r| {
            r.as_mut().is_some_and(|r| {
                r.battle
                    .cast(
                        seat as usize,
                        CastInput {
                            slot: slot as usize,
                            ground: [gx, gz],
                            aim: [ax, az],
                        },
                        &r.world,
                    )
                    .is_ok()
            }) as i32
        })
    }

    #[no_mangle]
    pub extern "C" fn duel_reload(seat: u32) -> i32 {
        ROOM.with_borrow_mut(|r| r.as_mut().is_some_and(|r| r.battle.reload(seat as usize)) as i32)
    }

    #[no_mangle]
    pub extern "C" fn duel_step(
        sdx: f32,
        sdz: f32,
        sax: f32,
        saz: f32,
        mdx: f32,
        mdz: f32,
        max: f32,
        maz: f32,
    ) {
        ROOM.with_borrow_mut(|r| {
            if let Some(r) = r {
                r.battle.step(
                    &[
                        Motion {
                            movement: [sdx, sdz],
                            aim: [sax, saz],
                        },
                        Motion {
                            movement: [mdx, mdz],
                            aim: [max, maz],
                        },
                    ],
                    &r.world,
                );
            }
        })
    }

    #[no_mangle]
    pub extern "C" fn duel_snapshot(seat: u32) -> *const u8 {
        ROOM.with_borrow_mut(|r| {
            let Some(r) = r else {
                return std::ptr::null();
            };
            let Some(s) = r.battle.snapshot(seat as usize) else {
                r.bytes.clear();
                return std::ptr::null();
            };
            r.bytes = serde_json::to_vec(&s).expect("finite match state");
            r.bytes.as_ptr()
        })
    }

    #[no_mangle]
    pub extern "C" fn duel_snapshot_len() -> usize {
        ROOM.with_borrow(|r| r.as_ref().map_or(0, |r| r.bytes.len()))
    }
}
