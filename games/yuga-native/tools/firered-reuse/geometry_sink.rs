// A small geometry recorder for the pinned source's fallback constructors.
// This file is combined with the caller's local source only by record_geometry.py.
#![allow(dead_code)]
use std::collections::HashMap;
use std::marker::PhantomData;
use std::ops::{Add, Mul};

#[derive(Clone, Copy, Debug)]
struct Vec3 {
    x: f32,
    y: f32,
    z: f32,
}
impl Vec3 {
    const ZERO: Self = Self::splat(0.);
    const Y: Self = Self::new(0., 1., 0.);
    const fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }
    const fn splat(v: f32) -> Self {
        Self::new(v, v, v)
    }
    fn write(self) {
        print!(" {} {} {}", self.x, self.y, self.z);
    }
}
impl Add for Vec3 {
    type Output = Vec3;
    fn add(self, r: Self) -> Self {
        Self::new(self.x + r.x, self.y + r.y, self.z + r.z)
    }
}
impl Mul<f32> for Vec3 {
    type Output = Vec3;
    fn mul(self, r: f32) -> Self {
        Self::new(self.x * r, self.y * r, self.z * r)
    }
}
#[derive(Clone, Copy)]
struct Vec2(f32, f32);
impl Vec2 {
    fn new(x: f32, y: f32) -> Self {
        Self(x, y)
    }
    fn distance(self, r: Self) -> f32 {
        (self.0 - r.0).hypot(self.1 - r.1)
    }
}
#[derive(Clone)]
enum Mesh {
    Cube,
    Prism([Vec2; 3], f32),
    Quad([Vec3; 4]),
}
struct Triangle2d;
impl Triangle2d {
    fn new(a: Vec2, b: Vec2, c: Vec2) -> [Vec2; 3] {
        [a, b, c]
    }
}
struct Extrusion;
impl Extrusion {
    fn new(profile: [Vec2; 3], depth: f32) -> Mesh {
        Mesh::Prism(profile, depth)
    }
}
struct Assets<T>(PhantomData<T>);
impl Assets<Mesh> {
    fn add(&mut self, m: Mesh) -> Mesh {
        m
    }
}
struct Transform {
    position: Vec3,
    scale: Vec3,
}
impl Transform {
    fn from_xyz(x: f32, y: f32, z: f32) -> Self {
        Self::from_translation(Vec3::new(x, y, z))
    }
    fn from_translation(position: Vec3) -> Self {
        Self {
            position,
            scale: Vec3::splat(1.),
        }
    }
    fn with_scale(mut self, scale: Vec3) -> Self {
        self.scale = scale;
        self
    }
    fn with_translation(mut self, position: Vec3) -> Self {
        self.position = position;
        self
    }
}
type Entity = usize;
struct Geometry;
struct NotShadowReceiver;
struct NotShadowCaster;
struct PlayerPart(Vec3);
struct NpcPart {
    id: u16,
    offset: Vec3,
    emote: bool,
    model: Option<Entity>,
}
enum Visibility {
    Hidden,
}
struct Mesh3d(Mesh);
struct MeshMaterial3d(usize);
struct Part {
    mesh: Mesh,
    transform: Transform,
    color: usize,
    hidden: bool,
}
impl Part {
    fn write(&self) {
        let pos = self.transform.position;
        let hidden = u8::from(self.hidden);
        match &self.mesh {
            Mesh::Cube => {
                print!("box {} {}", self.color, hidden);
                pos.write();
                self.transform.scale.write();
            }
            Mesh::Prism(profile, depth) => {
                print!("triangular_prism {} {}", self.color, hidden);
                pos.write();
                for p in profile {
                    print!(" {} {}", p.0, p.1);
                }
                print!(" {}", depth);
            }
            Mesh::Quad(vertices) => {
                print!("quad {} {}", self.color, hidden);
                for v in vertices {
                    (*v + pos).write();
                }
            }
        }
        println!();
    }
}
trait MeshBundle {
    fn part(self) -> Part;
}
impl MeshBundle for (Geometry, Mesh3d, MeshMaterial3d, Transform) {
    fn part(self) -> Part {
        Part {
            mesh: self.1 .0,
            color: self.2 .0,
            transform: self.3,
            hidden: false,
        }
    }
}
impl MeshBundle
    for (
        Geometry,
        Mesh3d,
        NotShadowReceiver,
        MeshMaterial3d,
        Transform,
    )
{
    fn part(self) -> Part {
        (self.0, self.1, self.3, self.4).part()
    }
}
struct Commands {
    parts: Vec<Part>,
}
struct Entry<'a> {
    slot: Entity,
    part: &'a mut Part,
}
trait MarkPart: Sized {
    fn annotate(self, _part: &mut Part) {}
}
impl MarkPart for PlayerPart {}
impl MarkPart for NpcPart {}
impl MarkPart for NotShadowCaster {}
impl MarkPart for (NotShadowCaster, NotShadowReceiver) {}
impl MarkPart for (NpcPart, Visibility) {
    fn annotate(self, part: &mut Part) {
        part.hidden = true;
    }
}
impl Entry<'_> {
    fn id(self) -> Entity {
        self.slot
    }
    fn insert<T: MarkPart>(self, tag: T) {
        tag.annotate(self.part);
    }
}
impl Commands {
    fn spawn(&mut self, bundle: impl MeshBundle) -> Entry<'_> {
        let i = self.parts.len();
        self.parts.push(bundle.part());
        self.entity(i)
    }
    fn entity(&mut self, slot: Entity) -> Entry<'_> {
        Entry {
            slot,
            part: &mut self.parts[slot],
        }
    }
}
struct Art {
    cube: Mesh,
    colors: Vec<usize>,
    textures: HashMap<String, usize>,
    kit_grass: usize,
    kit_path: usize,
    kit_stone: usize,
    kit_cliff: usize,
    kit_tree: (),
    kit_grass_piece: (),
    kit_flower: (),
}
fn origin() -> Vec3 {
    Vec3::ZERO
}
fn surface(c: &mut Commands, _: &mut Assets<Mesh>, material: usize, points: [Vec3; 4]) {
    c.spawn((
        Geometry,
        Mesh3d(Mesh::Quad(points)),
        MeshMaterial3d(material),
        Transform::from_translation(origin()),
    ));
}
#[derive(Clone, Copy)]
struct Cell(i32, i32);
struct Prop {
    kind: String,
    at: Cell,
    size: Cell,
    door: Option<Cell>,
}
struct Preferences {
    source_art: bool,
    letsgo_scenery: bool,
}
mod models {
    use super::Vec2;
    pub struct Kit {
        pub ready: bool,
    }
    pub struct Heights {
        pub trees: Vec<Vec2>,
    }
    impl Heights {
        pub fn at(&self, _: f32, _: f32) -> f32 {
            panic!("RomFS terrain unavailable");
        }
    }
}
mod firered_native_prototype {
    use super::{Cell, Prop};
    pub struct Map {
        pub indoor: bool,
        pub id: String,
        pub tiles: Vec<String>,
        pub props: Vec<Prop>,
        pub metatile: u16,
    }
    impl Map {
        pub fn cell(&self, _: Cell) -> u16 {
            self.metatile
        }
    }
}
fn piece(_: &mut Commands, _: &(), _: Vec3, _: usize, _: f32, _: f32) {
    panic!("External scene reference cannot be treated as generated geometry")
}

