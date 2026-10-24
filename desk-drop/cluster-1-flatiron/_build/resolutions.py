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
