# PASS A (pandas/numpy/statsmodels/pdfplumber/openpyxl): Nebraska full reversal, 2026* statewide races.
import json, glob, os, re, sys, numpy as np, pandas as pd, statsmodels.api as sm, openpyxl
sys.path.insert(0,'/workspace/nebraska-elections/scripts'); import vr
R='/workspace/nebraska-reverse/raw/'; O='/workspace/nebraska-reverse/passA/'; NE='/workspace/nebraska-elections/'
RACES=[('senate','U.S. Senate','13224_102','PET','REP'),('governor','Governor','13508_105','DEM','REP'),
       ('secretary_of_state','Secretary of State','13222_106','DEM','REP'),('treasurer','State Treasurer','13223_107','DEM','REP'),
       ('attorney_general','Attorney General','13217_108','DEM','REP')]
# ballots per county (turnout export)
B={}
for f in glob.glob(R+'turnout_20261127/*.xlsx'):
    ws=openpyxl.load_workbook(f).active; rows=list(ws.iter_rows(values_only=True))
    i=[k for k,r in enumerate(rows) if r[0]=='County'][0]; r=rows[i+1]; B[r[0].strip()]=(int(r[1]),int(r[2]))
assert len(B)==93
proc,_,vrows=vr.parse(R+'vr_Statewide-November-2026.pdf'); assert proc=='11/01/2026'
FIX=lambda n:'McPherson' if n=='Mcpherson' else n
REG={FIX(r[0]):dict(rep=r[1],dem=r[2],lib=r[3],np=r[7],tot=r[8]) for r in vrows if r[0]!='Grand Total'}; assert len(REG)==93
for r in REG.values(): assert r['tot']>0
proc22,_,v22=vr.parse(NE+'sources/vr_Statewide-November-2022.pdf')
REG22={FIX(r[0]):r for r in v22 if r[0]!='Grand Total'}
pop=pd.read_csv(NE+'sources/census_co-est2025-alldata.csv',encoding='latin1'); pop=pop[(pop.STATE==31)&(pop.COUNTY>0)]
POP=dict(zip(pop.CTYNAME.str.replace(' County',''),pop.POPESTIMATE2025)); assert len(POP)==93
panel=pd.read_csv(NE+'statewide/NE Statewide Reverse-Factoring - all 93 counties all cycles.csv').set_index('county')
def rhalf(x): return np.sign(x)*np.floor(np.abs(x)+0.5)
OUT={}; ALL={}
for slug,label,rid,dp,rp in RACES:
    d=json.load(open(R+f'sos_portal_20261127/SW_{rid}.json'))['d']; rows={}
    for x in d:
        c=x['CountyName'].strip(); rows.setdefault(c,{}); rows[c][x['PartyCode']]=rows[c].get(x['PartyCode'],0)+int(x['calcCandidateVotes'])
    assert len(rows)==93
    cand={x['PartyCode']:x['calcCandidate'].strip() for x in d}
    df=pd.DataFrame([dict(county=c,population=int(POP[c]),cd=panel.loc[c,'cd'],all_mail=panel.loc[c,'all_mail'],ballots=B[c][0],registered_portal=B[c][1],
        dem_reg=REG[c]['dem'],tot_reg=REG[c]['tot'],dem=v[dp],rep=v[rp],race_total=sum(v.values())) for c,v in rows.items()])
    df['D_reg_pct']=df.dem_reg/df.tot_reg*100; df['S_pct_ballots']=df.dem/df.ballots*100; df['gap']=df.S_pct_ballots-df.D_reg_pct
    df['gap_2022_gov']=df.county.map(panel.G_2022); df['dG_vs_2022_gov']=df.gap-df.gap_2022_gov
    m=sm.OLS(df.gap,sm.add_constant(df.D_reg_pct/100)).fit(); M=float(m.params.iloc[1]); Bo=float(m.params.iloc[0])
    df['line']=M*df.D_reg_pct/100+Bo; df['residual']=df.gap-df.line; df['offset']=Bo
    df['removal_pct_raw']=df.residual+Bo; df['zeroed']=df.removal_pct_raw<0; df['removal_pct']=df.removal_pct_raw.clip(lower=0)
    df['removal_votes_exact']=df.removal_pct/100*df.ballots; df['removal_votes']=rhalf(df.removal_votes_exact).astype(int)
    df['offset_part']=np.where(df.zeroed,0,Bo/100*df.ballots); df['resid_part']=np.where(df.zeroed,0,df.residual/100*df.ballots)
    df['capped']=df.removal_votes>df.dem; df['removal_votes']=np.minimum(df.removal_votes,df.dem)
    df['dem_after']=df.dem-df.removal_votes; df['rep_after']=df.rep+df.removal_votes
    df['win_before']=np.where(df.dem>df.rep,'D',np.where(df.rep>df.dem,'R','tie')); df['win_after']=np.where(df.dem_after>df.rep_after,'D',np.where(df.rep_after>df.dem_after,'R','tie'))
    df=df.sort_values(['population','county'],ascending=[False,True]).reset_index(drop=True); df.insert(0,'pop_rank',range(1,94))
    Dt,Rt,Tt,Bt=int(df.dem.sum()),int(df.rep.sum()),int(df.race_total.sum()),int(df.ballots.sum()); Rem=int(df.removal_votes.sum())
    OUT[slug]=dict(label=label,race_id=rid,dem_party=dp,dem_cand=cand[dp],rep_cand=cand[rp],dem=Dt,rep=Rt,race_total=Tt,ballots=Bt,m=M,b=Bo,r2=float(m.rsquared),
        m_se=float(m.bse.iloc[1]),b_se=float(m.bse.iloc[0]),removed=Rem,removed_exact=float(df.removal_votes_exact.sum()),offset_part=float(df.offset_part.sum()),resid_part=float(df.resid_part.sum()),
        dem_pct=100*Dt/Tt,rep_pct=100*Rt/Tt,dem_after=Dt-Rem,rep_after=Rt+Rem,dem_pct_after=100*(Dt-Rem)/Tt,rep_pct_after=100*(Rt+Rem)/Tt,
        margin_before=100*(Dt-Rt)/Tt,margin_after=100*(Dt-Rt-2*Rem)/Tt,remove_only_dem_pct=100*(Dt-Rem)/(Tt-Rem),remove_only_rep_pct=100*Rt/(Tt-Rem),
        winner_before=cand[dp] if Dt>Rt else cand[rp],winner_after=cand[dp] if Dt-Rem>Rt+Rem else cand[rp],
        n_D_before=int((df.win_before=='D').sum()),n_D_after=int((df.win_after=='D').sum()),zeroed=df.loc[df.zeroed,'county'].tolist(),capped=df.loc[df.capped,'county'].tolist(),
        n_pos_resid=int((df.residual>0).sum()),others={k:v for k,v in cand.items() if k not in(dp,rp)},
        top10=df.nlargest(10,'removal_votes')[['county','population','cd','ballots','dem','removal_pct','removal_votes']].to_dict('records'))
    df.to_csv(O+f'{slug}.csv',index=False,float_format='%.10f'); ALL[slug]=df
