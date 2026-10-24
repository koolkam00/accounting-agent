"""Pass 2: the formula of every grey (A) column, by name. See trackerdef.py for the rules."""
import json
import os

import trackerdef as T
from trackerdef import R, cfg, lk, hdr_lookup, HOL, BL0, BL1, TODAY, wd

SPEC = json.load(open(os.path.join(T.ROOT, "spec", "forms.json")))


def setf(tab, name, f):
    T.TABS[tab].cols[T.TABS[tab].index[name]].f = f


def c(tab, name):
    return T.C(tab, name)


def nz(x):
    """Blank-safe number: "" -> 0."""
    return "N(%s)" % x


def maxdate(expr):
    """SUMPRODUCT(MAX(...)) that returns "" instead of 0."""
    return 'IFERROR(1/(1/SUMPRODUCT(MAX(%s))),"")' % expr


def drops():
    t = "drops"
    D = c(t, "drop_date")
    ok = '%s="OK"' % c(t, "date_check")
    setf(t, "date_check", (
        'IF({D}="","",IF(AND(WEEKDAY({D})<>3,WEEKDAY({D})<>4),"REFUSED: a "&TEXT({D},"dddd")&". Tuesday or Wednesday only",'
        'IF(COUNTIF({H},{D})>0,"REFUSED: a federal holiday",IF(COUNTIFS({B0},"<="&WORKDAY({D},4,{H}),{B1},">="&{D})>0,'
        '"REFUSED: the five-day window overlaps a blackout","OK"))))').format(D=D, H=HOL, B0=BL0, B1=BL1))
    setf(t, "weekday", 'IF({D}="","",TEXT({D},"ddd"))'.format(D=D))
    offs = {"t_minus_10": -10, "t_minus_5": -5, "t_minus_3": -3, "t_minus_1": -1, "t_plus_1": 1, "t_plus_2": 2,
            "t_plus_4": 4, "t_plus_5": 5, "t_plus_7": 7, "t_plus_10": 10, "t_plus_14": 14}
    for k, n in offs.items():
        setf(t, k, 'IF({ok},{w},"")'.format(ok=ok, w=wd(D, n)))
    setf(t, "t_plus_30_cal", 'IF({ok},{D}+30,"")'.format(ok=ok, D=D))
    t10, t5 = c(t, "t_minus_10"), c(t, "t_minus_5")
    x = "SUMPRODUCT(({B0}<={t5})*({B1}>={t10})*{B0})".format(B0=BL0, B1=BL1, t5=t5, t10=t10)
    setf(t, "ship_by_requested", 'IF({ok},IF({x}=0,{t10},MIN({t10},WORKDAY({x}+5,-1,{H}))),"")'.format(ok=ok, x=x, t10=t10, H=HOL))
    steps = [("t_minus_10", "T-10 brand ships; approvals in"), ("t_minus_5", "T-5 receive and count"),
             ("t_minus_3", "T-3 print cards, send windows and posts"), ("t_minus_1", "T-1 confirm owners, pack"),
             ("drop_date", "T drop day"), ("t_plus_1", "T+1 placement confirmation"), ("t_plus_2", "T+2 day-3 photos and top-ups"),
             ("t_plus_4", "T+4 close survey, leftovers"), ("t_plus_5", "T+5 newsletter list, reserve"),
             ("t_plus_7", "T+7 report and office summaries"), ("t_plus_10", "T+10 brand debrief, export actuals"),
             ("t_plus_14", "T+14 return-label deadline"), ("t_plus_30_cal", "T+30 redemption check")]
    lab, dat = '"done"', '""'
    for k, label in reversed(steps):
        cell = c(t, k)
        lab = 'IF({c}>={td},"{l}",{rest})'.format(c=cell, td=TODAY, l=label, rest=lab)
        dat = 'IF({c}>={td},{c},{rest})'.format(c=cell, td=TODAY, rest=dat)
    setf(t, "next_step", 'IF(NOT({ok}),"",{l})'.format(ok=ok, l=lab))
    setf(t, "next_step_date", 'IF(NOT({ok}),"",{d})'.format(ok=ok, d=dat))
    A = c(t, "drop_id")
    setf(t, "campaigns", 'IF({A}="","",COUNTIF({r},{A}))'.format(A=A, r=R("campaigns", "drop_id")))
    setf(t, "stops", 'IF({A}="","",COUNTIF({r},{A}))'.format(A=A, r=R("stops", "drop_id")))
    setf(t, "units_allocated", 'IF({A}="","",SUMIFS({u},{d},{A},{ap},"Y"))'.format(
        A=A, u=R("approvals", "units_allocated"), d=R("approvals", "drop_id"), ap=R("approvals", "approved")))
    setf(t, "revenue_usd", 'IF({A}="","",SUMIFS({v},{d},{A}))'.format(A=A, v=R("campaigns", "revenue_usd"), d=R("campaigns", "drop_id")))
    for name, typ in (("kit_cost_usd", "kit"), ("transport_cost_usd", "transport"), ("other_direct_cost_usd", "other_direct")):
        setf(t, name, 'IF({A}="","",SUMIFS({v},{d},{A},{ty},"{typ}"))'.format(
            A=A, v=R("costs", "amount_usd"), d=R("costs", "drop_id"), ty=R("costs", "cost_type"), typ=typ))
    setf(t, "direct_cost_usd", 'IF({A}="","",{k}+{tr}+{o})'.format(A=A, k=c(t, "kit_cost_usd"), tr=c(t, "transport_cost_usd"), o=c(t, "other_direct_cost_usd")))
    setf(t, "cost_per_stop_usd", 'IF(OR({A}="",N({s})=0),"",ROUND({dc}/{s},2))'.format(A=A, s=c(t, "stops"), dc=c(t, "direct_cost_usd")))
    setf(t, "hours", 'IF({A}="","",SUMIFS({h},{d},{A}))'.format(A=A, h=R("hours", "hours"), d=R("hours", "drop_id")))
    setf(t, "contribution_usd", 'IF({A}="","",{rev}-SUMIFS({fee},{d},{A})-{dc})'.format(
        A=A, rev=c(t, "revenue_usd"), fee=R("campaigns", "processing_fee_usd"), d=R("campaigns", "drop_id"), dc=c(t, "direct_cost_usd")))
    setf(t, "contribution_per_hour_usd", 'IF(OR({A}="",N({h})=0),"",ROUND({cu}/{h},2))'.format(A=A, h=c(t, "hours"), cu=c(t, "contribution_usd")))
    cp = lambda col: R("campaigns", col)
    setf(t, "gate2_placed_share", 'IF(OR({A}="",SUMIFS({d},{dr},{A})=0),"",SUMIFS({w},{dr},{A})/SUMIFS({d},{dr},{A}))'.format(
        A=A, d=cp("units_delivered"), w=cp("units_placed_within_1bd"), dr=cp("drop_id")))
    setf(t, "gate2_min_responses", 'IF(OR({A}="",COUNTIFS({ad},{A},{aa},"Y")=0),"",SUMPRODUCT(MIN({k}+({ad}<>{A})*1000000)))'.format(
        A=A, ad=R("approvals", "drop_id"), aa=R("approvals", "on_drop"), k=R("approvals", "resp_min_key")))
    setf(t, "gate2_reports_late", 'IF(OR({A}="",{t7}=""),"",COUNTIFS({dr},{A},{g},"late"))'.format(A=A, t7=c(t, "t_plus_7"), dr=cp("drop_id"), g=cp("gate2_report_on_time")))
    setf(t, "gate2_buy_again_yes", 'IF({A}="","",COUNTIFS({dr},{A},{b},"yes"))'.format(A=A, dr=cp("drop_id"), b=cp("brand_would_buy_again")))


