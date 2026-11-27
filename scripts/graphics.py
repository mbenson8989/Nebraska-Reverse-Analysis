import json, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
B='/workspace/nebraska-reverse/'; A=json.load(open(B+'passA/results.json'))['races']; Pb=json.load(open(B+'passB/results.json'))['races']
NAMES={'senate':('Dan Osborn','Pete Ricketts','U.S. SENATE','(I)'),'governor':('Lynne Walz','Jim Pillen','GOVERNOR','(D)'),'secretary_of_state':('Sarah Slattery','Scott Petersen','SECRETARY OF STATE','(D)'),
 'treasurer':('Daniel Ebers','Joey Spellerberg','STATE TREASURER','(D)'),'attorney_general':('Jocelyn Brasher','Mike Hilgers','ATTORNEY GENERAL','(D)')}
BG='#0a0a0c'; W='white'; RED='#ff3030'; BLUE='#2f7bff'; DIM='#b5b5b5'; OTH='#55555c'; plt.rcParams['font.family']='DejaVu Sans'
SRC='Source: Nebraska Secretary of State · 2026 unofficial*, pre-canvass (Nov 27, 2026)'
def frame():
    fig=plt.figure(figsize=(7.2,7.2),dpi=300,facecolor=BG); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off'); return fig,ax
def foot(ax):
    ax.add_patch(Rectangle((0,0),1,.05,color='#1c1c20',lw=0)); ax.text(.5,.025,SRC,ha='center',va='center',color='#9a9a9a',fontsize=9)
out=[]
for i,(slug,v) in enumerate(A.items(),1):
    vb=Pb[slug]; assert v['removed']==vb['removed'] and abs(v['dem_pct_after']-vb['dem_pct_after'])<1e-9
    dn,rn,title,tag=NAMES[slug]; dl,rl=dn.split()[-1],rn.split()[-1]; fig,ax=frame()
    ax.text(.5,.95,f'NEBRASKA {title}',ha='center',va='center',color=W,fontsize=26 if len(title)<16 else 21,weight='bold')
    ax.text(.5,.905,f'{dn} {tag}  vs  {rn} (R)  ·  2026 unofficial*',ha='center',va='center',color=DIM,fontsize=12,weight='bold')
    x0,L,h=.06,.88,.09
    def bar(y,head,d,r,marg,col):
        ax.text(x0,y+h/2+.03,head,ha='left',va='center',color=W,fontsize=16,weight='bold')
        ax.add_patch(Rectangle((x0,y-h/2),L*d/100,h,color=BLUE,lw=0)); ax.add_patch(Rectangle((x0+L*d/100,y-h/2),L*(100-d-r)/100,h,color=OTH,lw=0)); ax.add_patch(Rectangle((x0+L*(100-r)/100,y-h/2),L*r/100,h,color=RED,lw=0))
        ax.text(x0+.012,y,f'{dl} {d:.2f}%',ha='left',va='center',color=W,fontsize=15,weight='bold'); ax.text(x0+L-.012,y,f'{rl} {r:.2f}%',ha='right',va='center',color=W,fontsize=15,weight='bold')
        ax.plot([x0+L/2]*2,[y-h/2-.008,y+h/2+.008],color=W,lw=1.5,ls=(0,(3,2))); ax.text(.5,y-h/2-.032,marg,ha='center',va='center',color=col,fontsize=16,weight='bold')
    mb=v['margin_before']; ma=v['margin_after']
    bar(.76,'ACTUAL RESULT*',v['dem_pct'],v['rep_pct'],(f"{rl} wins by {-mb:.2f} pts" if mb<0 else f"{dl} wins by {mb:.2f} pts"),RED if mb<0 else BLUE)
    bar(.545,'WITH THE INJECTION EQUATION REMOVED',v['dem_pct_after'],v['rep_pct_after'],(f"{rl} wins by {-ma:.2f} pts" if ma<0 else f"{dl} wins by {ma:.2f} pts"),RED if ma<0 else BLUE)
    ax.text(.5,.365,f"{v['removed']:,}",ha='center',va='center',color=W,fontsize=56,weight='bold')
    ax.text(.5,.285,'votes removed by the equation',ha='center',va='center',color=W,fontsize=21,weight='bold')
    ax.text(.5,.215,'Removed votes are moved from the challenger to the Republican.',ha='center',va='center',color=W,fontsize=12.5)
    ax.text(.5,.18,'Treating them as injected votes is a hypothesis to examine, not a finding.',ha='center',va='center',color=W,fontsize=12.5)
    sub='Measured against Democratic registration share (SOS, Nov 1, 2026)' + ('\nNo Democratic nominee: Osborn (independent) stands in as the challenger' if slug=='senate' else '')
    ax.text(.5,.11 if slug!='senate' else .115,sub,ha='center',va='center',color=DIM,fontsize=10.5,linespacing=1.4)
    foot(ax); p=B+f'graphics/{i}_NE_{slug}_injection_removed.png'; fig.savefig(p,dpi=300,facecolor=BG); plt.close(fig); out.append(p)
