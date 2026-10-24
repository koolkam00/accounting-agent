"""Every editable number in the scoring and estimate, in one place.

Change a value here and re-run `python3 clay-icp-tables/_build/build_all.py`.
"""

# ---------------------------------------------------------------- offices
# In-office rate on an average weekday (plan.md, Market reality check, Partnership for
# New York City, March 2025 survey): firms under 500 employees 67%; all Manhattan office
# workers 57%; firms over 5,000 46%. The plan gives no figure for 500 to 4,999, so the
# all-firm 57% is used there. Tuesday is the peak day (Kastle), so these understate Tuesday.
RATE_UNDER_500 = 0.67
RATE_500_TO_4999 = 0.57
RATE_5000_PLUS = 0.46

# Share of a company-wide headcount assumed to sit in the New York office when no
# New York count exists. Assumptions, not facts (stage1-notes.md, assumption A3).
SHARE_NYC_OFFICE_COUNT = (1.0, 1.0)     # the count is already the New York office
SHARE_HQ_NYC = (0.5, 1.0)               # company-wide count, HQ in New York
SHARE_HQ_ELSEWHERE = (0.05, 1.0)        # company-wide count, HQ elsewhere or unknown

# Space check (review round 1, R1-03): a Tuesday estimate can never exceed what the row's own leased square
# footage can seat. Office planning rules of thumb (assumption, stage1-notes A3b): 125 sf per person is a
# dense open plan, 150 a typical tech office, 250 a roomy one. The cap uses the largest square footage the
# sources mention for the company at this address (so a building size or a second tenant's lease can only
# loosen it, never tighten it).
SF_PER_PERSON_DENSE = 125     # onsite_high is never above leased sf / 125
SF_PER_PERSON_TYPICAL = 150   # the central estimate is never above leased sf / 150
SF_PER_PERSON_ROOMY = 250     # low end of a range built from space alone (HQ outside New York, one sf figure)

# Gates (prompt: hard floor 30, ceiling 250; 30 to 39 is the founder's call)
ONSITE_FLOOR = 30
ONSITE_TARGET_LOW = 40
ONSITE_CEILING = 250

# Score weights (points). Total 100.
W_ONSITE_FIT = 25          # x share of the estimated range inside 40 to 250 (ratio scale)
W_ONSITE_NYC_COUNT = 5     # bonus when the count is for the New York office itself
P_ONSITE_UNKNOWN = 7       # unknown headcount: scores lower than a likely fit
W_SIZE = 15                # company size under 500 (CONTRACTS headcount bands)
P_SIZE = {"le500": 15, "501-1000": 6, "1001-4999": 2, "5000+": 0, "unknown": 8}
P_PARENT_NAMED = -4        # a named controlling parent: the pantry decision may sit there
W_ATTEND = 15
P_ATTEND = {"in-office-5": 15, "hybrid-4": 12, "hybrid-3": 10, "hybrid-unspecified": 7,
            "hybrid-2-or-less": 5, "unknown": 6, "remote": -5}
P_TUESDAY_NAMED = 3        # the employer's policy text names Tuesday as an office day (cap W_ATTEND)
W_ADDRESS = 15
P_LEASE = {"occupied": 10, "occupancy-unconfirmed": 5, "signed-not-occupied": 2, "moving-out": 0,
           # coworking operator site status
           "open": 10, "open-unverified": 5, "unverified": 2, "possibly-closed": 0}
P_CONF = {"high": 5, "medium": 3, "low": 0}
W_TITLE = 10               # primary contact title: exact family 10, adjacent 5, none 0
P_TITLE = {"exact": 10, "adjacent": 5, "none": 0}
W_KNOWN = 15               # known_to_founder = Y

# ---------------------------------------------------------------- brands
# Score weights (points). Total 100.
B_BUY_PATH = {  # best graded store within ten blocks, else online
    ("store_selector", "inside"): 25, ("store_selector", "near"): 20,
    ("brand_claim", "inside"): 17, ("brand_claim", "near"): 13,
    ("online", None): 6, ("none", None): 0}
B_NY = {"nyc": 20, "nys": 13, "northeast": 8, "elsewhere": 3, "unknown": 4}   # "New York brands come first"
B_NY_UNVERIFIED_PENALTY = -3
B_WHY_NOW = {("press", "0-180"): 15, ("press", "181-365"): 8,
             ("listing", "0-180"): 8, ("listing", "181-365"): 4, ("none", None): 0}
B_REVENUE = {"500k-10m": 10, "unknown": 5, "under-500k": 2, "over-10m": 0}
B_FIT = {"shelf": {"Y": 4, "likely": 2, "unknown": 1},
         "single": {"Y": 3, "unknown": 1, "N": 0},
         "online": {"Y": 3, "unknown": 1, "N": 0}}
B_CONTACT = {"founder_full": 6, "founder_partial": 3, "marketing": 4,
             "marketing_snippet": 2}  # stage 3: a marketing lead seen only in a snippet earns half
B_STARTUP_CPG = 0          # public Startup CPG participation is a channel note, not a score
B_KNOWN = 10
# founder_review types (the most severe one applies; see stage1-notes.md)
B_REVIEW_PENALTY = {"owner": -25, "scale-reported": -35, "scale": -12, "dormant": -12, "not-emerging": -10, "perishable-risk": -8,
                    "under-floor": -5, "alcohol-adjacent": -5, "claim-functional": -4, "nutrient-claim": -4,
                    "format": -4, "format-unconfirmed": 0,
                    "other": -2}

WHY_NOW_WINDOW_DAYS = 365

# ---------------------------------------------------------------- stage 3: views and Clay
DAILY_VIEW_SIZE = 10        # rows per daily view (CONTRACTS 6.2); the founder sends about five per side a day
CLAY_FREE_ROW_LIMIT = 200   # Clay Free: "Run up to 200 rows per table" (clay.com/pricing, opened 2026-10-24)
CLAY_IMPORT_ROWS = 175      # passed rows imported per table, leaving 25 rows for referrals and new seeds
# Brands made by one parent company: one group, never two in flight (stage 2 contact notes:
# Expo West 2026 lists Moshi under Brooklyn Food & Beverage; a BevNET 2020 summary says it also makes
# Bruce Cost Ginger Ale, unverified). Grouping only restricts outreach, so an unverified link is enough.
BRAND_PARENT_GROUPS = {"AB-130": "Brooklyn Food & Beverage", "AB-131": "Brooklyn Food & Beverage"}
