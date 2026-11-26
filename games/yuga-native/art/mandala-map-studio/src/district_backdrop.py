"""Sculpt the river basin and settle its banks around the measured Mandala floor.

The bed runs below the playable decks. Every above-deck cluster reserves a
clear disk against their actual swept footprints before it is added.
"""
from math import cos, hypot, pi, sin, tau
from random import Random

from rooms import Piece, motif, ring_faces


# Survey stations are expressed as fractions of the map radius. Narrow the
# upstream and downstream caps and let only the middle reach span the full site.
BANK_PROFILE = ((-1.01,.12),(-.97,.30),(-.91,.56),(-.81,.79),(-.70,.91),
                (-.53,.98),(-.35,.95),(-.19,.99),(0,1.01),(.17,.98),
                (.30,.96),(.48,1.0),(.64,.96),(.78,.87),(.89,.64),(.97,.34),(1.012,.13))


def half_width(t):
    for (a,w),(b,v) in zip(BANK_PROFILE,BANK_PROFILE[1:]):
        if t<=b:return w+(v-w)*(t-a)/(b-a)
    return BANK_PROFILE[-1][1]


def banks(y,sx,sy):
    t=y/sy
    half=sx*half_width(t)
    west=-half*(1+.016*sin(y*.13))
    east=half*(.982+.025*cos(y*.088))
    river=west+(.17+.034*cos(y*.079)+.025*sin(y*.042))*(east-west)
    radius=min((east-west)*.108,4.2+2.15*(1+cos(y*.052+.5)))
    return west,east,river,radius


def merge(target,piece):
    # Pieces have already applied their local frames. Keep district-scale batches
    # in world space, so distant houses share materials and draw calls.
    for material,(points,faces) in piece.parts.items():
        target.geom(material,points,faces)


def landscape(sx,sy):
    earth=Piece('Flood bed · river silts and cut earth',0,0)
    water=Piece('River · channel, foam seams and ripples',0,0)
    rows=[];rims=[]
    rng=Random(721)
    for j in range(75):
        t=BANK_PROFILE[0][0]+(BANK_PROFILE[-1][0]-BANK_PROFILE[0][0])*j/74
        y=t*sy
        west,east,r,width=banks(y,sx,sy)
        # The low-water boundary is precisely one of the graded ground edges.
        profile=[(west,-1.03),(west+(r-width*1.12-west)*.53,-.96),(r-width*1.12,-1.10),
                 (r-width,-1.26),(r-width*.77,-1.68),(r+width*.70,-1.80),
                 (r+width,-1.26),(r+width*1.13,-.96),(r+width*1.5,-1.03),
                 (r+width*1.5+(east-r-width*1.5)*.32,-1.16),
                 (r+width*1.5+(east-r-width*1.5)*.74,-1.05),(east,-1.01)]
        rows.append([(x,y,z) for x,z in profile]);rims.append((r-width,y,r+width))
    finishes=('#647751','#81916A','#A2A07C','#8E9A80','#778979','#738275',
              '#B2A482','#ADAA84','#A9A484','#AC9C80','#AD8C68')
    for j in range(len(rows)-1):
        row,after=rows[j:j+2]
        for i,mat in enumerate(finishes):
            earth.geom(mat,[row[i],row[i+1],after[i+1],after[i]],[(0,1,2),(0,2,3)])
        l,y,r=rims[j];ll,yy,rr=rims[j+1]
        water.geom('#57918C',[(l,y,-1.235),(r,y,-1.235),(rr,yy,-1.235),(ll,yy,-1.235)],[(0,1,2,3)])
        if j%2==0:
            near=l+(r-l)*rng.uniform(.13,.80);span=(r-l)*rng.uniform(.10,.19); yc=(y+yy)/2
            water.geom('#82A6A0',[(near-span,yc,-1.221),(near,yc+.11,-1.221),
                (near+span,yc-.02,-1.221),(near,yc-.04,-1.221)],[(0,1,2,3)])
    def seam(v,depth,k):
        x,y,_=v
        return x*k,y*k,depth+.10*sin(.07*x+.109*y)

    outline=[r[0] for r in rows]+rows[-1][1:]+[r[-1] for r in reversed(rows[:-1])]+list(reversed(rows[0][1:-1]))
    for i,a in enumerate(outline):
        b=outline[(i+1)%len(outline)]
        top=(a,b);middle=(seam(a,-1.97,1.001),seam(b,-1.97,1.001));toe=(seam(a,-3.18,.986),seam(b,-3.18,.986))
        earth.geom('#946E52',[top[0],top[1],middle[1],middle[0]],[(0,1,2,3)])
        earth.geom('#625D55',[middle[0],middle[1],toe[1],toe[0]],[(0,1,2,3)])
    for row,after in zip(rows,rows[1:]):
        for i in range(len(row)-1):
            underside=[seam(v,-3.18,.986) for v in (row[i],after[i],after[i+1],row[i+1])]
            earth.geom('#625D55',underside,[(0,1,2),(0,2,3)])
    earth.finish();water.finish()


