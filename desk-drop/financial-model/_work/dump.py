import sys, recalc
wb, res = recalc.recalc(sys.argv[1] if len(sys.argv)>1 and sys.argv[1].endswith('.xlsx') else recalc.DEFAULT)
def show(sheet, rng):
    ws = wb[sheet]
    for row in ws[rng]:
        vals = []
        for c in row:
            v = c.value
            if v is None: v = ""
            elif hasattr(v,'strftime'): v = v.strftime('%Y-%m-%d')
            elif isinstance(v,float): v = round(v,2)
            vals.append(str(v)[:22])
        if any(vals): print(" | ".join(vals))
for spec in sys.argv[1:]:
    if spec.endswith('.xlsx'): continue
    sh, rng = spec.split(':',1)
    print(f"=== {sh} {rng}"); show(sh, rng)