def brands():
    t = "brands"
    K = c(t, "intake_key")
    for f in ["brand_name", "website", "category", "product_sku", "hq_city", "contact_name", "contact_title",
              "contact_email", "contact_phone", "online_store_url", "nyc_retailers", "can_issue_discount_code",
              "budget_approver_name_title", "q1_sealed_shelf_stable_60d", "q2_labeled_ingredients_allergens",
              "q3_buy_path_near_cluster", "q4_can_ship_275_in_10bd", "q5_product_liability_insurance",
              "q6_contact_can_approve_600", "q7_why_now", "excluded_category_confirmed"]:
        setf(t, f, 'IF({K}="","",IF(COUNTIF({w},{K})>0,{a},{b}))'.format(
            K=K, w=R("brand_intake", "submitted_at"), a=lk("brand_intake", "submitted_at", K, f),
            b=lk("brand_intake_founder", "submitted_at", K, f)))
    qs = ["q1_sealed_shelf_stable_60d", "q2_labeled_ingredients_allergens", "q3_buy_path_near_cluster",
          "q4_can_ship_275_in_10bd", "q5_product_liability_insurance", "q6_contact_can_approve_600"]
    A = c(t, "brand_id")
    setf(t, "checks_yes", 'IF({K}="","",{s}+(LEN({q7})>0))'.format(K=K, s="+".join('(%s="Y")' % c(t, q) for q in qs), q7=c(t, "q7_why_now")))
    fails = "&".join('IF(%s<>"Y","%d ","")' % (c(t, q), i + 1) for i, q in enumerate(qs)) + '&IF(LEN(%s)=0,"7 ","")' % c(t, "q7_why_now")
    setf(t, "qualified", 'IF({K}="","",IF(AND({cy}=7,{ex}="Y"),"Y (as answered)","N: check "&{fails}&IF({ex}<>"Y","excluded? ","")))'.format(
        K=K, cy=c(t, "checks_yes"), ex=c(t, "excluded_category_confirmed"), fails=fails))
    setf(t, "campaigns", 'IF({A}="","",COUNTIF({r},{A}))'.format(A=A, r=R("campaigns", "brand_id")))
    fd = 'SUMIFS({sd},{b},{A},{ti},"founding",{lo},"<>Y")'.format(sd=R("campaigns", "agreement_signed_date"), b=R("campaigns", "brand_id"), A=A,
                                                                  ti=R("campaigns", "tier"), lo=R("campaigns", "founding_lock"))
    setf(t, "founding_rank", 'IF(OR({A}="",{fd}=0),"",COUNTIFS({ti},"founding",{lo},"<>Y",{sd},"<="&{fd},{sd},">0"))'.format(
        A=A, fd=fd, ti=R("campaigns", "tier"), lo=R("campaigns", "founding_lock"), sd=R("campaigns", "agreement_signed_date")))
    # Review round 1 (R1-06): payments reach the financial model once, through E's pipeline_log (payment_1/2 on E's
    # paid_brands row). The invoices tab here releases the ship date. This column says when the two disagree.
    pb = T.TABS["in_paid_brands"]
    area = "in_paid_brands!$A$2:$BZ$%d" % pb.last()
    hdr = "in_paid_brands!$A$1:$BZ$1"
    exists = 'IFERROR(COUNTIF(INDEX({ar},0,MATCH("brand_id",{h},0)),{A}),0)>0'.format(ar=area, h=hdr, A=A)
    e = lambda f: hdr_lookup("in_paid_brands", "brand_id", A, f)
    ecid = e("campaign_id")
    nv = lambda x: 'IFERROR(VALUE(%s&""),0)' % x
    dv = lambda x: 'IF(ISNUMBER(%s),%s,IFERROR(DATEVALUE(%s),0))' % (x, x, x)
    iv = lambda col: R("invoices", col)
    fpre = 'SUMIFS({pa},{c},{e},{rs},"Y")'.format(pa=iv("paid_amount_usd"), c=iv("campaign_id"), e=ecid, rs=iv("releases_ship"))
    fpre_d = 'N(SUMPRODUCT(MAX(({c}={e})*({rs}="Y")*{pd})))'.format(c=iv("campaign_id"), e=ecid, rs=iv("releases_ship"), pd=iv("paid_date"))
    fbal = 'SUMIFS({pa},{c},{e},{ty},"standard_balance")'.format(pa=iv("paid_amount_usd"), c=iv("campaign_id"), e=ecid, ty=iv("invoice_type"))
    fbal_d = 'N(SUMPRODUCT(MAX(({c}={e})*({ty}="standard_balance")*{pd})))'.format(c=iv("campaign_id"), e=ecid, ty=iv("invoice_type"), pd=iv("paid_date"))
    day = lambda x: 'IF(N({x})=0,"none",TEXT({x},"yyyy-mm-dd"))'.format(x=x)
    p1, d1, p2, d2 = nv(e("payment_1_usd")), dv(e("payment_1_date")), nv(e("payment_2_usd")), dv(e("payment_2_date"))
    setf(t, "e_payment_check", (
        'IF(OR({A}="",NOT({ex})),"",IF({ecid}="","E\'s paid_brands row has no campaign_id: type the CMP-### there; ",'
        'IF(OR(ABS({p1}-{fpre})>0.005,{d1}<>{fpre_d}),"payment 1 differs: E "&{p1}&" on "&{d1t}&", invoices "&{fpre}&" on "&{fpred}&"; ","")&'
        'IF(OR(ABS({p2}-{fbal})>0.005,{d2}<>{fbal_d}),"payment 2 differs: E "&{p2}&" on "&{d2t}&", invoices "&{fbal}&" on "&{fbald}&"; ","")))').format(
        A=A, ex=exists, ecid=ecid, p1=p1, d1=d1, p2=p2, d2=d2, fpre=fpre, fpre_d=fpre_d, fbal=fbal, fbal_d=fbal_d,
        d1t=day(d1), d2t=day(d2), fpred=day(fpre_d), fbald=day(fbal_d)))


def offices():
    t = "offices"
    A = c(t, "office_id")
    for f in ["company", "office_address", "floor_suite", "tuesday_headcount", "contact_name", "contact_phone",
              "contact_email", "pantry_owner_name", "pantry_owner_title", "pantry_owner_is_contact", "receiving_type",
              "receiving_window", "coi_required", "survey_channel", "categories_wanted", "vetoes",
              "agreement_signed_date", "founding_roster_named", "public_naming_ok", "clay_row_id"]:
        setf(t, f, 'IF({A}="","",{v})'.format(A=A, v=hdr_lookup("in_signed_offices", "office_id", A, f)))
    setf(t, "industry", 'IF({A}="","",IF({o}<>"",{o},{v}))'.format(A=A, o=c(t, "industry_override"), v=hdr_lookup("in_signed_offices", "office_id", A, "industry")))
    setf(t, "owner_phone", 'IF({A}="","",IF({o}<>"",{o},IF({v}<>"",{v},IF({ic}="Y",{cp},""))))'.format(
        A=A, o=c(t, "pantry_owner_phone_override"), v=hdr_lookup("in_signed_offices", "office_id", A, "pantry_owner_phone"),
        ic=c(t, "pantry_owner_is_contact"), cp=c(t, "contact_phone")))
    h = c(t, "tuesday_headcount")
    setf(t, "headcount_band", 'IF({A}="","",IF({h}="","unknown",IF({h}<40,"under-40",IF({h}<=75,"40-75",IF({h}<=150,"76-150",IF({h}<=250,"151-250",IF({h}<=500,"251-500","over-500")))))))'.format(A=A, h=h))
    setf(t, "size_check", 'IF({A}="","",IF({co}="","not on in_signed_offices: paste the outreach file",IF({h}="","no Tuesday headcount",IF({h}<30,"below the hard floor of 30",IF({h}<40,"30 to 39: founder\'s call",IF({h}>250,"over 250: outside the plan","OK"))))))'.format(A=A, h=h, co=c(t, "company")))
    setf(t, "default_units", 'IF(OR({A}="",{h}=""),"",MIN({mx},MAX({mn},MROUND({b}+{p}*{h},{rd}))))'.format(
        A=A, h=h, mx=cfg("units_max"), mn=cfg("units_min"), b=cfg("units_base"), p=cfg("units_per_person"), rd=cfg("units_round")))
    setf(t, "drops_so_far", 'IF({A}="","",COUNTIFS({so},{A},{sd},"<="&{td}))'.format(A=A, so=R("stops", "office_id"), sd=R("stops", "drop_date"), td=TODAY))
    setf(t, "declines", 'IF({A}="","",COUNTIFS({so},{A},{oc},"declined"))'.format(A=A, so=R("stops", "office_id"), oc=R("stops", "outcome")))


def resp_rng(colL, row_campaign):
    return 'INDIRECT("\'"&{c}&"\'!${L}$2:${L}${n}")'.format(c=row_campaign, L=colL, n=T.N["responses_rows"] + 1)


