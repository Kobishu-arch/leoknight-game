# Generates the bard frames (idle + walk cycles, 48x64) as anim.json for the Aseprite bridge (aseprite_animation).
# Run from any folder; it writes anim.json, tags.json and anim_sheet.png next to where it runs.
# The result lives in art/bard/bard_animations.aseprite; edit that file directly for small fixes.
import json, math
from PIL import Image, ImageDraw
W,H=48,64
PAL={}
def ramp(keys, cols):
    for k,c in zip(keys,cols): PAL[k]=c
    return list(keys)
HAIR=ramp('1234',['#3e1c12','#6a3218','#94501f','#bc6c2c']); PAL['5']='#e09a52'; PAL['6']='#f6c88a'
SKIN=ramp('abcd',['#a8644e','#d8987a','#f4c4a0','#ffe0c4'])
BLUE=ramp('efgh',['#16204a','#243a7a','#3a5cae','#5c88d2'])
SLEEVE=ramp('7890',['#1c2c62','#30509e','#5480cc','#82a8ea'])
GOLD=ramp('ijlm',['#7c4c16','#bc8226','#e8b440','#fce68c'])
RED =ramp('nopq',['#4e1224','#841c32','#b42e40','#dc5058'])
CAPE=ramp('rstu',['#2c0c22','#4e1634','#742440','#983448'])
PANT=ramp('vwxy',['#20161e','#362630','#4e3a46','#66525e'])
BOOT=ramp('ABCD',['#2c180e','#4c2c18','#744628','#9c6840'])
FLUT=ramp('EFGI',['#4a5270','#8a92ae','#c6cee2','#f6f9ff'])
PAL.update({'K':'#24141e','W':'#ffffff','e':'#5a3424','P':'#f08c80','O':'#24141e','-':'#00000000'})
# darker ramps for the far side in profile
PANT_F=[PANT[0],PANT[0],PANT[1],PANT[2]]; BOOT_F=[BOOT[0],BOOT[0],BOOT[1],BOOT[2]]
GOLD_F=[GOLD[0],GOLD[0],GOLD[1],GOLD[2]]; SLEEVE_F=[BLUE[0],SLEEVE[0],SLEEVE[1],SLEEVE[2]]