def mound(p,radius,height,phase):
    steps=18;verts=[]
    for scale,level in ((1.0,0),(.92,.23),(.69,.70),(.31,.98)):
        for i in range(steps):
            a=tau*i/steps
            rr=radius*scale*(.91+.06*cos(3*a+phase)+.025*sin(5*a-phase))
            verts.append((rr*cos(a),rr*.81*sin(a),height*level+.10*level*sin(3*a+phase)))
    for j,mat in enumerate(('#78805A','#79905E','#91A16D')):
        fs=[(j*steps+i,j*steps+(i+1)%steps,(j+1)*steps+(i+1)%steps,(j+1)*steps+i) for i in range(steps)]
        p.geom(mat,verts,fs)
    p.geom('#90A274',verts[-steps:],[tuple(range(steps))])


def crown(p,x,y,z,r,h,phase,finish):
    # Unequal crown lobes produce a continuous broken silhouette at street scale.
    steps=11;verts=[]
    for scale,height in ((.10,0),(.71,.13),(1.0,.37),(.95,.61),(.70,.85),(.16,1.0)):
        for i in range(steps):
            angle=tau*i/steps
            width=r*scale*(1+.10*sin(3*angle+phase)+.045*cos(5*angle-phase))
            verts.append((x+width*cos(angle),y+.82*width*sin(angle),z+h*height+.06*h*scale*sin(2*angle+phase)))
    p.geom(finish,verts,ring_faces(steps,6))


def grove(p,rng,canopy_height,spread):
    h=canopy_height
    p.rod('timber',(0,0,0),(.13,-.12,.42*h),.31,.23,10)
    for i in range(5):
        a=tau*i/5+rng.uniform(-.29,.29); length=spread*rng.uniform(.30,.62)
        x=cos(a)*length;y=sin(a)*length;z=h*rng.uniform(.63,.82)
        p.rod('timber',(.13,-.12,h*.36),(x*.55,y*.55,h*.56),.23,.12)
        p.rod('timber',(x*.55,y*.55,h*.56),(x,y,z),.13,.043)
        top=h*rng.uniform(.27,.36)
        crown(p,x,y,z-top*.44,spread*.50,top,a,('#506E50','#5E7C55','#758B5B')[i%3])
    for i in range(4):
        a=tau*i/4+.44
        p.rod('timber',(cos(a)*.83,sin(a)*.83,.035),(.12,-.12,1.08),.045,.20)