def approvals():
    t = "approvals"
    A, B = c(t, "campaign_id"), c(t, "office_id")
    g = lambda col: 'IF({A}="","",{v})'.format(A=A, v=lk("campaigns", "campaign_id", A, col))
    setf(t, "drop_id", g("drop_id"))
    setf(t, "drop_date", g("drop_date"))
    setf(t, "brand_name", g("brand_name"))
    setf(t, "company", 'IF({B}="","",{v})'.format(B=B, v=lk("offices", "office_id", B, "company")))
    L = T.TABS[t].letter("campaign_id")
    # Letters run over the offices that took the brand: not those that said no (stage 2, R5), nor those that turned it
    # away at the door (review round 1, R1-02), so a report never skips a letter.
    OD = T.TABS[t].letter("on_drop")
    setf(t, "office_seq", 'IF({A}="","",IF({od}="N","",COUNTIFS(${L}${f}:${L}{{r}},{A},${OD}${f}:${OD}{{r}},"<>N")))'.format(
        A=A, L=L, f=T.TABS[t].first(), od=c(t, "on_drop"), OD=OD))
    setf(t, "office_label", 'IF(OR({A}="",{seq}=""),"",IF(AND({mode}="names_if_public",{pub}="Y"),{co},CHAR(64+{seq})))'.format(
        A=A, mode=cfg("report_office_names"), pub=lk("offices", "office_id", B, "public_naming_ok"), co=c(t, "company"), seq=c(t, "office_seq")))
    dd = c(t, "drop_date")
    setf(t, "office_drop_number", 'IF(OR({A}="",{dd}=""),"",COUNTIFS({so},{B},{sd},"<"&{dd},{oc},"<>not_delivered")+1)'.format(
        A=A, B=B, dd=dd, so=R("stops", "office_id"), sd=R("stops", "drop_date"), oc=R("stops", "outcome")))
    setf(t, "approval_mode", 'IF({A}="","",IF(N({n})<={x},"explicit","opt-out"))'.format(A=A, n=c(t, "office_drop_number"), x=cfg("approvals_explicit_drops")))
    rep, ask = c(t, "reply"), c(t, "asked_date")
    setf(t, "approved", ('IF({A}="","",IF({m}="explicit",IF({rep}="yes","Y",IF({rep}="no","N","pending")),'
                         'IF({rep}="no","N",IF(AND({ask}<>"",{dd}<>"",{ask}<=WORKDAY(N({dd}),-5,{H})),"Y","pending"))))').format(
        A=A, m=c(t, "approval_mode"), rep=rep, ask=ask, dd=dd, H=HOL))
    # On the drop: approved, and not turned away at the door (stop outcome declined, building_refused or not_delivered
    # with no units delivered for this brand). Review round 1, R1-02.
    st = lambda col: R("stops", col)
    refused = "+".join('COUNTIFS({sd},{did},{so},{B},{oc},"{x}")'.format(sd=st("drop_id"), did=c(t, "drop_id"), so=st("office_id"), B=B, oc=st("outcome"), x=x)
                       for x in ("declined", "building_refused", "not_delivered"))
    setf(t, "on_drop", 'IF({A}="","",IF({ap}="N","N",IF({ap}<>"Y","pending",IF(AND(({rf})>0,N({ud})=0),"N","Y"))))'.format(
        A=A, ap=c(t, "approved"), rf=refused, ud=c(t, "units_delivered")))
    cat = lk("campaigns", "campaign_id", A, "category")
    cw = lk("offices", "office_id", B, "categories_wanted")
    vet = lk("offices", "office_id", B, "vetoes")
    setf(t, "fit_check", ('IF({A}="","",IF(COUNTIFS(${L}${f}:${L}${l},{A},${O}${f}:${O}${l},{B})>1,"DUPLICATE ROW; ","")&'
                          'IF(AND({vet}<>"",ISNUMBER(SEARCH({bn},{vet}))),"BRAND VETOED; ","")&'
                          'IF(ISNUMBER(SEARCH({cat},{cw})),"","info: category not on the office\'s list; ")&IF({vet}<>"","info: read the vetoes against the label; ",""))').format(
        A=A, B=B, cat=cat, cw=cw, vet=vet, bn=c(t, "brand_name"), L=L, O=T.TABS[t].letter("office_id"), f=T.TABS[t].first(), l=T.TABS[t].last()))
    setf(t, "units_allocated", 'IF({A}="","",IF({o}<>"",{o},{v}))'.format(A=A, o=c(t, "units_override"), v=lk("offices", "office_id", B, "default_units")))
    setf(t, "card_code", 'IF({A}="","",{A}&"."&{B})'.format(A=A, B=B))
    inv = lambda col: R("inventory", col)
    setf(t, "units_delivered", 'IF({A}="","",SUMIFS({q},{c},{A},{o},{B},{m},"delivered"))'.format(A=A, B=B, q=inv("qty"), c=inv("campaign_id"), o=inv("office_id"), m=inv("movement")))
    setf(t, "delivered_at", 'IF({A}="","",{x})'.format(A=A, x=maxdate('({c}={A})*({o}={B})*({m}="delivered")*({d}+{tm})'.format(
        c=inv("campaign_id"), o=inv("office_id"), m=inv("movement"), d=inv("date"), tm=inv("time"), A=A, B=B))))
    setf(t, "delivered_count_source", 'IF({A}="","",{v})'.format(A=A, v=lk("inventory", "key", '{A}&"|"&{B}&"|delivered"'.format(A=A, B=B), "count_source")))
    pk = '{A}&"|"&{B}&"|placement|Y"'.format(A=A, B=B)
    setf(t, "placement_photo_file", 'IF({A}="","",{v})'.format(A=A, v=lk("photos", "key", pk, "file_name")))
    setf(t, "placement_photo_date", 'IF({A}="","",{v})'.format(A=A, v=lk("photos", "key", pk, "taken_date")))
    cnt = lambda col: R("counts", col)
    setf(t, "placed_count", 'IF({A}="","",IF(COUNTIFS({c},{A},{o},{B},{ty},"placed")=0,"",SUMIFS({u},{c},{A},{o},{B},{ty},"placed")))'.format(
        A=A, B=B, c=cnt("campaign_id"), o=cnt("office_id"), ty=cnt("count_type"), u=cnt("units")))
    setf(t, "units_placed", 'IF({A}="","",IF({pd}="",0,N({pc})))'.format(A=A, pd=c(t, "placement_photo_date"), pc=c(t, "placed_count")))
    setf(t, "placed_within_1bd", 'IF({A}="","",IF(OR({pd}="",{dd}=""),"N",IF({pd}<=WORKDAY(N({dd}),1,{H}),"Y","N")))'.format(A=A, pd=c(t, "placement_photo_date"), dd=dd, H=HOL))
    ptime = lk("photos", "key", pk, "taken_time")
    setf(t, "placement_lag_hours", 'IF(OR({A}="",{da}="",{pd}=""),"",ROUND(({pd}+N({pt})-{da})*24,1))'.format(A=A, da=c(t, "delivered_at"), pd=c(t, "placement_photo_date"), pt=ptime))
    setf(t, "units_topped_up", 'IF({A}="","",SUMIFS({q},{c},{A},{o},{B},{m},"topped_up"))'.format(A=A, B=B, q=inv("qty"), c=inv("campaign_id"), o=inv("office_id"), m=inv("movement")))
    for col, ty in (("remaining_day3", "remaining_day3"), ("remaining_day5", "remaining_day5")):
        setf(t, col, 'IF({A}="","",IF(COUNTIFS({c},{A},{o},{B},{ty},"{x}")=0,"",SUMIFS({u},{c},{A},{o},{B},{ty},"{x}")))'.format(
            A=A, B=B, c=cnt("campaign_id"), o=cnt("office_id"), ty=cnt("count_type"), u=cnt("units"), x=ty))
    setf(t, "units_depleted_day5", 'IF(OR({A}="",{r5}=""),"",MAX(0,{up}+{tu}-{r5}))'.format(A=A, r5=c(t, "remaining_day5"), up=c(t, "units_placed"), tu=c(t, "units_topped_up")))
    ph = lambda col: R("photos", col)
    ld = maxdate('({c}={A})*({o}={B})*({ty}="later")*({u}="Y")*{d}'.format(c=ph("campaign_id"), o=ph("office_id"), ty=ph("photo_type"), u=ph("usable"), d=ph("taken_date"), A=A, B=B))
    setf(t, "later_photo_date", 'IF({A}="","",{x})'.format(A=A, x=ld))
    setf(t, "later_photo_file", 'IF(OR({A}="",{ld}=""),"",{v})'.format(A=A, ld=c(t, "later_photo_date"),
                                                                       v=lk("photos", "key2", '{A}&"|"&{B}&"|later|Y|"&{ld}'.format(A=A, B=B, ld=c(t, "later_photo_date")), "file_name")))
    setf(t, "later_photo_day", 'IF(OR({A}="",{ld}="",{dd}=""),"",NETWORKDAYS({dd},{ld},{H}))'.format(A=A, ld=c(t, "later_photo_date"), dd=dd, H=HOL))
    setf(t, "both_photos", 'IF({A}="","",IF(AND({p}<>"",{l}<>""),"Y","N"))'.format(A=A, p=c(t, "placement_photo_file"), l=c(t, "later_photo_file")))
    setf(t, "window_end", 'IF({A}="","",{v})'.format(A=A, v=lk("drops", "drop_id", c(t, "drop_id"), "t_plus_4")))
    setf(t, "resp_min_key", 'IF(OR({A}="",{od}<>"Y"),1000000,N({sr}))'.format(A=A, od=c(t, "on_drop"), sr=c(t, "survey_responses")))
    # Frozen survey totals (R1-12): once a campaign's raw answers are deleted, its numbers come from survey_frozen.
    fk = R("survey_frozen", "key")
    setf(t, "survey_frozen", 'IF({A}="","",IF(COUNTIF({fk},{A}&"|"&{B})>0,"Y",""))'.format(A=A, B=B, fk=fk))
    frz = lambda col, live: 'IF({fz}="Y",SUMIFS({v},{fk},{A}&"|"&{B}),{live})'.format(fz=c(t, "survey_frozen"), v=R("survey_frozen", col), fk=fk, A=A, B=B, live=live)
    setf(t, "seq_key", 'IF({A}="","",{A}&"|"&{s})'.format(A=A, s=c(t, "office_seq")))
    we = c(t, "window_end")
    base = '{rb},{cc},{ra},">="&{dd},{ra},"<"&({we}+1)'.format(rb=resp_rng("B", A), cc=c(t, "card_code"), ra=resp_rng("A", A), dd=dd, we=we)
    guard0 = lambda x: 'IF(OR({A}="",{dd}=""),"",IFERROR({x},0))'.format(A=A, dd=dd, x=x)
    gs = lambda col, x: 'IF(OR({A}="",{dd}=""),"",{f})'.format(A=A, dd=dd, f=frz(col, "IFERROR(%s,0)" % x))
    setf(t, "survey_responses", gs("survey_responses", "COUNTIFS(%s)" % base))
    setf(t, "tried_yes", gs("tried_yes", 'COUNTIFS(%s,%s,"Yes")' % (base, resp_rng("C", A))))
    for col, rc, val in (("tried_no_didnt_see", "F", "Didn't see it"), ("tried_no_not_for_me", "F", "Not for me"),
                         ("tried_no_gone", "F", "Gone by the time I looked"), ("buy_yes", "E", "Yes"),
                         ("buy_maybe", "E", "Maybe"), ("buy_no", "E", "No")):
        setf(t, col, gs(col, 'COUNTIFS(%s,%s,"%s")' % (base, resp_rng(rc, A), val)))
    setf(t, "rating_n", gs("rating_n", 'COUNTIFS(%s,%s,">=1")' % (base, resp_rng("D", A))))
    setf(t, "rating_sum", gs("rating_sum", 'SUMIFS(%s,%s)' % (resp_rng("D", A), base)))
    setf(t, "comments", gs("comments", 'COUNTIFS(%s,%s,"<>")' % (base, resp_rng("G", A))))
    guard = guard0
    setf(t, "qr_scans", _scan_delta(t, A, B, "q"))
    setf(t, "post_link_opens", _scan_delta(t, A, B, "p"))
    # Extra per-office survey columns, hidden at the right (the campaign totals add these up).
    checks = ('IF({A}="","",IF(COUNTIF({ofr},{B})=0,"office_id not on offices; ","")&IF(COUNTIF({cpr},{A})=0,"campaign_id not on campaigns; ","")&'
              'IF({ap}="pending","approval pending; ","")&'
              'IF(AND({ud}>0,{pd}="",OR({dd}="",{td}<=WORKDAY(N({dd}),4,{H}))),"no usable placement photo yet; ","")&IF(AND({pd}<>"",{pc}=""),"log the placed count; ","")&'
              'IF(N({up})>N({ud}),"placed more than delivered; ","")&'
              'IF(AND({r5}<>"",N({r5})>N({up})+N({tu})),"day-5 count above placed plus top-ups; ","")&'
              'IF(AND({ud}>0,{dd}<>"",{td}>WORKDAY(N({dd}),4,{H}),{r5}=""),"day-5 count missing; ","")&'
              'IF(AND({ud}>0,{dd}<>"",{td}>WORKDAY(N({dd}),4,{H}),{qs}=""),"no close link reading; ","")&{fit}&'
              'IF({ap}="N","info: office said no; ","")&IF(AND({ap}="Y",{od}="N"),"info: turned away at the door, so not on the drop (no letter, not in the report or Gate 2; the credit check is on campaigns); ","")&'
              'IF(AND({ud}>0,{pd}="",{dd}<>"",{td}>WORKDAY(N({dd}),4,{H})),"info: no usable placement photo, so nothing counts as placed; ","")&'
              'IF(AND({ud}>0,{dd}<>"",{td}>WORKDAY(N({dd}),4,{H}),N({sr})<{mr}),"info: under "&{mr}&" responses; ","")&'
              'IF({dcs}="packing_list","info: delivered count not verified; ",""))').format(
        A=A, B=B, ofr=R("offices", "office_id"), cpr=R("campaigns", "campaign_id"), fit=c(t, "fit_check"), ap=c(t, "approved"), od=c(t, "on_drop"), ud=c(t, "units_delivered"), pd=c(t, "placement_photo_date"), pc=c(t, "placed_count"),
        up=c(t, "units_placed"), r5=c(t, "remaining_day5"), tu=c(t, "units_topped_up"), dd=dd, td=TODAY, H=HOL,
        sr=c(t, "survey_responses"), mr=cfg("min_responses_per_office"), qs=c(t, "qr_scans"), dcs=c(t, "delivered_count_source"))
    setf(t, "checks", checks)
    return base, guard


