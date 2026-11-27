# PASS B (Python standard library only + poppler pdftotext -bbox; exact Fractions). Independent re-read of every raw file.
import json, csv, re, zipfile, glob, subprocess, html
from fractions import Fraction as F
R='/workspace/nebraska-reverse/raw/'; O='/workspace/nebraska-reverse/passB/'; NE='/workspace/nebraska-elections/'
norm=lambda s: re.sub(r'\s+',' ',s).strip().replace('Mcpherson','McPherson')
# --- statewide CSV: candidate id -> party, statewide totals
SWC=list(csv.DictReader(open(R+'sos_portal_20261127/er2026_SW.csv')))
PARTY={(r['RaceID'],r['CandidateID']):r['PartyCode'] for r in SWC}; SWTOT={(r['RaceID'],r['PartyCode']):int(r['CandidateVotes']) for r in SWC}
RACES={'senate':('13224','102','PET'),'governor':('13508','105','DEM'),'secretary_of_state':('13222','106','DEM'),'treasurer':('13223','107','DEM'),'attorney_general':('13217','108','DEM')}
# --- ballots: raw xlsx XML
def xlsx_rows(fn):
    z=zipfile.ZipFile(fn); ss=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        ss=[html.unescape(''.join(re.findall(r'<(?:x:)?t[^>]*>(.*?)</(?:x:)?t>',si,re.S))) for si in re.findall(r'<(?:x:)?si>(.*?)</(?:x:)?si>',z.read('xl/sharedStrings.xml').decode(),re.S)]
    sh=[n for n in z.namelist() if n.startswith('xl/worksheets/sheet')][0]; out=[]
    for row in re.findall(r'<(?:x:)?row[^>]*>(.*?)</(?:x:)?row>',z.read(sh).decode(),re.S):
        cells=[]
        for attrs,body in re.findall(r'<(?:x:)?c( [^>]*?)(?:/>|>(.*?)</(?:x:)?c>)',row,re.S):
            v=re.search(r'<(?:x:)?v>(.*?)</(?:x:)?v>',body or ''); isv=re.search(r'<(?:x:)?is>.*?<(?:x:)?t[^>]*>(.*?)</(?:x:)?t>',body or '',re.S)
            t=re.search(r't="(\w+)"',attrs)
            cells.append(ss[int(v.group(1))] if (t and t.group(1)=='s' and v) else (isv.group(1) if isv else (v.group(1) if v else None)))
        out.append(cells)
    return out
BAL={}
for fn in glob.glob(R+'turnout_20261127/*.xlsx'):
    rows=xlsx_rows(fn); k=[i for i,r in enumerate(rows) if r and r[0]=='County'][0]; r=rows[k+1]
    BAL[norm(r[0])]=int(float(r[1]))
