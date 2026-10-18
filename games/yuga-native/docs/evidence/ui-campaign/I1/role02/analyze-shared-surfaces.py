#!/usr/bin/env python3
"""Read-only source contrast/sizing diagnostic; not rendered accessibility certification."""
import argparse,hashlib,json,pathlib,re
p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--report',required=True);a=p.parse_args();root=pathlib.Path(a.project)
files=['scripts/hero_ui_theme.gd','scripts/launch_shell.gd','scripts/rama_hero_hud.gd','scripts/confluence_world.gd','scripts/world_atlas.gd']
sources={f:(root/f).read_text() for f in files}; theme=sources[files[0]]
colors=dict(re.findall(r'const (\w+) := Color\("([0-9a-f]{6})"\)',theme))
def rgb(value):return [int(value[i:i+2],16)/255 for i in [0,2,4]]
def lum(v):
 c=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
 return sum(x*y for x,y in zip(c,[.2126,.7152,.0722]))
def contrast(a,b):
 x,y=sorted([lum(a),lum(b)]);return (y+.05)/(x+.05)
pairs=[]
for fg,bg,use in [('CREAM','INK','default panel text'),('MIST','INK','caption panel text'),('GOLD','DEEP','eyebrow / secondary focus'),('CREAM','SURFACE','secondary normal'),('CREAM','HOVER','secondary hover / selected normal'),('CREAM','PRESSED','secondary pressed'),('MUTED','INK','disabled secondary text'),('DEEP','GOLD','primary normal / inset focus'),('DEEP','GOLD_HOVER','primary hover'),('DEEP','GOLD_PRESSED','primary pressed'),('DEEP','GOLD_DISABLED','disabled primary text'),('GOLD','PRESSED','secondary focus over pressed'),('LINE','INK','panel border'),('LINE','SURFACE','button border')]:
 pairs.append({'use':use,'foreground':fg,'background':bg,'source_srgb_hex':[colors[fg],colors[bg]],'ratio':round(contrast(rgb(colors[fg]),rgb(colors[bg])),3)})
# Original run logical width 1280: noncompact card x=52, width=438. The
# gradient alpha interpolates .95 at .32 to .65 at .47. White is a bound,
# not a claim that these pixels contain white or use this exact blend space.
right=(52+438)/1280;alpha=.95+((right-.32)/(.47-.32))*(.65-.95)
scrim=[.025,.035,.09];white_bound=[x*alpha+1*(1-alpha) for x in scrim]
report={'scope':'Source sRGB contrast and layout semantics for exact r1 sources. Ratios do not measure rendered glyph edges, minimum readable size, color vision, or full accessibility. Background opacity is separate from contrast.','project':str(root),'source_sha256':{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},'pairs':pairs,'native_presentation':{'logical_canvas':[1280,720],'framebuffer':[960,540],'scale':.75,'body_logical':17,'body_framebuffer':12.75,'caption_logical':14,'caption_framebuffer':10.5,'compact_hud_logical':[11,12],'compact_hud_framebuffer':[8.25,9],'minimum_button_logical':44,'minimum_button_framebuffer':33,'focus_width_logical':2,'focus_width_framebuffer':1.5},'surface_semantics':{'panel_color_alpha':1.0,'panel_background':'INK; DEEP for strong panels, hero status and atlas','button_background':'opaque role/state colors','launch_background':'Transparent card over a gradient scrim; evaluate separately from opaque panels','hero_status_background':'Opaque DEEP behind health and notice; opaque INK slots','map_shape_coding':'Sun triangles, Moon squares, relay outline plus owner shape and crossed contested marker'},'launch_scrim_bound':{'logical_right_x':490,'normalized_x':right,'estimated_minimum_alpha_over_text_column':round(alpha,5),'white_background_source_srgb_blend':white_bound,'mist_text_ratio':round(contrast(rgb(colors['MIST']),white_bound),3),'scope':'Analytical worst-white source-color bound at original-run column edge using sRGB alpha interpolation; not measured pixel contrast or a claim covering resized layouts.'}}
pathlib.Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pairs':len(pairs),'minimum_text_pair_ratio':min(x['ratio'] for x in pairs if 'border' not in x['use']),'scrim_mist_bound':report['launch_scrim_bound']['mist_text_ratio']}))