def _scan_delta(t, A, B, kind):
    slug = slug_expr(A, B, kind)
    sc = lambda col: R("scans", col)
    close = 'SUMPRODUCT(MAX(({s}={slug})*({ty}="close")*{c}))'.format(s=sc("slug"), slug=slug, ty=sc("reading_type"), c=sc("clicks_to_date"))
    base = 'SUMPRODUCT(MAX(({s}={slug})*({ty}="baseline")*{c}))'.format(s=sc("slug"), slug=slug, ty=sc("reading_type"), c=sc("clicks_to_date"))
    return 'IF({A}="","",IF(COUNTIFS({s},{slug},{ty},"close")=0,"",{cl}-{bs}))'.format(A=A, s=sc("slug"), slug=slug, ty=sc("reading_type"), cl=close, bs=base)


def slug_expr(A, B, kind):
    """SAMPLE-CMP-001 + SAMPLE-O-001 + q -> SAMPLE-c001-o001-q ; CMP-001 + O-003 + p -> c001-o003-p"""
    pre = 'IF(LEFT({A},7)="SAMPLE-","SAMPLE-","")'.format(A=A)
    cc = 'LOWER(SUBSTITUTE(SUBSTITUTE({A},"SAMPLE-",""),"CMP-","c"))'.format(A=A)
    oo = 'LOWER(SUBSTITUTE(SUBSTITUTE({B},"SAMPLE-",""),"O-","o"))'.format(B=B)
    return '({pre}&{cc}&"-"&{oo}&"-{k}")'.format(pre=pre, cc=cc, oo=oo, k=kind)