assert len(BAL)==93
# --- registration: pdftotext -bbox, column by header x positions
def vrpdf(fn):
    x=subprocess.run(['pdftotext','-bbox',fn,'-'],capture_output=True,text=True).stdout; res={}
    for pg in x.split('<page')[1:]:
        W=[(float(a),float(b),float(c),html.unescape(t)) for a,b,c,t in re.findall(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>',pg)]
        hdr={t:a for a,b,c,t in W if t in('Republican','Democratic','Libertarian','Legal','America','Nonpartisan','Grand') and b<215}
        if 'Republican' not in hdr: continue
        nb=[a for a,b,c,t in W if t=='Nebraska' and 160<b<215]
        if nb: hdr['Nebraska']=min(nb)
        cols=sorted(hdr.items(),key=lambda kv:kv[1]); names=[k for k,_ in cols]; xs=[v for _,v in cols]
        lines={}
        for a,b,c,t in W:
            if b<205: continue
            lines.setdefault(round(b),[]).append((a,c,t))
        for y,ws in lines.items():
            ws.sort(); name=' '.join(t for a,c,t in ws if not re.fullmatch(r'[\d,]+',t))
            if not name or 'Page' in name or 'Copyright' in name: continue
            v=dict.fromkeys(['Republican','Democratic','Libertarian','Legal','Nebraska','America','Nonpartisan','Grand'],0)
            for a,c,t in ws:
                if re.fullmatch(r'[\d,]+',t):
                    i=sum(1 for X in xs if X<c-3)-1; v[names[i]]=int(t.replace(',',''))
            assert v['Republican']+v['Democratic']+v['Libertarian']+v['Legal']+v['Nebraska']+v['America']+v['Nonpartisan']==v['Grand'],(name,v)
            res[norm(name)]=dict(rep=v['Republican'],dem=v['Democratic'],lib=v['Libertarian'],np=v['Nonpartisan'],tot=v['Grand'])
    return res
REG=vrpdf(R+'vr_Statewide-November-2026.pdf'); REG22=vrpdf(NE+'sources/vr_Statewide-November-2022.pdf')
GT=REG.pop('Grand Total'); REG22.pop('Grand Total'); assert len(REG)==93==len(REG22)
assert sum(r['tot'] for r in REG.values())==GT['tot']
POP={}
for r in csv.DictReader(open(NE+'sources/census_co-est2025-alldata.csv',encoding='latin-1')):
    if r['STATE']=='31' and r['COUNTY']!='000': POP[r['CTYNAME'].replace(' County','')]=int(r['POPESTIMATE2025'])
PAN={r['county']:r for r in csv.DictReader(open(NE+'statewide/NE Statewide Reverse-Factoring - all 93 counties all cycles.csv'))}
def ols(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n; m=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs); return m,my-m*mx
def rnd(x):
    q=abs(x); n=int(q); n+=(q-n)>=F(1,2); return n if x>=0 else -n
OUT={}
for slug,(rid,osn,dp) in RACES.items():
    V={}
    for x in json.load(open(R+f'sos_portal_20261127/SW_{rid}_{osn}.json'))['d']:
        p=PARTY[(rid,x['CandidateID'])]; c=norm(x['CountyName']); V.setdefault(c,{}); V[c][p]=V[c].get(p,0)+x['calcCandidateVotes']
    for p in {p for v in V.values() for p in v}: assert sum(v[p] for v in V.values())==SWTOT[(rid,p)]  # county sums = SOS statewide
    C=sorted(V); xs=[F(REG[c]['dem']*100,REG[c]['tot'])/100 for c in C]
    G={c:F(V[c][dp]*100,BAL[c])-F(REG[c]['dem']*100,REG[c]['tot']) for c in C}
    m,b=ols(xs,[G[c] for c in C]); rows={}
    for c,x in zip(C,xs):
        res=G[c]-(m*x+b); raw=res+b; rem=max(raw,F(0)); rv=min(rnd(rem*BAL[c]/100),V[c][dp])
        rows[c]=dict(county=c,population=POP[c],ballots=BAL[c],dem_reg=REG[c]['dem'],tot_reg=REG[c]['tot'],dem=V[c][dp],rep=V[c]['REP'],race_total=sum(V[c].values()),
            D_reg_pct=float(x*100),gap=float(G[c]),residual=float(res),removal_pct=float(rem),removal_votes=rv,dem_after=V[c][dp]-rv,rep_after=V[c]['REP']+rv,zeroed=raw<0)
    Dt=sum(V[c][dp] for c in C); Rt=sum(V[c]['REP'] for c in C); Tt=sum(sum(V[c].values()) for c in C); Rem=sum(r['removal_votes'] for r in rows.values())
    OUT[slug]=dict(m=float(m),b=float(b),dem=Dt,rep=Rt,race_total=Tt,removed=Rem,dem_after=Dt-Rem,rep_after=Rt+Rem,dem_pct=float(F(100*Dt,Tt)),rep_pct=float(F(100*Rt,Tt)),
        dem_pct_after=float(F(100*(Dt-Rem),Tt)),rep_pct_after=float(F(100*(Rt+Rem),Tt)),zeroed=sorted(c for c in C if rows[c]['zeroed']),rows=rows)
    with open(O+f'{slug}.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[C[0]])); w.writeheader(); [w.writerow(rows[c]) for c in sorted(C,key=lambda c:(-POP[c],c))]
# history from panel raw counts (exact)
H={}
for y in ('2018','2020','2022','2024'):
    C=sorted(PAN); xs=[F(int(float(PAN[c][f'reg_dem_{y}'])),int(float(PAN[c][f'reg_tot_{y}']))) for c in C]
    g=[F(int(float(PAN[c][f'D_{y}']))*100,int(float(PAN[c][f'ballots_{y}'])))-x*100 for c,x in zip(C,xs)]
    m,b=ols(xs,g); rem=sum(rnd(max(gi-m*x,F(0))*int(float(PAN[c][f'ballots_{y}']))/100) for c,x,gi in zip(C,xs,g))
    H[y]=dict(m=float(m),b=float(b),mean_gap=float(sum(g)/93),n_gap_pos=sum(1 for v in g if v>0),removed=rem)
# notes
gv=OUT['governor']['rows']; dG={c:gv[c]['gap']-float(PAN[c]['G_2022']) for c in gv}
sixteen=sorted(c for c in PAN if float(PAN[c]['dG_2018to2022'])>0)
N=dict(dG_mean=sum(dG.values())/93,dG_allmail=sum(dG[c] for c in dG if PAN[c]['all_mail']=='yes')/11,dG_other=sum(dG[c] for c in dG if PAN[c]['all_mail']=='no')/82,sixteen=sixteen,
   cd={cd:dict(mean_resid=sum(gv[c]['residual'] for c in gv if PAN[c]['cd']==cd)/sum(1 for c in gv if PAN[c]['cd']==cd),removed=sum(gv[c]['removal_votes'] for c in gv if PAN[c]['cd']==cd),
       mean_dG=sum(dG[c] for c in gv if PAN[c]['cd']==cd)/sum(1 for c in gv if PAN[c]['cd']==cd)) for cd in ('CD1','CD2','CD3')})
PR={}
for c in REG:
    a,b=REG22[c],REG[c]; PR[c]={k:float(F(100*b[k],b['tot'])-F(100*a[k],a['tot'])) for k in ('dem','rep','lib','np')}
N['reg_change']={nm:{k:sum(PR[c][k] for c in grp)/len(grp) for k in ('dem','rep','lib','np')} for nm,grp in
   (('all',list(PR)),('sixteen',sixteen),('cd3',[c for c in PR if PAN[c]['cd']=='CD3']),('allmail',[c for c in PR if PAN[c]['all_mail']=='yes']))}
N['n_np_down']=sum(1 for v in PR.values() if v['np']<0); N['n_lib_down']=sum(1 for v in PR.values() if v['lib']<0); N['n_rep_down']=sum(1 for v in PR.values() if v['rep']<0)
N['party_reg_change']=PR
for v in OUT.values():
    for r in v['rows'].values(): r['zeroed']=bool(r['zeroed'])
json.dump(dict(races=OUT,history=H,notes=N,reg_grand_total=GT),open(O+'results.json','w'),indent=1)
for s,v in OUT.items(): print(s,round(v['m'],4),round(v['b'],4),v['removed'],round(v['dem_pct_after'],2),round(v['rep_pct_after'],2),len(v['zeroed']))
print(H); print({k:v for k,v in N.items() if k!='party_reg_change'})
# --- extra analyst-note stats (pass B, from raw count columns)
def Gp(c,y): return F(int(float(PAN[c][f'D_{y}']))*100,int(float(PAN[c][f'ballots_{y}'])))-F(int(float(PAN[c][f'reg_dem_{y}']))*100,int(float(PAN[c][f'reg_tot_{y}'])))
X={}
for cd in ('CD1','CD2','CD3'):
    cs=[c for c in PAN if PAN[c]['cd']==cd]; X[cd]=dict(dG1822=float(sum(Gp(c,'2022')-Gp(c,'2018') for c in cs)/len(cs)),dG2024=float(sum(Gp(c,'2024')-Gp(c,'2020') for c in cs)/len(cs)))
s16=[c for c in PAN if Gp(c,'2022')-Gp(c,'2018')>0]; oth=[c for c in PAN if c not in s16]; assert sorted(s16)==sixteen
mean=lambda xs:sum(xs)/len(xs)
X['sixteen']=dict(n_cd3=sum(PAN[c]['cd']=='CD3' for c in s16),RD2022_16=float(mean([F(int(float(PAN[c]['reg_dem_2022']))*100,int(float(PAN[c]['reg_tot_2022']))) for c in s16])),
  RD2022_other=float(mean([F(int(float(PAN[c]['reg_dem_2022']))*100,int(float(PAN[c]['reg_tot_2022']))) for c in oth])),
  resid26_16=mean([gv[c]['residual'] for c in s16]),resid26_other=mean([gv[c]['residual'] for c in oth]),dG26_16=mean([dG[c] for c in s16]),dG26_other=mean([dG[c] for c in oth]),
  zeroed26=sorted(c for c in s16 if gv[c]['zeroed']),dG1822_16=float(mean([Gp(c,'2022')-Gp(c,'2018') for c in s16])),dem_reg22_16=sum(int(float(PAN[c]['reg_dem_2022'])) for c in s16),pop_16=sum(POP[c] for c in s16))
def corr(a,b):
    ma,mb=mean(a),mean(b); return sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
C=sorted(gv); X['corr_resid_drep']=corr([gv[c]['residual'] for c in C],[PR[c]['rep'] for c in C]); X['corr_resid_dnp']=corr([gv[c]['residual'] for c in C],[PR[c]['np'] for c in C]); X['corr_resid_dlib']=corr([gv[c]['residual'] for c in C],[PR[c]['lib'] for c in C])
X['ballots_total']=sum(BAL.values()); X['gov_total_over_ballots']=float(F(OUT['governor']['race_total'],sum(BAL.values())))
json.dump(X,open(O+'extra.json','w'),indent=1); print(X)
# --- extra verification of every remaining published figure
Y={}
for slug,v in OUT.items():
    rows=v['rows']; Dt,Rt,Tt,Rem=v['dem'],v['rep'],v['race_total'],v['removed']; b=F(v['b']).limit_denominator(10**15)
    Y[slug]=dict(remove_only_dem_pct=Dt*100/(Tt-Rem) if False else float(F(100*(Dt-Rem),Tt-Rem)),remove_only_rep_pct=float(F(100*Rt,Tt-Rem)),
      n_D_before=sum(1 for r in rows.values() if r['dem']>r['rep']),n_D_after=sum(1 for r in rows.values() if r['dem_after']>r['rep_after']),
      n_pos_resid=sum(1 for r in rows.values() if r['residual']>0),
      offset_share=sum(v['b']/100*r['ballots'] for r in rows.values() if not r['zeroed'])/sum(r['removal_pct']/100*r['ballots'] for r in rows.values()))
    xs=[r['D_reg_pct'] for r in rows.values()]; ys=[r['gap'] for r in rows.values()]; mx=mean(xs); my=mean(ys)
    Y[slug]['r2']=sum((x-mx)*(y-my) for x,y in zip(xs,ys))**2/(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))
for y in ('2018','2020','2022','2024'):
    C=sorted(PAN); Y['H'+y]=dict(pooled_G=float(F(100*sum(int(float(PAN[c][f'D_{y}'])) for c in C),sum(int(float(PAN[c][f'ballots_{y}'])) for c in C))-F(100*sum(int(float(PAN[c][f'reg_dem_{y}'])) for c in C),sum(int(float(PAN[c][f'reg_tot_{y}'])) for c in C))))
    g=[float(Gp(c,y)) for c in C]; xs=[float(F(int(float(PAN[c][f'reg_dem_{y}'])),int(float(PAN[c][f'reg_tot_{y}'])))) for c in C]; mx=mean(xs); my=mean(g)
    Y['H'+y]['r2']=sum((a-mx)*(b-my) for a,b in zip(xs,g))**2/(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in g))
gvr=OUT['governor']['rows']; Y['H2026']=dict(pooled_G=float(F(100*OUT['governor']['dem'],sum(r['ballots'] for r in gvr.values()))-F(100*sum(r['dem_reg'] for r in gvr.values()),sum(r['tot_reg'] for r in gvr.values()))))
for cd in ('CD1','CD2','CD3'):
    cs=[c for c in gvr if PAN[c]['cd']==cd]; Y[cd]=dict(n=len(cs),pooled_removal_pct=float(F(100*sum(gvr[c]['removal_votes'] for c in cs),sum(gvr[c]['ballots'] for c in cs))))
top10=sorted(gvr,key=lambda c:-gvr[c]['residual'])[:10]
for nm,grp in (('cd12',[c for c in PR if PAN[c]['cd']!='CD3']),('top10_resid',top10)):
    Y['reg_'+nm]={k:sum(PR[c][k] for c in grp)/len(grp) for k in ('dem','rep','lib','np')}|{'n':len(grp)}
json.dump(Y,open(O+'extra2.json','w'),indent=1)