def fan_palm(p,x,y,h,phase):
    # Bent trunk and overlapping leaflets distinguish palm crowns in silhouette.
    offx=.43*cos(phase);offy=.43*sin(phase)
    p.rod('timber',(x,y,0),(x+offx*.35,y+offy*.35,h*.58),.21,.16,10)
    p.rod('timber',(x+offx*.35,y+offy*.35,h*.58),(x+offx,y+offy,h),.16,.11,10)
    for j in range(9):
        a=phase+tau*j/9;dx,dy=cos(a),sin(a);scale=1.9+.30*sin(j*5+phase)
        loc=[]
        for k in range(8):
            t=k/7;loc.append((x+offx+scale*t*dx,y+offy+scale*t*dy,h+.52*sin(pi*t)-.84*t*t))
        for k in range(7):
            p.rod('reed',loc[k],loc[k+1],.031*(1-k/10),sides=5)
            if k==0:continue
            u,v,z=loc[k];span=.40*sin(pi*k/8)+.15
            for side in (-1,1):
                ex=u+dx*.31-side*dy*span;ey=v+dy*.31+side*dx*span
                verts=[(u,v,z),(u+dx*.23-side*dy*span*.35,v+dy*.23+side*dx*span*.35,z+.06),
                       (ex,ey,z-.25),(u+dx*.13-side*dy*span*.39,v+dy*.13+side*dx*span*.39,z-.02)]
                p.geom('#49755D' if (j+k)%3 else '#769461',verts,[(0,1,2),(0,2,3)])


def pitched_roof(p,width,depth,height,rise):
    w,d=width*.5,depth*.5
    for side in (-1,1):
        q=.26*side
        p.geom('terracotta',[(-w,side*d,height),(w,side*d,height),(w*.91,q,height+rise),(-w*.91,q,height+rise)],
               [(0,1,2,3)] if side<0 else [(3,2,1,0)])
        p.rod('madder',(-w,side*d,height),(w,side*d,height),.115)
        for i in range(int(width/.64)+1):
            x=-w+.23+i*(width-.46)/max(1,int(width/.64))
            p.rod('#BD7857',(x,side*d,height+.015),(x*.91,q,height+rise+.025),.045,sides=6)
    p.rod('terracotta',(-w*.92,0,height+rise+.04),(w*.92,0,height+rise+.04),.18,sides=10)
    for side in (-1,1):
        p.geom('sandstone',[(side*w,-d,height),(side*w,d,height),(side*w*.91,0,height+rise)],[(0,1,2)] if side>0 else [(2,1,0)])


def town_house(p,w,d,storeys,variant):
    cornice=3.20;span=w/3
    p.box('basalt',(0,0,.19),(w,d,.38),.09)
    p.box('sandstone' if variant%2 else '#CB9D73',(0,d*.16,1.66),(w*.96,d*.64,2.65),.06)
    for k in range(4):
        x=-w*.48+k*(w*.96/3)
        p.box('limestone',(x,-d*.32,.48),(.55,.65,.22))
        p.box('sandstone',(x,-d*.32,1.68),(.43,.48,2.22),.07,.91)
    for k in range(3):
        x=(k-1)*span
        p.arch('limestone',(x,-d*.32,2.65),span*.86,.47,.17,.48,scallop=.056)
        p.box('teal' if (k+variant)%3==0 else 'timber',(x,-d*.17,1.50),(span*.54,.09,2.11),.035)
    p.box('granite',(0,0,3.08),(w*1.02,d*1.04,.23),.06)
    if storeys==2:
        p.box('#B98568',(0,.03*d,4.33),(w*.94,d*.86,2.28),.08)
        for j in range(5):
            x=(j-2)*w*.162
            p.box('ink',(x,-.402*d,4.34),(.71,.095,1.27),.035)
            p.box('teal' if variant%3 else 'timber',(x,-.414*d,4.35),(.51,.10,.94),.024)
            p.box('limestone',(x,-.42*d,3.71),(.96,.25,.10),.023)
        cornice=5.5
    p.box('limestone',(0,0,cornice+.035),(w*1.04,d*1.02,.20),.05)
    pitched_roof(p,w*1.09,d*1.14,cornice+.18,1.14 if storeys==2 else .86)
    if variant%3==0:
        p.turned('patina',(w*.29,.18*d,cornice+.76),[(0,.32),(.29,.44),(.60,.28),(.74,.16)],12)