def campaigns():
    t = "campaigns"
    A = c(t, "campaign_id")
    g = lambda tab, key, col: lk(tab, key, c(t, key) if key in T.TABS[t].index else key, col)
    bid, did = c(t, "brand_id"), c(t, "drop_id")
    guard = lambda x: 'IF({A}="","",{x})'.format(A=A, x=x)
    setf(t, "brand_name", guard(lk("brands", "brand_id", bid, "brand_name")))
    setf(t, "category", guard(lk("brands", "brand_id", bid, "category")))
    setf(t, "drop_date", guard('IF({ok}="OK",{d},"")'.format(ok=lk("drops", "drop_id", did, "date_check"), d=lk("drops", "drop_id", did, "drop_date"))))
    setf(t, "delivery_model", guard(lk("drops", "drop_id", did, "delivery_model")))
    n, tier, lock = c(t, "offices_contracted"), c(t, "tier"), c(t, "founding_lock")
    setf(t, "price_expected_usd", guard(
        'IF({n}="","",IF({tier}="founding",IF({lock}="Y",{lp}*MIN({n},{lm})+{ex}*MAX(0,{n}-{lm}),{fp}+{ex}*MAX(0,{n}-{fo})),'
        'IF({tier}="standard",{sp}+{ex}*MAX(0,{n}-{so}),"")))'.format(
            n=n, tier=tier, lock=lock, lp=cfg("founding_lock_per_office_usd"), lm=cfg("founding_lock_max_offices"),
            ex=cfg("extra_office_usd"), fp=cfg("founding_price_usd"), fo=cfg("founding_offices"), sp=cfg("standard_price_usd"), so=cfg("standard_offices"))))
    setf(t, "price_usd", guard('IF({o}<>"",{o},{e})'.format(o=c(t, "price_override_usd"), e=c(t, "price_expected_usd"))))
    setf(t, "payment_terms", guard('IF({tier}="founding","100% within "&{bd}&" business days of the invoice, before shipping",IF({tier}="standard","50% on signing; 50% at placement confirmation (T+1)",""))'.format(tier=tier, bd=cfg("founding_due_bd"))))
    setf(t, "cancel_by", guard(lk("drops", "drop_id", did, "t_minus_10")))
    setf(t, "ship_by_requested", guard(lk("drops", "drop_id", did, "ship_by_requested")))
    ap = lambda col: R("approvals", col)
    setf(t, "offices_on_route", guard('COUNTIF({r},{A})'.format(r=ap("campaign_id"), A=A)))
    setf(t, "offices_approved", guard('COUNTIFS({r},{A},{a},"Y")'.format(r=ap("campaign_id"), A=A, a=ap("approved"))))
    setf(t, "offices_on_drop", guard('COUNTIFS({r},{A},{a},"Y")'.format(r=ap("campaign_id"), A=A, a=ap("on_drop"))))
    setf(t, "approvals_pending", guard('COUNTIFS({r},{A},{a},"pending")'.format(r=ap("campaign_id"), A=A, a=ap("approved"))))
    setf(t, "units_allocated", guard('SUMIFS({u},{r},{A},{a},"Y")'.format(u=ap("units_allocated"), r=ap("campaign_id"), A=A, a=ap("approved"))))
    setf(t, "reserve_planned", guard('ROUNDUP({u}*{s},0)'.format(u=c(t, "units_allocated"), s=cfg("reserve_share"))))
    setf(t, "units_to_ship", guard('{u}+{r}'.format(u=c(t, "units_allocated"), r=c(t, "reserve_planned"))))
    iv = lambda col: R("invoices", col)
    setf(t, "pre_ship_paid_usd", guard('SUMIFS({p},{c},{A},{rs},"Y",{pd},">0")'.format(p=iv("paid_amount_usd"), c=iv("campaign_id"), A=A, rs=iv("releases_ship"), pd=iv("paid_date"))))
    setf(t, "pre_ship_due_usd", guard('IF({p}="","",IF({tier}="founding",{p},ROUND({p}*{ds},2)))'.format(p=c(t, "price_usd"), tier=tier, ds=cfg("deposit_share"))))
    paid_on = maxdate('({c}={A})*({rs}="Y")*N(+{pd})'.format(c=iv("campaign_id"), A=A, rs=iv("releases_ship"), pd=iv("paid_date"))).replace("N(+", "(")
    coi_ok = 'AND({cr}<>"",{ck}="Y")'.format(cr=c(t, "coi_received_date"), ck=lk("brands", "brand_id", bid, "coi_check_ok"))
    # Review round 1 (R1-07): the brand must be on brands and pass the seven checks before anything ships.
    qual_ok = 'LEFT({q},1)="Y"'.format(q=lk("brands", "brand_id", bid, "qualified"))
    setf(t, "ship_release", guard(
        ('IF(AND(N({paid})>=N({due}),N({due})>0,{sig}<>"",{coi},{qok},{dd}<>"",{pend}=0,{oa}>0),'
         '"RELEASED "&TEXT(MAX({paidon},{sig},{crd},{apd}),"yyyy-mm-dd")&": ship by "&TEXT({sbr},"ddd yyyy-mm-dd")&" (latest "&TEXT({cb},"ddd yyyy-mm-dd")&")",'
         '"HOLD: "&IF(N({paid})<N({due}),"payment ("&TEXT(N({paid}),"0")&" of "&TEXT(N({due}),"0")&") ","")&IF({sig}="","agreement ","")&'
         'IF(NOT({coi}),"certificate ","")&IF(NOT({qok}),"qualification ","")&IF({dd}="","drop date ","")&IF({pend}>0,"approvals ("&{pend}&" pending) ","")&IF({oa}=0,"no office approved ",""))').format(
            paid=c(t, "pre_ship_paid_usd"), due=c(t, "pre_ship_due_usd"), sig=c(t, "agreement_signed_date"), coi=coi_ok, qok=qual_ok,
            dd=c(t, "drop_date"), oa=c(t, "offices_approved"), oc=c(t, "offices_contracted"), paidon=paid_on, pend=c(t, "approvals_pending"),
            sbr=c(t, "ship_by_requested"), cb=c(t, "cancel_by"), crd=c(t, "coi_received_date"),
            apd='SUMPRODUCT(MAX(({ac}={A})*({aa}="Y")*({ard}+({ard}=0)*{aad})))'.format(ac=ap("campaign_id"), A=A, aa=ap("approved"), ard=ap("reply_date"), aad=ap("asked_date")))))
    inv = lambda col: R("inventory", col)
    setf(t, "units_received", guard('SUMIFS({q},{c},{A},{m},"received")'.format(q=inv("qty"), c=inv("campaign_id"), A=A, m=inv("movement"))))
    setf(t, "units_rejected", guard('SUMIFS({q},{c},{A},{m},"rejected")'.format(q=inv("qty"), c=inv("campaign_id"), A=A, m=inv("movement"))))
    setf(t, "reserve_on_hand", guard('SUMIFS({q},{c},{A})'.format(q=inv("reserve_delta"), c=inv("campaign_id"), A=A)))
    setf(t, "leftover_on_hand", guard('SUMIFS({q},{c},{A})'.format(q=inv("leftover_delta"), c=inv("campaign_id"), A=A)))
    for col in ("units_delivered", "units_placed", "units_topped_up", "survey_responses", "tried_no_didnt_see",
                "tried_no_not_for_me", "tried_no_gone", "qr_scans", "post_link_opens"):
        setf(t, col, guard('SUMIFS({v},{r},{A})'.format(v=ap(col), r=ap("campaign_id"), A=A)))
    setf(t, "units_placed_within_1bd", guard('SUMIFS({v},{r},{A},{w},"Y")'.format(v=ap("units_placed"), r=ap("campaign_id"), A=A, w=ap("placed_within_1bd"))))
    setf(t, "placed_share_1bd", guard('IF(N({d})=0,"",{w}/{d})'.format(d=c(t, "units_delivered"), w=c(t, "units_placed_within_1bd"))))
    # Offices on the drop only (R1-02): an office that turned the brand away at the door has no day-5 count to wait for.
    setf(t, "units_depleted_day5", guard('IF(COUNTIFS({r},{A},{a},"Y",{v},"")>0,"",SUMIFS({v},{r},{A},{a},"Y"))'.format(v=ap("units_depleted_day5"), r=ap("campaign_id"), A=A, a=ap("on_drop"))))
    setf(t, "survey_responses_min_office", guard('IF(N({n})=0,"",SUMPRODUCT(MIN({v}+({r}<>{A})*1000000)))'.format(
        n=c(t, "offices_on_drop"), r=ap("campaign_id"), A=A, v=ap("resp_min_key"))))
    setf(t, "offices_under_5", guard('COUNTIFS({r},{A},{a},"Y",{v},"<"&{m})'.format(r=ap("campaign_id"), A=A, a=ap("on_drop"), v=ap("survey_responses"), m=cfg("min_responses_per_office"))))
    setf(t, "survey_tried_yes", guard('SUMIFS({v},{r},{A})'.format(v=ap("tried_yes"), r=ap("campaign_id"), A=A)))
    setf(t, "survey_rating_n", guard('SUMIFS({v},{r},{A})'.format(v=ap("rating_n"), r=ap("campaign_id"), A=A)))
    setf(t, "survey_rating_avg", guard('IF(N({n})=0,"",ROUND(SUMIFS({s},{r},{A})/{n},1))'.format(n=c(t, "survey_rating_n"), s=ap("rating_sum"), r=ap("campaign_id"), A=A)))
    for col, src in (("survey_buy_yes", "buy_yes"), ("survey_buy_maybe", "buy_maybe"), ("survey_buy_no", "buy_no"), ("comments_total", "comments")):
        setf(t, col, guard('SUMIFS({v},{r},{A})'.format(v=ap(src), r=ap("campaign_id"), A=A)))
    ra = resp_rng("A", A)
    dd, we = c(t, "drop_date"), lk("drops", "drop_id", did, "t_plus_4")
    tot = 'IFERROR(COUNT({ra}),0)'.format(ra=ra)
    inw = 'IFERROR(COUNTIFS({ra},">="&{dd},{ra},"<"&({we}+1)),0)'.format(ra=ra, dd=dd, we=we)
    # After the 12-month deletion (answers_deleted_date) these two cannot be known any more: blank.
    adl = c(t, "answers_deleted_date")
    setf(t, "responses_outside_window", guard('IF(OR({dd}="",{adl}<>""),"",{tot}-{inw})'.format(dd=dd, adl=adl, tot=tot, inw=inw)))
    setf(t, "responses_unmatched_code", guard('IF(OR({dd}="",{adl}<>""),"",{inw}-N({sr}))'.format(dd=dd, adl=adl, inw=inw, sr=c(t, "survey_responses"))))
    rd = lambda col: R("redemptions", col)
    asof = maxdate('({c}={A})*{d}'.format(c=rd("campaign_id"), A=A, d=rd("as_of_date")))
    setf(t, "code_redemptions_as_of", guard(asof))
    setf(t, "code_redemptions_to_date", guard('IF({a}="","",SUMIFS({v},{c},{A},{d},{a}))'.format(a=c(t, "code_redemptions_as_of"), v=rd("redemptions_to_date"), c=rd("campaign_id"), A=A, d=rd("as_of_date"))))
    d30 = 'SUMPRODUCT(MIN(({c}={A})*({y}="Y")*{d}+(({c}<>{A})+({y}<>"Y")>0)*1000000))'.format(c=rd("campaign_id"), A=A, y=rd("is_day30"), d=rd("as_of_date"))
    setf(t, "code_redemptions_day30", guard('IF(COUNTIFS({c},{A},{y},"Y")=0,"",SUMIFS({v},{c},{A},{d},{d30}))'.format(c=rd("campaign_id"), A=A, y=rd("is_day30"), v=rd("redemptions_to_date"), d=rd("as_of_date"), d30=d30)))
    setf(t, "revenue_usd", guard('SUMIFS({v},{c},{A})'.format(v=iv("amount_usd"), c=iv("campaign_id"), A=A)))
    setf(t, "deposit_usd", guard('IF(COUNTIFS({c},{A},{ty},"standard_deposit",{p},">0")=0,"",SUMIFS({pa},{c},{A},{ty},"standard_deposit"))'.format(c=iv("campaign_id"), A=A, ty=iv("invoice_type"), p=iv("paid_date"), pa=iv("paid_amount_usd"))))
    setf(t, "deposit_paid_date", guard(maxdate('({c}={A})*({ty}="standard_deposit")*{p}'.format(c=iv("campaign_id"), A=A, ty=iv("invoice_type"), p=iv("paid_date")))))
    setf(t, "invoice_paid_date", guard(maxdate('({c}={A})*(({ty}="founding_full")+({ty}="standard_balance"))*{p}'.format(c=iv("campaign_id"), A=A, ty=iv("invoice_type"), p=iv("paid_date")))))
    setf(t, "processing_fee_usd", guard('SUMIFS({v},{c},{A})'.format(v=iv("processing_fee_usd"), c=iv("campaign_id"), A=A)))
    co = lambda col: R("costs", col)
    setf(t, "direct_cost_usd", guard('SUMIFS({v},{c},{A})'.format(v=co("amount_usd"), c=co("campaign_id"), A=A)))
    share = 'IF(SUMIFS({oa},{dr},{did})=0,0,{me}/SUMIFS({oa},{dr},{did}))'.format(oa=R("campaigns", "offices_approved"), dr=R("campaigns", "drop_id"), did=did, me=c(t, "offices_approved"))
    shared_cost = '(SUMIFS({v},{d},{did})-SUMPRODUCT(({d}={did})*(LEN({c})>0)*{v}))'.format(v=co("amount_usd"), d=co("drop_id"), did=did, c=co("campaign_id"))
    setf(t, "shared_cost_usd", guard('ROUND({s}*{x},2)'.format(s=share, x=shared_cost)))
    hr = lambda col: R("hours", col)
    setf(t, "hours_direct", guard('SUMIFS({v},{c},{A})'.format(v=hr("hours"), c=hr("campaign_id"), A=A)))
    shared_h = '(SUMIFS({v},{d},{did})-SUMPRODUCT(({d}={did})*(LEN({c})>0)*{v}))'.format(v=hr("hours"), d=hr("drop_id"), did=did, c=hr("campaign_id"))
    setf(t, "hours_shared", guard('ROUND({s}*{x},2)'.format(s=share, x=shared_h)))
    setf(t, "contribution_usd", guard('{r}-{f}-{d}-{s}'.format(r=c(t, "revenue_usd"), f=c(t, "processing_fee_usd"), d=c(t, "direct_cost_usd"), s=c(t, "shared_cost_usd"))))
    setf(t, "contribution_per_hour_usd", guard('IF(N({a})+N({b})=0,"",ROUND({cu}/({a}+{b}),2))'.format(a=c(t, "hours_direct"), b=c(t, "hours_shared"), cu=c(t, "contribution_usd"))))
    setf(t, "photo_compliance", guard('IF(N({n})=0,"",COUNTIFS({r},{A},{a},"Y",{b},"Y")/{n})'.format(n=c(t, "offices_on_drop"), r=ap("campaign_id"), A=A, a=ap("on_drop"), b=ap("both_photos"))))
    setf(t, "placement_lag_hours_avg", guard('IF(COUNTIFS({r},{A},{l},">=0")=0,"",ROUND(SUMIFS({l},{r},{A})/COUNTIFS({r},{A},{l},">=0"),1))'.format(r=ap("campaign_id"), A=A, l=ap("placement_lag_hours"))))
    setf(t, "report_due", guard(lk("drops", "drop_id", did, "t_plus_7")))
    setf(t, "debrief_due", guard(lk("drops", "drop_id", did, "t_plus_10")))
    setf(t, "redemption_check_date", guard(lk("drops", "drop_id", did, "t_plus_30_cal")))
    setf(t, "gate2_placed", guard('IF({s}="","",IF({s}>={g},"pass","miss"))'.format(s=c(t, "placed_share_1bd"), g=cfg("gate2_placed_share"))))
    setf(t, "gate2_responses", guard('IF({m}="","",IF({m}>={x},"pass","miss"))'.format(m=c(t, "survey_responses_min_office"), x=cfg("min_responses_per_office"))))
    setf(t, "gate2_report_on_time", guard('IF({rd}="",IF({due}="","",IF({td}>{due},"late","due")),IF({rd}<={due},"pass","late"))'.format(rd=c(t, "report_delivered_date"), due=c(t, "report_due"), td=TODAY)))
    td = TODAY
    w = lambda name: c(t, name)
    checks = ('IF({A}="","",'
              'IF(COUNTIF({drr},{did})=0,"drop_id not on drops; ",IF({dd}="","drop date missing or refused; ",""))&'
              'IF(AND({po}<>"",{po}<>{pe}),"price differs from the price list; ","")&'
              'IF(AND(LEFT({sr},4)="HOLD",{cb}<>"",{td}>=WORKDAY(N({cb}),-3,{H})),"SHIP HOLD within 3 business days of T-10; ","")&'
              'IF(AND({ap}>0,{cb}<>"",{td}>{cb}),"approvals still pending after T-10; ","")&'
              'IF({roh}<0,"reserve below zero: check inventory; ","")&'
              'IF(AND({dd}<>"",{td}>WORKDAY(N({dd}),14,{H}),N({roh})+N({loh})<>0),"units still on hand after T+14; ","")&'
              'IF(N({um})>0,"info: "&{um}&" in-window responses with a card code that matches no office (not counted); ","")&'
              'IF(AND({nl}="Y",{nfu}=""),"newsletter form URL missing; ","")&'
              'IF(AND({nl}="Y",{dd}<>"",{td}>WORKDAY(N({dd}),5,{H}),{npd}=""),"newsletter list not yet passed on (due T+5); ","")&'
              'IF(AND({npd}<>"",{nud}=""),"delete unticked emails; ","")&'
              'IF(AND({npd}<>"",{nd}="",{td}>{npd}+{keep}),"DELETE the consented emails (30 days after passing on); ","")&'
              'IF(AND({dd}<>"",{spt}="",{td}>=WORKDAY(N({dd}),-4,{H})),"survey prefill template missing (due T-4); ","")&'
              'IF(AND({spt}<>"",ISERROR(SEARCH("CARDCODE",{spt}))),"prefill template has no CARDCODE; ","")&'
              'IF(AND({cps}="",{dd}<>"",{td}>=WORKDAY(N({dd}),-3,{H})),"card text not yet sent to the brand; ","")&'
              'IF(AND({rdd}="",{rcd}<>"",{td}>{rcd}),"day-30 redemption count due; ","")&'
              'IF(AND(LEFT({sr},8)="RELEASED",{sed}=""),"ship-date email due (template 02): send it, then log ship_email_sent_date and ship_email_units; ","")&'
              'IF(AND({seu}<>"",N({uts})>0,N({urc})=0,N({seu})<>N({uts})),"units changed since the ship-date email of "&IF({sed}="","?",TEXT({sed},"yyyy-mm-dd"))&" ("&{seu}&", now "&{uts}&"): send the brand the revised numbers (template 02) and log them; ","")&'
              'IF({g3}="late","report late; ","")&'
              'IF(AND(N({oc})>0,{oa}<N({oc}),{ap}=0),"info: "&(N({oc})-{oa})&" office(s) short of the contract: add a roster office or credit $"&IF({tier}="founding",{fl},{ex})&" each; ","")&'
              'IF({adl}<>"",IF(COUNTIF({sfc},{A})=0,"answers deleted but no frozen totals: the survey numbers now read 0 (tools/freeze_survey.py, SOP answers_delete); ",""),'
              'IF(AND({dd}<>"",{td}>={dd},ISREF(INDIRECT("\'"&{A}&"\'!B1"))),IF(INDIRECT("\'"&{A}&"\'!B1")<>"Card code (filled in for you)","survey tab column B is not the card code: fix the form or the tab; ",""),IF(AND({dd}<>"",{td}>={dd}),"no survey tab named "&{A}&"; ","")))&'
              'IF(COUNTIF({brr},{bid})=0,"brand_id not on brands; ",IF(LEFT({qual},1)<>"Y","brand not qualified ("&{qual}&"): nothing ships until it is; ",""))&'
              'IF(AND(COUNTIF({brr},{bid})>0,OR({bln}="",{bad}="",{bem}="")),"brand billing details missing on brands (legal name, address, email): needed for the invoice; ","")&'
              'IF(AND({tier}="founding",{lock}<>"Y",N({frank})>3),"the founding tier is for the first three brands only (this is brand "&{frank}&"): use standard; ","")&'
              'IF(AND({tier}="founding",{lock}<>"Y",COUNTIFS({cbr},{bid},{ctr},"founding",{clr},"<>Y")>1),"a brand has the founding price once; its next two campaigns are founding_lock = Y; ","")&'
              'IF(AND({lock}="Y",COUNTIFS({cbr},{bid},{ctr},"founding",{clr},"Y")>2),"founding_lock is for the brand\'s next two campaigns only (this is a third): use standard; ","")&'
              'IF(AND({lock}="Y",COUNTIFS({cbr},{bid},{ctr},"founding",{clr},"<>Y")=0),"founding_lock without a first founding campaign for this brand; ","")&'
              'IF(AND(N({urc})>0,{dd}<>"",{td}>=WORKDAY(N({dd}),-5,{H})),IF(N({urc})-N({urj})<N({ua}),"received "&(N({urc})-N({urj}))&" usable units for "&{ua}&" allocated: reduce units_override evenly (SOP section 4, short shipment); ","")&'
              'IF(AND(N({urc})<N({uts}),COUNTIFS({isc},{A},{ist},"short_shipment")=0),"received "&{urc}&" of "&{uts}&" due: log a short_shipment issue and tell the brand today; ",""),"")&'
              'IF(AND({dd}<>"",{td}>=WORKDAY(N({dd}),1,{H}),N({oc})>0,{cred}<{cexp}-0.005),"credit due from T+1: "&MAX(0,N({oc})-{plc})&" of "&{oc}&" contracted offices not placed by T+1, $"&{cexp}&" due, $"&{cred}&" in credit notes so far (template 06, make_invoice.py); ","")&'
              'IF(AND({pe2}<>"",{dd}<>"",{pe2}<EDATE(WORKDAY(N({dd}),4,{H}),12)),"info: brand insurance ends "&TEXT({pe2},"yyyy-mm-dd")&": diary the renewal certificate; ",""))').format(
        drr=R("drops", "drop_id"), did=w("drop_id"), pe2=lk("brands", "brand_id", bid, "coi_policy_end_date"), oc=w("offices_contracted"), oa=w("offices_approved"), tier=w("tier"),
        fl=cfg("founding_lock_per_office_usd"), ex=cfg("extra_office_usd"),
        A=A, dd=w("drop_date"), po=w("price_override_usd"), pe=w("price_expected_usd"), sr=w("ship_release"), cb=w("cancel_by"),
        td=td, H=HOL, ap=w("approvals_pending"), roh=w("reserve_on_hand"), loh=w("leftover_on_hand"), um=w("responses_unmatched_code"),
        nl=w("newsletter_option"), nfu=w("newsletter_form_url"), npd=w("newsletter_passed_date"), nud=w("newsletter_unticked_deleted_date"),
        nd=w("newsletter_deleted_date"), keep=cfg("newsletter_keep_days"), spt=w("survey_prefill_template"), cps=w("card_proof_sent_date"),
        rdd=w("code_redemptions_day30"), rcd=w("redemption_check_date"), g3=w("gate2_report_on_time"),
        sed=w("ship_email_sent_date"), seu=w("ship_email_units"), uts=w("units_to_ship"), urc=w("units_received"),
        adl=w("answers_deleted_date"), sfc=R("survey_frozen", "campaign_id"), brr=R("brands", "brand_id"), bid=bid,
        qual=lk("brands", "brand_id", bid, "qualified"), bln=lk("brands", "brand_id", bid, "brand_legal_name"),
        bad=lk("brands", "brand_id", bid, "billing_address"), bem=lk("brands", "brand_id", bid, "billing_email"),
        lock=w("founding_lock"), frank=lk("brands", "brand_id", bid, "founding_rank"), cbr=R("campaigns", "brand_id"),
        ctr=R("campaigns", "tier"), clr=R("campaigns", "founding_lock"), urj=w("units_rejected"), ua=w("units_allocated"),
        isc=R("issues", "campaign_id"), ist=R("issues", "issue_type"),
        cred='(-SUMIFS({a},{c},{A},{ty},"credit_note"))'.format(a=iv("amount_usd"), c=iv("campaign_id"), A=A, ty=iv("invoice_type")),
        cexp='(IF({tier}="founding",{fl},{ex})*MAX(0,N({oc})-{plc}))'.format(tier=w("tier"), fl=cfg("founding_lock_per_office_usd"), ex=cfg("extra_office_usd"), oc=w("offices_contracted"),
                                                                     plc='COUNTIFS({r},{A},{od},"Y",{w1},"Y")'.format(r=ap("campaign_id"), A=A, od=ap("on_drop"), w1=ap("placed_within_1bd"))),
        plc='COUNTIFS({r},{A},{od},"Y",{w1},"Y")'.format(r=ap("campaign_id"), A=A, od=ap("on_drop"), w1=ap("placed_within_1bd")))
    setf(t, "checks", checks)


