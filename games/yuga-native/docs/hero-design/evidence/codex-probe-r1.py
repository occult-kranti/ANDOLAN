import copy,hashlib,importlib.util,json
from pathlib import Path
root=Path("/workspace/ANDOLAN")
validator=root/"games/yuga-native/tools/check-hero-codex.py"
spec=importlib.util.spec_from_file_location("codex_qa",validator);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
raw,base=m.load_catalogue(m.DEFAULT);baseline=m.browser_roster(str(root))
def demo(d):return d["heroes"][0]["abilities"][2]["native_demo"]
cases=[
 ("baseline",lambda d:None),
 ("huge_integer_radius",lambda d:demo(d).update(radius_m=10**400)),
 ("wrong_baseline_effect_family",lambda d:demo(d).update(family="summon_pair")),
 ("zero_complete_effect_geometry",lambda d:demo(d).update(range_m=0,radius_m=0,width_m=0,height_m=0)),
 ("positive_projectile_range_zero_travel",lambda d:(demo(d)["timing"].update(travel_s=0),demo(d).update(payload_at_s=1))),
 ("bool_telegraph_lead",lambda d:demo(d)["telegraph"].update(lead_s=True)),
 ("bool_global_light_cap",lambda d:d["limits"].update(max_lights_per_cast=True)),
 ("invalid_palette_color",lambda d:d["heroes"][0]["art_direction"]["palette"].update(body="not-a-color")),
 ("primary_claims_implemented",lambda d:d["heroes"][0]["primary"].update(native_status="production_accepted")),
]
rows=[]
for name,mutate in cases:
 d=copy.deepcopy(base);mutate(d)
 try:
  errors=m.validate(d,root,baseline);rows.append({"case":name,"returned_errors":errors,"accepted":not errors,"exception":None})
 except Exception as exc:rows.append({"case":name,"accepted":None,"exception":repr(exc)})
report={"validator_sha256":hashlib.sha256(validator.read_bytes()).hexdigest(),"catalogue_sha256":hashlib.sha256(raw).hexdigest(),"rows":rows,"scope":"Independent catalogue validator mutations; no native rendering or gameplay claim"}
out=Path("/workspace/scratch/yuga-batch1-independent/codex-probe-r1.json");out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