# history: same line G=m(D/100)+b fitted each cycle from the prior verified panel (ballots denominator)
H={}
for y in (2018,2020,2022,2024):
    g=panel[f'G_{y}']; Dp=panel[f'RD_{y}']; m=sm.OLS(g,sm.add_constant(Dp/100)).fit(); M=float(m.params.iloc[1]); Bo=float(m.params.iloc[0])
    res=g-(M*Dp/100+Bo); rem=(res+Bo).clip(lower=0); votes=rhalf(rem/100*panel[f'ballots_{y}']).astype(int)
    pooled=100*panel[f'D_{y}'].sum()/panel[f'ballots_{y}'].sum()-100*panel[f'reg_dem_{y}'].sum()/panel[f'reg_tot_{y}'].sum()
    H[y]=dict(m=M,b=Bo,r2=float(m.rsquared),mean_gap=float(g.mean()),n_gap_pos=int((g>0).sum()),pooled_G=float(pooled),removed=int(votes.sum()),n_zeroed=int((res+Bo<0).sum()),
              race={2018:'Governor (Krist)',2020:'President (Biden)',2022:'Governor (Blood)',2024:'President (Harris)'}[y])
gv=ALL['governor'].set_index('county')
H[2026]=dict(m=OUT['governor']['m'],b=OUT['governor']['b'],r2=OUT['governor']['r2'],mean_gap=float(gv.gap.mean()),n_gap_pos=int((gv.gap>0).sum()),
    pooled_G=100*gv.dem.sum()/gv.ballots.sum()-100*gv.dem_reg.sum()/gv.tot_reg.sum(),removed=OUT['governor']['removed'],n_zeroed=len(OUT['governor']['zeroed']),race='Governor (Walz)*')
# analyst-notes data
dg=gv.dG_vs_2022_gov
N=dict(dG_mean=float(dg.mean()),dG_allmail=float(dg[gv.all_mail=='yes'].mean()),dG_other=float(dg[gv.all_mail=='no'].mean()),n_dG_pos=int((dg>0).sum()),
  by_cd={cd:dict(n=int((gv.cd==cd).sum()),mean_resid=float(gv.residual[gv.cd==cd].mean()),mean_removal_pct=float(gv.removal_pct[gv.cd==cd].mean()),mean_dG=float(dg[gv.cd==cd].mean()),
     removed=int(gv.removal_votes[gv.cd==cd].sum()),ballots=int(gv.ballots[gv.cd==cd].sum()),pooled_removal_pct=float(100*gv.removal_votes[gv.cd==cd].sum()/gv.ballots[gv.cd==cd].sum())) for cd in ('CD1','CD2','CD3')})