# statewide by race
LAB={'senate':'U.S. Senate (Osborn, I)','governor':'Governor','secretary_of_state':'Secretary of State','treasurer':'State Treasurer','attorney_general':'Attorney General'}
fig,ax=frame()
ax.text(.5,.95,'NEBRASKA 2026*:',ha='center',va='center',color=W,fontsize=26,weight='bold'); ax.text(.5,.905,'VOTES REMOVED BY THE INJECTION EQUATION',ha='center',va='center',color=W,fontsize=18,weight='bold')
ax.text(.5,.862,'One bar per statewide race  ·  2026 unofficial*',ha='center',va='center',color=DIM,fontsize=11.5,weight='bold')
x0,L,h=.06,.62,.07; mx=max(v['removed'] for v in A.values()); y=.77
for k,v in A.items():
    ax.text(x0,y+h/2+.018,LAB[k],ha='left',va='center',color=W,fontsize=15,weight='bold'); ax.add_patch(Rectangle((x0,y-h/2+.004),L*v['removed']/mx,h-.012,color=RED,lw=0))
    ax.text(x0+L*v['removed']/mx+.015,y-.002,f"{v['removed']:,}",ha='left',va='center',color=W,fontsize=20,weight='bold'); y-=.125
ax.text(.5,.15,'Each race measured on its own. The same ballots are counted in every race,',ha='center',va='center',color=W,fontsize=11.5)
ax.text(.5,.12,'so the races are NOT added together. No combined total.',ha='center',va='center',color=W,fontsize=11.5,weight='bold')
ax.text(.5,.08,'Auditor not shown: no Democratic or independent challenger on the ballot.',ha='center',va='center',color=DIM,fontsize=10)
foot(ax); p=B+'graphics/6_NE_votes_removed_by_race.png'; fig.savefig(p,dpi=300,facecolor=BG); plt.close(fig); out.append(p)
# top ten counties (ranked by Governor removal)
g=pd.read_csv(B+'passA/governor.csv').set_index('county'); top=g.nlargest(10,'removal_votes')
fig,ax=frame()
ax.text(.5,.95,'NEBRASKA 2026*: TOP 10 COUNTIES',ha='center',va='center',color=W,fontsize=22,weight='bold')
ax.text(.5,.908,'Votes removed by the injection equation, Governor race',ha='center',va='center',color=DIM,fontsize=12,weight='bold')
x0,L=.25,.45; mx=top.removal_votes.max(); y=.84
for c,r in top.iterrows():
    ax.text(x0-.015,y,c,ha='right',va='center',color=W,fontsize=13,weight='bold'); ax.add_patch(Rectangle((x0,y-.022),L*r.removal_votes/mx,.044,color=RED,lw=0))
    ax.text(x0+L*r.removal_votes/mx+.012,y,f"{int(r.removal_votes):,}",ha='left',va='center',color=W,fontsize=13,weight='bold')
    ax.text(x0+L*r.removal_votes/mx+.012,y-.026,f"{r.removal_pct:.1f} pts of {int(r.ballots):,} ballots",ha='left',va='center',color=DIM,fontsize=8.5); y-=.068
ax.text(.5,.12,f"Top 10 = {int(top.removal_votes.sum()):,} of {int(g.removal_votes.sum()):,} Governor votes removed statewide",ha='center',va='center',color=W,fontsize=12)
ax.text(.5,.085,'Large counties lead because they cast the most ballots. A hypothesis to examine.',ha='center',va='center',color=DIM,fontsize=10.5)
foot(ax); p=B+'graphics/7_NE_top10_counties_governor.png'; fig.savefig(p,dpi=300,facecolor=BG); plt.close(fig); out.append(p)
print('\n'.join(out))
