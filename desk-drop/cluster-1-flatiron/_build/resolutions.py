"""Manual decisions made at assembly (2026-10-24), each with its evidence.

Keys are company_name exactly as written in _work/companies_S*.csv.
Nothing here invents a fact: every change cites a source opened on 2026-10-24
or a fact already in the slice notes.
"""

TODAY = "2026-10-24"
CUTOFF_24M = "2024-10-24"  # a source dated on or after this is "under 24 months old"

# ---------------------------------------------------------------- merges
# Same company found twice, or the same pantry under two names: one row survives.
MERGES = [
    {
        "keep": "SEIU 32BJ",
        "drop": ["Building Service 32BJ Benefit Funds"],
        "company_name": "SEIU 32BJ and 32BJ Benefit Funds",
        "website": "https://www.seiu32bj.org",
        "second_source_url": "https://32bjfunds.org/contact-us/",
        "second_source_date": "2026-10-23",
        "confidence": "high",
        "note": "Merged at assembly: S1 found the union HQ and S2 found the related Benefit Funds at the same address and tax lot (25 W 18th St = 620 Avenue of the Americas lot, BBL 1008207505). Treated as one pantry contact until the walk or a call shows two separate offices. Sources: union contact page (seiu32bj.org, opened 2026-10-23), funds contact page (32bjfunds.org, opened 2026-10-23), CO 2024-09 (moved into 245,000 sf in 2010; ground-floor expansion). Staff count not published; the union's members are building workers, not office staff.",
    },
    {
        "keep": "Grammarly",
        "drop": ["Superhuman (formerly Grammarly)"],
        "company_name": "Superhuman (formerly Grammarly)",
        "headcount_band": "over-500",
        "headcount_scope": "whole-company",
        "headcount_source_url": "https://www.builtinnyc.com/company/superhuman-1/offices",
        "headcount_source_date": "2026-10-23",
        "confidence": "medium",
        "note": "Merged at assembly: S3 (Grammarly, 360 PAS) and S4 (Superhuman, 450 PAS) are one company. CO 2025-09-02 reports a 23,038 sf full-floor lease at 360 Park Ave S (its NYC address then was 29 W 30th St) and CO 2026-01-22 lists Grammarly as a current 360 PAS tenant, so 360 PAS is used. Built In's 450 Park Ave S address is the building of WeWork 450 Park Ave S and looks like a coworking membership or a stale entry. Built In: 1,500 total employees, so over 500 either way: near-miss.",
    },
    {
        "keep": "The Hudson Companies",
        "drop": ["Broadway Builders"],
        "company_name": "The Hudson Companies and Broadway Builders",
        "note": "Merged at assembly: affiliates sharing one full-floor 12th-floor tenancy at 902 Broadway (CO 2026-03-24, CO 2026-06-09), so one pantry. Both websites still list 826 Broadway, 11th floor (opened 2026-10-23), so the move date is unconfirmed.",
    },
]

# ---------------------------------------------------------------- field overrides (conflicts)
OVERRIDES = {
    "Kaltura": {
        "note_add": "Conflict resolved at assembly: S2 saw an SEC business address of 250 Park Ave S, 10th floor. CO 2022-01 says Kaltura took the entire 3rd floor of 860 Broadway 'moving from 250 Park Ave S', and CO 2026-08-07 names it a current 860 Broadway tenant, so the SEC address is a stale registrant address. Kept at 860 Broadway. Over 500 either way.",
    },
    "Adyen": {
        "lease_status": "moving-out", "move_in_date": "unknown",
        "note_add": "Conflict resolved at assembly: current office is 71 Fifth (own offices page, opened 2026-10-23). It signed 90,000 sf across 111 and 115 Fifth (CO 2026-04-07), move date not stated. Both addresses are inside the boundary; over 500 either way.",
    },
    "WW International (WeightWatchers)": {
        "note_add": "Conflict resolved at assembly: the 10-Q for the quarter to 2026-06-30 gives 18 W 18th St, 7th floor; it is newer than the Built In entry (675 Sixth Ave), so 18 W 18th is used. WeWork 18 West 18th Street occupies five unnamed floors of this 12-storey building (wework.com building page, opened 2026-10-24), so whether the 7th floor is a WeWork suite is unknown (coworking_check = floor-unknown). Over 500: near-miss.",
    },
    "Instacart": {
        "lease_status": "moving-out", "move_in_date": "unknown",
        "note_add": "Conflict carried: CO 2026-07-20 reports a new 26,134 sf lease at 111 W 33rd St; whether it leaves 50 W 23rd is not stated. Kept low. Over 500: near-miss.",
    },
    "K Health": {
        "floor": "9",
        "second_source_url": "https://khealth.com/terms-of-use/",
        "second_source_date": TODAY,
        "confidence": "high",
        "lease_status": "occupied",
        "note_add": "Conflict resolved at assembly: K Health's own terms of use (opened 2026-10-24) give 'Company's Legal Department, 387 Park Ave South, 9th Floor, NY, NY 10016', which agrees with the Connect CRE renewal at 387 PAS (late 2025). Built In's 298 Fifth Ave, 7th floor is stale. Upgraded to high.",
    },
    "Ziff Davis": {
        "second_source_url": "https://www.ziffdavis.com/",
        "second_source_date": TODAY,
        "confidence": "high",
        "lease_status": "occupied",
        "note_add": "Conflict resolved at assembly: ziffdavis.com's own structured data (opened 2026-10-24) gives streetAddress '360 Park Avenue South', 10010, agreeing with CO 2025-05-20. Built In's 114 Fifth Ave is stale. S3 also found theSkimm's legal pages pointing to Ziff Davis at 360 PAS, 17th floor. Over 500: near-miss.",
    },
    "U.S. News & World Report": {
        "lease_status": "moving-out", "move_in_date": "unknown",
        "note_add": "Conflict carried: CO 2026-04-28 reports offices moving from 129 W 29th St to 31 Penn Plaza; CO 2026-10-19 lists it at 120 Fifth. Not resolvable from public sources; over 500 either way.",
    },
    "Hex Technologies": {
        "note_add": "Conflict carried: lease at 250 PAS floor 7 (CO 2026-01-09); Built In still lists 44 W 18th St. Both addresses are inside the boundary. Check the 250 PAS lobby directory on the walk.",
    },
    "Pilot Fiber": {
        "note_add": "Coworking check at assembly: Pilot Fiber's legal page (re-opened 2026-10-24) gives '1115 Broadway Floor 12'. Select Office Suites' own page (opened 2026-10-24) gives its Flatiron centre as '1115 Broadway (aka 16 Madison Square West), 9th, 10th, 11th, & 12th Floors'. Same floor as a serviced-office operator, so flagged in_coworking = Y and excluded until the founder confirms Pilot Fiber holds its own lease there.",
    },
    "Deerfield Management": {
        "note_add": "Coworking check at assembly: Cure's residents page (wewillcure.com/community/residents, opened 2026-10-24) lists 'Deerfield Management Company' among Cure residents. Cure is operated by Cure Experience Services, LLC (site footer). Deerfield owns the building (Wikipedia). Flagged in_coworking = Y: approach Cure as the one office (coworking tab) rather than Deerfield separately. Founder to confirm whether Deerfield runs its own pantry.",
    },
    "Augury": {
        "candidate_status": "excluded-not-office",
        "note_add": "Excluded at assembly: Built In marks the company 'Remote Workplace' and the '#169' suite looks like a mailbox or shared suite, so there is probably no staffed office to host a pantry drop.",
    },
    "Mercury": {"note_add": "Built In's 150 total employees looks low against other reporting (S1 flag); band kept as sourced."},
    "Robin Hood": {"note_add": "Built In's 659 for this nonprofit may include non-staff counts (S1 flag)."},
}

