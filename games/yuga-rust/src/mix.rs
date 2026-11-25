//! Bounded in-place Web Audio blocks for the pinned openbf stereo limiter.
use std::cell::RefCell;

// Keep upstream's optional Kira adapter, license and test intact.
#[allow(dead_code, unexpected_cfgs)]
#[path = "vendor/openbf/limiter.rs"]
mod donor;

const BLOCK: usize = 256;
struct Mixer {
    limiter: donor::Limiter,
    left: [f32; BLOCK],
    right: [f32; BLOCK],
}
impl Mixer {
    fn process(&mut self, frames: usize) {
        for (l, r) in self.left[..frames]
            .iter_mut()
            .zip(&mut self.right[..frames])
        {
            let input = (*l, *r);
            (*l, *r) = self.limiter.process(
                if input.0.is_finite() { input.0 } else { 0. },
                if input.1.is_finite() { input.1 } else { 0. },
            );
        }
    }
}

thread_local! {static MIXER: RefCell<Option<Mixer>> = const { RefCell::new(None) };}

#[no_mangle]
pub extern "C" fn mix_init(sample_rate: u32) -> u32 {
    if !(8000..=192000).contains(&sample_rate) {
        return 0;
    }
    MIXER.with_borrow_mut(|state| {
        *state = Some(Mixer {
            limiter: donor::Limiter::new(sample_rate),
            left: [0.; BLOCK],
            right: [0.; BLOCK],
        })
    });
    BLOCK as u32
}

#[no_mangle]
pub extern "C" fn mix_delay_frames() -> u32 {
    MIXER.with_borrow(|state| state.as_ref().map_or(0, |m| m.limiter.delay() as u32))
}

#[no_mangle]
pub extern "C" fn mix_left_ptr() -> *mut f32 {
    MIXER.with_borrow_mut(|state| {
        state
            .as_mut()
            .map_or(std::ptr::null_mut(), |m| m.left.as_mut_ptr())
    })
}
#[no_mangle]
pub extern "C" fn mix_right_ptr() -> *mut f32 {
    MIXER.with_borrow_mut(|state| {
        state
            .as_mut()
            .map_or(std::ptr::null_mut(), |m| m.right.as_mut_ptr())
    })
}
#[no_mangle]
pub extern "C" fn mix_process(frames: u32) -> u32 {
    if frames as usize > BLOCK {
        return 0;
    }
    MIXER.with_borrow_mut(|state| {
        if let Some(mixer) = state {
            mixer.process(frames as usize);
            frames
        } else {
            0
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn uninitialized_and_invalid_blocks_cannot_write_outside_mix_storage() {
        assert_eq!(mix_process(128), 0);
        assert!(mix_left_ptr().is_null());
        assert_eq!(mix_init(0), 0);
        assert_eq!(mix_init(192001), 0);
        assert_eq!(mix_init(48000), 256);
        assert!(!mix_left_ptr().is_null());
        assert_ne!(mix_left_ptr(), mix_right_ptr());
        assert_eq!(mix_process(257), 0);
        assert_eq!(mix_process(256), 256);
    }
    #[test]
    fn reinitialize_drops_delayed_audio_and_sanitizes_invalid_samples() {
        assert_eq!(mix_init(24000), 256);
        MIXER.with_borrow_mut(|s| {
            let m = s.as_mut().unwrap();
            m.left[0] = f32::NAN;
            m.right[0] = f32::INFINITY;
            m.left[1] = 3.;
            m.right[1] = -1.5;
        });
        assert_eq!(mix_process(50), 50);
        MIXER.with_borrow(|s| {
            let m = s.as_ref().unwrap();
            assert_eq!((m.left[48], m.right[48]), (0., 0.));
            assert_eq!((m.left[49], m.right[49]), (1., -0.5));
        });
        assert_eq!(mix_init(96000), 256);
        assert_eq!(mix_process(256), 256);
        MIXER.with_borrow(|s| assert!(s.as_ref().unwrap().left.iter().all(|s| *s == 0.)));
    }
}