// SOURCE_FUNCTIONS_GO_HERE

fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let kind = &args[0][..];
    let (w, d) = (args[1].parse().unwrap(), args[2].parse().unwrap());
    let mut c = Commands { parts: Vec::new() };
    let texture_names = [
        "wall",
        "roof",
        "lab_wall",
        "lab_roof",
        "window",
        "door",
        "fixture_ground",
    ];
    let art = Art {
        cube: Mesh::Cube,
        colors: (0..22).collect(),
        textures: texture_names
            .iter()
            .enumerate()
            .map(|(i, n)| (n.to_string(), 22 + i))
            .collect(),
        kit_grass: 29,
        kit_path: 30,
        kit_stone: 31,
        kit_cliff: 32,
        kit_tree: (),
        kit_grass_piece: (),
        kit_flower: (),
    };
    let mut meshes = Assets(PhantomData);
    match kind {
        "tree" => tree(&mut c, &art, 0., 0.),
        "window_front" | "window_side" => window(&mut c, &art, 0., 0.45, 0., kind == "window_side"),
        "player" | "npc" => character(&mut c, &art, Vec3::ZERO, kind == "player", 1, None),
        "house" | "house_door_mat" | "lab" | "house_panels" | "lab_panels" => {
            let x = if kind == "house_door_mat" { 4 } else { 0 };
            let p = Prop {
                kind: kind.split('_').next().unwrap().into(),
                at: Cell(x, 0),
                size: Cell(w, d),
                door: None,
            };
            building(&mut c, &art, &mut meshes, &p, kind.ends_with("_panels"));
        }
        "table" | "sofa" | "bed" | "plant" => {
            let p = Prop {
                kind: kind.into(),
                at: Cell(0, 0),
                size: Cell(w, d),
                door: None,
            };
            furniture(&mut c, &art, &p);
        }
        _ => {
            let tile = &args[3];
            let mid = args[4].parse().unwrap();
            let indoor = args[5] == "indoor";
            let mut map = firered_native_prototype::Map {
                indoor,
                id: "fixture".into(),
                tiles: tile.split('/').map(str::to_owned).collect(),
                metatile: mid,
                props: Vec::new(),
            };
            let kit_enabled = kind.starts_with("kit_");
            let settings = Preferences {
                source_art: kind == "field_ground_panel",
                letsgo_scenery: kit_enabled,
            };
            let kit = models::Kit { ready: kit_enabled };
            // A second pass with the same empty tile excludes its base under standalone prop outputs.
            if kind == "fence" || kind == "sign" {
                let mut baseline = Commands { parts: Vec::new() };
                spawn_map_blocks(
                    &mut baseline,
                    &art,
                    &mut meshes,
                    &map,
                    &settings,
                    &kit,
                    None,
                );
                map.props.push(Prop {
                    kind: kind.into(),
                    at: Cell(0, 0),
                    size: Cell(w, d),
                    door: None,
                });
                spawn_map_blocks(&mut c, &art, &mut meshes, &map, &settings, &kit, None);
                c.parts.drain(..baseline.parts.len());
            } else {
                spawn_map_blocks(&mut c, &art, &mut meshes, &map, &settings, &kit, None);
            }
        }
    }
    for part in c.parts {
        part.write();
    }
}