# ---------------------------------------------------------------- coworking rows to add (verified 2026-10-24)
NEW_COWORKING = [
    {
        "temp_id": "W-30",
        "operator": "Cure (Cure Experience Services, LLC; Deerfield-affiliated)",
        "location_name": "Cure, 345 Park Avenue South",
        "street_address": "345 Park Avenue South, New York, NY 10010",
        "geocode": "345 Park Avenue South",
        "floors": "unknown",
        "pantry_control": "operator",
        "pantry_source_url": "https://wewillcure.com/community/residents",
        "pantry_note": "Operator page (opened 2026-10-24): 'Members can access hotdesking, private conference rooms, event space, a cafe, and a gym'. S3 also quoted a 'fully stocked pantry' from wewillcure.com (opened 2026-10-23); that phrase was not on the pages re-opened on 2026-10-24, so pantry_control rests on the operator-run cafe and residency services.",
        "source_url": "https://wewillcure.com/community/residents",
        "source_date": "2026-10-24",
        "second_source_url": "https://en.wikipedia.org/wiki/Deerfield_Management",
        "confidence": "high",
        "status": "open",
        "exclusive_food_contract_signal": "operator-run cafe (NaCl Cafe per S3); outside snack placement likely needs operator approval",
        "notes": "Healthcare innovation hub with a 'Collaboration Residency', hot desks, labs and offices. Footer: '(c) 2026 Cure Experience Services, LLC'. Residents listed include Deerfield Management Company, Lexeo Therapeutics and Insilico Medicine (flagged in_coworking = Y) and Advancium, ANVIA, Apertura, Ascertain, Buckle Therapeutics, CobiCure, Concerto Care, Deerfield Catalyst, Helaina, Hop Labs, Panacea Capital, Plum Alley Ventures, Protara, Sparian, Wandercraft (not recorded as rows). Address: the site's Facebook link 'CureAt345ParkAveSouth' and S3's building research; Wikipedia gives Deerfield's HQ and building purchase at 345 PAS. A healthcare audience may have food-policy limits near labs: ask.",
    },
    {
        "temp_id": "W-31",
        "operator": "WeWork",
        "location_name": "WeWork 27 E 28th St (79 Madison Ave building)",
        "street_address": "27 East 28th Street, New York, NY 10016",
        "geocode": "27 East 28th Street",
        "floors": "eight floors of 17 (unnamed)",
        "pantry_control": "unknown",
        "pantry_source_url": "https://liquidspace.com/us/ny/new-york/wework-27-e-28th-st",
        "pantry_note": "LiquidSpace lists 'Kitchen', 'Coffee/Tea' and 'Filtered Water' (opened 2026-10-24). Not the operator's own page.",
        "source_url": "https://liquidspace.com/us/ny/new-york/wework-27-e-28th-st",
        "source_date": "2026-10-24",
        "second_source_url": "https://www.builtinnyc.com/company/monte-carlo/offices",
        "confidence": "low",
        "status": "possibly-closed",
        "exclusive_food_contract_signal": "none found",
        "notes": "CONFLICT: LiquidSpace says 'Confirmed Open' and Monte Carlo's Built In page lists a hub at 27 E 28th St, Suite 1656, but the location is NOT on WeWork's NYC index (wework.com/l/coworking-space/new-york-city--NY, opened 2026-10-24) and the wework.com building page redirects to a generic listing. The building was marketed for a condo conversion (CO 2025-03-04). Treat as possibly closed; check on the walk.",
    },
    {
        "temp_id": "W-32",
        "operator": "Hub Seventeen",
        "location_name": "Hub Seventeen, 114 Fifth Avenue",
        "street_address": "114 Fifth Avenue, New York, NY 10011",
        "geocode": "114 Fifth Avenue",
        "floors": "unknown",
        "pantry_control": "unknown",
        "pantry_source_url": "",
        "pantry_note": "No operator page found: hubseventeen.com belongs to an unrelated organisation in Nigeria (opened 2026-10-24).",
        "source_url": "https://commercialobserver.com/2025/02/capital-one-expansion-114-fifth-avenue/",
        "source_date": "2025-02-11",
        "second_source_url": "",
        "confidence": "medium",
        "status": "unverified",
        "exclusive_food_contract_signal": "none found",
        "notes": "CO 2025-02-11 (re-opened 2026-10-24): 'Other tenants of the 350,000-square-foot office building between West 16th and West 17th streets include marketing consultant Acxiom and coworking space Hub Seventeen.' No floor, size, pantry or website found. Founder to confirm on the walk.",
    },
]

# Corrections to existing coworking rows
COWORKING_OVERRIDES = {
    "W-14": {
        "notes_add": "Address conflict carried: Williams Equities' building page (S3, opened 2026-10-23) places NeueHouse at 104 East 25th Street; the NYREJ acquisition item and the operator page use 110 East 25th Street. Both numbers are on the same tax lot (BBL 1008800084), so the pin holds.",
    },
    "W-05": {"status": "open-unverified",
             "notes_add": "Not on WeWork's NYC index as opened 2026-10-24, but a wework.com listing page shows a '4th Floor' office at 245 5th Ave, so it is probably open; founder to confirm."},
    "W-18": {"notes_add": "S2 noted IWG's Spaces signed the whole office portion (floors 2-9, CO 2018); the places researcher found Le Parc operating on floor 2 now. Spaces' status here is unverified."},
    "W-01": {"notes_add": "WeWork occupies five unnamed floors of the 12-storey building (operator page, opened 2026-10-24). WW International's 10-Q address is the 7th floor here; overlap unknown."},
    "W-29": {"notes_add": "Zero Irving tenants Alpine Investors (12), GameChanger (17) and Senator (20) hold their own leases (CO), so they are not Civic Hall members."},
    "W-08": {"notes_add": "Industrious holds three floors (51,765 sf, to 2035, per the 215 PAS rent roll cited by S1). The 215 PAS company rows are direct leases on that rent roll, so they are not Industrious members."},
}

# ---------------------------------------------------------------- lease status
# occupied | occupancy-unconfirmed | signed-not-occupied | moving-out
# move_in_date: YYYY-MM, a planned season, or 'unknown' (only for signed-not-occupied)
SNO = "signed-not-occupied"
LEASE = {
    # S1
    "Rockwell Group": "occupied", "Profound": (SNO, "unknown"), "Selldorf Architects": "occupied",
    "Valon": "occupied", "Kaltura": "occupied", "Adyen": ("moving-out", "unknown"),
    "Nayya": "occupied", "Cognitiv": "occupied", "Stellar Health": "occupied", "Global Strategy Group": "occupied",
    "Baseten": "occupied", "Rakuten USA": "occupied", "Charlie Health": "occupied", "Matador Content": "occupied",
    "Stone Source": "occupied", "Lepercq de Neuflize & Co.": "occupied", "Nourish": "occupied",
    "Eagle AI": (SNO, "unknown"), "Delos Capital": "occupied", "Walleye Financial": "occupied",
    "Chime": "occupied", "eBay": (SNO, "unknown"), "Microsoft (AdTech hub)": "occupied",
    "Robin Hood": (SNO, "unknown"), "Gresham Investment Management": "occupied",
    "Biohub (Chan Zuckerberg Biohub)": (SNO, "unknown"), "Fundraise Up": (SNO, "unknown"),
    "Thinking Machines Lab": (SNO, "unknown"), "Capgemini America": ("moving-out", "unknown"), "Hulu": "occupied",
    "LUMA Partners": "occupied", "Capital One": "occupied", "Acxiom": "occupied",
    "Galvanize Climate Solutions": (SNO, "unknown"), "Prophet": "occupied", "monday.com": "occupied",
    "Battery Ventures": "occupied", "Casa Komos Brand Group": "occupied", "Union Square Hospitality Group": "occupied",
    "Con Edison": "occupied", "SEIU 32BJ": "occupied", "Palantir Technologies": "occupied",
    "Alpine Investors": "occupied", "GameChanger": "occupied", "Senator Investment Group": "occupied",
    "U.S. News & World Report": ("moving-out", "unknown"),
    # S2
    "Hex Technologies": (SNO, "unknown"), "Pentagram": "occupied", "Wilson Daniels": (SNO, "unknown"),
    "Extend AI": "occupied", "Actively AI": "occupied", "Vivaldi": "occupied", "Warp": "occupied",
    "The Hudson Companies": (SNO, "unknown"), "Synthesia": (SNO, "unknown"), "Candid Health": (SNO, "unknown"),
    "Aterian": "occupied", "LoveShackFancy": "occupied", "Farmacy Beauty": "occupied", "Fresh (LVMH)": "occupied",
    "Options Group": (SNO, "unknown"), "Argentic Investment Management": (SNO, "unknown"), "ISAIA": "occupied",
    "Varley": "occupied", "Instant": "occupied", "Cobalt Service Partners": "occupied", "PlayPlay": "occupied",
    "Stash": (SNO, "unknown"), "CompStak": "occupied", "Morning Brew": "occupied", "ZGF Architects": "occupied",
    "Phipps Houses": "occupied", "The Information": "occupied", "Global Trading Systems (GTS)": "occupied",
    "Ro": "occupied", "Reaktor": "occupied", "Airbnb": "occupied", "Netflix": "occupied", "Fenwick & West": "occupied",
    "William Grant & Sons": "occupied", "Mastercard": "occupied", "Infor": "occupied", "dsm-firmenich": "occupied",
    "Tory Burch": "occupied", "Cole Haan": "occupied", "Warner Bros. Discovery": "occupied",
    "The Vita Coco Company": "occupied", "WW International (WeightWatchers)": "occupied", "Bombas": "occupied",
    "Dashlane": "occupied", "Empathy": "occupied", "Perkins Eastman": "occupied", "Heard City": "occupied",
    "e.l.f. Beauty": "occupied", "IMG Worldwide (WME Group)": "occupied", "Daily Harvest": "occupied",
    "Retool": "occupied", "Airtable": "occupied", "Similarweb": "occupied",
    # S3
    "Inspiren": "occupied", "Foursquare": "occupied", "BMF (We Are BMF)": "occupied", "Chalk": (SNO, "unknown"),
    "BuzzFeed": "occupied", "Instacart": ("moving-out", "unknown"), "Trustpilot": "occupied", "Huge": (SNO, "unknown"),
    "TileBar": "occupied", "Tiffany & Co.": "occupied", "Grey Group": "occupied", "DoorDash": "occupied",
    "Goodwin Procter": (SNO, "2026 late (planned)"), "FanDuel": "occupied", "PitchBook": "occupied",
    "Wellcom Worldwide": "occupied", "Pilot Fiber": "occupied", "Green Mountain Energy": "occupied",
    "Pinterest": (SNO, "unknown"), "Sony Music Entertainment": "occupied", "UBS": "occupied",
    "Suntory Global Spirits (Jim Beam Brands)": "occupied", "WME": "occupied", "Clay": (SNO, "unknown"),
    "Legora": (SNO, "unknown"), "IBM": "occupied", "Franklin Templeton": "occupied", "Coinbase": "occupied",
    "Flutter Entertainment": "occupied", "Palo Alto Networks": "occupied", "Ramp": "occupied", "Kodansha USA": "occupied",
    "Betches Media": (SNO, "unknown"), "Rogo": "occupied", "Hunter Point Capital": (SNO, "unknown"),
    "Trexquant": (SNO, "unknown"), "1stDibs": "occupied", "LaForce": "occupied", "M&C Saatchi Group (New York)": "occupied",
    "TripleLift": "occupied", "Deerfield Management": "occupied", "Lexeo Therapeutics": "occupied",
    "Insilico Medicine": "occupied", "Orbital": (SNO, "unknown"), "Sapien AI": (SNO, "unknown"),
    "MediaCo Holding (HOT 97, WBLS)": "occupied", "RepRally": "occupied", "United Talent Agency (UTA)": ("moving-out", "2027 summer (planned move to the Empire State Building)"),
    "At-Bay": "occupied", "BrainPOP": "occupied", "TKO Group Holdings": "occupied", "Madison Square Park Conservancy": "occupied",
    "Normal Computing": (SNO, "2026-11"),
    # S4
    "Primary Venture Partners": "occupied", "Sigma Computing": (SNO, "unknown"), "Hanover Park": (SNO, "unknown"),
    "PMG Worldwide": "occupied", "Criteo": "occupied", "K Health": "occupied", "Activate Consulting": "occupied",
    "Order.co": (SNO, "unknown"), "Warren Equity Partners": "occupied", "Suvretta Capital Management": (SNO, "unknown"),
    "Butterfly Network": "occupied", "Holocene Advisors": "occupied", "Jump Trading": "occupied",
    "Vestal Point Capital": (SNO, "unknown"), "Mega 97.9 (radio station)": "occupied",
    "BrightTower": (SNO, "2026-Q2 (planned, not confirmed)"), "SharkNinja": "occupied", "MCM Worldwide": (SNO, "unknown"),
    "FCA (architecture and design)": "occupied", "MiQ Digital USA": "occupied",
    "The Corcoran Group": (SNO, "2026 summer (planned)"), "Optiver": "occupied", "Ziff Davis": "occupied",
    "ICONIQ Capital": "occupied", "Sierra": (SNO, "unknown"), "Spring Health": "occupied",
    "Grimshaw (New York studio)": "occupied", "Collected Strategies": "occupied", "Tenex Labs": (SNO, "unknown"),
    "GovWell Technologies": (SNO, "unknown"), "Full Picture": "occupied", "Arca Financial Group": (SNO, "unknown"),
    "Simplebet": "occupied", "Pumpkin Pet Insurance": "occupied", "Mediaplus Group (North America)": (SNO, "unknown"),
    "Signal AI": "occupied", "Innovant": "occupied", "accessiBe": "occupied", "Primary Wave": "occupied",
    "Christian Louboutin": "occupied", "Polar Asset Management Partners": "occupied",
    "TenBerke (formerly Deborah Berke Partners)": "occupied", "Mphasis": "occupied",
    "Zip (digital banking)": (SNO, "2027-04"), "Lee & Low Books": "occupied",
    "Institute for Integrative Nutrition": "occupied", "American Eagle Outfitters (NYC headquarters offices)": "occupied",
    "Prosek Partners": "occupied", "Carbyne": "occupied", "OTTO Brand Lab": "occupied", "Seedtag": "occupied",
    "Ford Models": "occupied", "The Ancillary Project": "occupied", "Monte Carlo (Monte Carlo Data)": "occupied",
    "Community Healthcare Network (administrative offices)": "occupied", "EnVogue International": "occupied",
    "SL Home Fashions": "occupied", "Runwise": "occupied", "The Knot Worldwide": (SNO, "unknown"),
    "Octus (formerly Reorg)": (SNO, "unknown"), "Parloa": "occupied", "Grammarly": "occupancy-unconfirmed",
}