def links():
    t = "links"
    first = T.TABS["approvals"].first()
    idx = 'INT((ROW()-{h})/2)+1'.format(h=T.TABS[t].first())
    camp = 'INDEX({r},{i})'.format(r=R("approvals", "campaign_id"), i=idx)
    off = 'INDEX({r},{i})'.format(r=R("approvals", "office_id"), i=idx)
    setf(t, "campaign_id", 'IF({c}="","",{c})'.format(c=camp))
    setf(t, "office_id", 'IF({c}="","",{o})'.format(c=camp, o=off))
    A, B = c(t, "campaign_id"), c(t, "office_id")
    setf(t, "link_type", 'IF({A}="","",IF(MOD(ROW()-{h},2)=0,"qr","post"))'.format(A=A, h=T.TABS[t].first()))
    k = 'IF({lt}="qr","q","p")'.format(lt=c(t, "link_type"))
    pre = 'IF(LEFT({A},7)="SAMPLE-","SAMPLE-","")'.format(A=A)
    cc = 'LOWER(SUBSTITUTE(SUBSTITUTE({A},"SAMPLE-",""),"CMP-","c"))'.format(A=A)
    oo = 'LOWER(SUBSTITUTE(SUBSTITUTE({B},"SAMPLE-",""),"O-","o"))'.format(B=B)
    setf(t, "slug", 'IF({A}="","",{pre}&{cc}&"-"&{oo}&"-"&{k})'.format(A=A, pre=pre, cc=cc, oo=oo, k=k))
    setf(t, "short_url", 'IF({A}="","","https://"&{d}&"/"&{s})'.format(A=A, d=cfg("short_link_domain"), s=c(t, "slug")))
    setf(t, "card_code", 'IF({A}="","",{A}&"."&{B})'.format(A=A, B=B))
    tpl = lk("campaigns", "campaign_id", A, "survey_prefill_template")
    setf(t, "destination_url", ('IF({A}="","",IF({tpl}="","(add the survey prefill template on campaigns)",'
                                'SUBSTITUTE({tpl},"CARDCODE",{cc})&"&utm_source=office-pantry&utm_medium="&{lt}&"&utm_campaign="&LOWER({A})&"&utm_content="&LOWER({B})))').format(
        A=A, B=B, tpl=tpl, cc=c(t, "card_code"), lt=c(t, "link_type")))
    setf(t, "qr_file", 'IF(OR({A}="",{lt}<>"qr"),"",{s}&".png")'.format(A=A, lt=c(t, "link_type"), s=c(t, "slug")))
    ddl = lk("campaigns", "campaign_id", A, "drop_date")
    setf(t, "checks", ('IF({A}="","",IF(AND({tpl}="",{dd}<>"",{td}>=WORKDAY(N({dd}),-4,{H})),"no prefill template yet (due T-4); ","")'
                       '&IF(COUNTIF({sl},{s})>1,"DUPLICATE slug; ",""))').format(
        A=A, tpl=tpl, dd=ddl, td=TODAY, H=HOL, sl=R("links", "slug"), s=c(t, "slug")))


def scans():
    t = "scans"
    S = c(t, "slug")
    for col in ("campaign_id", "office_id", "link_type"):
        setf(t, col, 'IF({S}="","",{v})'.format(S=S, v=lk("links", "slug", S, col)))
    setf(t, "checks", 'IF({S}="","",IF({c}="","slug not in links; ","")&IF({r}="","reading type missing; ","")&IF(COUNTIFS({sl},{S},{rt},{r})>1,"two readings of this type: keep one; ",""))'.format(
        S=S, c=c(t, "campaign_id"), r=c(t, "reading_type"), sl=R("scans", "slug"), rt=R("scans", "reading_type")))


