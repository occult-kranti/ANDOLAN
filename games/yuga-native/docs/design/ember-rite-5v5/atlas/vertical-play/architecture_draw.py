"""Draw Mandala's entrance, cover and clearance sheets from its verified survey."""
from pathlib import Path
import json
import math
import os
import subprocess
import tempfile
import xml.etree.ElementTree as E

W,H=1480,1080
PAPER,INK,LINE,DIM='#f8f4e8','#1c4142','#b1bdb1','#436261'
FLOOR,GROUND,SHADOW='#fffaea','#dce8e0','#415758'
WARM,COOL,ORANGE='#945333','#355c83','#ae4928'
SANS,SERIF,MONO='DejaVu Sans, sans-serif','DejaVu Serif, serif','DejaVu Sans Mono, monospace'
NAMES=('mandala-ghat','mandala-bazaar','mandala-entrances')


def num(x):return f'{x:.2f}'.rstrip('0').rstrip('.') if isinstance(x,float) else str(x)
def tag(p,what,**attrs):return E.SubElement(p,what,{k.replace('_','-'):num(v) for k,v in attrs.items()})
def txt(p,x,y,s,size=16,fill=INK,font=SANS,**kw):
    o=tag(p,'text',x=x,y=y,fill=fill,font_size=size,font_family=font,**kw);o.text=str(s);return o
def box(p,x,y,w,h,fill,**kw):return tag(p,'rect',x=x,y=y,width=w,height=h,fill=fill,**kw)
def line(p,a,b,color=LINE,w=1,**kw):return tag(p,'line',x1=a[0],y1=a[1],x2=b[0],y2=b[1],stroke=color,stroke_width=w,**kw)
def poly(p,pts,color,w=1,fill='none',**kw):return tag(p,'polyline',points=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts),fill=fill,stroke=color,stroke_width=w,stroke_linejoin='round',stroke_linecap='round',**kw)
def dot(p,pos,r,fill='none',**kw):return tag(p,'circle',cx=pos[0],cy=pos[1],r=r,fill=fill,**kw)
def diamond(p,pos,r,fill,stroke):
    x,y=pos;return poly(p,[(x,y-r),(x+r,y),(x,y+r),(x-r,y),(x,y-r)],stroke,1.4,fill)
def key(p,x,y,s):return txt(p,x,y,s.upper(),13,DIM,MONO,letter_spacing=1.)
def fpoint(p,prec=1):return '('+', '.join(f'{v:.{prec}f}'.rstrip('0').rstrip('.') if v else '0' for v in p)+')'
def start(title,tagline,page):
    svg=E.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','viewBox':f'0 0 {W} {H}','width':str(W),'height':str(H),'role':'img','aria-labelledby':'title description'})
    tag(svg,'title',id='title').text=title;tag(svg,'desc',id='description').text=tagline
    defs=tag(svg,'defs')
    hatch=tag(defs,'pattern',id='low',patternUnits='userSpaceOnUse',width=5,height=5)
    box(hatch,0,0,5,5,'#b8bc9d');line(hatch,(0,5),(5,0),'#66755c',.8)
    leaves=tag(defs,'pattern',id='soft',patternUnits='userSpaceOnUse',width=5,height=5)
    box(leaves,0,0,5,5,'#c8d3ae');dot(leaves,(2,2),.9,'#4e7057')
    box(svg,0,0,W,H,PAPER);box(svg,0,0,W,8,INK)
    key(svg,42,42,'YUGA   /   Mandala Rift   /   Vertical play')
    txt(svg,W-43,42,f'COVER SURVEY    /    {page:02}/03',14,DIM,MONO,text_anchor='end')
    txt(svg,40,97,title,48,INK,SERIF);txt(svg,43,133,tagline,17,DIM)
    line(svg,(42,153),(W-42,153),INK,1.4)
    return svg,defs

def finish(svg):
    E.indent(svg,space='  ')
    return E.tostring(svg,encoding='utf-8',xml_declaration=True)+b'\n'