# ---------------------------------------------------------------- reasons for an unknown band
# Default reason when nothing specific applies:
UNKNOWN_BAND_DEFAULT = "No opened source gives a count: no Built In profile with a total, the company site publishes none, and LinkedIn was off-limits. Founder to confirm at intake."
UNKNOWN_BAND_REASON = {
    "Profound": "Fortune 2026-02-24 says 'fewer than 120 employees', which spans two bands (40-75 and 76-150).",
    "Perplexity": "Built In shows 41, which conflicts with reported growth; band left unknown rather than guessed.",
    "Phia": "A Built In 'Phia' profile (77 employees, Fairfax VA) could not be tied to this company.",
    "Walleye Financial": "May or may not be Walleye Capital (Built In 181); not confirmed, so no count used.",
    "Sapien AI": "The Built In 'sapien' profile is a different 5-person Berkeley firm.",
    "Rogo": "The Built In 'rogo' profile is a different company in Indiana; Empire State Development's 422 jobs is a hiring plan, not a headcount.",
    "Zip (digital banking)": "The Built In 'zip' profile is a different company (ZipHQ).",
    "Flexible Finance (Flex)": "The Built In 'flex' profile is a different LA company.",
    "SEIU 32BJ and 32BJ Benefit Funds": "Staff count not published; the union's large membership is building workers, not office staff. CO reports 245,000 sf here, a large footprint.",
    "The Hudson Companies and Broadway Builders": "Neither firm publishes a count.",
    "Grammarly": "Merged; band taken from Built In Superhuman profile.",
}

# ---------------------------------------------------------------- headcount bands sourced at assembly (critique round 2)
# Wikipedia infoboxes opened with WebFetch on 2026-10-24. Whole-company figures; the NYC office may be smaller.
WIKI = "https://en.wikipedia.org/wiki/"
HEADCOUNT_UPDATES = {
    "Palantir Technologies": (WIKI + "Palantir_Technologies", "2025", "Wikipedia infobox: 4,429 employees (2025)."),
    "Kohler Co. (NYC office)": (WIKI + "Kohler_Co.", "2019", "Wikipedia infobox: 40,000 employees (2019)."),
    "Lockton Re": (WIKI + "Lockton_Companies", "2026-10-24", "Wikipedia infobox for Lockton Companies, the parent: '13,100+' employees (no year given)."),
    "Jump Trading": (WIKI + "Jump_Trading", "2026-10-24", "Wikipedia infobox: '2000+' employees (no year given)."),
    "IMG Worldwide (WME Group)": (WIKI + "IMG_(company)", "2026-10-24", "Wikipedia infobox: '3,000+' employees (no year given)."),
    "ZGF Architects": (WIKI + "ZGF_Architects", "2021-10", "Wikipedia infobox: 750 employees (footnote cites an October 2021 article)."),
    "Grimshaw (New York studio)": (WIKI + "Grimshaw_Architects", "2026-10-24", "Wikipedia body text: 'employing over 600 staff' (no infobox count)."),
}
UNKNOWN_BAND_REASON["Perplexity"] = ("Built In shows 41 and Wikipedia's infobox shows 52 (2024), both of which conflict with a 22,000 sf NYC office leased in 2025-26; "
                                     "band left unknown rather than set from stale counts.")

# ---------------------------------------------------------------- public map exclusions (brand-founder critique)
PUBLIC_EXCLUDE = {
    "New Foods of India": "Niche South Asian grocery: useful only for spice-led or South Asian brands, so private map only.",
    "Kalustyan's": "Niche spice and international specialty store, so private map only.",
    "Sunac (765 Sixth Ave)": "Neighbourhood deli-market format with no natural set confirmed, so private map only.",
    "Sunac (4 West 18th St)": "Neighbourhood deli-market format with no natural set confirmed, so private map only.",
}


# ================================================================ review round 1 (2026-10-24)
# Fixes for _review/round-1.md. Every value below cites a source opened on 2026-10-24 or a
# fact already in the row's notes.

# R1-05: undated third-party profiles are undated, not fresh. A "high" needs a dated source on or
# after CUTOFF_24M, or the company's or operator's own live page, plus one independent confirmation.
UNDATED_PROFILE_DOMAINS = {"builtinnyc.com", "builtin.com", "deskpass.com", "api.deskpass.com", "liquidspace.com"}

