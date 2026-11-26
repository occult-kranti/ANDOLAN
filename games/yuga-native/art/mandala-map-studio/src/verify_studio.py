#!/usr/bin/env python3
"""Verify the registered studio release, including decoded picture content and motion."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from hashlib import sha256
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
from xml.etree import ElementTree as ET

from PIL import Image, ImageChops, ImageStat

ROOT=Path(__file__).resolve().parents[1]
CAPTURE=(128,72)
CHANNEL=CAPTURE[0]*CAPTURE[1]

def require(condition,message):
    if not condition:raise ValueError(message)

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def run(command):
    return subprocess.run(command,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout

def manifest_hash(files):
    h=sha256()
    for name,path in sorted(files):
        h.update(name.encode()+b"\0"+digest(path).encode()+b"\n")
    return h.hexdigest()

def webp(path):
    with Image.open(path) as src:
        require(src.format=="WEBP" and src.n_frames==1,f"Expected one WebP at {path}")
        src.load()
        size=src.size
        thumb=src.convert("L").resize(CAPTURE,Image.Resampling.BOX)
    spread=ImageStat.Stat(thumb).stddev[0]
    require(min(size)>=96 and spread>2 and thumb.getextrema()[1]-thumb.getextrema()[0]>24,
            f"Empty or tiny image {path}")
    return size,thumb.tobytes()

def stills_and_drawings(rows,index):
    concepts=ROOT/"concepts"
    run([sys.executable,str(concepts/"verify.py")])
    require(len(index["boards"])==14,"Expected fourteen full concept boards")
    boards={item["id"]: item for item in index["boards"]}
    sources=set()
    for board in boards.values():
        size,_=webp(concepts/board["file"])
        require(list(size)==[board["width"],board["height"]],board["id"]+" board size disagrees")
        sources.add(board["source_png_sha256"])
    require(len(sources)==len(boards),"Two full boards claim the same source image")
    hero=index["hero"]
    hero_size,_=webp(concepts/hero["file"])
    hero_brief=json.loads((concepts/hero["brief_file"]).read_text())
    require(hero_brief["webp_sha256"]==digest(concepts/hero["file"]) and hero_brief["prompt"],
            "Cover painting does not match its recorded brief and digest")
    pinned={"paintings":[],"renders":[],"drawings":[]}
    signatures={"paintings":set(),"renders":set()}
    sizes={"paintings":set(),"renders":set()}
    indexed_pages=set()
    crop_errors=[];drawn_geometry=set();render_views=set()
    ns="{http://www.w3.org/2000/svg}"
    for row in rows:
        ident=row["id"]; graph=ROOT/row["plate"]
        svg=ET.parse(graph).getroot()
        require(svg.find(ns+"title").text==row["title"],ident+" SVG title mismatch")
        views=[el for el in svg.findall(ns+"g") if el.get("data-view")]
        require(len(views)==2 and all(len(list(el.iter()))>=4 for el in views),ident+" missing drawn views")
        # Two sheets with different titles still have to show different geometry.
        for view in views:
            for el in view.iter():
                for child in list(el):
                    if child.tag in (ns+"text",ns+"title"):el.remove(child)
        shape_key=sha256(b"".join(ET.tostring(view) for view in views)).digest()
        require(shape_key not in drawn_geometry,"Relabelled duplicate drawing for "+ident)
        drawn_geometry.add(shape_key)
        pinned["drawings"].append((ident,graph))
        item=index["items"][ident]
        art=concepts/item["file"]; render=ROOT/row["render"]
        for key,path in [("paintings",art),("renders",render)]:
            sz,raw=webp(path)
            signature=sha256(raw).digest()
            require(signature not in signatures[key],f"Duplicate decoded {key} image at {ident}")
            signatures[key].add(signature);sizes[key].add(sz);pinned[key].append((ident,path))
        with Image.open(render) as sheet:
            require(sheet.size==(1538,1018),"Unexpected four-view sheet size at "+ident)
            distinct=set()
            for i in range(4):
                x=22+i%2*758; y=97+i//2*451
                camera=sheet.crop((x+22,y+17,x+714,y+398)).convert("L").resize(CAPTURE,Image.Resampling.BOX)
                require(ImageStat.Stat(camera).stddev[0]>2,"Blank camera panel at "+ident)
                distinct.add(sha256(camera.tobytes()).digest())
            require(len(distinct)==4,"Four separate views required for "+ident)
            render_views.update(distinct)
        bp=concepts/boards[item["board"]]["file"]
        indexed_pages.add(bp)
        with Image.open(bp) as full, Image.open(art) as individual:
            crop=full.crop(item["source_box"]).convert("L").resize(CAPTURE,Image.Resampling.BOX)
            region=individual.convert("L").resize(CAPTURE,Image.Resampling.BOX)
            delta=ImageStat.Stat(ImageChops.difference(crop,region)).mean[0]
            require(delta<10,f"{ident} crop does not agree with its assigned board ({delta:.1f} luma levels)")
            crop_errors.append(delta)
    require(len(indexed_pages)==14,"Every painted board must have a catalog subject")
    return {"boards":len(boards),"individual_paintings":len(rows),"drawings":len(rows),"renders":len(rows),
            "drawing_views_per_sheet":2,"camera_views_per_render":4,"distinct_render_interiors":len(render_views),"unique_drawings_with_text_hidden":len(drawn_geometry),"cover_painting_px":list(hero_size),
            "painting_sizes_px":sorted(map(list,sizes["paintings"])),"render_sizes_px":sorted(map(list,sizes["renders"])),
            "worst_painted_crop_mean_luma_error":round(max(crop_errors),3),
            "content_sha256":{key:manifest_hash(tuples) for key,tuples in pinned.items()},
            "boards_sha256":manifest_hash([(b["id"],concepts/b["file"]) for b in boards.values()])}

def film(path):
    meta=json.loads(run(["ffprobe","-v","error","-show_streams","-show_chapters","-of","json",str(path)]))
    stream,=[s for s in meta["streams"] if s["codec_type"]=="video"]
    rate=Fraction(stream["avg_frame_rate"]);size=[stream["width"],stream["height"]]
    require(stream["codec_name"]=="h264" and rate>0 and stream.get("pix_fmt")=="yuv420p",str(path)+" unplayable video encoding")
    # The centre 80% by 62% excludes the title and timing strips. Decode every presentation
    # frame. A moving caption or two equal end poses alone cannot establish this test.
    raw=run(["ffmpeg","-nostdin","-v","error","-xerror","-threads","1","-filter_threads","1",
             "-i",str(path),"-map","0:v:0","-vf","crop=iw*0.80:ih*0.62,scale=128:72:flags=area,format=gray",
             "-fps_mode","passthrough","-threads","1","-f","rawvideo","pipe:1"])
    require(len(raw)%CHANNEL==0,f"Partial frame in {path}")
    frames=len(raw)//CHANNEL
    require(frames>=3 and frames==int(stream["nb_frames"]),f"Undecodable or missing frames in {path}")
    first=Image.frombytes("L",CAPTURE,raw[:CHANNEL])
    distinct=set();differences=[];coverage=[]
    for offset in range(0,len(raw),CHANNEL):
        chunk=raw[offset:offset+CHANNEL];distinct.add(sha256(chunk).digest())
        delta=ImageChops.difference(first,Image.frombytes("L",CAPTURE,chunk))
        hist=delta.histogram()
        differences.append(sum(i*n for i,n in enumerate(hist))/CHANNEL)
        coverage.append(sum(hist[5:])/CHANNEL)
    require(len(distinct)>=3 and max(differences)>.65 and max(coverage)>.012,
            f"Insufficient motion in centre of {path.name}: {max(differences):.3f} luma, {max(coverage):.4f} changed area")
    chapters=[{"title":c.get("tags",{}).get("title"),"start_s":float(c["start_time"]),"end_s":float(c["end_time"])} for c in meta.get("chapters",[])]
    return {"width":size[0],"height":size[1],"fps":float(rate),"decoded_frames":frames,"seconds":round(float(frames/rate),4),
            "distinct_centres":len(distinct),"best_first_to_later_luma":round(max(differences),3),
            "best_first_to_later_changed_fraction":round(max(coverage),4),"chapters":chapters}

def check_clips(rows,workers):
    paths=[ROOT/row["clip"] for row in rows]
    blobs=[digest(p) for p in paths]
    require(len(set(blobs))==len(rows),"Duplicate element films")
    with ThreadPoolExecutor(max_workers=workers) as pool: reviews=list(pool.map(film,paths))
    bands={}
    for row,rec in zip(rows,reviews):
        bounds=(rec["width"],rec["height"],rec["fps"],rec["decoded_frames"])
        bands.setdefault(bounds,[]).append(row["id"])
    return {"clips":len(rows),"frames_decoded":sum(i["decoded_frames"] for i in reviews),
            "aggregate_seconds":round(sum(i["seconds"] for i in reviews),3),
            "formats":[{"size_px":[w,h],"fps":fps,"frames":frames,"count":len(ids)}
                       for (w,h,fps,frames),ids in sorted(bands.items())],
            "min_distinct_centres":min(i["distinct_centres"] for i in reviews),
            "min_best_first_to_later_luma":min(i["best_first_to_later_luma"] for i in reviews),
            "min_best_first_to_later_changed_fraction":min(i["best_first_to_later_changed_fraction"] for i in reviews),
            "sha256":manifest_hash([(row["id"],p) for row,p in zip(rows,paths)])}

def glb(path):
    data=path.read_bytes()
    magic,version,length=struct.unpack_from("<4sII",data)
    require(magic==b"glTF" and version==2 and length==len(data),"Invalid GLB header or length")
    cursor=12;chunks=[]
    while cursor<len(data):
        size,kind=struct.unpack_from("<I4s",data,cursor);cursor+=8
        require(size%4==0 and cursor+size<=len(data),"Invalid GLB chunk alignment")
        chunks.append((kind,memoryview(data)[cursor:cursor+size]));cursor+=size
    require([c[0] for c in chunks]==[b"JSON",b"BIN\0"],"Expected one JSON and one embedded binary chunk")
    doc=json.loads(chunks[0][1].tobytes());binary=chunks[1][1]
    require(doc["asset"]["version"]=="2.0" and len(doc["buffers"])==1 and "uri" not in doc["buffers"][0],"GLB references an external buffer")
    require(0<=len(binary)-doc["buffers"][0]["byteLength"]<=3,"GLB buffer length mismatch")
    for v in doc["bufferViews"]:
        require(v["buffer"]==0 and 0<=v.get("byteOffset",0)<=v.get("byteOffset",0)+v["byteLength"]<=len(binary),"Out-of-bounds glTF view")
    type_width={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT2":4,"MAT3":9,"MAT4":16}
    bytes_per={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
    for a in doc["accessors"]:
        v=doc["bufferViews"][a["bufferView"]];size=type_width[a["type"]]*bytes_per[a["componentType"]]
        require(a["count"]>0 and a.get("byteOffset",0)+(a["count"]-1)*v.get("byteStride",size)+size<=v["byteLength"],"Out-of-bounds glTF accessor")
    for image in doc.get("images",[]):
        require("uri" not in image and 0<=image["bufferView"]<len(doc["bufferViews"]),"GLB has an external or missing image")
    index_max={}
    def maximum_index(index):
        if index not in index_max:
            a=doc["accessors"][index];v=doc["bufferViews"][a["bufferView"]]
            unpack=struct.Struct("<"+{5121:"B",5123:"H",5125:"I"}[a["componentType"]])
            start=v.get("byteOffset",0)+a.get("byteOffset",0);stride=v.get("byteStride",unpack.size)
            if stride==unpack.size:
                values=unpack.iter_unpack(binary[start:start+a["count"]*stride])
            else:values=(unpack.unpack_from(binary,start+i*stride) for i in range(a["count"]))
            index_max[index]=max(x[0] for x in values)
        return index_max[index]
    triangle_counts=[];normal_mapped=0
    for mesh in doc["meshes"]:
        triangles=0
        for p in mesh["primitives"]:
            require(p.get("mode",4)==4,"Expected triangle primitives")
            if "material" in p and "normalTexture" in doc["materials"][p["material"]]:
                normal_mapped+=1
                require("TANGENT" in p["attributes"],f"{path.name} lacks the exported tangents for a normal-mapped primitive")
                tangents=doc["accessors"][p["attributes"]["TANGENT"]]
                require(tangents["type"]=="VEC4" and tangents["count"]==doc["accessors"][p["attributes"]["POSITION"]]["count"],"Invalid mesh tangent frame")
            pos=doc["accessors"][p["attributes"]["POSITION"]]
            require(pos["type"]=="VEC3" and all(math.isfinite(n) for n in pos["min"]+pos["max"]),"Invalid mesh bounds")
            ia=doc["accessors"][p["indices"]]
            require(ia["type"]=="SCALAR" and ia["count"]%3==0 and maximum_index(p["indices"])<pos["count"],"Invalid triangle indices")
            triangles+=ia["count"]//3
        triangle_counts.append(triangles)
    graph=doc["nodes"];reachable=set()
    def visit(i):
        if i in reachable:return
        reachable.add(i);node=graph[i]
        if "mesh" in node:require(0<=node["mesh"]<len(doc["meshes"]),"Missing node mesh")
        for child in node.get("children",[]):visit(child)
    for i in doc["scenes"][doc["scene"]]["nodes"]:visit(i)
    require(len(reachable)==len(graph),"GLB contains unreachable scene nodes")
    return {"bytes":len(data),"sha256":digest(path),"version":version,"reachable_nodes":len(graph),
            "mesh_definitions":len(doc["meshes"]),"triangles_in_mesh_definitions":sum(triangle_counts),
            "mesh_instances":sum("mesh" in n for n in graph),"triangles_in_scene":sum(triangle_counts[n["mesh"]] for n in graph if "mesh" in n),
            "normal_mapped_primitives_with_tangents":normal_mapped,"materials":len(doc.get("materials",[])),"embedded_images":len(doc.get("images",[]))}

def scene(rows,layout_hash):
    path=ROOT/"mandala-rift.blend"
    read_header=path.read_bytes()[:12]
    require(read_header.startswith(b"BLENDER") or read_header.startswith(b"\x28\xb5\x2f\xfd") or read_header.startswith(b"\x1f\x8b"),"Invalid Blender container")
    expression="""import bpy,json
