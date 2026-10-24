import pandas as pd, re
from urllib.parse import urlparse
B='/home/user/accounting-agent/desk-drop/cluster-1-flatiron/'
CUT='2024-10-24'
UNDATED=('builtin','deskpass','liquidspace')
def dom(u):
    try:
        h=urlparse(u).netloc.lower()
        h=h[4:] if h.startswith('www.') else h
        return h
    except: return ''
def fresh(url,date,typ=''):
    if not url: return False
    d=dom(url)
    if any(x in d for x in UNDATED): return False
    if not date: return False
    # month-only: treat YYYY-MM as first of month conservatively? use end of month (lenient)
    if re.fullmatch(r'\d{4}',date): return date>='2025'
    if re.fullmatch(r'\d{4}-\d{2}',date): return date>=CUT[:7]
    return date>=CUT
def test(df,name,u1,d1,u2,d2,conf='confidence'):
    bad=[]
    for _,r in df.iterrows():
        f1=fresh(r[u1],r[d1]); f2=fresh(r[u2],r[d2]) if u2 else False
        anyfresh=f1 or f2
        indep = bool(r[u2]) and dom(r[u1])!=dom(r[u2]) if u2 else False
        c=r[conf]
        if c=='high' and not (anyfresh and indep): bad.append((r.iloc[0],c,'high w/o fresh+indep',r[u1],r[d1],r[u2] if u2 else '',r[d2] if d2 else ''))
        if c=='medium' and not anyfresh: bad.append((r.iloc[0],c,'medium w/o fresh',r[u1],r[d1],r[u2] if u2 else '',r[d2] if d2 else ''))
        # high where second source old?
    print(name,len(df),'violations',len(bad))
    for b in bad: print('   ',b)
    return bad
c=pd.read_csv(B+'companies.csv',dtype=str,keep_default_na=False)
n=pd.read_csv(B+'near_miss.csv',dtype=str,keep_default_na=False)
test(c,'companies','address_source_url','address_source_date','second_source_url','second_source_date')
test(n,'near_miss','address_source_url','address_source_date','second_source_url','second_source_date')
w=pd.read_csv(B+'coworking.csv',dtype=str,keep_default_na=False)
w['sd2']=''
test(w,'coworking','source_url','source_date','second_source_url','sd2')
r=pd.read_csv(B+'retailers.csv',dtype=str,keep_default_na=False)
print(r[['retailer_id','retailer_name','confidence','source_url','source_date','operating_evidence_url']].to_string())
# high rows where both sources are within 24m?
for df,nm in [(c,'companies'),(n,'near')]:
    h=df[df.confidence=='high']
    old2=h[[not fresh(a,b) for a,b in zip(h.second_source_url,h.second_source_date)]]
    old1=h[[not fresh(a,b) for a,b in zip(h.address_source_url,h.address_source_date)]]
    print(nm,'high rows with 2nd source not fresh:',len(old2),'; 1st not fresh:',len(old1))
    print(old2[['company_id','company_name','address_source_url','address_source_date','second_source_url','second_source_date']].to_string())