BI = "https://www.builtinnyc.com/company/"
REVIEW1_OVERRIDES = {
    # kept high: the company's own live page (opened 2026-10-24) confirms the address; Built In is the independent second source
    "CompStak": {
        "address_source_url": "https://compstak.com/about", "address_source_date": TODAY, "address_source_type": "company-site",
        "second_source_url": BI + "compstak/offices", "second_source_date": "2026-10-23",
        "note_add": "Review round 1: CompStak's own About page (opened 2026-10-24) prints '675 6th Ave, Floor 4, New York, NY 10010', so the row stays high on its own page plus Built In. The CO 2022-12-20 lease is the older third source.",
    },
    "Empathy": {
        "address_source_url": "https://www.empathy.com/", "address_source_date": TODAY, "address_source_type": "company-site",
        "second_source_url": BI + "empathy/offices", "second_source_date": "2026-10-23",
        "note_add": "Review round 1: Empathy's own homepage structured data (opened 2026-10-24) gives streetAddress '56 W 22nd Street', 10010, so the row stays high on its own page plus Built In. The CO 2024-03-06 lease is the older third source.",
    },
    "Signal AI": {
        "address_source_url": "https://www.signal-ai.com/", "address_source_date": TODAY, "address_source_type": "company-site",
        "second_source_url": BI + "signal-ai/offices", "second_source_date": "2026-10-23",
        "note_add": "Review round 1: Signal AI's own site footer (opened 2026-10-24) lists 'United States 440 Park Avenue South, 14th floor, New York NY 10016' beside its London office, so the row stays high on its own page plus Built In.",
    },
    "Simplebet": {
        "address_source_url": "https://commercialobserver.com/2025/05/empire-capital-buys-373-381-park-avenue-south/",
        "address_source_date": "2025-05-22", "address_source_type": "leasing-press",
        "second_source_url": BI + "simplebet/offices", "second_source_date": "2026-10-23",
        "note_add": "Review round 1: CO 2025-05-22 (opened 2026-10-24): 'Current tenants at 373 Park Avenue South include sports betting firm Simplebet', a dated source under 24 months, so the row stays high with Built In as the independent second source. The company site failed TLS from this environment.",
    },
    # lowered: no dated source under 24 months and no own page reachable
    "Morning Brew": {"confidence": "medium",
                     "note_add": "Review round 1: lowered from high to medium. Built In is undated and the only other source is the CO 2022-02-24 lease (older than 24 months); morningbrew.com's contact and legal pages print no address (opened 2026-10-24)."},
    "Bombas": {"confidence": "medium",
               "note_add": "Review round 1: lowered from high to medium. Built In is undated and the CO lease is 2019-04-10; bombas.com returned HTTP 429 again on 2026-10-24."},
    "accessiBe": {"confidence": "medium",
                  "note_add": "Review round 1: lowered from high to medium. Built In is undated and the CO lease is 2022-07-07; accessibe.com's terms and privacy pages print no street address (opened 2026-10-24)."},
    "Pumpkin Pet Insurance": {
        "confidence": "low", "lease_status": "occupancy-unconfirmed",
        "note_add": "Review round 1: CONFLICT, lowered from high to low. Pumpkin's own homepage (opened 2026-10-24) says the agency is 'Domiciled in New York with offices at 666 3rd Avenue, Floor 23, New York, NY 10017' and gives that as its mailing address, which is outside the boundary. Against it: CO 2026-06-08 (https://commercialobserver.com/2026/06/mediaplus-group-lease-432-park-avenue-south/) lists Pumpkin among 432 Park Ave S tenants, citing its January 2023 lease, and Built In lists 432 PAS. Check the 432 PAS lobby directory on the walk before any outreach.",
    },
    # R1-06: a source counts the NYC office; R1-20: current office
    "Normal Computing": {
        "headcount_band": "under-40", "headcount_scope": "nyc-office",
        "headcount_source_url": "https://commercialobserver.com/2026/09/normal-computing-inspiren-leases-61-west-23rd-street/",
        "headcount_source_date": "2026-09-21",
        "note_add": "Review round 1: band changed from 40-75 (Built In's whole-company 51) to under-40, scope nyc-office, because the address source itself counts the NYC office: about 30 employees at the new HQ (CO 2026-09-21). The brief's hard floor is 30 and 30 to 39 is the founder's call, so the row stays a candidate for the founder to decide.",
    },
    "Synthesia": {
        "note_add": "Review round 1 correction: the current office at 245 Fifth Ave is INSIDE the boundary (not 'outside slice'). CO 2025-08-14 (https://commercialobserver.com/2025/08/synthesia-lease-moinian-245-fifth-avenue/, opened 2026-10-24): a five-year direct lease of 13,600 sf at 245 Fifth Ave, expanding from 6,490 sf on the 16th floor taken in April 2023 when it left 111 E 14th St; CO 2026-10-08 says it will relocate from 245 Fifth to 675 Sixth Ave, date unclear. So Synthesia sits at 245 Fifth Ave today, until the move date. Built In's 111 E 14th St is stale (pre-2023).",
    },
}
FOUNDER_CALL_30_39 = {"Normal Computing"}  # under-40 rows kept as candidates: a source puts the NYC office at about 30

