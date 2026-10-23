extends RefCounted
## Validated presentation fixture. It does not simulate or authorize combat.
static func event(kind: String, cast_id: int, sequence: int, age: float) -> Dictionary:
    var origin:=Vector3(-0.35,0.68,0.0)
    var forward:=Vector3.RIGHT
    var target:=Vector3(1.10,0.68,0.0)
    var e: Dictionary={"schema":1,"kind":kind,"generation":1,"cast_id":cast_id,"event_seq":sequence,"ability_id":"kodanda","duration_s":1.2,"age_s":age,"time_s":maxf(0,age),"origin":origin,"forward":forward,"target":target,"timing":{"windup_s":.25,"recovery_s":.20,"travel_s":.50,"active_s":0.0,"movement_s":0.0},"geometry":{"kind":"projectiles","origin":origin,"center":target,"forward":forward,"range_m":1.5,"radius_m":.065,"speed_mps":3.0,"projectiles":[{"index":0,"origin":origin,"forward":forward,"delay_s":0.0}]},"receipts":[]}
    if kind=="impact":
        e["contact_position"]=target;e["projectile_index"]=0;e["terminal"]=true;e["reason"]="wall"
    return e
