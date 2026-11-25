use serde::{Deserialize, Serialize};

pub type Point = [f64; 2];
pub const DT: f64 = 0.05;
pub fn distance(a: Point, b: Point) -> f64 {
    (a[0] - b[0]).hypot(a[1] - b[1])
}

#[derive(Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Hero {
    pub id: String,
    pub name: String,
    pub health: f64,
    pub speed: f64,
    pub damage: f64,
    pub fire_interval: f64,
    pub projectile_speed: f64,
    pub abilities: [Ability; 3],
}
#[derive(Clone, Deserialize, Serialize)]
pub struct Ability {
    pub kind: Kind,
    pub name: String,
    pub cooldown: f64,
    pub power: f64,
    pub range: f64,
    pub radius: f64,
    pub duration: f64,
    pub mechanic: Option<Mechanic>,
    pub windup: Option<f64>,
}
#[derive(Clone, Copy, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Kind {
    Bolt,
    Line,
    Burst,
    Cone,
    Dash,
    Leap,
    Nova,
    Heal,
    Ward,
    Slow,
    Pull,
    Summon,
}
#[derive(Clone, Copy, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Mechanic {
    DawnVolley,
    MountainDescent,
    MithilaSanctuary,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Rules {
    pub max_actors: usize,
    pub max_projectiles: usize,
    pub max_zones: usize,
}
#[derive(Clone, Serialize)]
pub struct Cast {
    pub slot: usize,
    pub mechanic: Mechanic,
    pub release: f64,
    pub end: f64,
    pub origin: Point,
    pub target: Point,
    pub yaw: f64,
    pub pitch: f64,
    pub phase: &'static str,
}
#[derive(Serialize)]
pub struct Actor {
    pub id: String,
    pub kind: &'static str,
    pub team: &'static str,
    pub hero: String,
    pub pos: Point,
    pub y: f64,
    pub yaw: f64,
    pub hp: f64,
    pub max_hp: f64,
    pub shield: f64,
    pub slow: f64,
    pub ward: f64,
    pub cds: [f64; 3],
    pub fire_cd: f64,
    pub cast: Option<Cast>,
    pub expires_at: Option<f64>,
    pub respawn: f64,
    #[serde(skip)]
    pub kit: usize,
    #[serde(skip)]
    pub vy: f64,
    #[serde(skip)]
    pub jumping: bool,
    #[serde(skip)]
    pub attack: f64,
    #[serde(skip)]
    pub waypoint: usize,
    #[serde(skip)]
    pub deaths: u32,
}
impl Actor {
    pub fn new(id: &str, team: &'static str, kit: usize, def: &Hero, pos: Point) -> Self {
        Self {
            id: id.into(),
            team,
            kind: "hero",
            hero: def.id.clone(),
            kit,
            pos,
            y: 0.,
            yaw: if team == "sun" {
                0.
            } else {
                std::f64::consts::PI
            },
            hp: def.health,
            max_hp: def.health,
            shield: 0.,
            slow: 0.,
            ward: 0.,
            cds: [0.; 3],
            fire_cd: 0.,
            cast: None,
            expires_at: None,
            respawn: 0.,
            vy: 0.,
            jumping: false,
            attack: 0.,
            waypoint: 0,
            deaths: 0,
        }
    }
    pub fn hurt(&mut self, amount: f64) {
        let absorbed = amount.min(self.shield);
        self.shield -= absorbed;
        self.hp = (self.hp - amount + absorbed).max(0.);
        if self.hp <= 0. && self.kind == "hero" {
            self.deaths += 1;
            self.cast = None;
            self.y = 0.;
            self.vy = 0.;
            self.respawn = (7. + f64::from(self.deaths) * 1.5).min(18.);
            self.ward = 0.;
            self.shield = 0.;
            self.slow = 0.;
        }
    }
}
#[derive(Serialize)]
pub struct Shot {
    pub owner: String,
    pub team: &'static str,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub vx: f64,
    pub vy: f64,
    pub vz: f64,
    pub damage: f64,
    pub radius: f64,
    pub life: f64,
}
#[derive(Serialize)]
pub struct Zone {
    pub kind: Kind,
    pub mechanic: Option<Mechanic>,
    pub x: f64,
    pub z: f64,
    pub power: f64,
    pub radius: f64,
    pub life: f64,
    pub duration: f64,
    pub team: &'static str,
}
#[derive(Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Input {
    pub actor: Option<String>,
    pub ticks: u32,
    pub cast: Option<usize>,
    pub movement: Point,
    pub yaw: Option<f64>,
    pub pitch: f64,
    pub fire: bool,
    pub jump: bool,
}
