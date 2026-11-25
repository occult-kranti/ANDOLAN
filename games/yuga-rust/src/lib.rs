//! The Rust authority owns the Confluence drill. Both desktop tests and the
//! browser call the same fixed-step simulation.
pub mod combat;
#[cfg(not(target_arch = "wasm32"))]
pub mod hero;
pub mod world;

#[cfg(target_arch = "wasm32")]
mod browser {
    use super::{combat::Combat, world::World};
    use std::cell::RefCell;

    struct Trial {
        world: World,
        combat: Combat,
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
                snapshot: Vec::new(),
            })
        });
        1
    }

    #[no_mangle]
    pub extern "C" fn trial_tick(dx: f32, dz: f32, aim_x: f32, aim_z: f32) {
        if ![dx, dz, aim_x, aim_z].iter().all(|v| v.is_finite()) {
            return;
        }
        TRIAL.with_borrow_mut(|trial| {
            if let Some(t) = trial {
                t.combat.set_aim([aim_x, aim_z]);
                t.combat.tick([dx, dz], &t.world);
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
            t.combat.set_aim([aim_x, aim_z]);
            i32::from(t.combat.cast(slot as usize, [gx, gz], &t.world).is_ok())
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_reset() {
        TRIAL.with_borrow_mut(|trial| {
            if let Some(t) = trial {
                t.combat.reset();
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
            t.snapshot = serde_json::to_vec(&t.combat.snapshot()).expect("finite combat state");
            t.snapshot.as_ptr()
        })
    }

    #[no_mangle]
    pub extern "C" fn trial_snapshot_len() -> usize {
        TRIAL.with_borrow(|trial| trial.as_ref().map_or(0, |t| t.snapshot.len()))
    }
}