class Frame:
    def __init__(f):
        f.c=[[None]*W for _ in range(H)]; f.o=[[None]*W for _ in range(H)]
    def mask(f, fn):
        m=Image.new('1',(W,H),0); fn(ImageDraw.Draw(m))
        return {(x,y) for y in range(H) for x in range(W) if m.getpixel((x,y))}
    def poly(f,p,mirror=False):
        s=f.mask(lambda d:d.polygon(p,fill=1))
        return s|{(W-1-x,y) for (x,y) in s} if mirror else s
    def ell(f,b): return f.mask(lambda d:d.ellipse(b,fill=1))
    def thick(f,p,w): return f.mask(lambda d:d.line(p,fill=1,width=w))
    def paint(f,name,pts,r,inner=True,shade=True):
        for (x,y) in pts:
            out=lambda dx,dy:(x+dx,y+dy) not in pts
            c=r[2]
            if shade:
                if out(1,0) or out(0,1) or out(1,1): c=r[1]
                elif out(-1,0) or out(0,-1): c=r[3]
            f.c[y][x]=c; f.o[y][x]=name
        if inner:
            for (x,y) in pts:
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<W and 0<=ny<H and (nx,ny) not in pts and f.o[ny][nx] not in (None,name):
                        f.c[y][x]=r[0]; break
        return pts
    def px(f,x,y,c):
        if 0<=x<W and 0<=y<H: f.c[y][x]=c
    def line(f,p,c,mirror=False):
        for (x,y) in f.mask(lambda d:d.line(p,fill=1)):
            f.px(x,y,c)
            if mirror: f.px(W-1-x,y,c)
    def rows(f):
        filled=lambda x,y:0<=x<W and 0<=y<H and f.c[y][x] is not None
        out=[r[:] for r in f.c]
        for y in range(H):
            for x in range(W):
                if out[y][x] is None and any(filled(x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): out[y][x]='O'
        return [''.join(c or '-' for c in r) for r in out]

T=lambda pts,dx,dy:[(x+dx,y+dy) for (x,y) in pts]
def lag(pts,dy,ylim):   # hair tips / cape hem keep their place while the body bobs
    return [(x,y+(0 if y>=ylim else dy)) for (x,y) in pts]
mir=lambda pts:[(W-1-x,y) for (x,y) in pts]

def head_front(f,b,blink=False,back=False):
    crown=f.paint('crown',f.ell((14,2+b,33,19+b if not back else 21+b)),HAIR)
    bangs=set()
    if not back:
        bangs=f.poly(T([(15,9),(33,9),(33,13),(32,15),(31,13),(29,14),(27,12),(25,13),(23,15),(21,14),(20,16),(18,15),(17,18),(15,17),(15,15)],0,b))
        f.paint('bangs',bangs,HAIR,inner=False,shade=False)
        for (x,y) in bangs:
            if (x,y+1) not in bangs and (x,y+1) not in crown: f.px(x,y,HAIR[1])
    cx,cy,rx,ry=23.5,10.5+b,9.5,8.5
    def arc(a0,a1,r0,r1,c):
        for (x,y) in crown|bangs:
            nx,ny=(x-cx)/rx,(y-cy)/ry
            r=math.hypot(nx,ny); ang=math.degrees(math.atan2(ny,nx))%360
            if r0<=r<=r1 and a0<=ang<=a1: f.px(x,y,c)
    arc(190,258,0.58,0.82,HAIR[3]); arc(198,252,0.63,0.76,'5'); arc(210,245,0.66,0.72,'6')
    arc(282,340,0.60,0.82,HAIR[3]); arc(290,330,0.65,0.75,'5')
    f.line(T([(23,2),(23,6)],0,b),HAIR[0]); f.line(T([(24,2),(24,5)],0,b),HAIR[1])
    if back:
        for p in ([(19,8),(17,16)],[(22,9),(21,18)],[(26,9),(27,18)],[(29,8),(31,16)]): f.line(T(p,0,b),HAIR[1])
        return
    for p in ([(19,10),(18,15)],[(24,10),(22,14)],[(28,10),(27,12)],[(32,10),(31,13)]): f.line(T(p,0,b),HAIR[1])
    for p in ([(21,10),(20,14)],[(26,10),(25,12)],[(30,10),(29,13)]): f.line(T(p,0,b),HAIR[3])
    for ex in (18,27):
        y=18+b
        if blink:
            for i in range(3): f.px(ex+i,y+2,'K')
            f.px(ex+1,y+3,SKIN[1])
        else:
            for i in range(3): f.px(ex+i,y,'K')
            f.px(ex,y+1,'K'); f.px(ex+1,y+1,'W'); f.px(ex+2,y+1,'e')
            f.px(ex,y+2,'K'); f.px(ex+1,y+2,'e'); f.px(ex+2,y+2,'e')
            f.px(ex+1,y+3,SKIN[1])
    f.px(17,18+b,'K'); f.px(30,18+b,'K')
    f.px(24,22+b,SKIN[1])
    for x in (17,18,29,30): f.px(x,22+b,'P')
    f.px(23,24+b,SKIN[0]); f.px(24,24+b,SKIN[0]); f.px(23,25+b,'P')

def leg_front(f,side,lift,back=False):
    # side -1: viewer's left leg, +1: viewer's right leg (mirror)
    m=(lambda p:p) if side<0 else mir
    d=-lift
    f.paint('leg%d'%side,f.poly(m(T([(16,49),(21,49),(21,55),(16,55)],0,d))),PANT)
    f.paint('boot%d'%side,f.poly(m(T([(16,55),(21,55),(21,60),(22,61),(15,61),(15,58)],0,d))),BOOT)
    f.line(m(T([(16,58),(21,58)],0,d)),BOOT[0])
    if not back:
        for (x,y) in m(T([(17,56),(17,57)],0,d)): f.px(x,y,BOOT[3])
        f.paint('knee%d'%side,f.ell(tuple(sorted([m([(16,50+d)])[0][0],m([(21,50+d)])[0][0]]))[0:1]+(50+d,)+tuple(sorted([m([(16,50+d)])[0][0],m([(21,50+d)])[0][0]]))[1:2]+(55+d,)),GOLD)
        kx=m([(18,51+d)])[0]; f.px(kx[0],kx[1],GOLD[3])
    else:
        f.line(m(T([(17,51),(20,51)],0,d)),PANT[3])

def arm_front(f,side,b,swing):
    m=(lambda p:p) if side<0 else mir
    hy=40+b+swing
    f.paint('arm%d'%side,f.thick(m([(15,31+b),(13,hy-1)]),4),SLEEVE)
    f.paint('brac%d'%side,f.thick(m([(13,hy-2),(13,hy)]),4),GOLD)
    hb=m([(11,hy),(15,hy+4)]); xs=sorted([hb[0][0],hb[1][0]])
    f.paint('hand%d'%side,f.ell((xs[0],hy,xs[1],hy+3)),SKIN)

def front(b=0,lift=(0,0),swing=(0,0),blink=False):
    f=Frame()
    hl=lambda pts:lag(pts,b,40)
    f.paint('cape',f.poly(lag(T([(15,30),(12,34),(9,42),(8,49),(9,53),(12,54),(14,52),(15,49)],0,b),-b,46),True),CAPE)
    f.line(lag(T([(12,38),(10,50)],0,b),-b,46),CAPE[3],True)
    f.paint('hair',f.poly(hl(T([(14,12),(11,19),(11,25),(10,30),(11,35),(9,40),(10,44),(12,43),(13,46),(15,43),(16,30)],0,b)),True),HAIR)
    f.line(hl(T([(13,18),(12,25),(12,31),(11,37),(11,42)],0,b)),HAIR[0],True)
    for p in ([(12,21),(12,26)],[(14,29),(13,35)],[(11,38),(11,41)]): f.line(hl(T(p,0,b)),HAIR[3],True)
    leg_front(f,-1,lift[0]); leg_front(f,1,lift[1])
    torso_front(f,b)
    # flute in the belt at her left hip
    for (x,y) in f.thick(T([(27,41),(30,49)],0,b),2): f.px(x,y,FLUT[2])
    f.line(T([(28,41),(31,49)],0,b),FLUT[0]); f.line(T([(27,41),(29,48)],0,b),FLUT[3])
    f.px(28,45+b,GOLD[2]); f.px(29,45+b,GOLD[1]); f.px(27,41+b,FLUT[1])
    arm_front(f,-1,b,swing[0]); arm_front(f,1,b,swing[1])
    f.paint('rpaul',f.ell((12,27+b,18,32+b)),GOLD); f.px(14,28+b,GOLD[3]); f.px(15,28+b,GOLD[3])
    f.paint('lpaul',f.ell((29,27+b,35,32+b)),GOLD); f.px(31,28+b,GOLD[3]); f.px(32,28+b,GOLD[3])
    f.paint('face',f.ell((16,10+b,31,27+b)),SKIN)
    head_front(f,b,blink)
    return f

def torso_front(f,b,back=False):
    f.paint('torso',f.poly(T([(16,28),(31,28),(31,34),(29,42),(18,42),(16,34)],0,b)),BLUE)
    if not back:
        for y in (32,35,38): f.px(23,y+b,GOLD[2]); f.px(24,y+b,GOLD[1])
        f.line(T([(19,30),(19,41)],0,b),BLUE[3]); f.line(T([(28,31),(28,41)],0,b),BLUE[1])
        for (x,y) in [(20,28),(21,29),(22,30),(23,31),(24,31),(25,30),(26,29),(27,28)]: f.px(x,y+b,GOLD[2])
        for (x,y) in [(21,28),(22,29),(23,30),(24,30),(25,29),(26,28)]: f.px(x,y+b,SKIN[1])
    for x in range(18,30): f.px(x,42+b,BOOT[1]); f.px(x,43+b,BOOT[2] if x%2 else BOOT[1])
    if not back:
        for (x,y,c) in [(22,42,GOLD[3]),(23,42,GOLD[2]),(24,42,GOLD[2]),(25,42,GOLD[1]),(22,43,GOLD[2]),(23,43,BOOT[0]),(24,43,BOOT[0]),(25,43,GOLD[1])]: f.px(x,y+b,c)
    skirt=f.paint('skirt',f.poly(T([(17,44),(30,44),(33,47),(34,49),(13,49),(14,47)],0,b)),RED)
    for x0 in (15,19,23,27,31):
        f.line(T([(x0+1,45),(x0-1 if x0<23 else x0+1 if x0>23 else x0,48)],0,b),RED[1])
    for x0 in (17,21,25,29): f.line(T([(x0,45),(x0,47)],0,b),RED[3])
    for (x,y) in list(skirt):
        if (x,y+1) not in skirt: f.px(x,y,GOLD[2] if x%4 else GOLD[1])
        if (x,y+2) not in skirt and (x,y+1) in skirt: f.px(x,y,GOLD[1])

def back(b=0,lift=(0,0),swing=(0,0)):
    f=Frame()
    leg_front(f,-1,lift[0],back=True); leg_front(f,1,lift[1],back=True)
    torso_front(f,b,back=True)
    arm_front(f,-1,b,swing[0]); arm_front(f,1,b,swing[1])
    cape=f.paint('cape',f.poly(lag(T([(16,28),(24,28),(24,52),(20,51),(16,53),(11,52),(12,46),(14,36)],0,b),-b,46),True),CAPE)
    for p in ([(18,34),(15,50)],[(21,36),(20,50)]): f.line(lag(T(p,0,b),-b,46),CAPE[1],True)
    for p in ([(17,33),(13,49)],[(22,38),(22,48)]): f.line(lag(T(p,0,b),-b,46),CAPE[3],True)
    hl=lambda pts:lag(pts,b,38)
    f.paint('hair',f.poly(hl(T([(15,12),(24,12),(24,45),(21,43),(19,46),(17,42),(15,44),(16,36),(17,28),(15,20)],0,b)),True),HAIR)
    for p in ([(17,20),(18,30),(17,38),(17,42)],[(21,20),(20,30),(21,38),(20,44)],[(23,24),(23,34),(23,44)]):
        f.line(hl(T(p,0,b)),HAIR[0],True)
    for p in ([(18,22),(19,28)],[(22,26),(22,34)],[(18,34),(18,40)],[(21,39),(21,42)]): f.line(hl(T(p,0,b)),HAIR[3],True)
    for p in ([(19,23),(19,26)],[(22,28),(22,31)]): f.line(hl(T(p,0,b)),'5',True)
    f.paint('rpaul',f.ell((12,27+b,18,32+b)),GOLD); f.px(14,28+b,GOLD[3]); f.px(15,28+b,GOLD[3])
    f.paint('lpaul',f.ell((29,27+b,35,32+b)),GOLD); f.px(31,28+b,GOLD[3]); f.px(32,28+b,GOLD[3])
    head_front(f,b,back=True)
    return f

def side_leg(f,name,hip,ankle,r_pant,r_boot,r_gold,heel_up=False):
    hx,hy=hip; ax,ay=ankle
    kx,ky=(hx+ax)//2-2,(hy+ay)//2
    f.paint(name+'t',f.thick([(hx,hy),(kx,ky)],5),r_pant)
    f.paint(name+'s',f.thick([(kx,ky+1),(ax,ay)],4),r_boot)
    foot=[(ax-4,ay+2),(ax+2,ay+2),(ax+2,ay-1),(ax-2,ay)] if not heel_up else [(ax-4,ay+3),(ax,ay+3),(ax+2,ay-1),(ax-1,ay-1)]
    ft=f.paint(name+'f',f.poly(foot),r_boot)
    for (x,y) in ft:
        if (x,y+1) not in ft: f.px(x,y,r_boot[0])
    f.paint(name+'k',f.ell((kx-2,ky-1,kx+1,ky+2)),r_gold)

def side_arm(f,name,shoulder,hand,r_sleeve,r_gold,r_skin):
    sx,sy=shoulder; hx,hy=hand
    f.paint(name,f.thick([(sx,sy),(hx,hy-1)],4),r_sleeve)
    bx,by=(sx+3*hx)//4,(sy+3*hy)//4
    f.paint(name+'b',f.thick([(bx,by),(hx,hy-1)],4),r_gold)
    f.paint(name+'h',f.ell((hx-2,hy-1,hx+1,hy+2)),r_skin)

def side(pose):
    # pose: (b, near_ankle, far_ankle, near_heel_up, far_heel_up, near_hand, far_hand)
    b,na,fa,nh,fh,nhand,fhand=pose
    f=Frame()
    hl=lambda pts:lag(pts,b,38)
    side_arm(f,'farm',(24,30+b),(fhand[0],fhand[1]+b),SLEEVE_F,GOLD_F,[SKIN[0],SKIN[0],SKIN[1],SKIN[2]])
    side_leg(f,'fleg',(25,47+b),fa,PANT_F,BOOT_F,GOLD_F,fh)
    f.paint('cape',f.poly(lag(T([(26,27),(30,28),(34,36),(37,46),(37,52),(33,53),(30,50),(28,44),(26,36)],0,b),-b,46)),CAPE)
    f.line(lag(T([(29,32),(34,50)],0,b),-b,46),CAPE[3]); f.line(lag(T([(28,38),(31,50)],0,b),-b,46),CAPE[1])
    f.paint('torso',f.poly(T([(19,27),(28,27),(29,33),(28,42),(20,42),(18,35),(18,30)],0,b)),BLUE)
    for (x,y) in [(19,28),(20,29),(21,30),(20,28)]: f.px(x,y+b,GOLD[2])
    for y in (33,36,39): f.px(19,y+b,GOLD[2])
    f.line(T([(21,31),(21,41)],0,b),BLUE[3])
    for x in range(19,30): f.px(x,42+b,BOOT[1]); f.px(x,43+b,BOOT[2] if x%2 else BOOT[1])
    f.px(19,42+b,GOLD[2]); f.px(19,43+b,GOLD[1]); f.px(20,42+b,GOLD[3])
    side_leg(f,'nleg',(23,47+b),na,PANT,BOOT,GOLD,nh)
    skirt=f.paint('skirt',f.poly(T([(19,44),(29,44),(31,47),(32,49),(16,49),(17,47)],0,b)),RED)
    for x0 in (20,24,28): f.line(T([(x0,45),(x0-1,48)],0,b),RED[1])
    for x0 in (18,22,26,30): f.line(T([(x0,45),(x0,47)],0,b),RED[3])
    for (x,y) in list(skirt):
        if (x,y+1) not in skirt: f.px(x,y,GOLD[2] if x%4 else GOLD[1])
        if (x,y+2) not in skirt and (x,y+1) in skirt: f.px(x,y,GOLD[1])
    # long hair down her back
    hair=f.paint('hair',f.poly(hl(T([(24,6),(32,8),(34,14),(34,22),(35,30),(34,38),(36,43),(32,45),(31,42),(29,45),(27,40),(28,32),(27,24),(25,18)],0,b))),HAIR)
    f.line(hl(T([(31,12),(31,22),(32,30),(31,38),(32,43)],0,b)),HAIR[0]); f.line(hl(T([(29,18),(29,28),(30,36)],0,b)),HAIR[1])
    for p in ([(32,16),(33,24)],[(30,26),(30,32)],[(33,32),(33,38)]): f.line(hl(T(p,0,b)),HAIR[3])
    # flute in the belt
    for (x,y) in f.thick(T([(23,41),(30,46)],0,b),2): f.px(x,y,FLUT[2])
    f.line(T([(23,42),(30,47)],0,b),FLUT[0]); f.line(T([(23,40),(30,45)],0,b),FLUT[3])
    f.px(26,43+b,GOLD[2]); f.px(26,44+b,GOLD[1])
    side_arm(f,'narm',(24,30+b),(nhand[0],nhand[1]+b),SLEEVE,GOLD,SKIN)
    f.paint('paul',f.ell((21,26+b,28,32+b)),GOLD); f.px(23,27+b,GOLD[3]); f.px(24,27+b,GOLD[3])
    # head in profile, facing left
    f.paint('neck',f.poly(T([(20,24),(24,24),(24,28),(20,28)],0,b)),SKIN,shade=False)
    for (x,y) in f.poly(T([(20,24),(24,24),(24,28),(20,28)],0,b)): f.px(x,y,SKIN[1])
    face=f.paint('face',f.mask(lambda d:(d.ellipse((14,8+b,27,26+b),fill=1),d.polygon(T([(13,18),(15,16),(15,22)],0,b),fill=1))),SKIN)
    crown=f.paint('crown',f.ell((16,2+b,33,20+b)),HAIR)
    bangs=f.poly(T([(15,8),(28,8),(27,15),(25,13),(23,15),(21,13),(19,15),(17,14),(15,13),(14,11)],0,b))
    f.paint('bangs',bangs,HAIR,inner=False,shade=False)
    for (x,y) in bangs:
        if (x,y+1) not in bangs and (x,y+1) not in crown: f.px(x,y,HAIR[1])
    cx,cy,rx,ry=24.5,11+b,8.5,9
    for (x,y) in crown|bangs:
        nx,ny=(x-cx)/rx,(y-cy)/ry; r=math.hypot(nx,ny); ang=math.degrees(math.atan2(ny,nx))%360
        if 0.58<=r<=0.82 and 200<=ang<=330: f.px(x,y,HAIR[3])
        if 0.64<=r<=0.75 and 215<=ang<=280: f.px(x,y,'5')
    for p in ([(19,9),(18,13)],[(23,9),(22,13)],[(27,10),(28,16)]): f.line(T(p,0,b),HAIR[1])
    y=17+b
    for x in (16,17,18): f.px(x,y,'K')
    f.px(17,y+1,'W'); f.px(18,y+1,'K'); f.px(17,y+2,'e'); f.px(18,y+2,'e'); f.px(17,y+3,SKIN[1])
    f.px(17,16+b,HAIR[2]); f.px(18,16+b,HAIR[2])
    f.px(13,19+b,SKIN[2]); f.px(13,20+b,SKIN[1])        # nose tip
    f.px(15,23+b,SKIN[0]); f.px(19,22+b,'P'); f.px(20,22+b,'P')
    return f

frames=[]; tags=[]
def add(tag,fs,dur):
    start=len(frames)+1
    for i,fr in enumerate(fs): frames.append({'rows':fr.rows() if isinstance(fr,Frame) else fr,'duration':dur[i] if isinstance(dur,list) else dur})
    tags.append((tag,start,len(frames)))
add('idle_down',[front(),front(b=1),front(),front(blink=True)],[0.6,0.6,0.5,0.12])
add('walk_down',[front(lift=(0,2),swing=(-1,1)),front(b=-1),front(lift=(2,0),swing=(1,-1)),front(b=-1)],0.15)
add('walk_up',[back(lift=(0,2),swing=(1,-1)),back(b=-1),back(lift=(2,0),swing=(-1,1)),back(b=-1)],0.15)
L=[side((0,(17,57),(31,56),False,True,(29,39),(16,39))),
   side((-1,(24,57),(23,54),False,False,(23,41),(23,41))),
   side((0,(31,56),(17,57),True,False,(17,39),(29,38))),
   side((-1,(23,54),(24,57),False,False,(23,41),(23,41)))]
add('walk_left',L,0.15)
add('walk_right',[[r[::-1] for r in fr.rows()] for fr in L],0.15)
json.dump({'palette':PAL,'frames':frames},open('anim.json','w'))
json.dump(tags,open('tags.json','w'))
# contact sheet preview
sheet=Image.new('RGBA',(W*len(frames),H),(104,168,78,255))
for i,fr in enumerate(frames):
    for y,r in enumerate(fr['rows']):
        for x,c in enumerate(r):
            if c!='-': h=PAL[c]; sheet.putpixel((i*W+x,y),tuple(int(h[k:k+2],16) for k in (1,3,5))+(255,))
sheet.resize((sheet.width*3,H*3),Image.NEAREST).save('anim_sheet.png')
print(len(frames),'frames',tags)
