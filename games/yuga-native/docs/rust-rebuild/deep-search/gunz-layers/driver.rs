use glam::{Quat, Vec3};
use std::fmt::Write as _;
use std::io::{self, Read};

#[derive(Clone, Copy)]
struct Transform {
    translation: Vec3,
    rotation: Quat,
    scale: Vec3,
}

struct Key<T> {
    tick: u32,
    value: T,
}

struct Upper {
    time: f32,
    looping: Loop,
    releasing: bool,
    fade: f32,
    weight: f32,
}

struct Speeds {
    speed: f32,
    upper_speed: f32,
}

include!(env!("GUNZ_FUNCTIONS"));

struct Joint {
    upper: bool,
    run: Vec<Key<Quat>>,
    fire: Vec<Key<Quat>>,
}

fn sample_local(keys: &[Key<Quat>], time: f32) -> Transform {
    Transform {
        translation: Vec3::ZERO,
        rotation: sample(keys, time * 4800.0, |v| v, Quat::slerp).expect("empty rotation track"),
        scale: Vec3::ONE,
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut words = input.split_whitespace();
    let mut number = || words.next().unwrap().parse::<f32>().unwrap();
    let (run_end, fire_end, mut run_t, dt, frames, joints) = (
        number(),
        number(),
        number(),
        number(),
        number() as usize,
        number() as usize,
    );
    let mut body = Vec::with_capacity(joints);
    for _ in 0..joints {
        let upper = number() > 0.0;
        let mut keys = || {
            (0..number() as usize)
                .map(|_| {
                    let tick = number() as u32;
                    let value = Quat::from_xyzw(number(), number(), number(), number()).normalize();
                    Key { tick, value }
                })
                .collect()
        };
        body.push(Joint {
            upper,
            run: keys(),
            fire: keys(),
        });
    }
    assert!(words.next().is_none());
    let mut layer = Upper {
        time: 0.0,
        looping: Loop::OnceLower,
        releasing: false,
        weight: 0.0,
        fade: 0.05,
    };
    let speeds = Speeds {
        speed: 1.0,
        upper_speed: 1.0,
    };
    let mut out = String::new();
    for _ in 0..frames {
        run_t = advance(run_t, dt, run_end, Loop::Wrap);
        advance_upper(&mut layer, &speeds, fire_end, dt);
        let weight = smooth(layer.weight);
        write!(&mut out, "{run_t} {} {weight}", layer.time).unwrap();
        for joint in &body {
            let base = sample_local(&joint.run, run_t);
            let final_pose = if joint.upper {
                blend(base, sample_local(&joint.fire, layer.time), weight)
            } else {
                base
            };
            for v in final_pose.rotation.to_array() {
                write!(&mut out, " {v}").unwrap();
            }
        }
        out.push('\n');
    }
    print!("{out}");
}