def build_backdrop(plan, clear_footprint):
    xmin,ymin,xmax,ymax=plan['bounds'];sx=max(abs(xmin),abs(xmax));sy=max(abs(ymin),abs(ymax))
    landscape(sx,sy)
    hills=Piece('Western bank · terraces and tree canopies',0,0)
    town=Piece('Eastern town · colonnades and roofscape',0,0)
    islands=Piece('River islands · orchard and marsh',0,0)
    rng=Random(1172)

    def fits(x,y,r):
        if abs(y)+r>=sy:return False
        left,right,_,_=banks(y,sx,sy)
        return left+r<x<right-r and clear_footprint(x,y,r)

    forest=[]
    for y in range(-108,110,9):
        left,_,river,radius=banks(y,sx,sy)
        for cx in (left+4.9,river-radius-4.8,river+radius+4.2):
            cy=y+rng.uniform(-1.8,1.8);x=cx+rng.uniform(-.8,.8);rad=rng.uniform(3.0,4.4)
            if not fits(x,cy,rad+.38) or any(hypot(x-px,cy-py)<rad+pr+.9 for px,py,pr in forest):continue
            forest.append((x,cy,rad));p=Piece('Bank tree',x,cy,-1.04)
            height=rng.uniform(1.06,2.10)
            mound(p,rad,height,rng.random()*tau)
            tree=Piece('Tree',x,cy,-1.04+height*.92)
            if len(forest)%4==0:fan_palm(tree,0,0,rng.uniform(4.0,6.0),rng.random()*tau)
            else:grove(tree,rng,rng.uniform(3.2,5.1),rad*.85)
            merge(hills,p); merge(hills,tree)
    homes=[]
    for rank in range(2):
        for j,y in enumerate(range(-102+rank*6,104,13)):
            left,right,_,_=banks(y,sx,sy)
            w=rng.uniform(6.6,9.5);d=rng.uniform(3.4,4.5);r=hypot(w*1.09,d*1.14)/2+.4
            x=right-r-1.2 if rank==0 else right-13.1
            if x<12 or not fits(x,y,r) or any(hypot(x-px,y-py)<r+rr+.6 for px,py,rr in homes):continue
            homes.append((x,y,r));p=Piece('Courtyard house',x,y,-1.09,yaw=-90+rng.uniform(-6,6))
            town_house(p,w,d,1+int((j+rank)%3==1),j+2*rank);merge(town,p)
    # Compact orchard islands on the inner bank; they never grow across a lane.
    for j,(x,y) in enumerate(((-18,-66),(-12,-14),(-7,27),(-14,71),(18,67),(26,-60),(33,19),(13,95))):
        r=3.10
        if not fits(x,y,r) or any(hypot(x-hx,y-hy)<r+rr for hx,hy,rr in homes):continue
        p=Piece('Inner bank orchard',x,y,-1.03)
        mound(p,r,.78,j*.75)
        q=Piece('Inner bank crown',x,y,-.29)
        if j%3:grove(q,rng,3.42,2.28)
        else:fan_palm(q,0,0,3.9,.61*j)
        merge(islands,p); merge(islands,q)
    hills.finish();town.finish();islands.finish()
    lotus_count=0
    for y in (-77,-58,-34,-12,9,28,57,78):
        _,_,river,width=banks(y,sx,sy);x=river+.48*width
        if fits(x,y,1.85):
            motif('Lotus Cluster',f'Backwater · lotus raft {lotus_count+1}',(x,y,-1.20),(2.55,1.80,.30),21+lotus_count*17)
            lotus_count+=1
    return {'bank_groves':len(forest),'arcaded_houses':len(homes),'lotus_rafts':lotus_count}
