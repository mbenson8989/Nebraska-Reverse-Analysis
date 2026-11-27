import json, csv
B='/workspace/nebraska-reverse/'; A=json.load(open(B+'passA/results.json')); Pb=json.load(open(B+'passB/results.json'))
COLS=['population','ballots','dem_reg','tot_reg','dem','rep','race_total','D_reg_pct','gap','residual','removal_pct','removal_votes','dem_after','rep_after','zeroed']
INT={'population','ballots','dem_reg','tot_reg','dem','rep','race_total','removal_votes','dem_after','rep_after'}
rep={}; log=[]; tot_c=tot_m=0
def eq(a,b,isint): return (a==b) if isint else abs(float(a)-float(b))<1e-9
for slug in Pb['races']:
    ra={r['county']:r for r in csv.DictReader(open(B+f'passA/{slug}.csv'))}; rb={r['county']:r for r in csv.DictReader(open(B+f'passB/{slug}.csv'))}
    assert set(ra)==set(rb) and len(ra)==93
    cells=mm=0
    for c in ra:
        for k in COLS:
            a,b=ra[c][k],rb[c][k]
            if k=='zeroed': ok=(a=='True')==(b=='True')
            elif k in INT: ok=int(float(a))==int(b)
            else: ok=abs(float(a)-float(b))<1e-9
            cells+=1; mm+=not ok
            if not ok: log.append((slug,c,k,a,b))
    sa,sb=A['races'][slug],Pb['races'][slug]; sc=0; smm=0
    for k in ('m','b','dem','rep','race_total','removed','dem_after','rep_after','dem_pct','rep_pct','dem_pct_after','rep_pct_after'):
        ok=eq(sa[k],sb[k],isinstance(sb[k],int)); sc+=1; smm+=not ok
        if not ok: log.append((slug,'SUMMARY',k,sa[k],sb[k]))
    ok=sorted(sa['zeroed'])==sorted(sb['zeroed']); sc+=1; smm+=not ok
    rep[slug]=dict(county_cells=cells,county_mismatches=mm,summary_checks=sc,summary_mismatches=smm,sos_statewide_checks='county sums = SOS statewide CSV for every candidate party (asserted in pass B)')
    tot_c+=cells+sc; tot_m+=mm+smm
hc=hm=0
for y,hb in Pb['history'].items():
    ha=A['history'][y]
    for k in ('m','b','mean_gap','n_gap_pos','removed'):
        ok=eq(ha[k],hb[k],isinstance(hb[k],int)); hc+=1; hm+=not ok
        if not ok: log.append(('history',y,k,ha[k],hb[k]))
nc=nm=0; NA,NB=A['notes'],Pb['notes']
for k in ('dG_mean','dG_allmail','dG_other'): ok=eq(NA[k],NB[k],False); nc+=1; nm+=not ok
ok=sorted(NA['sixteen'])==NB['sixteen']; nc+=1; nm+=not ok
for cd in ('CD1','CD2','CD3'):
    for k in ('mean_resid','removed','mean_dG'): ok=eq(NA['by_cd'][cd][k],NB['cd'][cd][k],k=='removed'); nc+=1; nm+=not ok
for g in ('all','sixteen','cd3','allmail'):
    for k in ('dem','rep','lib','np'): ok=eq(NA['reg_change'][g][k],NB['reg_change'][g][k],False); nc+=1; nm+=not ok
for k in ('n_np_down','n_lib_down','n_rep_down'): ok=NA[k]==NB[k]; nc+=1; nm+=not ok
pa={r['county']:r for r in csv.DictReader(open(B+'passA/party_reg_change_2022_2026.csv'))}
for c,v in NB['party_reg_change'].items():
    for k in ('dem','rep','lib','np'): ok=abs(float(pa[c]['d_'+k])-v[k])<1e-9; nc+=1; nm+=not ok
out=dict(races=rep,history=dict(checks=hc,mismatches=hm),notes=dict(checks=nc,mismatches=nm),total_checks=tot_c+hc+nc,total_mismatches=tot_m+hm+nm,mismatch_log=log[:50])
json.dump(out,open(B+'verification/compare_summary.json','w'),indent=1); print(json.dumps({k:v for k,v in out.items() if k!='mismatch_log'},indent=1)); print(log[:10])
XA=json.load(open(B+'passA/extra.json')); XB=json.load(open(B+'passB/extra.json')); xc=xm=0
def walk(a,b,path=''):
    global xc,xm
    if isinstance(b,dict): [walk(a[k],b[k],path+'/'+k) for k in b]
    else:
        ok=(a==b) if isinstance(b,(int,list,str)) else abs(a-b)<1e-9; xc+=1; xm+=not ok
        if not ok: print('MISMATCH',path,a,b)
walk(XA,XB); out['extra']=dict(checks=xc,mismatches=xm); out['total_checks']+=xc; out['total_mismatches']+=xm
json.dump(out,open(B+'verification/compare_summary.json','w'),indent=1); print('extra',xc,xm,'TOTAL',out['total_checks'],out['total_mismatches'])
Y=json.load(open(B+'passB/extra2.json')); RAa=A; yc=ym=0
def chk(a,b,tag):
    global yc,ym
    ok=(a==b) if isinstance(b,int) else abs(a-b)<1e-9; yc+=1; ym+=not ok
    if not ok: print('MISMATCH',tag,a,b)
for s in Pb['races']:
    a=RAa['races'][s]
    for k in ('remove_only_dem_pct','remove_only_rep_pct','n_D_before','n_D_after','n_pos_resid','r2'): chk(a[k],Y[s][k],s+k)
    chk(a['offset_part']/a['removed_exact'],Y[s]['offset_share'],s+'offshare')
for y in ('2018','2020','2022','2024'): chk(RAa['history'][y]['pooled_G'],Y['H'+y]['pooled_G'],y); chk(RAa['history'][y]['r2'],Y['H'+y]['r2'],y+'r2')
chk(RAa['history']['2026']['pooled_G'],Y['H2026']['pooled_G'],'2026')
for cd in ('CD1','CD2','CD3'): chk(RAa['notes']['by_cd'][cd]['n'],Y[cd]['n'],cd); chk(RAa['notes']['by_cd'][cd]['pooled_removal_pct'],Y[cd]['pooled_removal_pct'],cd+'p')
for nm in ('cd12','top10_resid'):
    for k in ('dem','rep','lib','np','n'): chk(RAa['notes']['reg_change'][nm][k],Y['reg_'+nm][k],nm+k)
out['extra2']=dict(checks=yc,mismatches=ym); out['total_checks']+=yc; out['total_mismatches']+=ym
json.dump(out,open(B+'verification/compare_summary.json','w'),indent=1); print('extra2',yc,ym,'TOTAL',out['total_checks'],out['total_mismatches'])
