#!/usr/bin/env python3
"""Print the stage 1 counts used in _work/stage1-notes.md and the report back (markdown)."""
import collections
import os

import pandas as pd

import common as C

o = pd.read_csv(os.path.join(C.A_DIR, "offices.csv"), dtype=str, keep_default_na=False)
b = pd.read_csv(os.path.join(C.A_DIR, "brands.csv"), dtype=str, keep_default_na=False)
po, pb = o[o.gate_result == "pass"], b[b.gate_result == "pass"]
to, tb = o[o.top50 == "Y"], b[b.top60 == "Y"]


def vc(s):
    return ", ".join(f"{k} {v}" for k, v in s.value_counts().items())


print("## Offices")
print(f"- rows {len(o)}: companies {sum(o.org_type == 'company')} (companies.csv {sum(o.b_candidate_status.isin(['candidate', 'excluded-coworking', 'excluded-not-office']))}, near_miss.csv {sum(o.b_candidate_status.str.startswith('near-miss'))}), coworking operator sites {sum(o.org_type == 'coworking-operator')}")
print(f"- passed gates {len(po)} (companies {sum(po.org_type == 'company')}: B candidates {sum(po.b_candidate_status == 'candidate')}, near-miss {sum(po.b_candidate_status.str.startswith('near-miss'))}; coworking operators {sum(po.org_type == 'coworking-operator')})")
c = collections.Counter()
for g in o[o.gate_result == "fail"].gate_reason:
    for part in g.split("; "):
        c[part.split(" (")[0]] += 1
print("- gate failures (a row can fail more than one): " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
print(f"- passed onsite band: {vc(po.onsite_band)}")
print(f"- passed attendance signal: {vc(po.attendance_signal)}; Tuesday named {sum(po.tuesday_named_in_policy == 'Y')}")
print(f"- passed holds: {sum(po.hold_before_outreach == 'Y')}")
print(f"- top 50: B candidates {sum(to.b_candidate_status == 'candidate')}, near-miss {sum(to.b_candidate_status.str.startswith('near-miss'))}, coworking {sum(to.org_type == 'coworking-operator')}; bands {vc(to.onsite_band)}")
print(f"- top 50 attendance: {vc(to.attendance_signal)}; lease {vc(to.lease_status)}; confidence {vc(to.confidence)}; holds {sum(to.hold_before_outreach == 'Y')}; why-now {sum(to.why_now != '')}")
print(f"- top 50 score range {to.score.astype(float).min()} to {to.score.astype(float).max()}; passed median {po.score.astype(float).median()}")
print(f"- contacts found: 0 (stage 2); lobby type known for {sum(po.lobby_type != 'unknown')} passed rows")
print()
print("## Brands")
print(f"- rows {len(b)} (BR1 {sum(b.research_slice == 'BR1')}, BR2 {sum(b.research_slice == 'BR2')}, BR3 {sum(b.research_slice == 'BR3')}, BR4 {sum(b.research_slice == 'BR4')}, BR5 {sum(b.research_slice == 'BR5')})")
c = collections.Counter()
for g in b[b.gate_result == "fail"].gate_failed:
    for k in g.split(";"):
        c[k] += 1
print(f"- passed gates {len(pb)}; failed {len(b) - len(pb)}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
print(f"- passed nearest grade: {vc(pb.nearest_retailer_grade)}; graded store inside the cluster {sum((pb.nearest_retailer_inside_cluster == 'Y') & (pb.nearest_retailer_grade != 'unverified'))}")
print(f"- passed HQ: {vc(pb.hq_class)}")
print(f"- passed why-now: {vc(pb.why_now_type)}")
print(f"- passed founder_review Y {sum(pb.founder_review == 'Y')}; Startup CPG Y {sum(pb.startup_cpg_member == 'Y')}")
print(f"- passed primary contact: {vc(pb.contact_status)}; backup named {sum(pb.backup_contact_name_as_found != '')}")
print(f"- top 60: HQ {vc(tb.hq_class)}")
print(f"- top 60: grade {vc(tb.nearest_retailer_grade)}; why-now {vc(tb.why_now_type)}; founder_review Y {sum(tb.founder_review == 'Y')}; Startup CPG Y {sum(tb.startup_cpg_member == 'Y')}")
print(f"- top 60 contacts: {vc(tb.contact_status)}; backup named {sum(tb.backup_contact_name_as_found != '')}; LinkedIn URL {sum(tb.contact_linkedin_url != '')}")
print(f"- top 60 score range {tb.score.astype(float).min()} to {tb.score.astype(float).max()}; passed median {pb.score.astype(float).median()}")
links = pd.read_csv(os.path.join(C.WORK, "brand_store_links.csv"), dtype=str, keep_default_na=False)
print(f"- store links {len(links)}: grade {vc(links.grade)}; within ten blocks {sum(links.within_ten_blocks == 'Y')}")
rc = os.path.join(C.WORK, "wfm_recheck_2026-10-24.csv")
if os.path.exists(rc):
    r = pd.read_csv(rc, dtype=str, keep_default_na=False)
    print(f"- WFM re-check 2026-10-24: {len(r)} store_selector links, found {sum(r.found_2026_10_24 == 'Y')}, not found {sum(r.found_2026_10_24 == 'N')}, failed {sum(r.found_2026_10_24 == 'unknown')}")