def inventory():
    t = "inventory"
    A, B, M, Q, BK = c(t, "campaign_id"), c(t, "office_id"), c(t, "movement"), c(t, "qty"), c(t, "bucket")
    setf(t, "drop_date", 'IF({A}="","",{v})'.format(A=A, v=lk("campaigns", "campaign_id", A, "drop_date")))
    bk = 'IF({BK}="","reserve",{BK})'.format(BK=BK)
    pile = '{M}="returned_to_brand",{M}="given_to_roster_office",{M}="released_to_office",{M}="disposed"'.format(M=M)
    setf(t, "reserve_delta", ('IF({A}="","",IF(OR({M}="received"),N({Q}),IF(OR({M}="rejected",{M}="delivered",{M}="topped_up"),-N({Q}),'
                              'IF(AND(OR({pile}),{bk}="reserve"),-N({Q}),IF(AND({M}="correction",{bk}="reserve"),N({Q}),0)))))').format(A=A, M=M, Q=Q, pile=pile, bk=bk))
    setf(t, "rejected_delta", ('IF({A}="","",IF({M}="rejected",N({Q}),IF(AND(OR({pile}),{bk}="rejected"),-N({Q}),IF(AND({M}="correction",{bk}="rejected"),N({Q}),0))))').format(A=A, M=M, Q=Q, pile=pile, bk=bk))
    setf(t, "leftover_delta", ('IF({A}="","",IF({M}="collected",N({Q}),IF(AND(OR({pile}),{bk}="leftover"),-N({Q}),IF(AND({M}="correction",{bk}="leftover"),N({Q}),0))))').format(A=A, M=M, Q=Q, pile=pile, bk=bk))
    BB, DD = c(t, "best_by"), c(t, "drop_date")
    setf(t, "best_by_ok", 'IF(OR({M}<>"received",{BB}="",{DD}=""),"",IF({BB}>={DD}+{d},"Y","N"))'.format(M=M, BB=BB, DD=DD, d=cfg("min_shelf_life_days")))
    setf(t, "key", 'IF({A}="","",{A}&"|"&{B}&"|"&{M})'.format(A=A, B=B, M=M))
    setf(t, "checks", ('IF({A}="","",'
                       'IF(COUNTIF({cpr},{A})=0,"campaign_id not on campaigns; ",IF(AND({B}<>"",COUNTIFS({apc},{A},{apo},{B})=0),"office not on this campaign (approvals tab); ",""))&IF(AND(OR({M}="delivered",{M}="topped_up",{M}="collected"),{B}=""),"office needed; ","")&'
                       'IF(AND({M}<>"correction",N({Q})<=0),"qty must be above 0; ","")&'
                       'IF(AND({M}="received",OR({BB}="",{lot}="")),"log lot and best-by; ","")&'
                       'IF(AND({ok}="N",SUMIFS({qr},{cr},{A},{lr},{lot},{mr},"rejected")<N({Q})),"UNDER "&{d}&" DAYS LEFT ON THE DROP DAY: reject these units; ","")&'
                       'IF(AND({M}="delivered",COUNTIF({kr},{key})>1),"two delivered rows for this office: use one; ","")&'
                       'IF(AND({M}="delivered",{src}=""),"who counted?; ",""))').format(
        cpr=R("campaigns", "campaign_id"), apc=R("approvals", "campaign_id"), apo=R("approvals", "office_id"), A=A, M=M, B=B, Q=Q, BB=BB, lot=c(t, "lot"), ok=c(t, "best_by_ok"), d=cfg("min_shelf_life_days"),
        kr=R("inventory", "key"), key=c(t, "key"), src=c(t, "count_source"),
        qr=R("inventory", "qty"), cr=R("inventory", "campaign_id"), lr=R("inventory", "lot"), mr=R("inventory", "movement")))


def counts():
    t = "counts"
    A, B, D = c(t, "campaign_id"), c(t, "office_id"), c(t, "date")
    dd = lk("campaigns", "campaign_id", A, "drop_date")
    setf(t, "window_day", 'IF(OR({A}="",{D}=""),"",IF({D}<{dd},0,NETWORKDAYS({dd},{D},{H})))'.format(A=A, D=D, dd=dd, H=HOL))
    setf(t, "checks", ('IF({A}="","",'
                       'IF(COUNTIF({cpr},{A})=0,"campaign_id not on campaigns; ",IF(AND({B}<>"",COUNTIFS({apc},{A},{apo},{B})=0),"office not on this campaign (approvals tab); ",""))&IF(COUNTIFS({ca},{A},{oa},{B},{ta},{ty})>1,"two "&{ty}&" counts: keep one; ","")&'
                       'IF(AND({ty}="remaining_day5",N({wd})<5),"day-5 count logged before day 5; ","")&'
                       'IF(AND({src}="photo",{pid}=""),"which photo?; ",""))').format(
        cpr=R("campaigns", "campaign_id"), apc=R("approvals", "campaign_id"), apo=R("approvals", "office_id"), A=A, B=B, ca=R("counts", "campaign_id"), oa=R("counts", "office_id"), ta=R("counts", "count_type"), ty=c(t, "count_type"),
        wd=c(t, "window_day"), src=c(t, "source"), pid=c(t, "photo_id")))


def photos():
    t = "photos"
    A, B, D, TY = c(t, "campaign_id"), c(t, "office_id"), c(t, "taken_date"), c(t, "photo_type")
    setf(t, "drop_date", 'IF({A}="","",{v})'.format(A=A, v=lk("campaigns", "campaign_id", A, "drop_date")))
    DD = c(t, "drop_date")
    setf(t, "window_day", 'IF(OR({A}="",{D}="",{DD}=""),"",IF({D}<{DD},0,NETWORKDAYS({DD},{D},{H})))'.format(A=A, D=D, DD=DD, H=HOL))
    setf(t, "usable", 'IF({A}="","",IF(AND({np}="Y",OR({TY}="later",{cv}="Y")),"Y","N"))'.format(A=A, np=c(t, "no_people_or_screens"), TY=TY, cv=c(t, "card_visible")))
    setf(t, "expected_file_name", 'IF(OR({A}="",{D}=""),"",{A}&"_"&{B}&"_"&{TY}&"_"&TEXT({D},"yyyy-mm-dd")&".jpg")'.format(A=A, B=B, TY=TY, D=D))
    setf(t, "key", 'IF({A}="","",{A}&"|"&{B}&"|"&{TY}&"|"&{u})'.format(A=A, B=B, TY=TY, u=c(t, "usable")))
    setf(t, "key2", 'IF({A}="","",{k}&"|"&N({D}))'.format(A=A, k=c(t, "key"), D=D))
    setf(t, "checks", ('IF({A}="","",'
                       'IF(COUNTIF({cpr},{A})=0,"campaign_id not on campaigns; ",IF(AND({B}<>"",COUNTIFS({apc},{A},{apo},{B})=0),"office not on this campaign (approvals tab); ",""))&IF({D}="","taken date missing; ","")&IF(AND({fn}<>"",{fn}<>{ef}),"file name differs from the convention; ","")&'
                       'IF(AND({TY}="placement",{u}="Y",COUNTIF({kr},{k})>1),"two usable placement photos: mark one N; ","")&'
                       'IF({np}<>"Y","info: not usable (a person, screen or whiteboard may show): never used, delete the file; ","")&'
                       'IF(AND({TY}="placement",{cv}<>"Y"),"info: not usable as a placement photo (no card); ","")&'
                       'IF(AND({TY}="placement",N({wd})>2),"info: placed after the first business day; ","")&'
                       'IF(AND({TY}="later",{wd}<>"",OR(N({wd})<3,N({wd})>5)),"info: later photo outside day 3 to 5; ",""))').format(
        cpr=R("campaigns", "campaign_id"), apc=R("approvals", "campaign_id"), apo=R("approvals", "office_id"), A=A, B=B, D=D, np=c(t, "no_people_or_screens"), TY=TY, cv=c(t, "card_visible"), fn=c(t, "file_name"), ef=c(t, "expected_file_name"),
        wd=c(t, "window_day"), u=c(t, "usable"), kr=R("photos", "key"), k=c(t, "key")))


def redemptions():
    t = "redemptions"
    A, D = c(t, "campaign_id"), c(t, "as_of_date")
    setf(t, "days_after_drop", 'IF(OR({A}="",{D}="",{dd}=""),"",{D}-N({dd}))'.format(A=A, D=D, dd=lk("campaigns", "campaign_id", A, "drop_date")))
    setf(t, "is_day30", 'IF({d}="","",IF({d}>=30,"Y","N"))'.format(d=c(t, "days_after_drop")))


def issues():
    t = "issues"
    D, TY = c(t, "date"), c(t, "issue_type")
    setf(t, "days_open", 'IF({D}="","",IF({cl}="",{td}-{D},{cl}-{D}))'.format(D=D, cl=c(t, "closed_date"), td=TODAY))
    setf(t, "checks", ('IF({D}="","",IF(AND({TY}="complaint_or_reaction",OR({bt}="",{bt}>{D})),"REMOVE the product at that office and tell the brand TODAY; ","")&'
                       'IF(AND({TY}="recall_or_pull",{cl}=""),"pull from every office within one business day; tell every office today; ","")&'
                       'IF({TY}="brand_asks_employee_data","info: decline: we collect no employee data; ","")&'
                       'IF(AND({TY}="late_arrival",{cl}=""),"not in by T-3: slip one week (tools/opscal.py slip), tell every office today; ",""))').format(
        D=D, TY=TY, bt=c(t, "brand_told_date"), cl=c(t, "closed_date")))


def hours():
    t = "hours"
    D, A, H, DR, CP = c(t, "date"), c(t, "activity"), c(t, "hours"), c(t, "drop_id"), c(t, "campaign_id")
    keys = ",".join('"%s"' % k for k in T.ACTIVITIES)
    setf(t, "checks", ('IF({D}="","",IF(ISNA(MATCH({A},{{{keys}}},0)),"activity must be one of the seven keys; ","")&'
                       'IF(OR(N({H})<=0,N({H})>16),"hours?; ","")&IF(AND({CP}<>"",{DR}=""),"campaign without drop_id; ","")&'
                       'IF(AND({DR}<>"",COUNTIF({dr},{DR})=0),"drop_id not on drops; ",""))').format(
        D=D, A=A, keys=keys, H=H, CP=CP, DR=DR, dr=R("drops", "drop_id")))


def costs():
    t = "costs"
    D, DR = c(t, "date"), c(t, "drop_id")
    setf(t, "checks", 'IF({D}="","",IF(COUNTIF({dr},{DR})=0,"drop_id not on drops; ","")&IF(N({a})<=0,"amount?; ","")&IF({ty}="","cost type?; ",""))'.format(
        D=D, DR=DR, dr=R("drops", "drop_id"), a=c(t, "amount_usd"), ty=c(t, "cost_type")))