def build_pages(data,plan,deep):
    codes={c['id']:f'C{i+1:02d}' for i,c in enumerate(data['covers'])}
    cover={c['id']:c for c in data['covers']};nodes=plan['nodes']
    deep_marks={(e['id'],p['cover_id']):p for e in deep['entrances'] for p in e['pockets']}
    codes_e={e['id']:e['site'].upper()+str(i+1) for site in ('a','b') for i,e in enumerate(k for k in data['entrances'] if k['site']==site)}
    def by_site(site):
        entries=[e for e in data['entrances'] if e['site']==site];cx,cz=nodes[site]['xz']
        svg,defs=start(nodes[site]['label'],f"{len(entries)} ordinary entrances · 22 × 20 m court · dry sill +0 m",1 if site=='a' else 2)
        key(svg,42,182,'Registered plan   /   north up');key(svg,898,182,'Cover schedule   /   width × depth × height')
        x,y,w,h=42,199,814,652;s=min((w-70)/38,(h-57)/33);ox=x+w/2;oy=y+h/2
        def point(p):return (ox+(p[0]-cx)*s,oy-(p[1]-cz)*s)
        clip=tag(defs,'clipPath',id='cut');box(clip,x,y,w,h,'white');g=tag(svg,'g',clip_path='url(#cut)');box(g,x,y,w,h,GROUND)
        for n in range(-22,23,2):
            q=point((cx+n,cz+n));line(g,(q[0],y),(q[0],y+h),'#a9bfb6',.7);line(g,(x,q[1]),(x+w,q[1]),'#a9bfb6',.7)
        def rect_at(p,sz,mat,**kw):
            q=point((p[0]-sz[0]/2,p[1]+sz[1]/2));box(g,*q,sz[0]*s,sz[1]*s,mat,**kw)
        for rim in (True,False):
            for e in plan['links']:
                if e['kind']=='fold':continue
                points=[nodes[e['from']]['xz'],*e.get('via',[]),nodes[e['to']]['xz']]
                poly(g,[point(p) for p in points],INK if rim else FLOOR,e['width']*s+(2 if rim else 0))
            for room in nodes.values():rect_at(room['xz'],room['size'],FLOOR,stroke=INK if rim else FLOOR,stroke_width=2 if rim else 0)
        for radius in (4.5,3):dot(g,point((cx,cz)),s*radius,'none',stroke=ORANGE,stroke_width=1.6,stroke_dasharray='6 4' if radius>3 else 'none')
        txt(g,ox,oy+6,'KUND '+site.upper(),13,ORANGE,MONO,text_anchor='middle')
        feature=next(e for e in entries if e['approach']=='mid')
        for i,pocket in enumerate(feature['pockets']):
            poly(g,[point(p) for p in pocket['forward_walk_xz']],'#a56638',1.8,
                 stroke_dasharray='7 4' if i==0 else '2 4')
        for c in data['covers']:
            fill='url(#soft)' if c['kind']=='soft' else 'url(#low)' if c['height_m']<1.8 else SHADOW
            rect_at(c['center_xz'],c['size_xz'],fill,stroke=INK,stroke_width=1)
            q=point(c['center_xz']);txt(g,q[0],q[1]+4,codes[c['id']],11,PAPER,MONO,text_anchor='middle',stroke=INK,stroke_width=2.8,paint_order='stroke')
        for e in entries:
            for p in e['pockets']:
                a,b=point(p['hide_xz']),point(p['peek_xz']);r,t=point(p['reverse_hide_xz']),point(p['reverse_peek_xz'])
                full=deep_marks[(e['id'],p['cover_id'])]
                p1,p2=point(full['forward']['hide_xz']),point(full['reverse']['hide_xz'])
                poly(g,[p1,a,b],WARM,1.7);poly(g,[p2,r,t],COOL,1.3,stroke_dasharray='4 2');dot(g,p1,3.9,WARM,stroke=PAPER,stroke_width=1);diamond(g,p2,4,PAPER,COOL)
            p=e['pockets'][0];end=point(e['mouth_xz']);startp=point(p['threat_xz']);poly(g,[startp,end],WARM,1.5,stroke_dasharray='4 3')
            dot(g,startp,3,'none',stroke=WARM,stroke_width=1.2)
            box(g,end[0]-13,end[1]-9,26,18,PAPER,stroke=WARM,stroke_width=1,rx=2)
            txt(g,end[0],end[1]+4,codes_e[e['id']],12,WARM,MONO,text_anchor='middle')
        key(g,x+w-35,y+31,'N');poly(g,[(x+w-27,y+40),(x+w-32,y+56),(x+w-27,y+52),(x+w-22,y+56),(x+w-27,y+40)],INK,1,INK)
        bar_y=y+h-17;box(g,x+11,bar_y-24,5*s+18,32,PAPER,opacity=.94);txt(g,x+18,bar_y-7,'5 m',12,DIM,MONO);line(g,(x+18,bar_y),(x+18+5*s,bar_y),INK,2)
        box(svg,x,y,w,h,'none',stroke=LINE)
        listed=[c for c in data['covers'] if c['site']==site]
        for i,c in enumerate(listed):
            yy=219+i*29
            txt(svg,898,yy,codes[c['id']],14,DIM,MONO);txt(svg,944,yy,c['label'],17,INK,SERIF)
            dims=' × '.join(num(v) for v in [*c['size_xz'],c['height_m']]);txt(svg,1438,yy,dims+' m',14,INK,MONO,text_anchor='end')
        yy=240+len(listed)*29;line(svg,(897,yy),(1438,yy),LINE);key(svg,898,yy+28,'Incoming angle and two independent pockets')
        for i,e in enumerate(entries):
            base=yy+64+i*69
            txt(svg,898,base,codes_e[e['id']],15,WARM,MONO);txt(svg,937,base,nodes[e['approach']]['label'],21,INK,SERIF)
            txt(svg,1438,base,f"{e['width_m']:g} m  /  {e['inbound_bearing_deg']:.0f}°",14,DIM,MONO,text_anchor='end')
            labels=[codes[p['cover_id']]+' '+cover[p['cover_id']]['label'] for p in e['pockets']]
            txt(svg,937,base+25,'  /  '.join(labels),15,DIM)
        line(svg,(898,835),(1438,835),LINE);txt(svg,898,859,'Bearings turn clockwise from north at the threshold.',14,DIM)
        key(svg,42,890,'Reading the plan');dot(svg,(47,920),4,WARM);txt(svg,60,925,'Shelter from the approaching witness',15)
        diamond(svg,(390,920),4,PAPER,COOL);txt(svg,405,925,'Shelter from the site witness',15)
        txt(svg,42,954,'Solid fill marks tall cover. Diagonal hatching marks low cover. Dots mark permeable set dressing.',15,DIM)
        txt(svg,42,981,'Strokes run from full-body cover through a shoulder mark to a peek. The 4.5 m ritual apron stays clear.',15,DIM)
        txt(svg,42,1003,'Dashed copper paths show the two independent Sluice walks with the alternate pocket occupied.',14,WARM)
        key(svg,898,904,'Gameplay clearance');txt(svg,898,932,'Two 0.65 m movement envelopes pass each mouth.',16)
        txt(svg,898,959,'Ground concealment depends on the viewing angle.',16)
        txt(svg,898,986,'See sheet 03 for the raised observer and stance changes.',15,DIM)
        line(svg,(42,1012),(1438,1012),INK);txt(svg,42,1043,'Source: registered Mandala floor GLB and cover survey. Plan coordinates use metres east and north.',14,DIM)
        txt(svg,1438,1043,'VERTICAL PLAY   /   YUGA',12,DIM,MONO,text_anchor='end')
        return finish(svg)
    def register():
        svg,_=start('Threshold register','Read each pair from the approaching route, then rehearse the opposite side from the Kund.',3)
        key(svg,42,181,'Mouth and cover');key(svg,506,181,'Forward   /   full hide → peek');key(svg,846,181,'Reverse   /   full hide → peek');key(svg,1268,181,'Raised   /   walk')
        cy=215
        for e in data['entrances']:
            key(svg,42,cy,codes_e[e['id']]+'   '+nodes[e['approach']]['label']+'   '+fpoint(e['mouth_xz'],2))
            for i,p in enumerate(e['pockets']):
                full=deep_marks[(e['id'],p['cover_id'])]
                py=cy+26+i*24;txt(svg,58,py,codes[p['cover_id']],14,DIM,MONO);txt(svg,103,py,cover[p['cover_id']]['label'],17,INK,SERIF)
                txt(svg,360,py,p['posture'],14,DIM)
                txt(svg,506,py,fpoint(full['forward']['hide_xz'])+' → '+fpoint(p['peek_xz']),15,WARM,MONO)
                txt(svg,846,py,fpoint(full['reverse']['hide_xz'])+' → '+fpoint(p['reverse_peek_xz']),15,COOL,MONO)
                trip=p['forward_walk_m']+full['forward']['step_to_shoulder_m']
                txt(svg,1268,py,f"{p['visible_air_rays']}/9   {trip:.1f} m",15,INK,MONO)
            line(svg,(42,cy+61),(1438,cy+61),LINE);cy+=89
        from architecture import slab
        e=next(e for e in data['entrances'] if e['id']=='b-pyramid_n')
        p=e['pockets'][0];c=cover[p['cover_id']];a,b=p['threat_xz'],p['hide_xz']
        span=slab(a,b,c['min_xyz'][:2],c['max_xyz'][:2]);dist=math.dist(a,b)
        key(svg,42,857,'B2  /  Cart chest sight section')
        ox,oy,scale=61,995,21
        def section(u,h):return (ox+u*dist*scale,oy-h*scale)
        floor=p['threat_floor_y'];top=data['silhouette_top_m']['crouched']
        l=section(span[0],c['max_xyz'][2]);r=section(span[1],c['base_y'])
        box(svg,l[0],l[1],r[0]-l[0],r[1]-l[1],'url(#low)',stroke=INK)
        line(svg,(ox-10,oy),(section(1,0)[0]+12,oy),INK)
        low=section(0,floor+1.6);high=section(0,floor+5.6);target=section(1,top)
        line(svg,low,target,WARM,1.7,stroke_dasharray='4 2');line(svg,high,target,COOL,1.7)
        for q in (low,high,target):dot(svg,q,3.2,PAPER,stroke=INK,stroke_width=1)
        txt(svg,ox+6,high[1]-5,'+4 m eye',12,COOL,MONO)
        txt(svg,248,892,'The low chest blocks all nine crouched ground samples.',15)
        txt(svg,248,922,'At the shoulder mark a 4 m rise reveals six of nine.',15,DIM)
        txt(svg,248,951,'Standing up on the ground reveals three.',15,DIM)
        txt(svg,248,981,'Walk is the incoming route with the alternate occupied.',14,DIM)
        key(svg,862,857,'B2  /  passing at the north threshold')
        sx,sy,ratio=868,929,34;full=e['width_m']*ratio
        box(svg,sx,sy-25,full,50,'#e9e8d9',stroke=LINE)
        mid=sx+full/2
        line(svg,(mid,sy-35),(mid,sy+35),DIM,1,stroke_dasharray='3 3')
        for sign in (-1,1):
            center=mid+(e['two_body_offset_from_mouth_m']+sign*e['two_body_center_separation_m']/2)*ratio
            dot(svg,(center,sy),e['two_body_clearance_radius_m']*ratio,'none',stroke=COOL,stroke_width=1.6)
            dot(svg,(center,sy),2,COOL)
        line(svg,(sx,sy+39),(sx+full,sy+39),INK)
        txt(svg,mid,sy+58,'6.00 m',13,INK,MONO,text_anchor='middle')
        txt(svg,1090,896,'Two 0.65 m radius hulls',18,INK,SERIF)
        txt(svg,1090,928,'Centre spacing 1.36 m',15,DIM)
        txt(svg,1090,956,'Pair offset −1.20 m from centre',15,DIM)
        txt(svg,1090,983,'Checked over 1.80 m of travel.',14,DIM)
        line(svg,(42,1012),(1438,1012),INK);txt(svg,42,1043,'Full hides contain a 0.45 m radius receiver. Raised counts are measured at the nearby shoulder mark. Exact coordinates are in the JSON surveys.',14,DIM)
        txt(svg,1438,1043,'GROUND AND AIR SIGHT   /   YUGA',12,DIM,MONO,text_anchor='end');return finish(svg)
    return {NAMES[0]+'.svg':by_site('a'),NAMES[1]+'.svg':by_site('b'),NAMES[2]+'.svg':register()}


def pdf(folder):
    from pypdf import PdfWriter
    title=['Ghat Mandapa','Bazaar Sanctuary','Threshold register']
    with tempfile.TemporaryDirectory() as temp:
        writer=PdfWriter()
        for i,name in enumerate(NAMES):
            path=Path(temp)/(name+'.pdf')
            subprocess.run(['inkscape',str(folder/(name+'.svg')),'--export-filename='+str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env={**os.environ,'SOURCE_DATE_EPOCH':'0'})
            writer.append(path,import_outline=False);writer.add_outline_item(title[i],i)
        writer.add_metadata({'/Title':'Mandala Rift | Entrance cover survey','/Author':'YUGA level design'})
        with (folder/'mandala-cover-atlas.pdf').open('wb') as stream:writer.write(stream)