s16=panel.index[panel.dG_2018to2022>0].tolist(); N['sixteen']=s16; N['dG1822_mean']=float(panel.dG_2018to2022.mean())
# NP/Lib/Rep registration share change Nov 2022 -> Nov 2026 per county
rows=[]
for c in gv.index:
    a=REG22[c]; b=REG[c]; t22=a[-1]; t26=b['tot']
    rows.append(dict(county=c,cd=gv.loc[c,'cd'],all_mail=gv.loc[c,'all_mail'],dem22=100*a[2]/t22,dem26=100*b['dem']/t26,rep22=100*a[1]/t22,rep26=100*b['rep']/t26,lib22=100*a[3]/t22,lib26=100*b['lib']/t26,np22=100*a[-2]/t22,np26=100*b['np']/t26,
        resid26=gv.loc[c,'residual'],dG=dg[c],in16=c in s16))
P=pd.DataFrame(rows)
for k in ('dem','rep','lib','np'): P[f'd_{k}']=P[f'{k}26']-P[f'{k}22']
P.to_csv(O+'party_reg_change_2022_2026.csv',index=False,float_format='%.10f')
grp=lambda q:{k:float(P.loc[q,f'd_{k}'].mean()) for k in ('dem','rep','lib','np')}|{'n':int(q.sum())}
top10=set(gv.nlargest(10,'residual').index)
N['reg_change']=dict(all=grp(P.county.notna()),sixteen=grp(P.in16),top10_resid=grp(P.county.isin(top10)),cd3=grp(P.cd=='CD3'),cd12=grp(P.cd!='CD3'),allmail=grp(P.all_mail=='yes'))
N['top10_resid']=sorted(top10)
N['corr_resid_vs_dnp']=float(np.corrcoef(P.resid26,P.d_np)[0,1]); N['corr_resid_vs_dlib']=float(np.corrcoef(P.resid26,P.d_lib)[0,1]); N['corr_resid_vs_drep']=float(np.corrcoef(P.resid26,P.d_rep)[0,1])
N['n_np_down']=int((P.d_np<0).sum()); N['n_lib_down']=int((P.d_lib<0).sum()); N['n_rep_down']=int((P.d_rep<0).sum())
# early / election-day governor split where county official report columns sum exactly (prior verified panel)
ED=panel[['S_ED_2026','S_early_2026']].dropna(); N['ed_early_n']=len(ED)
json.dump(dict(races=OUT,history=H,notes=N),open(O+'results.json','w'),indent=1,default=lambda o:o.item() if hasattr(o,'item') else str(o))
for s,v in OUT.items(): print(s,f"m={v['m']:.4f} b={v['b']:.4f} r2={v['r2']:.3f} D={v['dem_pct']:.2f} R={v['rep_pct']:.2f} rem={v['removed']:,} after D={v['dem_pct_after']:.2f} R={v['rep_pct_after']:.2f} win {v['winner_before']}->{v['winner_after']} zeroed={v['zeroed']} capped={v['capped']} offshare={v['offset_part']/v['removed_exact']:.3f}")
for y,v in H.items(): print(y,{k:(round(x,3) if isinstance(x,float) else x) for k,x in v.items()})
print(json.dumps(N,indent=0,default=str)[:3000])
# --- extra analyst-note stats (pass A)
X={}
for cd in ('CD1','CD2','CD3'):
    q=panel.cd==cd; X[cd]=dict(dG1822=float(panel.dG_2018to2022[q].mean()),dG2024=float(panel.dG_2020to2024[q].mean()))
in16=gv.index.isin(s16)
X['sixteen']=dict(n_cd3=int((panel.loc[s16,'cd']=='CD3').sum()),RD2022_16=float(panel.loc[s16,'RD_2022'].mean()),RD2022_other=float(panel.loc[~panel.index.isin(s16),'RD_2022'].mean()),
  resid26_16=float(gv.residual[in16].mean()),resid26_other=float(gv.residual[~in16].mean()),dG26_16=float(dg[in16].mean()),dG26_other=float(dg[~in16].mean()),
  zeroed26=sorted(set(s16)&set(OUT['governor']['zeroed'])),dG1822_16=float(panel.loc[s16,'dG_2018to2022'].mean()),dem_reg22_16=int(panel.loc[s16,'reg_dem_2022'].sum()),pop_16=int(panel.loc[s16,'pop2025'].sum()))
X['corr_resid_drep']=float(np.corrcoef(P.resid26,P.d_rep)[0,1]); X['corr_resid_dnp']=float(np.corrcoef(P.resid26,P.d_np)[0,1]); X['corr_resid_dlib']=float(np.corrcoef(P.resid26,P.d_lib)[0,1])
X['ballots_total']=int(gv.ballots.sum()); X['gov_total_over_ballots']=float(gv.race_total.sum()/gv.ballots.sum())
X['allmail_counties']=sorted(gv.index[gv.all_mail=='yes'])
json.dump(X,open(O+'extra.json','w'),indent=1); print(X)
