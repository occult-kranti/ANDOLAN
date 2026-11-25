//! Byte-buffer ABI shared by the classic browser roster and native regression suite.
#[path = "../../src/bin/roster/abilities.rs"]
mod abilities;
#[path = "../../src/bin/roster/geometry.rs"]
mod geometry;
#[path = "../../src/bin/roster/lab.rs"]
mod lab;
#[path = "../../src/bin/roster/model.rs"]
mod model;

use lab::Lab;
use model::Input;
use serde_json::Value;
use std::cell::RefCell;
use std::io::{self, Write};

const INPUT_CAP: usize = 4096;
const SNAPSHOT_CAP: usize = 256 * 1024;
const ERROR_CAP: usize = 512;

#[derive(Default)]
struct Output(Vec<u8>);
impl Write for Output {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        if data.len() > SNAPSHOT_CAP - self.0.len() {
            return Err(io::Error::other("Roster snapshot exceeds buffer capacity"));
        }
        self.0.extend_from_slice(data);
        Ok(data.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

struct Session {
    input: [u8; INPUT_CAP],
    lab: Option<Lab>,
    snapshot: Output,
    scratch: Output,
    error: String,
}

impl Session {
    const fn new() -> Self {
        Self {
            input: [0; INPUT_CAP],
            lab: None,
            snapshot: Output(Vec::new()),
            scratch: Output(Vec::new()),
            error: String::new(),
        }
    }
    fn input(&self, len: u32) -> Result<&str, String> {
        let bytes = self
            .input
            .get(..len as usize)
            .filter(|value| !value.is_empty())
            .ok_or("Input length is out of range")?;
        std::str::from_utf8(bytes).map_err(|_| "Input must be UTF-8".into())
    }
    fn publish(&mut self, snapshot: &Value) -> Result<(), String> {
        self.scratch.0.clear();
        serde_json::to_writer(&mut self.scratch, snapshot).map_err(|e| e.to_string())?;
        std::mem::swap(&mut self.snapshot, &mut self.scratch);
        Ok(())
    }
    fn reset(&mut self, len: u32) -> Result<(), String> {
        let hero = self.input(len)?;
        if hero.len() > 64 || !hero.bytes().all(|b| b.is_ascii_lowercase() || b == b'-') {
            return Err("Expected a classic hero ID".into());
        }
        let fresh = Lab::load(hero)?;
        self.publish(&fresh.snapshot(None))?;
        self.lab = Some(fresh);
        Ok(())
    }
    fn command(&mut self, len: u32) -> Result<(), String> {
        let input: Input = serde_json::from_str(self.input(len)?).map_err(|e| e.to_string())?;
        let next = self
            .lab
            .as_mut()
            .ok_or("Select a hero first")?
            .command(&input)?;
        self.publish(&next)
    }
    fn status(&mut self, result: Result<(), String>) -> i32 {
        match result {
            Ok(()) => {
                self.error.clear();
                1
            }
            Err(e) => {
                self.error = if e.len() <= ERROR_CAP {
                    e
                } else {
                    "Invalid roster command".into()
                };
                0
            }
        }
    }
}
thread_local! { static SESSION: RefCell<Session> = const {RefCell::new(Session::new())}; }

#[no_mangle]
pub extern "C" fn roster_input_capacity() -> u32 {
    INPUT_CAP as u32
}
#[no_mangle]
pub extern "C" fn roster_input_ptr() -> *mut u8 {
    SESSION.with_borrow_mut(|s| s.input.as_mut_ptr())
}
#[no_mangle]
pub extern "C" fn roster_reset(len: u32) -> i32 {
    SESSION.with_borrow_mut(|s| {
        let r = s.reset(len);
        s.status(r)
    })
}
#[no_mangle]
pub extern "C" fn roster_command(len: u32) -> i32 {
    SESSION.with_borrow_mut(|s| {
        let r = s.command(len);
        s.status(r)
    })
}
#[no_mangle]
pub extern "C" fn roster_snapshot_ptr() -> *const u8 {
    SESSION.with_borrow(|s| s.snapshot.0.as_ptr())
}
#[no_mangle]
pub extern "C" fn roster_snapshot_len() -> usize {
    SESSION.with_borrow(|s| s.snapshot.0.len())
}
#[no_mangle]
pub extern "C" fn roster_error_ptr() -> *const u8 {
    SESSION.with_borrow(|s| s.error.as_ptr())
}
#[no_mangle]
pub extern "C" fn roster_error_len() -> usize {
    SESSION.with_borrow(|s| s.error.len())
}

#[cfg(test)]
mod abi_tests {
    use super::*;
    #[test]
    fn bounded_writer_and_malformed_reset_preserve_the_previous_snapshot() {
        let mut session = Session::new();
        session.input[..4].copy_from_slice(b"rama");
        session.reset(4).unwrap();
        let old = session.snapshot.0.clone();
        assert!(session
            .publish(&Value::String("x".repeat(SNAPSHOT_CAP)))
            .is_err());
        session.input[0] = 0xff;
        assert!(session.reset(1).is_err());
        assert!(session.command(u32::MAX).is_err());
        assert_eq!(session.snapshot.0, old);
    }
}