# R1-09, R1-11: notes rewritten to state sources only (no size guesses) and to keep the business name out of the data
NOTE_EDITS = {
    "Lepercq de Neuflize & Co.": [("Headcount not found; may be under 40.", "Headcount not sourced (no Built In total, no company figure); founder to confirm at intake.")],
    "Union Square Hospitality Group": [("Corporate headcount not found; total company including restaurants is likely large, founder to confirm before treating it as a pantry office.",
                                        "Corporate office headcount not sourced; any company-wide count would include restaurant staff, so it would not describe this office. Founder to confirm at intake before treating it as a pantry office.")],
    "Gresham Investment Management": [("Headcount unknown; may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Battery Ventures": [("NYC headcount unknown and may be under 40.", "NYC headcount not sourced; founder to confirm at intake.")],
    "Delos Capital": [("Headcount unknown; may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Roboflow": [("the NYC office alone may be under 40.", "the whole company is 44 across two offices, so the NYC office is under 44 by arithmetic; its own count is not sourced.")],
    "Cobalt Service Partners": [("Headcount not sourced; may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Instant": [("so the NYC team is likely smaller.", "so the NYC team is at most 40 by arithmetic; its own count is not sourced.")],
    "Vitesse PSP": [("NYC office size suggests a small team, headcount not sourced.", "NYC headcount not sourced.")],
    "The Information": [("NYC bureau may be under 40 people (not sourced).", "NYC bureau headcount not sourced.")],
    "Heard City": [("Headcount not sourced; may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Sussex Publishers (Psychology Today)": [("Small space; headcount not sourced and may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Madison Square Park Conservancy": [("Headcount not stated; may be under 40, founder to confirm.", "Headcount not sourced; founder to confirm at intake.")],
    "OTTO Brand Lab": [("Headcount not found; office size suggests it may be under 40, founder to confirm.", "Headcount not sourced (no Built In total, no company figure); founder to confirm at intake.")],
    "Sierra": [("162 total employees, likely understated.", "162 total employees; the Built In count is undated."),
               ("A 94,000 SF space may not be fully occupied yet.", "Occupancy of the 94,000 SF space is not confirmed.")],
    "Eton (US office and showroom)": [("may be under 40 people in NYC.", "NYC headcount not sourced.")],
    "Christian Louboutin": [("headcount unknown; likely over 500 globally, not sourced.", "headcount not sourced.")],
    "Biologique Recherche (US)": [("size suggests under 40 onsite, founder to confirm.", "headcount not sourced; founder to confirm at intake.")],
    "Davies Group": [("Company-wide headcount not sourced (likely large).", "Company-wide headcount not sourced.")],
    "IMG Worldwide (WME Group)": [("likely large but headcount not sourced.", "the slice found no count (the Wikipedia figure added at assembly is below).")],
    "The Ancillary Project": [("Headcount not found; may be under 40.", "Headcount not sourced; founder to confirm at intake.")],
    "Casa Komos Brand Group": [("never as a Desk Drop brand.", "never as a brand on this programme (alcohol is excluded).")],
    "Daily Harvest": [("(frozen, so not a Desk Drop product)", "(frozen, so not an eligible product: refrigerated and frozen goods are excluded)")],
    "Suntory Global Spirits (Jim Beam Brands)": [("the NYC office itself may be in Desk Drop's range", "the NYC office alone may fit the 40-250 band")],
    "RepRally": [("Also relevant to Desk Drop's brand side", "Also relevant to the programme's brand side")],
}
UNKNOWN_BAND_REASON["SEIU 32BJ and 32BJ Benefit Funds"] = ("Staff count not published; the union's membership is building workers, not office staff. "
                                                           "CO reports 245,000 sf here.")
# Phrases that must never appear in a note (build.py fails if one does)
BANNED_NOTE_PATTERNS = [r"suggests? (?:it )?(?:may be )?(?:under|over)", r"may be under", r"likely over", r"likely understated",
                        r"likely large", r"likely smaller", r"size suggests", r"Desk Drop"]

SEC_NOTE = ("SEC EDGAR source (sec.gov): this agent will not re-open it, because EDGAR serves only requests that carry a "
            "contact email and the project rule forbids sending one; the founder may open it in a browser.")

# R1-10: coworking source dates are publication dates; the independent source moves from notes into second_source_url
DESKPASS_NYC = "https://www.deskpass.com/us-en/ny/new-york-city"
COWORKING_REVIEW1 = {
    "W-07": {"second_source_url": DESKPASS_NYC},
    "W-08": {"second_source_url": DESKPASS_NYC},
    "W-15": {"source_date": "2025-06-19", "second_source_url": "https://commercialobserver.com/2024/11/the-malin-lease-895-broadway"},
    "W-06": {"second_source_url": "https://commercialobserver.com/2026/03/industrious-leases-110-east-42nd-street/"},
    "W-12": {"second_source_url": "https://www.connectcre.com/stories/industrious-commits-to-full-floor-space-in-flatiron-district/"},
    "W-18": {"source_date": "2024-06-26", "second_source_url": DESKPASS_NYC, "confidence": "low", "status": "unverified",
             "notes_add": "Review round 1: lowered from high to low. The Flatiron NoMad Partnership profile is dated 2024-06-26 (older than 24 months) and the Deskpass index line is an undated listing whose detail page returned 'space not found'; IWG's Spaces held a 2018 lease for the building. Walk it before treating it as open."},
    "W-14": {"source_date": "2026-03-10", "second_source_url": "https://www.neuehouse.com/private-events/madison-square/"},
    "W-17": {"second_source_url": "https://liquidspace.com/US/NY/new-york/select-office-suites-flatiron"},
    "W-09": {"second_source_url": "https://commercialobserver.com/2026/03/industrious-leases-110-east-42nd-street/",
             "notes_add": "CO 2026-03-19 URL confirmed on 2026-10-24: https://commercialobserver.com/2026/03/industrious-leases-110-east-42nd-street/ ('At J.P. Morgan Investment Management's 776 Avenue of the Americas, Industrious plans to grow by 24,000 square feet')."},
    "W-13": {"second_source_url": "https://www.deskpass.com/us-en/ny/new-york-city/coworking-space/nomad"},
    "W-11": {"second_source_url": "https://commercialobserver.com/2026/02/industrious-lease-386-park-avenue-south/"},
    "W-16": {"source_date": "2024-11-18", "second_source_url": "https://api.deskpass.com/api/spaces/the-malin-nomad"},
    "W-21": {"second_source_url": "https://api.deskpass.com/api/spaces/luminary"},
    "W-22": {"second_source_url": "https://api.deskpass.com/api/spaces/sage-workspace"},
    "W-23": {"second_source_url": "https://api.deskpass.com/api/spaces/nomadworks"},
    "W-20": {"source_date": "2025-12-04", "second_source_url": "https://residentcompanyclub.com/"},
    "W-10": {"second_source_url": DESKPASS_NYC},
    "W-19": {"second_source_url": "https://commercialobserver.com/2025/12/coworking-resident-company-club-lease-113-university-place/"},
    "W-24": {"second_source_url": "https://api.deskpass.com/api/spaces/two-park-avenue-coworking"},
}

# R1-04: published store coordinates beat the geocode
PIN_OVERRIDES = {
    "Whole Foods Market NoMad": (40.74358, -73.986105, "wholefoodsmarket.com/stores/nomad structured data, opened 2026-10-24"),
    "Whole Foods Market Union Square": (40.7347324, -73.9908921, "wholefoodsmarket.com/stores/unionsquare structured data, opened 2026-10-24"),
    "Whole Foods Market Chelsea": (40.745148, -73.995342, "wholefoodsmarket.com/stores/chelsea structured data, opened 2026-10-24"),
}

# R1-12, R1-13: retailer corrections and the public map's wording
RETAILER_REVIEW1 = {
    "Trader Joe's Chelsea (store 543)": {"emerging_brand_evidence": "Assumption: Trader Joe's is mostly private label (not sourced); confirm on the walk."},
    "Trader Joe's Union Square (store 540)": {"emerging_brand_evidence": "Assumption: Trader Joe's is mostly private label (not sourced); confirm on the walk."},
    "Wholesome Organic Market": {"street_address": "343 Second Avenue, New York, NY 10003",
                                 "notes_add": "Review round 1: ZIP corrected from 10010 to 10003, as on NYS licence 752904 (re-opened 2026-10-24: 2,800 sq ft)."},
}
PUBLIC_EXCLUDE.update({
    "Wholesome Organic Market": "Evidence is the licence name only (no operator page opened), so private map only until it is walked.",
    "Merci Market Union Square": "Deli-and-grocery format with no natural or emerging set confirmed, the same reason the Sunac delis are left off: private map only until walked.",
})
PUBLIC_DESC = {  # plain public wording of the store format, from each store's own site or licence record
    "Eataly NYC Flatiron": "Italian food market and restaurants",
    "Fairway Market Chelsea": "Specialty supermarket",
    "Fairway Market Kips Bay": "Specialty supermarket",
    "Whole Foods Market NoMad": "Natural and organic supermarket",
    "Whole Foods Market Union Square": "Natural and organic supermarket",
    "Whole Foods Market Chelsea": "Natural and organic supermarket",
    "Westside Market NYC (84 Third Ave)": "Gourmet neighbourhood market",
    "Westside Market NYC (180 Third Ave)": "Gourmet neighbourhood market",
    "Westside Market NYC (170 West 23rd St)": "Gourmet neighbourhood market",
    "Westside Market NYC (77 Seventh Ave)": "Gourmet neighbourhood market",
    "Eden Gourmet Marketplace Gramercy Park": "Gourmet and specialty grocer",
    "Citarella Greenwich Village": "Gourmet market",
    "Wegmans Astor Place": "Large supermarket with natural, organic and specialty sections",
    "LifeThyme Natural Market": "Independent natural and organic grocer",
}

# R1-17: the model route leaves out food and drink brand offices (a pantry full of a rival's product invites a veto)
CPG_INDUSTRY_RX = r"beverage|food brand|snack|drink|spirits|wine|coffee brand|consumer packaged|\bcpg\b"

NOTE_EDITS["Suntory Global Spirits (Jim Beam Brands)"].append(("but Desk Drop brands exclude alcohol", "but the programme's brands exclude alcohol"))

# R1-16: company-wide counts for near-miss rows whose notes give no parseable number
NEAR_COUNT_OVERRIDES = {
    "Amazon": (1576000, "Wikipedia infobox, Amazon (company): 1,576,000 employees (2025), opened 2026-10-24"),
    "Microsoft (AdTech hub)": (223000, "Wikipedia infobox, Microsoft: 223,000 employees (2026), opened 2026-10-24"),
    "MSQ Partners": (1850, "MSQ's own About page as quoted in the slice notes: '1850+' people"),
}


# ================================================================ review round 2 (2026-10-24)
# Fixes for _review/round-2.md. Every value cites a page opened on 2026-10-24 (raw extracts in
# _work/headcount_second_2026-10-24.csv) or a fact already in the row's notes.

# R2-02, R2-03: a second, independent headcount for banded rows.
# Revelio Labs public pages (https://www.reveliolabs.com/companies/<slug>/employees), opened 2026-10-24 with curl
# (generic browser User-Agent, no personal data). Each page states "approximately N total employees worldwide as of
# March 2026" and carries datePublished 2026-08-31. A page counts only when its legal name and description match the
# row's company (rejected look-alikes are listed in _work/headcount_second_2026-10-24.csv). These are third-party
# estimates of the whole company.
REV = "https://www.reveliolabs.com/companies/"
REV_DATE = "2026-08-31"  # the pages' datePublished; figures "as of March 2026"


def _rev(slug, n, legal, hq):
    return {"count": n, "url": REV + slug + "/employees", "date": REV_DATE, "kind": "third-party",
            "label": f"Revelio Labs ({legal}, HQ {hq}): about {n:,} employees worldwide as of March 2026"}


HEADCOUNT_SECOND = {
    # company_name: second source
    "HUMAN Security": None,  # 'human' is Human Technologies (SC staffing); 'human-security' mixes in a Mexican security firm
    "First Look Media": _rev("first-look-media", 32, "First Look Media, Inc.", "Los Angeles"),
    "Nourish": _rev("nourish", 4082, "Nourish, Inc. (New York)", "Austin"),
    "Personetics": _rev("personetics", 336, "Personetics Technologies, Inc.", "New York City"),
    "GameChanger": _rev("gamechanger-media", 667, "GameChanger Media, Inc.", "New York City"),
    "Rockwell Group": _rev("rockwell-group", 542, "Rockwell Group", "New York City"),
    "Biohub (Chan Zuckerberg Biohub)": _rev("biohub", 436, "Chan Zuckerberg Biohub", "San Francisco"),
    "Thinking Machines Lab": _rev("thinking-machines-lab", 153, "Thinking Machines Lab, Inc.", "San Francisco"),
    "Mercury": _rev("mercury", 1279, "Mercury Technologies, Inc.", "San Francisco"),
    "Valon": _rev("valon-mortgage", 529, "Valon Mortgage, Inc.", "Chandler, Arizona"),
    "Prepared 911": _rev("prepared", 135, "Prepared LLC", "Wilmington, Delaware"),
    "Roboflow": _rev("roboflow", 132, "Roboflow, Inc.", "Des Moines"),
    "Dashlane": _rev("dashlane", 319, "Dashlane, Inc.", "New York City"),
    "Baseten": _rev("baseten-labs", 285, "Baseten Labs, Inc.", "San Francisco"),
    "Cognitiv": _rev("cognitiv", 166, "Cognitiv Corp.", "New York City"),
    "Nayya": _rev("nayya-health", 200, "Nayya Health, Inc.", "New York City"),
    "Stellar Health": _rev("stellar-health-group", 188, "The Stellar Health Group, Inc.", "New York City"),
    "VidMob": _rev("vidmob", 90, "VidMob, Inc.", "New York City"),
    "Radar": _rev("radar-labs", 99, "Radar Labs, Inc.", "New York City"),
    "The Vita Coco Company": _rev("vita-coco", 368, "The Vita Coco Co", "New York City"),
    "Aterian": _rev("aterian-group", 94, "Aterian Group, Inc.", "New York City"),
    "Global Trading Systems (GTS)": _rev("global-trading-systems", 410, "Global Trading Systems LLC", "New York City"),
    "Morning Brew": _rev("morning-brew", 286, "Morning Brew, Inc.", "New York City"),
    "Bombas": _rev("bombas", 303, "Bombas LLC", "New York City"),
    "Stash": _rev("stash-financial", 174, "Stash Financial, Inc.", "New York City"),
    "Hex Technologies": _rev("hex", 232, "Hex Technologies, Inc.", "San Francisco"),
    "Actively AI": _rev("actively", 83, "Taurus Labs, Inc., whose page describes Actively", "New York City"),
    "Retool": _rev("retool", 372, "Retool, Inc.", "San Francisco"),
    "PlayPlay": _rev("playplay", 181, "PlayPlay SASU", "Paris"),
    "Candid Health": {"count": 130, "url": "https://www.candidhealth.com/about", "date": "2025", "kind": "own-site",
                      "label": "Candid Health's own About page timeline, 2025 entry: 'Grew team to 130+ employees' (opened 2026-10-24)"},
    "CompStak": _rev("compstak", 157, "CompStak, Inc.", "New York City"),
    "Synthesia": _rev("synthesia", 774, "Synthesia Ltd.", "London"),
    "Hungryroot": _rev("hungryroot", 326, "Hungryroot, Inc.", "New York City"),
    "1stDibs": _rev("1stdibs", 281, "1stdibs.com, Inc.", "New York City"),
    "Foursquare": _rev("foursquare-labs", 430, "Foursquare Labs, Inc.", "San Francisco"),
    "TripleLift": _rev("triple-lift", 415, "Triple Lift, Inc.", "New York City"),
    "Chalk": _rev("chalk-ai", 126, "Chalk AI, Inc.", "San Francisco"),
    "Normal Computing": _rev("normal-computing", 71, "Normal Computing Corp.", "Chicago"),
    "Harvey": _rev("harvey-ai", 1130, "Harvey AI Corp.", "San Francisco"),
    "Clay": _rev("clay-labs", 710, "Clay Labs, Inc.", "New York City"),
    "Orbital": {"count": 150, "url": "https://www.orbital.tech/about", "date": "2026-10-24", "kind": "own-site",
                "label": "Orbital's own About page (opened 2026-10-24): '150+ employees'"},
    "Ellevest": _rev("ellevest", 38, "Ellevest, Inc.", "New York City"),
    "Green Mountain Energy": _rev("green-mountain-energy", 257, "Green Mountain Energy Co.", "Houston"),
    "Trexquant": _rev("trexquant-management", 340, "Trexquant Investment LP", "Stamford"),
    "At-Bay": _rev("at-bay", 335, "At-Bay, Inc.", "San Francisco"),
    "Butterfly Network": _rev("butterfly-network", 236, "Butterfly Network, Inc.", "Burlington, Massachusetts"),
    "Sierra": _rev("sierra", 756, "Sierra Technologies, Inc., described as 'the conversational AI platform for businesses'", "San Francisco"),
    "accessiBe": _rev("accessibe", 268, "accessiBe Ltd.", "Tel Aviv"),
    "Carbyne": _rev("carbyne", 146, "Carbyne Ltd.", "Tel Aviv"),
    "Seedtag": _rev("seedtag-advertising", 819, "Seedtag Advertising SL", "Madrid"),
    "Primary Wave": _rev("primary-wave-entmt", 134, "Primary Wave Entertainment LLC", "New York City"),
    "Primary Venture Partners": _rev("primary-venture-partners", 304, "Primary Venture Management LLC", "New York City"),
    "Sigma Computing": _rev("sigma-computing", 964, "Sigma Computing, Inc.", "San Francisco"),
    "K Health": _rev("k-health", 419, "K Health, Inc.", "New York City"),
    "Agentio": _rev("agentio", 71, "Agentio Inc.", "Brooklyn"),
}
HEADCOUNT_SECOND = {k: v for k, v in HEADCOUNT_SECOND.items() if v}
# The count the band rests on, where the notes give it in a form the build cannot parse
HEADCOUNT_FIRST_COUNT = {"Normal Computing": 30, "Rockwell Group": 350, "Selldorf Architects": 65,
                         "Primary Venture Partners": 40, "Christie's International Real Estate Group": 75}
# First sources that are the company's own statement: a third-party estimate does not overrule them (it makes the band unknown)
FIRST_SOURCE_OWN = {"Rockwell Group", "The Vita Coco Company"}
# Rows whose first count is scoped to the NYC office while the second is whole-company: not comparable
SCOPE_DIFFERS_KEEP = {"Normal Computing"}
# R2-02: rows that move to Near-miss because the second count is over 500. Lease sizes from each row's notes.
NYC_MAY_FIT_R2 = {
    "Mercury": "Its NYC lease is 10,000 sf on one floor (CO 2025-03-27) against an HQ in San Francisco",
    "Synthesia": "Its NYC office is 13,600 sf at 245 Fifth Ave (CO 2025-08-14) against an HQ in London",
    "Sigma Computing": "Its NYC lease is 26,252 sf (row notes) against an HQ in San Francisco",
    "Seedtag": "Its NYC office is its first US office, 5,909 sf on one floor (CO 2023) against an HQ in Madrid",
    "Valon": "Its office here is one 13,815 sf floor (REBusiness 2023-12-22); Built In also lists a Phoenix office",
    "Nourish": "Its NYC office is one 7,563 sf floor (NYREJ 2025-04-08); Revelio's page describes a dietitian telehealth service",
}

# R2-04: reworded floor (Method row 40). Applied in assemble.audit_confidence.
FLOOR_NOTE = ("An undated third-party profile (Built In, Deskpass, LiquidSpace) is never the under-24-month source: it can only "
              "confirm a dated source or the company's own live page.")

# R2-05: notes rewritten to state sources only
NOTE_EDITS.update({
    "Nourish": [("many clinicians likely remote, NYC office count unknown.", "NYC office headcount not sourced; founder to confirm at intake.")],
    "Kharon": [("so the NYC office is likely a fraction.", "so the band describes the whole company; NYC headcount not sourced.")],
    "Matador Content": [("so its own occupancy may be small.", "so part of its floor is sublet; its own headcount is not sourced.")],
    "Arca Financial Group": [("Headcount not found; may be small.", "Headcount not sourced; founder to confirm at intake.")],
    "EnVogue International": [("Showroom building, so staff onsite may be small; headcount not found.", "Showroom building (New York MarketCenter); headcount not sourced.")],
    "The Corcoran Group": [("Likely a sales office with agents rather than fixed staff.", "A residential brokerage sales office; whether agents work fixed hours here is not sourced.")],
    "U.S. News & World Report": [("NYC office size unknown and could be small.", "NYC office headcount not sourced.")],
    "Reaktor": [("NYC office likely far smaller but not sourced.", "NYC office headcount not sourced.")],
    "Jump Trading": [("Likely a large global firm but no headcount source opened, so band unknown.", "The slice opened no headcount source (the Wikipedia figure added at assembly is below).")],
    "Thinking Machines Lab": [("(company-wide; NYC team will be smaller at first).", "(company-wide; NYC headcount not sourced).")],
    "Augury": [("so probably no staffed office here. Founder to confirm; likely not a pantry host.", "and whether a staffed office exists here is not sourced. Founder to confirm.")],
})
NOTE_EDITS["Madison Square Park Conservancy"].append(("Useful neighborhood partner even if too small to host.", "Also a possible neighbourhood partner."))
OVERRIDES["Augury"]["note_add"] = ("Excluded at assembly: Built In marks the company 'Remote Workplace' and the address carries suite '#169'; "
                                   "no source shows a staffed office here.")
BUILDING_NOTE_EDITS = [
    ("Pushkin Industries also here per 2022 press but skipped as likely under 40.", "Pushkin Industries also here per 2022 press; not recorded (source older than 24 months, no headcount)."),
    ("Hack VC took the 8th floor (sublease term to Dec 2028), likely under 40, not recorded.", "Hack VC took the 8th floor (sublease term to Dec 2028); not recorded (no headcount source)."),
    ("Vine Ventures (VC) also listed, likely small, not recorded.", "Vine Ventures (VC) also listed; not recorded (no headcount source)."),
]
BANNED_NOTE_PATTERNS += [r"likely (?:remote|a fraction|far smaller|a large|a sales|under|small)", r"may be small", r"could be small",
                         r"too small", r"staff onsite may", r"occupancy may be small", r"will be smaller", r"probably no staffed"]

# R2-07: HQ where Built In is silent, from the row's own sources, the company's own page or the Revelio page above
HQ_R2 = {
    "Personetics": ("New York", "Y", REV + "personetics/employees"),
    "Rockwell Group": ("New York", "Y", "https://www.rockwellgroup.com/about"),
    "Thinking Machines Lab": ("San Francisco", "N", REV + "thinking-machines-lab/employees"),
    "Selldorf Architects": ("New York", "Y", "https://en.wikipedia.org/wiki/Selldorf_Architects"),
    "The Vita Coco Company": ("New York", "Y", REV + "vita-coco/employees"),
    "Instant": ("Sydney", "N", "row notes (CO lease report: 'Sydney-based')"),
    "PlayPlay": ("Paris", "N", REV + "playplay/employees"),
    "Synthesia": ("London", "N", REV + "synthesia/employees"),
    "Normal Computing": ("New York", "Y", "https://commercialobserver.com/2026/09/normal-computing-inspiren-leases-61-west-23rd-street/"),
    "Orbital": ("New York", "Y", "https://commercialobserver.com/2026/09/orbital-ai-lease-kaufman-organization-40-west-25th-street/"),
    "Sierra": ("San Francisco", "N", REV + "sierra/employees"),
    "Seedtag": ("Madrid", "N", REV + "seedtag-advertising/employees"),
    "Primary Wave": ("New York", "Y", REV + "primary-wave-entmt/employees"),
    "Primary Venture Partners": ("New York", "Y", REV + "primary-venture-partners/employees"),
    "Signal AI": ("London", "N", "https://www.signal-ai.com/"),
    "Warren Equity Partners": ("Jacksonville Beach, FL", "N", "https://warrenequity.com/contact-us/"),
    "Vivaldi": ("New York", "Y", "https://www.vivaldigroup.com/contact"),
    "Perplexity": ("San Francisco", "N", "row notes"),
    "ICONIQ Capital": ("San Francisco", "N", "row notes"),
    "SL Home Fashions": ("Vernon, CA", "N", "row notes"),
    "FCA (architecture and design)": ("Philadelphia", "N", "row notes"),
    "The Information": ("San Francisco", "N", "row notes (the About page lists an East Coast bureau here)"),
    "Profound": ("New York", "Y", "row notes"),
    "GovWell Technologies": ("New York", "Y", "row notes (Built In profile)"),
    "SEIU 32BJ and 32BJ Benefit Funds": ("New York", "Y", "https://www.seiu32bj.org"),
}
# R2-07: parent company, sourced or unknown
PARENT_R2 = {
    "Farmacy Beauty": ("Procter & Gamble", "https://www.happi.com/breaking-news/procter-gamble-acquires-farmacy-beauty/ (2021-11-15 acquisition report); farmacybeauty.com/pages/contact-us (opened 2026-10-24) carries P&G sign-up terms"),
    "GameChanger": ("Dick's Sporting Goods", "row notes (CO 2022-12, 2024-08: Dick's leased the space for GameChanger)"),
    "Gresham Investment Management": ("Nuveen", "row notes"),
    "Fresh (LVMH)": ("LVMH", "row notes"),
    "Morning Brew": ("Insider Inc. (majority owner)", "row notes"),
    "Green Mountain Energy": ("NRG Energy", "row notes"),
    "Wellcom Worldwide": ("Innocean Worldwide", "row notes"),
    "Hulu": ("Disney", "row notes"),
    "IMG Worldwide (WME Group)": ("WME Group", "row name"),
    "Lockton Re": ("Lockton Companies", "row notes"),
}

# R2-11: passed move dates re-checked; move_in_date is YYYY-MM or unknown, qualifiers in notes
REVIEW2_OVERRIDES = {
    "BrightTower": {"lease_status": "occupancy-unconfirmed", "move_in_date": "",
                    "note_add": "Review round 2: the planned Q2 2026 move date has passed. brighttower.com (home page opened 2026-10-24) prints no address, so the move is not confirmed. Check the 41 Madison Ave lobby directory on the walk."},
    "The Corcoran Group": {"lease_status": "occupancy-unconfirmed", "move_in_date": "",
                           "note_add": "Review round 2: the planned summer 2026 move has passed. corcoran.com (opened 2026-10-24) lists only its 590 Madison Ave head office, so the move from 387 to 381 Park Ave S is not confirmed; both addresses are inside the line. Check the 381 PAS lobby directory on the walk."},
}
MOVE_IN_FREE_TEXT = {  # company_name: note text replacing a free-text move_in_date
    "Goodwin Procter": "Move planned for late 2026 (row sources).",
    "United Talent Agency (UTA)": "Move to the Empire State Building planned for summer 2027 (row sources).",
}

# R2-12: retailer corrections
RETAILER_REVIEW2 = {
    "Trader Joe's Union Square (store 540)": {"notes_replace": [("about 3 blocks outside the east edge.", "inside the boundary's Union Square frame (University Pl to Third Ave, 13th to 15th St).")]},
    "Kalustyan's": {"confidence": "medium",
                    "notes_add": "Review round 2: lowered from high to medium. The licence is the one dated source; the operator site did not render store text, so nothing independent confirms the address."},
    "Wegmans Astor Place": {"buy_path_tier": "B",
                            "notes_replace": [("Buy-path tier A (documented natural, local or emerging set).", "Buy-path tier B (large supermarket with natural, organic and specialty aisles; no emerging set documented).")],
                            "notes_add": "Review round 2: moved from tier A to tier B. The store page lists aisles such as 'Living Gluten Free' but no local or emerging-brand set, and no store-level brand list was checked."},
}

# ================================================================ review round 3 (2026-10-24)
WP = "https://en.wikipedia.org/wiki/"
SEC_215PAS = "https://www.sec.gov/Archives/edgar/data/1013454/000153949726000704/n5676_x5-424h.htm"
# R3-06: a profile or listing whose content the subject itself supplies or can edit (Built In's employer profiles carry
# "Is This Your Company? Manage"; Deskpass and LiquidSpace listings are written by the operator) is not independent of the
# subject's own page. A high row needs its confirmation from a publisher the subject does not write: press, a landlord or
# broker release, a filing, a licence or an encyclopedia.
SUBJECT_EDITABLE_DOMAINS = {"builtinnyc.com", "builtin.com", "deskpass.com", "api.deskpass.com", "liquidspace.com"}
THIRD_PARTY_DOMAINS = {"commercialobserver.com", "nyrej.com", "rebusinessonline.com", "connectcre.com", "therealdeal.com",
                       "flatironnomad.nyc", "en.wikipedia.org", "sec.gov", "bisnow.com", "globest.com", "mannpublications.com",
                       "coworkingcafe.com", "crainsnewyork.com", "metro-manhattan.com"} | SUBJECT_EDITABLE_DOMAINS
R3_KEPT = ("Review round 3: Built In is an employer-editable profile, so it no longer counts as the independent confirmation of the "
           "company's own page. ")
REVIEW3_OVERRIDES = {
    "Dashlane": {"second_source_url": "https://commercialobserver.com/2019/04/dashlane-lease-44-west-18th-street-forty-four-eighteen-associates/",
                 "second_source_date": "2019-04-22",
                 "note_add": R3_KEPT + "The independent source is now CO 2019-04-22 (opened 2026-10-24): 'signed a 10-year lease for the entire fourth "
                             "floor' of 44 West 18th Street; Mann Report 2019-10-03 adds the third floor on a second 10-year lease. The row stays high."},
    "CompStak": {"second_source_url": "https://commercialobserver.com/2022/12/compstak-leases-27k-sf-at-675-avenue-of-the-americas/",
                 "second_source_date": "2022-12-20",
                 "note_add": R3_KEPT + "The independent source is now CO 2022-12-20 (opened 2026-10-24): 'signed a five-year lease to relocate its "
                             "global headquarters to 25,644 square feet at 675 Avenue of the Americas'. The row stays high."},
    "Empathy": {"second_source_url": "https://commercialobserver.com/2024/03/nyu-langones-empathy-project-takes-6k-sf-in-flatiron-district/",
                "second_source_date": "2024-03-06",
                "note_add": R3_KEPT + "The independent source is now CO 2024-03-06 (opened 2026-10-24; headline 'Loss Support Organization Empathy "
                            "Takes 6K SF in Flatiron District'): 'moving its headquarters to the top floor of Kaufman Organization's 56 West 22nd "
                            "Street'. The row stays high."},
    "Signal AI": {"second_source_url": "https://commercialobserver.com/2022/12/signal-ai-doubles-offices-in-move-to-440-park-avenue-south/",
                  "second_source_date": "2022-12-19",
                  "note_add": R3_KEPT + "The independent source is now CO 2022-12-19 (opened 2026-10-24): 'signed a lease for space at Samco "
                              "Properties at 440 Park Avenue South' (11,140 sf; lease length not disclosed). The row stays high."},
    "Carbyne": {"second_source_url": "https://www.connectcre.com/stories/software-company-carbyne-911-inks-downtown-lease/",
                "second_source_date": "2023-08-18",
                "note_add": R3_KEPT + "The independent source is now Connect CRE 2023-08-18 (opened 2026-10-24): 'signed a lease for 5,702 square feet "
                            "of space at 45 West 27th Street ... will occupy the second floor ... as its headquarters'. The row stays high."},
    "TripleLift": {"note_add": R3_KEPT + "No press, landlord or filing source naming TripleLift at 53 West 23rd Street was found "
                               "(one web search on 2026-10-24 returned only directory aggregators and other tenants' leases), so the row is medium."},
    "Seedtag": {"confidence": "medium",
                "note_add": "Review round 3: lowered from high to medium. The independent source (CO 2023-03-28) reports a three-year lease, so its "
                            "stated term ended about 2026-03 and it cannot confirm the office today; the company's own contact page is the one current source."},
    # R3-05: parents named by a public source (Wikipedia pages opened 2026-10-24)
    "General Assembly": {"parent_company": "The Adecco Group",
                         "parent_company_source": WP + "General_Assembly_(school) (opened 2026-10-24, last edited 2026-10-05): 'purchased by the Adecco Group in 2018'"},
    "The Corcoran Group": {"parent_company": "Compass, Inc.",
                           "parent_company_source": WP + "Corcoran_Group (opened 2026-10-24, last edited 2026-05-27): infobox 'parent = Compass, Inc.'"},
    "BrainPOP": {"parent_company": "Kirkbi A/S",
                 "parent_company_source": WP + "BrainPop (opened 2026-10-24, last edited 2026-10-09): 'In 2022, Kirkbi A/S ... acquired BrainPop'; infobox owner Kirkbi"},
    # R3-09 (6): Foursquare's HQ city: Built In says New York, Revelio says San Francisco
    "Foursquare": {"hq_city": "unknown", "hq_in_nyc": "unknown",
                   "note_add": "Review round 3: HQ city set to unknown because the sources conflict: the Built In offices page says HQ New York "
                               "(50 West 23rd Street) and the Revelio Labs page cited for the second count says HQ San Francisco."},
    # R3-10: year-only source dates
    "HUMAN Security": {"second_source_date": "2023-03-23",
                       "note_add": "Review round 3: second_source_date set from '2023' to 2023-03-23, the Built In article's datePublished (opened 2026-10-24)."},
}
REVIEW3_OVERRIDES["BrainPOP"]["note_add"] = (R3_KEPT + "The only independent source found is CO 2010-08-10 (opened 2026-10-24): a 15-year lease "
                                              "for the entire 17th floor, so its stated term ended about 2025 and it cannot confirm the office today. "
                                              "The row is medium on its own live page.")
HEADCOUNT_DATE_R3 = {  # R3-10: a year-only date moves into the notes and the date is left blank
    "Candid Health": ("headcount_second_source_date", "Review round 3: headcount_second_source_date left blank (date not stated): the About page "
                      "timeline puts 'Grew team to 130+ employees' under 2025 with no month; the page was opened 2026-10-24."),
    "Palantir Technologies": ("headcount_source_date", "Review round 3: headcount_source_date left blank (date not stated): the Wikipedia infobox "
                              "dates the 4,429 employee figure to 2025 with no month."),
    "Kohler Co. (NYC office)": ("headcount_source_date", "Review round 3: headcount_source_date left blank (date not stated): the Wikipedia infobox "
                                "dates the 40,000 employee figure to 2019 with no month."),
}
# R3-04: 'occupied' needs a dated source under 24 months or the company's own live page; otherwise occupancy-unconfirmed
OCCUPIED_NOTE = ("Review round 3: lease status set from occupied to occupancy-unconfirmed: only an undated profile places it here "
                 "(Built In, Deskpass or LiquidSpace), and B treats such profiles as often stale. Check the lobby directory on the walk.")
# R3-07: the last inferences in notes rewritten to state sources only (appended after any earlier edit of the same row)
for _k, _v in ({
    "TripleLift": [("the contact page says '400+ Talented Workers' across 8+ locations, so the whole company may be near the top of the band.",
                    "the contact page says '400+ Talented Workers' across 8+ locations (whole company).")],
    "Stone Source": [("Likely includes a showroom; headcount not found.", "Use of the space not sourced; headcount not found.")],
    "Hungryroot": [("term likely ended around 2024 and no current confirmation found", "a five-year term from 2019 ends about 2024 by arithmetic, and no current confirmation was found")],
    "Sapien AI": [("is a 5-person Berkeley firm, likely a different company)", "is a 5-person Berkeley firm; not used, as nothing ties it to this company)")],
    "Hunter Point Capital": [("so it has probably not moved yet;", "so the move is not confirmed;")],
    "Vestal Point Capital": [("Downgraded to low because it is probably not in the building yet.", "Downgraded to low because no source confirms it has moved in.")],
    "Everlast Worldwide (US headquarters)": [("Term was one year, so likely stale; not reconfirmed.", "Term was one year, so the lease as reported has ended; not reconfirmed.")],
    "Augury": [("The #169 suite number suggests a mailbox or shared suite, and whether", "The address carries suite '#169', and whether")],
}).items():
    NOTE_EDITS.setdefault(_k, []).extend(_v)
COWORKING_REVIEW3 = {
    "W-08": {"second_source_url": SEC_215PAS, "second_source_date": "2026-02-05",
             "notes_add": "Review round 3: Deskpass is an operator-written listing, so it no longer counts as the independent source. The independent "
                          "source is now the 215 Park Avenue South CMBS prospectus rent roll (sec.gov, 2026-02-05, cited by research slice S1): Industrious "
                          "holds three floors, 51,765 sf, to 2035. The row stays high. " + SEC_NOTE},
    "W-20": {"notes_replace": [("designed for consumer-brand founders': members are likely emerging CPG founders (a brand-side lead source as well as an office).",
                                "designed for consumer-brand founders'. Members are not listed.")]},
    "W-17": {"notes_replace": [("which suggests a partnership; not confirmed.", "a partnership between the two operators is not confirmed.")]},
    "W-25": {"notes_replace": [("which suggests stale text)", "so the page text may be old)")]},
    "W-05": {"notes_replace": [("shows staffed hours and availability, so probably open; open status unverified, founder to confirm.",
                                "shows staffed hours and availability; open status unverified, founder to confirm."),
                               ("office at 245 5th Ave, so it is probably open; founder to confirm.", "office at 245 5th Ave; open status unverified, founder to confirm.")]},
    "W-14": {"exclusive_food_contract_signal_replace": [("outside food placement likely needs operator approval (inference)",
                                                         "whether outside food needs operator approval is not sourced; ask at intake")]},
    "W-30": {"exclusive_food_contract_signal_replace": [("outside snack placement likely needs operator approval",
                                                         "whether outside snacks need operator approval is not sourced; ask at intake")]},
}
COWORKING_EDITABLE_NOTE = ("Review round 3: lowered from high to medium. The second source is a listing the operator writes (Deskpass or LiquidSpace), "
                           "so it does not independently confirm the operator's own page; no press, landlord or filing source was found. A walk-by can raise it.")
BANNED_NOTE_PATTERNS += [r"near the top of the band", r"likely includes", r"are likely", r"probably (?:not|open)", r"likely stale",
                         r"likely a different", r"likely needs", r"likely ended", r"suggests (?:a|stale)"]
# R3-05: owner pass over the remaining candidates on Wikipedia (raw wikitext and page footer, opened 2026-10-24). Recorded only where the
# infobox or the text names a controlling owner; minority stakes (Exor 24% of Christian Louboutin, Blue Owl 6% of ICONIQ) and a former
# corporate name (Vita Coco's 'All Market Inc.') are not parents.
PARENT_R3 = {
    "Biohub (Chan Zuckerberg Biohub)": ("Chan Zuckerberg Initiative", WP + "Chan_Zuckerberg_Biohub (opened 2026-10-24, last edited 2026-08-22): infobox 'parent = Chan Zuckerberg Initiative'"),
    "Matador Content": ("Boat Rocker Media", WP + "Matador_Content (opened 2026-10-24, last edited 2026-06-16): 'In 2018, Matador Content was acquired by the Canadian company Boat Rocker Media'"),
    "Daily Harvest": ("Chobani", WP + "Daily_Harvest (opened 2026-10-24, last edited 2026-07-13): infobox 'owner = Chobani'"),
    "Kodansha USA": ("Kodansha", WP + "Kodansha_USA (opened 2026-10-24, last edited 2026-09-11): infobox 'parent = Kodansha'"),
    "Foursquare": ("Infillion (acquisition announced 2026-09-18)", WP + "Foursquare_(company) (opened 2026-10-24, last edited 2026-10-24): 'In September 2026, Foursquare was acquired by Infillion', citing Infillion's release of 2026-09-18"),
    "Everlast Worldwide (US headquarters)": ("Frasers Group", WP + "Everlast_(brand) (opened 2026-10-24, last edited 2026-06-01): 'In 2007, Everlast was acquired by the British retailing group Frasers Group'"),
    "MCM Worldwide": ("Sungjoo Group", WP + "MCM_Worldwide (opened 2026-10-24, last edited 2026-10-23): infobox 'parent = Sungjoo Group'"),
}
REVIEW3_OVERRIDES["The Corcoran Group"]["note_add"] = ("Review round 3: parent Compass, Inc. (Wikipedia, opened 2026-10-24); Corcoran's own headcount "
                                                     "is not sourced; founder to confirm before approach.")
NOTE_EDITS.setdefault("The Corcoran Group", []).append(
    ("Headcount not sourced; a large brokerage, check for over-500 before use.", "Headcount not sourced."))
BANNED_NOTE_PATTERNS += [r"a large brokerage"]