def invoices():
    t = "invoices"
    I, A, TY, ISS = c(t, "invoice_id"), c(t, "campaign_id"), c(t, "invoice_type"), c(t, "issued_date")
    setf(t, "brand_name", 'IF({A}="","",{v})'.format(A=A, v=lk("campaigns", "campaign_id", A, "brand_name")))
    setf(t, "due_date", 'IF(OR({I}="",{ISS}=""),"",IF({TY}="founding_full",WORKDAY({ISS},{bd},{H}),{ISS}))'.format(I=I, ISS=ISS, TY=TY, bd=cfg("founding_due_bd"), H=HOL))
    setf(t, "total_usd", 'IF({I}="","",N({a})+N({tx}))'.format(I=I, a=c(t, "amount_usd"), tx=c(t, "sales_tax_usd")))
    tot, pd, pa = c(t, "total_usd"), c(t, "paid_date"), c(t, "paid_amount_usd")
    applied = '(-SUMPRODUCT(({cr}={A})*({tr}="credit_note")*(LEN({pr})=0)*{ar}))'.format(cr=R("invoices", "campaign_id"), A=A, tr=R("invoices", "invoice_type"), pr=R("invoices", "paid_date"), ar=R("invoices", "amount_usd"))
    setf(t, "status", ('IF({I}="","",IF({TY}="credit_note",IF({pd}<>"","refunded","credit applied"),IF({pd}<>"",IF(N({pa})>={tot}-0.005,"paid",'
                       'IF(AND({TY}="standard_balance",N({pa})+{ap}>={tot}-0.005),"paid (less credit)","part paid")),'
                       'IF({ISS}="","draft",IF({td}>{due},"overdue","sent")))))').format(I=I, TY=TY, pd=pd, pa=pa, tot=tot, ISS=ISS, td=TODAY, due=c(t, "due_date"), ap=applied))
    setf(t, "releases_ship", 'IF({I}="","",IF(OR({TY}="founding_full",{TY}="standard_deposit"),"Y","N"))'.format(I=I, TY=TY))
    price = lk("campaigns", "campaign_id", A, "price_usd")
    exp = 'IF({TY}="founding_full",{p},IF({TY}="standard_deposit",ROUND({p}*{ds},2),IF({TY}="standard_balance",{p}-ROUND({p}*{ds},2),"")))'.format(TY=TY, p=price, ds=cfg("deposit_share"))
    setf(t, "checks", ('IF({I}="","",IF(COUNTIF({ir},{I})>1,"DUPLICATE invoice number; ","")&IF(COUNTIF({cpr},{A})=0,"campaign_id missing or not on campaigns; ","")&'
                       'IF(AND({TY}<>"credit_note",{exp}<>"",ABS(N({a})-N({exp}))>0.005),"amount differs from the price ("&{exp}&") - credit notes go on their own row; ","")&'
                       'IF(AND({TY}="credit_note",N({a})>=0),"a credit note is negative; ","")&'
                       'IF(AND({pd}<>"",N({pa})>{tot}+0.005,{TY}<>"credit_note"),"paid more than the total; ","")&'
                       'IF(AND({pd}<>"",{m}=""),"method?; ",""))').format(
        I=I, A=A, cpr=R("campaigns", "campaign_id"), ir=R("invoices", "invoice_id"), TY=TY, exp=exp, a=c(t, "amount_usd"), pd=pd, pa=pa, tot=tot, m=c(t, "method")))


def intake_founder():
    """office_intake_founder / brand_intake_founder: CONTRACTS 6.3 columns from the Google Form tabs.
    INDIRECT so the formulas survive the founder replacing the form tab when linking the form."""
    cats = SPEC["categories"]

    def src(tab, L):
        x = 'INDIRECT("{t}!{L}"&ROW())'.format(t=tab, L=L)
        return 'IF({x}="","",{x})'.format(x=x)

    def opts(item):
        return item["options"]

    for key, tab, target in (("office_intake", "office_form", "office_intake_founder"), ("brand_intake", "brand_form", "brand_intake_founder")):
        form = SPEC["forms"][key]
        letters = {}
        for i, it in enumerate(form["items"]):
            letters[it["maps_to"]] = T.colletter(i + 2)
        ts = 'INDIRECT("{t}!A"&ROW())'.format(t=tab)
        on = lambda x: 'IF({ts}="","",{x})'.format(ts=ts, x=x)
        cols = T.TABS[target].cols
        for col in cols:
            n = col.name
            if n == "submitted_at":
                col.f = 'IF({ts}="","",TEXT({ts},"yyyy-mm-dd""T""hh:mm:ss"))'.format(ts=ts)
                continue
            if n == "form_version":
                col.f = on(cfg("office_form_version" if key == "office_intake" else "brand_form_version"))
                continue
            if n == "source":
                col.f = on('"founder"')
                continue
            if n not in letters:
                col.f = '""'
                continue
            L = letters[n]
            v = src(tab, L)
            item = next(it for it in form["items"] if it["maps_to"] == n)
            if n == "categories_wanted":
                parts = "&".join('IF(ISNUMBER(SEARCH("%s",%s)),"%s;","")' % (lab, v, k) for k, lab, blab in cats)
                allk = ";".join(k for k, a, b in cats)
                col.f = on('IF(ISNUMBER(SEARCH("Any of them",{v})),"{allk}",IF(LEN({p})=0,"",LEFT({p},LEN({p})-1)))'.format(v=v, allk=allk, p=parts))
            elif n == "category":
                expr = '""'
                for k, lab, blab in reversed(cats):
                    expr = 'IF({v}="{b}","{k}",{rest})'.format(v=v, b=blab, k=k, rest=expr)
                col.f = on(expr)
            elif n in ("website", "online_store_url"):
                col.f = on('IF({v}="","",IF(LEFT(LOWER({v}),4)="http",{v},"https://"&{v}))'.format(v=v))
            elif n == "pantry_owner_name":
                col.f = on('IF({ic}="Y",{cn},{v})'.format(ic=T.C(target, "pantry_owner_is_contact"), cn=T.C(target, "contact_name"), v=v))
            elif n == "pantry_owner_title":
                col.f = on('IF({ic}="Y",{ct},{v})'.format(ic=T.C(target, "pantry_owner_is_contact"), ct=T.C(target, "contact_title"), v=v))
            elif n == "budget_approver_name_title":
                col.f = on('IF({ic}="Y",{cn}&", "&{ct},{v})'.format(ic=T.C(target, "budget_approver_is_contact"), cn=T.C(target, "contact_name"), ct=T.C(target, "contact_title"), v=v))
            elif n == "excluded_category_confirmed":
                col.f = on('IF({v}<>"","Y","")'.format(v=v))
            elif isinstance(item.get("options"), list) and item["type"] in ("mc", "dropdown"):
                expr = v if item["type"] == "mc_other" else '""'
                for lab, val in reversed(item["options"]):
                    expr = 'IF({v}="{l}","{val}",{rest})'.format(v=v, l=lab, val=val, rest=expr)
                col.f = on(expr)
            else:
                col.f = on(v)


def stops():
    t = "stops"
    A, B = c(t, "drop_id"), c(t, "office_id")
    setf(t, "drop_date", 'IF({A}="","",IF({ok}="OK",{d},""))'.format(A=A, ok=lk("drops", "drop_id", A, "date_check"), d=lk("drops", "drop_id", A, "drop_date")))
    for col in ("company", "office_address", "floor_suite", "receiving_window", "receiving_type", "pantry_owner_name",
                "owner_phone", "front_desk_fallback_ok", "building_coi_status"):
        setf(t, col, 'IF({B}="","",{v})'.format(B=B, v=lk("offices", "office_id", B, col)))
    ap = lambda col: R("approvals", col)
    setf(t, "campaigns_here", 'IF({A}="","",COUNTIFS({d},{A},{o},{B},{a},"Y"))'.format(A=A, B=B, d=ap("drop_id"), o=ap("office_id"), a=ap("approved")))
    setf(t, "units_here", 'IF({A}="","",SUMIFS({u},{d},{A},{o},{B},{a},"Y"))'.format(A=A, B=B, u=ap("units_allocated"), d=ap("drop_id"), o=ap("office_id"), a=ap("approved")))
    dd = c(t, "drop_date")
    setf(t, "first_drop", 'IF(OR({A}="",{dd}=""),"",IF(COUNTIFS({so},{B},{sd},"<"&{dd},{oc},"<>not_delivered")=0,"Y","N"))'.format(
        A=A, B=B, dd=dd, so=R("stops", "office_id"), sd=R("stops", "drop_date"), oc=R("stops", "outcome")))
    setf(t, "minutes_on_site", 'IF(OR({a}="",{b}=""),"",ROUND(({b}-{a})*1440,0))'.format(a=c(t, "arrival_time"), b=c(t, "departure_time")))
    model = lk("drops", "drop_id", A, "delivery_model")
    setf(t, "checks", ('IF({A}="","",IF(COUNTIFS({dr},{A},{orr},{B})>1,"DUPLICATE stop; ","")&'
                       'IF(AND(OR({coi}="yes",{coi}="unsure"),{cs}<>"received",{cs}<>"not_needed"),"building certificate not received; ","")&'
                       'IF({ph}="","owner phone missing; ","")&IF(N({ch})=0,"no approved brand for this stop; ","")&'
                       'IF(AND({dd}<>"",{td}>{dd},{oc}=""),"log the outcome; ","")&'
                       'IF(AND(OR({oc}="declined",{oc}="building_refused",{oc}="not_delivered"),N({ch})>0,{dlv}>=N({ch})),"outcome says "&{oc}&" but every brand here is logged delivered: fix the outcome, or delete the wrong delivered rows (SOP section 4); ","")&'
                       'IF(AND(OR({oc}="declined",{oc}="building_refused",{oc}="not_delivered"),{dlv}>0,{dlv}<N({ch})),"info: "&(N({ch})-{dlv})&" brand(s) turned away at the door, the rest delivered; ","")&'
                       'IF(AND({fd}="Y",{model}="direct-ship"),"info: first drop: visit in person on T; ","")&'
                       'IF(AND({rt}="front desk",{fb}<>"Y"),"info: front desk not agreed: the owner must take it; ",""))').format(
        A=A, B=B, dr=R("stops", "drop_id"), orr=R("stops", "office_id"), coi=lk("offices", "office_id", B, "coi_required"),
        cs=c(t, "building_coi_status"), ph=c(t, "owner_phone"), ch=c(t, "campaigns_here"), fd=c(t, "first_drop"), model=model,
        rt=c(t, "receiving_type"), fb=c(t, "front_desk_fallback_ok"), dd=dd, td=TODAY, oc=c(t, "outcome"),
        dlv='COUNTIFS({d},{A},{o},{B},{a},"Y",{u},">0")'.format(d=ap("drop_id"), A=A, o=ap("office_id"), B=B, a=ap("approved"), u=ap("units_delivered"))))


def survey_frozen():
    t = "survey_frozen"
    A, B = c(t, "campaign_id"), c(t, "office_id")
    setf(t, "key", 'IF({A}="","",{A}&"|"&{B})'.format(A=A, B=B))


def build_all():
    T.define()
    drops(); brands(); offices(); stops(); approvals(); campaigns(); links(); scans(); inventory(); counts(); photos()
    redemptions(); issues(); hours(); costs(); invoices(); intake_founder(); survey_frozen()
    missing = [(t.name, col.name) for t in T.TABS.values() for col in t.cols if col.kind == "A" and col.f is None]
    if missing:
        raise SystemExit("formula missing: %s" % missing)
    return T.TABS