groups={c.get("catalog_id"):sum(o.type=="MESH" for o in c.all_objects) for c in bpy.data.collections if c.get("catalog_id")}
print("STUDIO_VALIDATION "+json.dumps({"groups":groups,"version":list(bpy.data.version),"layout":bpy.context.scene.get("layout_sha256"),"cameras":len(bpy.data.cameras),"meshes":len(bpy.data.meshes)}))
"""
    output=run(["blender","-b","--factory-startup","--disable-autoexec","-t","1",str(path),
                "--python-exit-code","1","--python-expr",expression]).decode("utf-8","replace").splitlines()
    receipt=json.loads(next(line.removeprefix("STUDIO_VALIDATION ") for line in output if line.startswith("STUDIO_VALIDATION ")))
    require(set(receipt["groups"])=={r["id"] for r in rows} and all(n>0 for n in receipt["groups"].values()),"Blender scene lacks a complete set of nonempty element collections")
    require(receipt["layout"]==layout_hash and receipt["cameras"]>0,"Scene has a different map registration or no cameras")
    return {"sha256":digest(path),"bytes":path.stat().st_size,"saved_version":receipt["version"],
            "element_collections":len(receipt["groups"]),"min_mesh_objects_per_collection":min(receipt["groups"].values()),
            "mesh_datablocks":receipt["meshes"],"cameras":receipt["cameras"]}

def assembly(row):
    files={k:ROOT/v for k,v in row["assembly"].items()}
    size,_=webp(files["plate"])
    manifest=json.loads(files["parts"].read_text())
    parts=manifest["parts"]; names=[p["name"] for p in parts]
    require(len(names)==62 and set(names)==set(row["parts"]), "Construction diagram differs from 62 registered pavilion parts")
    require(all(len(p["rest_center_m"])==len(p["exploded_offset_m"])==3 for p in parts), "Invalid registered part transforms")
    groups=Counter(p["group"] for p in parts)
    require(set(groups)=={"foundations","piers","threshold","roof","crown"} and dict(groups)==manifest["groups"], "Missing or inconsistent pavilion assembly stages")
    require(manifest["installed_envelope_m"]==row["size_m"],"Installed pavilion differs from its registered envelope")
    for piece in parts:
        start,apart=piece["open_frames"];close,end=piece["close_frames"]
        require(1<=start<apart<=close<end<=manifest["frames"],"Unordered pavilion motion for "+piece["name"])
        require(all(math.isfinite(n) for n in piece["rest_center_m"]+piece["exploded_offset_m"]),"Invalid rest transform")
        require(any(abs(n)>0.001 for n in piece["exploded_offset_m"]),"Part lost its assembly motion")

    require(manifest["clear_width_m"]==row["clear_width_m"] and math.isclose(manifest["clear_height_m"],row["clear_height_m"],abs_tol=.001),"Pavilion passage dimension mismatch")
    require(manifest["source_glb_sha256"]==digest(ROOT.parent.parent/"docs/design/ember-rite-5v5/atlas/massing/mandala-architecture.glb"),"Pavilion construction starts from a different registered model")
    moving=film(files["clip"])
    require(moving["decoded_frames"]==manifest["frames"] and moving["fps"]==manifest["fps"],"Construction clip differs from its frame manifest")
    return {"parts":len(names),"groups":dict(sorted(groups.items())),"plate_px":list(size),"video":moving,
            "files_sha256":{key:digest(p) for key,p in sorted(files.items())}}

class HtmlFiles(HTMLParser):
    def __init__(self):
        super().__init__();self.refs=set()
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        for key in ("src","href","poster"):
            if key in d and d[key].startswith("./"):self.refs.add(d[key][2:])

def check_gallery():
    gallery=ROOT/"index.html";resource=HtmlFiles();resource.feed(gallery.read_text())
    required={"gallery.js","gallery.css","district.webp","tour.mp4","mandala-rift.blend","mandala-rift.glb","catalog.json"}
    require(required<=resource.refs,"Gallery does not link all studio entry resources")
    for ref in resource.refs-{"verification.json"}:
        require((ROOT/ref).is_file(),"Missing gallery entry asset "+ref)
    return {"links_checked":len(resource.refs),"entry_sha256":digest(gallery)}

def models(rows):
    root=ROOT/"models";index=json.loads((root/"index.json").read_text())
    registered=json.loads((ROOT/"catalog.json").read_text())["layout_sha256"]
    require(index["layout_sha256"]==registered and index["axes"]==["east","up","south"],"Individual models use a different map registration")
    records=index["models"]
    require(set(records)=={r["id"] for r in rows}, "Individual model manifest coverage differs")
    files=[];triangles=0;nodes=0;floor_counts=Counter()
    for row in rows:
        ident=row["id"];entry=records[ident];filename=root/(ident+".glb")
        require(entry["file"]==filename.name,"Unexpected model file for "+ident)
        result=glb(filename)
        require(result["bytes"]==entry["bytes"] and result["sha256"]==entry["sha256"], "Model digest differs for "+ident)
        require(result["triangles_in_scene"]==entry["triangles"] and result["mesh_instances"]==entry["mesh_instances"],"Invalid model index statistics for "+ident)
        pos=row["center_xyz"]
        require(entry["origin_map_xyz_m"]==pos and entry["origin_gltf_m"]==[pos[0],pos[2],-pos[1]],"Incorrect local model origin for "+ident)
        lower,upper=entry["bounds_local_gltf_m"]
        require(all(math.isfinite(v) for v in lower+upper) and all(abs((hi-lo)-size)<.001 for lo,hi,size in zip(lower,upper,entry["size_m"])), "Invalid bounds in "+ident)
        if entry["floor_triangles"]:
            floor_counts[row["kind"]]+=1
        triangles+=entry["triangles"];nodes+=result["reachable_nodes"];files.append((ident,filename))
    # This independent second pass measures the transformed, indexed vertex positions
    # against the manifest's world-to-local bounds rather than trusting JSON min/max.
    run([sys.executable,str(ROOT/"src/export_elements.py"),"--check"])
    return {"model_count":len(files),"models_with_floor_by_kind":dict(sorted(floor_counts.items())),
            "sum_individual_triangles":triangles,"sum_reachable_nodes":nodes,
            "manifest_sha256":digest(root/"index.json"),"files_sha256":manifest_hash(files)}

def artbook(rows):
    import fitz
    path=ROOT/"mandala-rift-artbook.pdf"
    with fitz.open(path) as book:
        require(len(book)==len(rows)+2,"The district art book must include a page for every element")
        links=0
        for page,row in zip(list(book)[2:],rows):
            page_text=" ".join(page.get_text().split())
            require(row["title"] in page_text, "Missing art book heading: "+row["id"])
            target="#element="+row["id"]
            require(any(link.get("uri","").endswith(target) for link in page.get_links()),"Missing art book permalink: "+row["id"])
            links+=1
        return {"pages":len(book),"element_permalinks":links,"file_bytes":path.stat().st_size,"sha256":digest(path)}

def lighting():
    path=ROOT/"lighting/study.webp"
    dims,_=webp(path)
    require(dims==(1480,1270),"The published lighting study is not the three full-resolution shots")
    regions={"ghat":(20,20,1460,670),"ewer":(20,743,733,1191),"pavilion":(747,743,1460,1191)}
    fingerprints=set()
    with Image.open(path) as sheet:
        for label,box in regions.items():
            centre=sheet.crop(box).convert("L").resize(CAPTURE,Image.Resampling.BOX)
            require(ImageStat.Stat(centre).stddev[0]>3,label+" lighting shot is blank")
            fingerprints.add(sha256(centre.tobytes()).digest())
    require(len(fingerprints)==len(regions),"Lighting sheet repeats one camera cut")
    return {"size_px":list(dims),"distinct_rendered_views":sorted(regions),"sha256":digest(path)}

def verify(workers):
    catalog=json.loads((ROOT/"catalog.json").read_text());rows=catalog["elements"]
    run([sys.executable,str(ROOT/"src/catalog.py"),"--check"])
    require(len(rows)==53,"Catalog entries changed; review coverage")
    ids={r["id"] for r in rows}
    for dirname,ext in [("plates",".svg"),("renders",".webp"),("clips",".mp4"),("concepts/items",".webp"),("models",".glb")]:
        actual={p.stem for p in (ROOT/dirname).glob("*"+ext)}
        require(actual==ids,f"{dirname} coverage differs: {sorted(ids ^ actual)}")
    index=json.loads((ROOT/"concepts/index.json").read_text())
    pictures=stills_and_drawings(rows,index)
    district_size,_=webp(ROOT/"district.webp")
    construction=assembly(next(r for r in rows if r["kind"]=="architecture"))
    clips=check_clips(rows,workers);tour=film(ROOT/"tour.mp4")
    require(len(tour["chapters"])>=2 and all(c["title"] and c["end_s"]>c["start_s"] for c in tour["chapters"]),"Tour lacks real named chapter intervals")
    return {"schema":1,"district":"Mandala Rift","layout_sha256":catalog["layout_sha256"],"catalog_sha256":digest(ROOT/"catalog.json"),
            "elements_by_kind":dict(sorted(Counter(r["kind"] for r in rows).items())),
            "gallery":check_gallery(),"art_book":artbook(rows),"stills":pictures,"district_view":{"size_px":list(district_size),"sha256":digest(ROOT/"district.webp")},
            "lighting_study":lighting(),
            "element_films":clips,"district_tour":dict(tour,sha256=digest(ROOT/"tour.mp4")),
            "construction":construction,"editable_scene":scene(rows,catalog["layout_sha256"]),
            "portable_scene":glb(ROOT/"mandala-rift.glb"),"element_models":models(rows)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check",action="store_true",help="repeat the complete audit and compare the stored receipt")
    p.add_argument("--jobs",type=int,choices=range(1,9),default=2,help="parallel movie decoders (1–8)")
    args=p.parse_args()
    out=ROOT/"verification.json"
    try:
        receipt=verify(args.jobs)
        raw=json.dumps(receipt,ensure_ascii=False,indent=2)+"\n"
        if args.check:
            require(out.is_file() and out.read_text()==raw,"Studio verification receipt is missing or stale. Rebuild it with verify_studio.py")
        else:out.write_text(raw)
        print(f"Verified 53 element studies, {receipt['element_films']['frames_decoded']} element frames, "
              f"{receipt['district_tour']['decoded_frames']} tour frames and {receipt['construction']['parts']} pavilion parts.")
    except (ValueError,KeyError,FileNotFoundError,subprocess.CalledProcessError) as exc:
        sys.exit(str(exc)+((": "+exc.stderr.decode("utf8","replace")[:1400]) if isinstance(exc,subprocess.CalledProcessError) and exc.stderr else ""))

if __name__=="__main__":main()
