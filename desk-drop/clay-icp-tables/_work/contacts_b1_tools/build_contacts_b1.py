"""Build clay-icp-tables/_work/contacts_b1.csv (stage 2, brand contacts, ranks 1 to 60).

Every value below was read on a page opened on 2026-10-24 (confidence 'opened') or seen only in a
search result or search summary (confidence 'snippet-unverified, founder to confirm').
Evidence pages are cached in _work/fetch/contacts_b1/. Search queries are in _work/contacts_b1_searchlog.csv.
Business data only: name, title, a public business profile URL. No emails, no phones.
Run: python3 -B clay-icp-tables/_work/contacts_b1_tools/build_contacts_b1.py
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'contacts_b1.csv')
TOP = os.path.join(HERE, '..', 'top60_brands.csv')
D = '2026-10-24'
OP = 'opened'
SN = 'snippet-unverified, founder to confirm'
NA = 'n/a'
COLS = ['row_id', 'company', 'contact_rank', 'first_name', 'last_name', 'title', 'contact_linkedin_url',
        'source_url', 'source_date', 'confidence', 'notes']

ORG = 'https://theorg.com/org/'
SCPG_FEED = 'https://feeds.transistor.fm/startupcpg'

rows = []

def R(rid, rank, fn, ln, title, li, src, conf, notes):
    rows.append(dict(row_id=rid, contact_rank=rank, first_name=fn, last_name=ln, title=title,
                     contact_linkedin_url=li, source_url=src, source_date=D, confidence=conf, notes=notes))

def NONE(rid, rank, src, notes):
    rows.append(dict(row_id=rid, contact_rank=rank, first_name='none found', last_name='', title='',
                     contact_linkedin_url='', source_url=src, source_date=D, confidence=NA, notes=notes))

# 1 The Matzo Project
R('AB-216', 'founder', 'Kevin', 'Rodriguez', 'Co-founder', '',
  'https://startupcpg.com/startup-cpg-newswire-the-matzo-project-does-something-unusual-for-passover-by-not-changing-a-thing/', OP,
  'Release (2026-02) quotes "Kevin Rodriguez, Co-Founder". Brand homepage names Ashley Albert and Kevin Rodriguez as founders. The Org lists Avi B. Markus as CEO and co-owner since 2024 (backup row); he may hold the budget.')
R('AB-216', 'marketing', 'Crystal', 'Bennett', 'Partner and company spokeswoman', '',
  'https://www.foodnavigator-usa.com/Article/2025/07/23/brands-give-jewish-staples-a-new-look-new-uses', OP,
  'FoodNavigator 2025-07-23 quotes her as "a spokeswoman for The Matzo Project" at the Summer Fancy Food Show. Brand homepage (https://www.matzoproject.com/) says she joined the founders as a partner. No formal marketing title found; closest public-facing role.')
R('AB-216', 'backup', 'Ashley', 'Albert', 'Co-founder', '', 'https://www.matzoproject.com/', OP,
  'Brand homepage: "The Matzo Project began when Ashley Albert and Kevin Rodriguez..."')
R('AB-216', 'backup', 'Avi', 'Markus', 'CEO and Co-owner', '', ORG + 'the-matzo-project/person/avi-b-markus', OP,
  'The Org position page (updated 2026-08-24): "CEO & Co-owner" since 2024, listed as Avi B. Markus. Brand homepage names Avi Markus as an added partner. The Org can lag.')

# 2 Haeppy Candy
R('AB-249', 'founder', 'Maxi', 'Heidenblut', 'Founder and CEO', 'https://www.linkedin.com/in/maxi-heidenblut-cfa-ab704024/',
  'https://startupcpg.com/startup-cpg-newswire-happy-candy-launches-nationwide-at-target-with-limited-edition-haunted-edition-halloween-variety-pack/', OP,
  'Release (2026-09) quotes "Maxi Heidenblut, Founder & CEO". LinkedIn URL from the episode links of the Startup CPG podcast "BONUS: Winter Fancy Food Show Recap" (2025-02-26) in the public feed ' + SCPG_FEED + '; LinkedIn not opened.')
NONE('AB-249', 'marketing', 'https://eathappycandy.com/pages/about-us',
     'Brand site, press releases and one web search name no marketing lead. Founder is the marketing contact.')

# 3 The Lucky Ox
R('AB-219', 'founder', 'Fane', 'He', 'Co-founder and Chief Motion Officer', 'https://www.linkedin.com/in/fane-he/',
  ORG + 'the-lucky-ox/person/fane-he', OP,
  'The Org (updated 2026-07-02); earlier role Co-founder and COO. Startup CPG podcast "Founder Feature - Fane He and Kyle Nguyen of The Lucky Ox" (2025-06-20) lists this LinkedIn URL; LinkedIn not opened.')
R('AB-219', 'marketing', 'Kyle', 'Nguyen', 'Creative Director (co-founder)', '',
  ORG + 'the-lucky-ox/person/kyle-nguyen', OP,
  'The Org (updated 2026-01-27): Creative Director since 2025. Named as a founder in the Startup CPG podcast episode title. No dedicated marketing title found; closest brand role.')

# 4 Harken Sweets
R('AB-111', 'founder', 'Katie', 'Lefkowitz', 'Founder and CEO', 'https://www.linkedin.com/in/katielefkowitz/',
  'https://startupcpg.transistor.fm/episodes/founder-feature-katie-lefkowitz-of-harken-sweets', OP,
  'Episode links on the Startup CPG podcast page and on https://karagoldin.com/podcasts/katie-lefkowitz/ both give this LinkedIn URL; LinkedIn not opened. The Org (harken-sweets) also lists her as Founder & CEO.')
R('AB-111', 'marketing', 'Shaila', 'Garde-Lester', 'VP of Marketing', '',
  'https://www.nosh.com/news/2025/expo-west-harken-secures-cash-rustic-bakery-adds-cookies-bubbies-goes-green', SN,
  'Seen only in a search summary of a 2025 Nosh Expo West article; Nosh returned 403 so the page was not opened. Title may have changed.')

# 5 Eleni's New York
R('AB-075', 'founder', 'Eleni', 'Gianopulos', 'Founder and CEO', '', ORG + 'elenis/person/eleni-gianopulos', OP,
  'The Org (updated 2024-10-17): CEO. The brand about page (https://elenis.com/pages/about-us) names her as founder but spells "Gianopulous"; The Org and press spell "Gianopulos". Founder to confirm the spelling before any email lookup.')
NONE('AB-075', 'marketing', 'https://elenis.com/pages/about-us',
     'One web search: a contact directory shows only initials for a "Creative Director of Marketing". Not recorded. The Org lists a Director of Sales, not marketing.')

# 6 Beyond Good
R('AB-097', 'founder', 'Tim', 'McCollum', 'Founder and CEO', '', ORG + 'beyond-good/person/tim-mccollum', OP,
  'The Org (updated 2026-01-28): Founder and CEO since 2008, HQ office. Wikipedia (https://en.wikipedia.org/wiki/Beyond_Good) names Tim McCollum and Brett Beach as founders.')
R('AB-097', 'marketing', 'Kristine', 'Ford', 'Head of Marketing', '', ORG + 'beyond-good/person/kristine-ford', OP,
  'The Org (updated 2026-02-02): Head of Marketing since 2024-11. Bio says she provides marketing leadership for mission-driven brands, so the role may be part-time or fractional.')
R('AB-097', 'backup', 'Stephen', 'Palsi', 'Senior Marketing Manager', '', ORG + 'beyond-good/person/stephen-palsi', OP,
  'The Org (updated 2026-01-21): Senior Marketing Manager since 2025, attached to the HQ office.')
R('AB-097', 'backup', 'Brett', 'Beach', 'Co-founder', '', 'https://en.wikipedia.org/wiki/Beyond_Good', OP,
  'Wikipedia names him co-founder (2008). Not on The Org chart; current role unknown.')

# 7 Fine & Raw
R('AB-071', 'founder', 'Daniel', 'Sklaar', 'Founder', '', 'https://www.fineandraw.com/pages/about', OP,
  'Brand about page: established in 2007 by Daniel Sklaar; homepage signs "Daniel, Founder, chocolate maker".')
NONE('AB-071', 'marketing', 'https://www.fineandraw.com/pages/about',
     'One web search found only an undated first name for a former sales and marketing manager. Not recorded.')

# 8 Steve & Andy's
R('AB-082', 'founder', 'Steve', 'Marino', 'Co-founder', '', 'https://steveandandys.com/pages/about', OP,
  'Brand about page: "Founders Steve Marino and Arjan \'Andy\' Khiani".')
NONE('AB-082', 'marketing', 'https://steveandandys.com/pages/about', 'One web search: no marketing lead found.')
R('AB-082', 'backup', 'Arjan', 'Khiani', 'Co-founder', '', 'https://steveandandys.com/pages/about', OP,
  'Goes by "Andy" per the brand about page.')

# 9 PRETZELIZED
R('AB-003', 'founder', 'Sammy', 'Kestenbaum', 'Co-founder and CEO', 'https://www.linkedin.com/in/samuel-kestenbaum-26154418/',
  'https://pretzelized.com/pages/press', OP,
  'Press page: "PRETZELIZED CEO Sammy Kestenbaum". Kara Goldin Show page (https://karagoldin.com/podcasts/sammy-kestembaum/, title "Co-Founder & CEO of PRETZELIZED") links this LinkedIn URL; LinkedIn not opened.')
R('AB-003', 'marketing', 'Caitlin', 'Mack', 'VP of Marketing', '',
  'search result, URL not recorded (stage 1 LinkedIn post snippet)', SN,
  'Stage 1 saw a LinkedIn post, about two months old, on joining PRETZELIZED as VP of Marketing. Conflict: Snack and Bakery (2025 Snack Producer of the Year) lists Caitlin Mack as VP of Marketing at LesserEvil (rank 44). She may have moved; confirm which brand she is at before contacting either.')
R('AB-003', 'backup', 'Dylan', 'Lipari', 'Marketing Director', 'https://www.linkedin.com/in/dylan-lipari-98314087/',
  'https://www.linkedin.com/in/dylan-lipari-98314087/', SN,
  'From a LinkedIn search result in stage 1 (Marketing Director since 2024-01); not opened. One search on 2026-10-24 found no other source.')

# 10 Simply Gum
R('AB-233', 'founder', 'Caron', 'Proschan', 'Founder and CEO', '',
  'https://www.snackandbakery.com/articles/112597-video-simply-on-vegan-candy-treats', OP,
  'Candy Industry 2024-12-06: "Caron Proschan, founder and CEO". The Org shows "Caron P., CEO".')
R('AB-233', 'marketing', 'Jeannie', 'Kim', 'Vice President, Marketing', '', ORG + 'simply-gum/person/jeannie-kim', OP,
  'The Org (updated 2024-10-31): VP Marketing since 2019. FoodNavigator 2022 (https://www.foodnavigator-usa.com/Article/2022/01/17/Simply-Gum-expands-into-gummies-chocolate-with-low-key-launches-featuring-clean-labels/) quotes her as vice president of marketing. No 2026 confirmation.')

# 11 Mezcla
R('AB-081', 'founder', 'Griffin', 'Spolansky', 'Co-founder and CEO', '', ORG + 'mezcla/person/griffin-spolansky', OP,
  'The Org company chart lists "Co-Founder | CEO"; Green Queen article names founders Griffin Spolansky and Coco Sotelo. The Org now lists Coco Sotelo as Director of Corporate and Social Responsibility. One search found no LinkedIn URL.')
R('AB-081', 'marketing', 'Michelle', 'Brintnall Chester', 'Vice President of Marketing', '',
  ORG + 'mezcla/person/michelle-brintnall-chester', OP, 'The Org (updated 2026-09-06): VP of Marketing since 2026.')
R('AB-081', 'backup', 'Polina', 'Budilina', 'Sr. Marketing Manager', '', ORG + 'mezcla/person/polina-budilina', OP,
  'The Org (updated 2026-02-15): Sr. Marketing Manager since 2026, with Mezcla since 2023.')
R('AB-081', 'backup', 'Yoga', 'Acharya', 'President and COO', 'https://www.linkedin.com/in/yogaacharya/',
  ORG + 'mezcla', OP,
  'The Org company chart: President & COO. Startup CPG podcast #251 (2026-06-02, public feed ' + SCPG_FEED + ') lists him as President & COO of Mezcla with this LinkedIn URL; LinkedIn not opened.')

# 12 Issa's
R('AB-235', 'founder', 'Andrew', 'Issa', 'Co-founder', '',
  'https://www.wkbw.com/news/local-news/believe-in-buffalo/buffalo-born-issas-makes-pita-chips-like-no-other-in-the-nation-using-family-recipe-and-flame-baking-process', OP,
  'WKBW: "Andrew, and his brother James Issa, co-founded Issa\'s Baked Pita Chips in 2016".')
NONE('AB-235', 'marketing', 'https://www.issaspitachips.com', 'Family brand; no marketing lead on site or The Org (no page). Not searched.')
R('AB-235', 'backup', 'James', 'Issa', 'Co-founder', '',
  'https://www.wkbw.com/news/local-news/believe-in-buffalo/buffalo-born-issas-makes-pita-chips-like-no-other-in-the-nation-using-family-recipe-and-flame-baking-process', OP,
  'Same article.')

# 13 Raaka Chocolate
R('AB-070', 'founder', 'Nathan', 'Hodge', 'CEO and co-founder', '', ORG + 'raaka-chocolate/person/nathan-hodge', OP,
  'The Org (updated 2024-10-31): CEO since 2021; Head Chocolate Maker and Co-Founder from 2010. Brand story page names co-founders "Ryan and Nate". Replaces the unverified stage-1 surname.')
R('AB-070', 'marketing', 'William', 'Mullan', 'Brand Manager', '', ORG + 'raaka-chocolate/person/william-mullan', OP,
  'The Org (updated 2024-10-31): Brand Manager since 2014, HQ office. Two years since the page was updated.')
R('AB-070', 'backup', 'Ryan', 'Cheney', 'Founder', '',
  'https://www.snackandbakery.com/articles/103080-raaka-chocolates-raw-flavor-powers-growth', OP,
  'Candy Industry (2014): "its founder Ryan Cheney". A 2020 Nosh article (search summary only) said he planned to become executive chairman; current role unknown.')

# 14 Zack's Mighty
R('AB-002', 'founder', 'Zack', 'Gazzaniga', 'Founder and CEO', '',
  'https://www.snackandbakery.com/articles/110099-zacks-mighty-reveals-first-ever-non-gmo-rolled-tortilla-chips', OP,
  'Article: founded in 2020 by Zack Gazzaniga. "CEO" from a Spoiler Alert case study seen in search results.')
R('AB-002', 'marketing', 'Kate', 'Scofield', 'Senior Brand Manager', '', ORG + 'zacks-mighty/person/kate-scofield', OP,
  'The Org (updated 2026-05-30): Senior Brand Manager since 2026.')

# 15 BjornQorn
R('AB-001', 'founder', 'Bjorn', 'Quenemoen', 'Co-founder', '', 'https://www.ecowatch.com/local-solar-popped-popcorn-2639003915.html', OP,
  'Modern Farmer via EcoWatch (2019): Bjorn Quenemoen and Jamie O\'Shea, popcorn makers.')
NONE('AB-001', 'marketing', 'https://bjornqorn.com', 'Two-founder brand; The Org lists only a Sales Strategy Director. Not searched.')
R('AB-001', 'backup', 'Jamie', "O'Shea", 'Co-founder', '', 'https://www.ecowatch.com/local-solar-popped-popcorn-2639003915.html', OP,
  'Stage 1 had him in the marketing slot; the page says co-founder only, so moved to backup.')

# 16 Goody's Granola
NONE('AB-236', 'founder', 'https://goodysgranola.nyc',
     'Brand site names no person; one web search found nothing. Channel falls back to the brand\'s contact form.')
NONE('AB-236', 'marketing', 'https://goodysgranola.nyc', 'Nothing found.')

# 17 Fruition Chocolate Works
R('AB-077', 'founder', 'Bryan', 'Graham', 'Founder', '', 'https://www.fruitionchocolateworks.com/pages/our-story', OP,
  'Our Story page: "Bryan Graham is the founder of Fruition Chocolate Works and Confectionery". Boston Globe 2026-02-24 agrees.')
NONE('AB-077', 'marketing', 'https://www.fruitionchocolateworks.com/pages/our-story', 'Family business; no marketing lead found. Not searched.')
R('AB-077', 'backup', 'Dahlia', 'unknown', 'Co-owner', '',
  'https://www.bostonglobe.com/2026/02/24/lifestyle/fruition-chocolate-works-pop-up-shop', OP,
  'Boston Globe: "With his wife, Dahlia, they craft chocolate". Surname not printed (stage 1 assumed Graham); founder to confirm.')

# 18 B-SIDES
R('AB-226', 'founder', 'Yousuf', 'Ahmed', 'Founder', 'https://www.linkedin.com/in/yousufmahmed/',
  'https://startupcpg.com/startup-cpg-newswire-b-sides-closes-500k-seed-round-to-scale-retail-expansion/', OP,
  'Release: "Founded by former Goldman Sachs private wealth advisor Yousuf Ahmed". The LinkedIn URL is linked from the brand\'s own homepage (https://www.enjoybsides.com/, site data "sameAs"); LinkedIn not opened.')
NONE('AB-226', 'marketing', 'https://www.enjoybsides.com/', 'Seed-stage brand; no marketing lead found. Not searched.')

# 19 Ella's Flats
R('AB-016', 'founder', 'Ellen', 'Macks', 'Founder', '', 'https://www.ellasflats.com/', OP,
  'Homepage: started by Ellen Macks in 2017. The Org (ellas-flats) lists her as Owner.')
NONE('AB-016', 'marketing', 'https://www.ellasflats.com/', 'Family-operated brand; no marketing lead found. Not searched.')

# 20 Taza Chocolate
R('AB-106', 'founder', 'Alex', 'Whitmore', 'Founder and CEO', '', 'https://www.tazachocolate.com/pages/about-taza', OP,
  'About page: "Taza founder and CEO Alex Whitmore". Kara Goldin Show page agrees; it lists no LinkedIn URL.')
R('AB-106', 'marketing', 'Stephanie', 'Larason', 'Brand and Marketing Director', 'https://www.linkedin.com/in/slarason/',
  'https://www.linkedin.com/in/slarason/', SN,
  'Stage-1 LinkedIn search snippet (one snapshot about 4.5 years old); not opened. Two searches on 2026-10-24 found no current marketing name (a 2018 COO and CMO appointment is stale).')

# 21 Treat House
R('AB-210', 'founder', 'Chris', 'Russell', 'Co-founder and co-owner', '',
  'https://www.dnainfo.com/new-york/20150720/upper-east-side/gourmet-rice-krispies-treats-eatery-opens-on-ues-with-adults-mind/', OP,
  'DNAinfo 2015: "the owners of Treat House, Chris and Jennifer Russell". Untapped Cities article (stage 1 source) names Chris, a chef, as the maker. Sources are 2015 to 2017.')
NONE('AB-210', 'marketing', 'https://treathouse.com', 'No marketing lead found.')
R('AB-210', 'backup', 'Jennifer', 'Russell', 'Co-founder', '',
  'https://www.creators.com/read/this-womans-work/08/17/giving-back-with-love-and-chocolate-an-interview-with-jennifer-russell', OP,
  'Creators 2017: "Jennifer Russell is the co-founder and co-creator of Treat House".')

# 22 Magic Spoon
R('AB-096', 'founder', 'Gabi', 'Lewis', 'Co-founder', 'https://www.linkedin.com/in/gabi-lewis-88483447/',
  ORG + 'magic-spoon/person/gabi-lewis', OP,
  'The Org (updated 2026-08-12): Co-Founder (formerly co-CEO). Brand Our Story page: "we\'re Greg and Gabi, co-founders". LinkedIn URL linked from https://karagoldin.com/podcasts/gabi-lewis/; LinkedIn not opened. Co-founder Greg Sewitz also on The Org.')
R('AB-096', 'marketing', 'Sarah', 'Barnes', 'Chief Marketing Officer', 'https://www.linkedin.com/in/sarah-barnes-30a301b/',
  'https://www.linkedin.com/in/sarah-barnes-30a301b/', SN,
  'Stage-1 LinkedIn search result title "Chief Marketing Officer at Magic Spoon"; not opened. A 2026-10-24 search found no press naming a CMO and a Senior Director of Brand Marketing role advertised.')
R('AB-096', 'backup', 'Emily', 'Geiger', 'Senior Brand Manager', '', ORG + 'magic-spoon/person/emily-geiger', OP,
  'The Org (updated 2026-09-03): Senior Brand Manager since 2026.')

# 23 Stiller's Soda
R('AB-207', 'founder', 'Alex', 'Doman', 'Co-founder', '', 'https://www.foodbusinessnews.net/articles/29686-the-goldilocks-of-soda', OP,
  'Food Business News: co-launched in 2025 by Ben Stiller and Alex Doman. The Org (' + ORG + 'stillers-soda/person/alexander-doman, updated 2026-08-31) lists Alexander Doman, "President of Global Soda Affairs" and co-founder.')
NONE('AB-207', 'marketing', 'https://stillerssoda.com', 'One web search: press names the ad agency but no in-house marketing lead.')

# 24 Hella Cocktail Co.
R('AB-239', 'founder', 'Tobin', 'Ludwig', 'Co-founder and COO', '', 'https://hellacocktail.co/pages/meet-the-founders', OP,
  'Meet the Founders page. Co-founder Jomaree Pinkard is now Chairman (backup row).')
R('AB-239', 'marketing', 'Eddie', 'Simeón', 'Co-founder and CMO', '', 'https://hellacocktail.co/pages/meet-the-founders', OP,
  'Meet the Founders page: "Eddie Simeón, Co-Founder & CMO".')
R('AB-239', 'backup', 'Jomaree', 'Pinkard', 'Co-founder and Chairman', '', 'https://hellacocktail.co/pages/meet-the-founders', OP,
  'Page: served as Co-Founder and CEO for a decade, now Chairman. The Org (hella-cocktail) lists him as Co-Founder.')

# 25 Figa Foods
R('AB-270', 'founder', 'Ariel', 'Altman', 'Co-founder', 'https://www.linkedin.com/in/ariel-altman-396b922b/',
  'https://startupcpg.com/founder-feature-ariel-altman-and-ronny-berger-of-figa-foods/', OP,
  'Startup CPG founder feature. LinkedIn URL from the episode links of the matching Startup CPG podcast episode (2025-08-01, public feed); LinkedIn not opened.')
NONE('AB-270', 'marketing', 'https://figafoods.com', 'Two-founder brand; no marketing lead found. Not searched.')
R('AB-270', 'backup', 'Ronny', 'Berger', 'Co-founder', 'https://www.linkedin.com/in/ronnyberger/',
  'https://startupcpg.com/founder-feature-ariel-altman-and-ronny-berger-of-figa-foods/', OP, 'Same feature and episode links.')

# 26 FitJoy Foods
R('AB-048', 'founder', 'Norman', 'Taliaferro', 'CEO and Founding Partner', '', 'https://fitjoyfoods.com/pages/our-people', OP,
  'Brand Our People page. The Org (fitjoy) agrees and also lists Doss Cunningham as Co-Founder and Chairman.')
R('AB-048', 'marketing', 'Micah', 'Mills', 'Director of Marketing', '', 'https://fitjoyfoods.com/pages/our-people', OP,
  'Brand Our People page; The Org (updated 2024-11-17) agrees, Director of Marketing since 2023.')

# 27 Daily Crunch
R('AB-004', 'founder', 'Laurel', 'Orley', 'Co-founder and CEO', 'https://www.linkedin.com/in/laurel-orley/',
  ORG + 'daily-crunch/person/laurel-orley', OP,
  'The Org (updated 2026-09-13): Co-Founder and CEO since 2018. LinkedIn URL from Startup CPG podcast #213 episode links (2025-09-09, public feed); LinkedIn not opened.')
NONE('AB-004', 'marketing', 'https://dailycrunchsnacks.com/pages/about-us',
     'About page says Laurel has a background in marketing; no separate marketing lead found. Not searched.')
R('AB-004', 'backup', 'Diane', 'unknown', 'Co-founder', '', 'https://dailycrunchsnacks.com/pages/about-us', OP,
  'About page: "Diane, Laurel\'s aunt & co-founder". Surname not given.')

# 28 Blue Stripes
R('AB-072', 'founder', 'Oded', 'Brenner', 'Founder and CEO', '', 'https://www.bluestripes.com/pages/about-us', OP,
  'About page: the founder, Oded Brenner. The Org lists him as Chief Executive Officer.')
NONE('AB-072', 'marketing', 'https://www.bluestripes.com/pages/about-us', 'One web search: no marketing lead named in press.')
R('AB-072', 'backup', 'Aviv', 'Schwietzer', 'Co-founder and COO', '', ORG + 'blue-stripes/person/aviv-schwietzer', OP,
  'The Org (updated 2024-11-04): Co-founder & Chief Operating Officer since 2019.')

# 29 Jack & Friends
R('AB-058', 'founder', 'Jessica', 'Kwong', 'Founder and CEO', '', 'https://jackandfriendsjerky.com/pages/about', OP,
  'About page: "our founder, Jessica Kwong". The Org (updated 2026-06-12): Founder & CEO since 2018.')
NONE('AB-058', 'marketing', 'https://jackandfriendsjerky.com/pages/about', 'Founder-led brand; no marketing lead found. Not searched.')

# 30 Go Raw
R('AB-047', 'founder', 'Robert', 'Freeland', 'Owner, Founder and CEO', '', ORG + 'go-raw/person/robert-freeland', OP,
  'The Org (updated 2023-07-24): "Owner - Founder - CEO" since 2002. The same chart lists Peter Grumhaus as CEO since 2023 (backup row); who holds the budget now is unconfirmed. Stage 1 had the brand manager in this slot.')
R('AB-047', 'marketing', 'Kimberly', 'Waldron', 'Vice President of Marketing', '', ORG + 'go-raw/person/kimberly-waldron', OP,
  'The Org (updated 2026-01-29): VP of Marketing since 2024.')
R('AB-047', 'backup', 'Maggie', 'Quinn', 'Brand Manager', '',
  'https://www.snackandbakery.com/articles/115681-go-raw-expands-lineup-with-its-first-cracker', OP,
  'Snack and Bakery 2026 quotes "Maggie Quinn, brand manager for Go Raw".')
R('AB-047', 'backup', 'Peter', 'Grumhaus', 'Chief Executive Officer', '', ORG + 'go-raw/person/peter-grumhaus', OP,
  'The Org (updated 2023-07-24): CEO since 2023, formerly COO. Three years since update.')

# 31 Seed + Mill
R('AB-073', 'founder', 'Rachel', 'Simons', 'CEO and Co-founder', '', 'https://www.seedandmill.com/a/press-kit', OP,
  'Brand press kit quotes a 2022 article: "Rachel Simons, the Australian-born CEO and Co-Founder of Seed + Mill". About page names three founders, Lisa, Rachel and Monica. Stage 1 source (Goldbelly) returned 403 today.')
NONE('AB-073', 'marketing', 'https://www.seedandmill.com/pages/about-us', 'Founder-run shop and brand; no marketing lead found. Not searched.')
R('AB-073', 'backup', 'Lisa', 'Mendelson', 'Co-founder', '', 'https://www.seedandmill.com/a/press-kit', OP,
  'Press kit quotes Kitchn: "the three co-founders of Seed + Mill (Rachel Simons, Lisa Mendelson, and Monica Molenaar)".')
R('AB-073', 'backup', 'Monica', 'Molenaar', 'Co-founder', '', 'https://www.seedandmill.com/a/press-kit', OP, 'Same page.')

# 32 Moshi
R('AB-130', 'founder', 'Alton', 'But', 'Founder', '',
  'https://attend.expowest.com/event/natural-products-expo-west-2026/exhibitor/RXhoaWJpdG9yXzIzNTgyMzE=', OP,
  'Expo West 2026 listing for Brooklyn Food & Beverage: "Founder Alton But ... launched Moshi" in 2020. The Org (brooklyn-food-and-beverage) lists him as Sales & Operations. Same parent as Bruce Cost Ginger Ale (rank 57): treat as one company, one contact in flight.')
R('AB-130', 'marketing', 'Horin', 'Yip', 'Brand Marketing Manager, Brooklyn Food & Beverage', '',
  'https://attend.expowest.com/event/natural-products-expo-west-2026/exhibitor/RXhoaWJpdG9yXzIzNTgyMzE=', OP,
  'Expo West 2026 exhibitor team list: "Horin Yip, Brand Marketing Manager, Brooklyn Crafted". Covers the parent\'s brands.')
R('AB-130', 'backup', 'Cody', 'But', 'Managing Partner, Brooklyn Food and Beverage', '',
  ORG + 'brooklyn-food-and-beverage/person/cody-but', OP, 'The Org (updated 2026-06-06): Managing Partner since 2023.')

# 33 Explorer Cold Brew
R('AB-172', 'founder', 'Cason', 'Crane', 'Founder and CEO', 'https://www.linkedin.com/in/casoncrane/',
  'https://explorercoldbrew.com/pages/meet-the-team', OP,
  'Meet the Team page. LinkedIn URL from the Startup CPG podcast "Founder Feature: Cason Crane" episode links (2024-11-22, public feed); LinkedIn not opened.')
NONE('AB-172', 'marketing', 'https://explorercoldbrew.com/pages/meet-the-team',
     'Meet the Team page lists only the founder and the COO. The only growth contact found (The Org, 2024) is a consultant who is not on the team page; kept as a backup row, not as the marketing lead.')
R('AB-172', 'backup', 'Michael', "O'Hagan", 'Head of Ecommerce and Growth (consultant)', '',
  ORG + 'explorer-cold-brew/person/michael-ohagan', OP,
  'The Org (updated 2024-11-01): consultant role since 2022. Not on the brand\'s Meet the Team page, so he may have left. Growth, not a marketing title.')
R('AB-172', 'backup', 'Matt', 'Adams', 'COO', '', 'https://explorercoldbrew.com/pages/meet-the-team', OP,
  'Meet the Team page. Stage 1 had him in the marketing slot; COO is not marketing, so moved to backup.')

# 34 Biena
R('AB-027', 'founder', 'Poorvi', 'Patodia', 'Founder and CEO', '', 'https://bienasnacks.com/pages/our-story', OP, 'Our Story page.')
R('AB-027', 'marketing', 'Samantha', 'Sieloff', 'Director of Brand Marketing', '', ORG + 'biena-snacks/person/samantha-sieloff', OP,
  'The Org (updated 2024-11-12): Director of Brand Marketing since 2023.')
R('AB-027', 'backup', 'Deepa', 'Kesa', 'Social Media and Marketing Manager', '', ORG + 'biena-snacks/person/deepa-kesa', OP,
  'The Org (updated 2026-01-21): since 2025, HQ office.')

# 35 Elements Truffles
R('AB-084', 'founder', 'Alak', 'Vasa', 'Co-founder', '', 'https://www.elementstruffles.com/pages/about-us', OP, 'About page, "meet our founders".')
NONE('AB-084', 'marketing', 'https://www.elementstruffles.com/pages/about-us', 'Two-founder brand; no marketing lead found. Not searched.')
R('AB-084', 'backup', 'Kushal', 'Choksi', 'Co-founder', '', 'https://www.elementstruffles.com/pages/about-us', OP,
  'About page: "Kushal M. Choksi", co-founder with Alak.')

# 36 Gigantic (Candy Deluxe)
R('AB-266', 'founder', 'Stu', 'Davidoff', 'Founder', '', 'https://gritdaily.com/gigantic-candy-deluxe-smaller-deliberate-candy/', OP,
  'Grit Daily: "Gigantic was founded by Stu Davidoff". The brand\'s Presshook page (https://www.presshook.com/brands/gigantic/) calls him a lifelong New Yorker; HQ is still unknown in the table.')
NONE('AB-266', 'marketing', 'https://giganticcandy.com', 'No marketing lead found.')

# 37 Firehook
R('AB-032', 'founder', 'Maura', 'Mottolese', 'CEO', '',
  'https://www.snackandbakery.com/articles/116020-firehook-crackers-grillos-strive-for-pickle-perfection', OP,
  'Snack and Bakery 2026: "Maura Mottolese, CEO of Firehook Crackers". Not a founder (Firehook is an older bakery now private-equity owned); CEO is the budget owner.')
R('AB-032', 'marketing', 'Ellen', 'Howse', 'Chief Marketing Officer', '',
  'https://www.foodnavigator.com/Article/2025/05/13/natural-cracker-brand-collaborates-with-standout-cross-category-companies/', OP,
  'FoodNavigator 2025-05-13: "Ellen Howse, CMO at Firehook". The Org agrees (updated 2024-10-31).')

# 38 Reelie
R('AB-034', 'founder', 'Juan Pablo', 'Guzman', 'CEO', '', 'https://www.cbinsights.com/company/artisan-tropic/people', SN,
  'Seen only in a search summary of the CB Insights people page (undated). Brand about page says the business was started by the family after Maca was diagnosed; Target Takeoff 2021 names the Guzman family.')
R('AB-034', 'marketing', 'Juan', 'Nino', 'Director of Marketing', '',
  'https://accelerators.target.com/alumni-stories/meet-artisan-tropic-of-target-takeoff-food-beverage-2021/', OP,
  'Target Takeoff interview (2021): "Juan Nino, Director of Marketing". Five years old, before the rename to Reelie. Stage 1 had him in the founder slot.')
R('AB-034', 'backup', 'Jose', 'Nino', 'Director of Sales', '',
  'https://accelerators.target.com/alumni-stories/meet-artisan-tropic-of-target-takeoff-food-beverage-2021/', OP, 'Same 2021 interview.')

# 39 Z Crackers
R('AB-237', 'founder', 'Keith', 'Pollack', 'Co-founder and President', '', 'https://www.zcrackers.com/', OP,
  'Homepage: "Pam and Keith Pollack, Founders" and "Keith Pollack, Z President" (Savory Pie Company).')
NONE('AB-237', 'marketing', 'https://www.zcrackers.com/', 'Family company; no marketing lead found. Not searched.')
R('AB-237', 'backup', 'Pam', 'Pollack', 'Co-founder', '', 'https://www.zcrackers.com/', OP, 'Same page.')

# 40 Mayana Chocolate
R('AB-087', 'founder', 'Daniel', 'Herskovic', 'Owner', '', 'https://www.mayanachocolate.com/pages/about-mayana-chocolate', OP,
  'About page: run by husband and wife Daniel and Tamara Herskovic. The Org (updated 2026-09-28) lists him as CEO since 2008.')
NONE('AB-087', 'marketing', 'https://www.mayanachocolate.com/pages/about-mayana-chocolate', 'Owner-run; no marketing lead found. Not searched.')
R('AB-087', 'backup', 'Tamara', 'Herskovic', 'Owner', '', 'https://www.mayanachocolate.com/pages/about-mayana-chocolate', OP, 'Same page.')

# 41 Shinzo Matcha
R('AB-222', 'founder', 'Zach', 'Hayworth', 'Co-founder', '',
  'https://startupcpg.com/startup-cpg-newswire-shinzo-matcha-launches-sparkling-matcha-soda/', OP,
  'Release quotes "co-founder Zach Hayworth". One web search found no other co-founder.')
NONE('AB-222', 'marketing', 'https://shinzomatcha.com', 'No marketing lead found.')

# 42 Doosra
R('AB-278', 'founder', 'Kartik', 'Das', 'Founder', 'https://www.linkedin.com/in/daskartik/', 'https://eatdoosra.com/pages/about', OP,
  'About page signed Kartik Das. LinkedIn URL from the Startup CPG podcast "Founder Feature: Kartik Das of Doosra" episode links (2026-02-06, public feed); LinkedIn not opened.')
NONE('AB-278', 'marketing', 'https://eatdoosra.com/pages/about', 'Solo-founder brand; no marketing lead found. Not searched.')

# 43 Effie's Homemade
R('AB-285', 'founder', 'Joan', 'MacIsaac', 'Co-founder', '', 'https://blog.harryanddavid.com/articles/profiles/effies-homemade-oatcake', OP,
  'Harry & David profile (2023-02-17, modified 2025-06-23): "Effie\'s Homemade founders and friends, Joan MacIsaac and Irene Costello". Brand about page names Joan (Effie\'s daughter). Fills the stage-1 surname gap.')
NONE('AB-285', 'marketing', 'https://effieshomemade.com/pages/about-us', 'No marketing lead found.')
R('AB-285', 'backup', 'Irene', 'Costello', 'Co-founder', '', 'https://blog.harryanddavid.com/articles/profiles/effies-homemade-oatcake', OP, 'Same page.')

# 44 LesserEvil
R('AB-024', 'founder', 'Charles', 'Coristine', 'President and CEO', 'https://www.linkedin.com/in/charles-coristine-7b611b13/',
  'https://www.snackandbakery.com/articles/114444-2025-snack-producer-of-the-year-lesserevil', OP,
  'Snack and Bakery 2025 key personnel: "Charles Coristine, CEO"; he bought the company in 2011, so owner rather than original founder. LinkedIn URL linked from https://karagoldin.com/podcasts/charles-coristine/; LinkedIn not opened.')
R('AB-024', 'marketing', 'Caitlin', 'Mack', 'VP of Marketing', '',
  'https://www.snackandbakery.com/articles/114444-2025-snack-producer-of-the-year-lesserevil', OP,
  'Snack and Bakery 2025 key personnel; Modern Retail 2024-09 called her director of digital and brand marketing. A stage-1 LinkedIn snippet (about two months old) says a Caitlin Mack joined PRETZELIZED (rank 9) as VP of Marketing; she may have left. Confirm before contacting.')
R('AB-024', 'backup', 'Megan', 'Reid', 'Senior Manager, Influencer Marketing and Partnerships', '', ORG + 'lesserevil/person/megan-reid', OP,
  'The Org (updated 2024-04-17): since 2023, HQ office. Over two years since update.')

# 45 JONI
R('AB-173', 'founder', 'Claire', 'Matern', 'Founder', '', 'https://andreastrong.substack.com/p/please-meet-joni', OP,
  'The Strong Buzz newsletter: "Joni was launched in January by Claire Matern".')
NONE('AB-173', 'marketing', 'https://drinkjoni.com/pages/our-story', 'Founder-run brand; no marketing lead found. Not searched.')

# 46 Nantucket Crisps
R('AB-025', 'founder', 'Hayden', 'Arnot', 'Co-founder', 'https://www.linkedin.com/in/hayden-arnot-ab9457107/',
  'https://startupcpg.com/14-chip-brands-taking-your-tastebuds-on-a-flavor-tour/', OP,
  'Startup CPG roundup lists "Founders: Hayden Arnot" and links this LinkedIn URL; LinkedIn not opened. The Org (updated 2026-06-06): Co-Founder since 2022.')
NONE('AB-025', 'marketing', 'https://nantucketcrisps.com', 'One web search: no marketing lead named; a 2026-06 release quotes the co-founder on marketing.')
R('AB-025', 'backup', 'Paul', 'Nardone', 'CEO', '',
  'https://startupcpg.com/nantucket-crisps-transitions-brand-platform-to-avocado-oil-and-names-cpg-industry-veteran-paul-nardone-ceo/', OP,
  'Release (2026-05): named CEO. Stage 1 had him in the marketing slot; CEO is the likely budget owner.')

# 47 UMAMI GRANOLA
R('AB-217', 'founder', 'Cindy', 'Lam', 'Founder', '', 'https://startupcpg.com/startup-cpg-newswire-umami-granola-makes-its-retail-debut/', OP,
  'Release (2026-08-20): "Cindy Lam, Founder of UMAMI GRANOLA".')
NONE('AB-217', 'marketing', 'https://umamigranola.com/pages/press', 'Solo founder; press page routes to a press inbox. Not searched.')

# 48 Mavericks Snacks
R('AB-091', 'founder', 'Livio', 'Bisterzo', 'Founder', '',
  'https://startupcpg.com/startup-cpg-newswire-mavericks-snacks-partners-with-paramount-pictures-for-transformers-one-film-release/', OP,
  'Release: "Livio Bisterzo, CEO of Green Park Brands, founded Mavericks Snacks". The Org (green-park-brands, updated 2024-10-11): CEO & Founder of the parent.')
R('AB-091', 'marketing', 'Tina', 'Pate', 'VP of Marketing', '', 'https://www.nosh.com/news/2022/mavericks-cookies-focuses-on-branding-to-land-target-store-partnership', SN,
  'Seen only in a search summary of a 2022 Nosh article (not opened). Four years old; likely stale.')
R('AB-091', 'backup', 'Brenden', 'Schaefer', 'President and General Manager', '',
  'https://www.foodnavigator.com/Article/2022/06/30/Mavericks-Snacks-ramps-up-distribution-We-very-strongly-believe-and-designed-this-brand-to-be-a-mainstream-proposition/', OP,
  'FoodNavigator 2022-06-30. Four years old; current role unknown.')

# 49 Sweet Loren's
R('AB-069', 'founder', 'Loren', 'Castle', 'Founder and CEO', 'https://www.linkedin.com/in/loren-brill-castle-56887121/',
  'https://www.sweetlorens.com/blogs/press', OP,
  'Brand press page carries the CNBC piece (2025-02-18): "Castle is founder and CEO of Sweet Loren\'s". The Org lists "Loren (Brill) Castle". LinkedIn URL linked from https://karagoldin.com/podcasts/loren-castle/; LinkedIn not opened. Fills the stage-1 surname gap.')
R('AB-069', 'marketing', 'Tracy', 'Garbowski', 'Senior Vice President, Marketing', '', ORG + 'sweet-lorens/person/tracy-garbowski', OP,
  'The Org (updated 2026-01-21): SVP Marketing since 2025. The earlier SVP Marketing, Robyn DeFina (appointed 2022-10 per Food Industry Executive, The Org updated 2023-01), appears superseded; not recorded as a contact.')

# 50 Joyride
R('AB-086', 'founder', 'Tyler', 'Merrick', 'Founder', '', 'https://www.joyridesweets.com/pages/joyride-story', OP, 'Brand story page.')
R('AB-086', 'marketing', 'Ryan', 'Trahan', 'Chief Creative Officer and co-owner', '',
  'https://www.snackandbakery.com/articles/115858-joyride-launches-consumer-powered-50-states-challenge', OP,
  'Candy Industry 2026-06-11: "chief creative officer and co-owner Ryan Trahan". He is a large YouTube creator; expect a gatekept inbox.')

# 51 Solely
R('AB-107', 'founder', 'Simon', 'Sacal', 'Founder and CEO', '', 'https://karagoldin.com/podcasts/simon-sacal/', OP,
  'Kara Goldin Show page title "Simon Sacal: Founder & CEO of Solely" (no LinkedIn link). Snack and Bakery 2026 calls him CEO.')
R('AB-107', 'marketing', 'Manish', 'Amin', 'Head of Marketing', '', ORG + 'solely-inc/person/manish-amin', OP,
  'The Org (updated 2024-11-04): since 2022. Two years since update. The Org also lists a CRO and EVP Sales and Marketing.')

# 52 Jonesbar
R('AB-088', 'founder', 'Taylor', 'Jones', 'Founder and CEO', '', 'https://jonesbar.com/pages/our-story-2', OP,
  'Our Story page: "taylor jones - founder/ceo".')
NONE('AB-088', 'marketing', 'https://jonesbar.com/pages/our-story-2', 'Founder-run brand; no marketing lead found. Not searched.')

# 53 Cirrus 9 Candy
R('AB-281', 'founder', 'Morganne', 'unknown', 'Founder', '', 'https://cirrus9candy.com/pages/about', OP,
  'About page: "Morganne, Founder, Flavor & craft". Surname not given; one web search found none.')
NONE('AB-281', 'marketing', 'https://cirrus9candy.com/pages/about', 'Two-person brand; no marketing lead.')
R('AB-281', 'backup', 'Makenna', 'unknown', 'Co-founder (tech)', '', 'https://cirrus9candy.com/pages/about', OP,
  'About page: "Makenna, Co-founder & tech". Stage 1 had her in the marketing slot; the page gives a tech role, so moved to backup.')

# 54 Goodio
R('AB-124', 'founder', 'Jukka', 'Peltola', 'Founder and Chief Creative Officer', '', 'https://goodiochocolate.com/pages/about-us', OP,
  'About page: "Chief Creative Officer and founder of Goodio, Jukka Peltola". The Org lists Jonni Sinkkonen as CEO & Founder (backup row) and Sami Nupponen as CEO; titles conflict. Finnish company, US sales contact unknown.')
NONE('AB-124', 'marketing', 'https://goodiochocolate.com/pages/about-us', 'No marketing lead found. Not searched.')
R('AB-124', 'backup', 'Jonni', 'Sinkkonen', 'CEO and Founder', '', ORG + 'goodio/person/jonni-sinkkonen', OP,
  'The Org (updated 2026-06-10): CEO & Founder since 2015.')

# 55 Maxine's Heavenly
R('AB-090', 'founder', 'Robert', 'Petrarca', 'Co-founder and CEO', '', 'https://maxinesheavenly.com/pages/press', OP,
  'Press page: "Its founder Robert Petrarca" and "talks business with our CEO". The Org (updated 2023-01-13): Co-Founder & CEO.')
NONE('AB-090', 'marketing', 'https://maxinesheavenly.com/pages/press', 'The Org lists sales, not marketing. Not searched.')

# 56 Unhinged
R('AB-220', 'founder', 'Byron', 'Sorrells', 'Co-founder', '', 'https://startupcpg.com/startup-cpg-newswire-unhinged-raises-1-1m-pre-seed/', OP,
  'Release (2026-10): "co-founder Byron Sorrells".')
NONE('AB-220', 'marketing', 'https://alwaysunhinged.com', 'No marketing lead found.')
R('AB-220', 'backup', 'Matt', 'Paine', 'Co-founder', '', 'https://business.newportbeach.com/directory/Details/always-unhinged-inc-4636037', SN,
  'Seen only in a search summary of a Newport Beach business directory listing (403). The listing places Always Unhinged, Inc. in Orange County, which conflicts with the New York HQ in the table.')

# 57 Bruce Cost Ginger Ale
R('AB-131', 'founder', 'Terry', 'Tang', 'Owner', '', 'https://www.bevnet.com/news/2017/bruce-cost-ginger-ale-look-separate-futures', SN,
  'Seen only in search summaries: BevNET 2017 says Tang bought out founder Bruce Cost in 2016 (BevNET 403). A 2020 BevNET item (search summary) says Brooklyn Food and Beverage makes Bruce Cost, Brooklyn Crafted and Moshi. Same parent as Moshi (rank 32): treat as one company, one contact in flight.')
R('AB-131', 'marketing', 'Horin', 'Yip', 'Brand Marketing Manager, Brooklyn Food & Beverage', '',
  'https://attend.expowest.com/event/natural-products-expo-west-2026/exhibitor/RXhoaWJpdG9yXzIzNTgyMzE=', SN,
  'Title confirmed on the opened Expo West 2026 page for Brooklyn Food & Beverage, but that this parent owns Bruce Cost rests on a BevNET search summary, so the brand link is unverified. Same person as Moshi\'s marketing row.')
R('AB-131', 'backup', 'Keli', 'Roberson', 'Marketing Director, BCGA Concept Corp', '', 'https://supermarketnews.co.nz/global/global-innovation/bcga/', SN,
  'Stage 1 opened this 2017 article; it returned 429 today, so not re-confirmed. Nine years old; likely stale.')

# 58 OOSO Sparkling Tea
R('AB-174', 'founder', 'Oliver', 'Spring', 'CEO and Co-founder', 'https://www.linkedin.com/in/oliverhspring/',
  ORG + 'ooso-sparkling-tea/person/oliver-spring', OP,
  'The Org (updated 2026-10-14): CEO & Co-founder. Team page lists him as co-founder. LinkedIn URL from the Startup CPG podcast "Founder Feature: Ollie & Sophie Spring of OOSO Sparkling Tea" episode links (2025-10-10, public feed); LinkedIn not opened. Stage 1 had Sophia in the founder slot; swapped because she leads marketing.')
R('AB-174', 'marketing', 'Sophia', 'Racciatti', 'Co-founder (leads marketing)', 'https://www.linkedin.com/in/sophiaracciatti/',
  'https://drinkooso.com/pages/the-team', OP,
  'Team page: co-founder who has "masterminded everything from how to market OOSO". The podcast episode title calls her Sophie Spring; she may use either surname. LinkedIn URL from the same episode links; not opened.')

# 59 GoMacro
R('AB-117', 'founder', 'Jola', 'Sonkin', 'CEO and Co-founder', '', ORG + 'gomacro/person/jola-sonkin', OP,
  'The Org (updated 2026-08-30): "CEO | Co-Founder". Brand story page: Amelia Kirchoff began GoMacro with her daughter, Jola. Fills the stage-1 surname gap.')
R('AB-117', 'marketing', 'Dan', 'Hickle', 'SVP, Head of Marketing', '', ORG + 'gomacro/person/dan-hickle', OP,
  'The Org (updated 2026-01-18): since 2025.')
R('AB-117', 'backup', 'Amelia', 'Kirchoff', 'Co-founder', '', 'https://gomacro.com/pages/our-story', OP,
  'Brand story page: founder of the original MacroBar (2004).')
R('AB-117', 'backup', 'Joyce', 'Lin', 'Director of Marketing and Communications', '', ORG + 'gomacro/person/joyce-lin', OP,
  'The Org (updated 2026-08-31): since 2026.')

# 60 Goodie Girl
R('AB-083', 'founder', 'Shira', 'Berk', 'Founder and CEO', '', 'https://goodiegirl.com/pages/our-story', OP, 'Our Story page.')
NONE('AB-083', 'marketing', 'https://goodiegirl.com/pages/our-story',
     'One web search: none named; Nosh 2017 (search summary) says the founder keeps control of creative.')


def main():
    top = list(csv.DictReader(open(TOP, encoding='utf-8')))
    names = {r['row_id']: r['company'] for r in top}
    order = {r['row_id']: int(r['rank']) for r in top}
    seen = set(r['row_id'] for r in rows)
    missing = [rid for rid in names if rid not in seen]
    if missing:
        sys.exit('missing brands: %s' % missing)
    for r in rows:
        if r['row_id'] not in names:
            sys.exit('unknown row_id %s' % r['row_id'])
        r['company'] = names[r['row_id']]
    for rid in names:
        ranks = [r['contact_rank'] for r in rows if r['row_id'] == rid]
        if ranks.count('founder') != 1 or ranks.count('marketing') != 1:
            sys.exit('%s needs exactly one founder and one marketing row: %s' % (rid, ranks))
    rk = {'founder': 0, 'marketing': 1, 'backup': 2}
    rows.sort(key=lambda r: (order[r['row_id']], rk[r['contact_rank']]))
    for r in rows:
        assert r['confidence'] in (OP, SN, NA), r
        assert '@' not in ''.join(r.values()), r
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    # counts
    def found(r):
        return r['first_name'] != 'none found'
    c = {}
    for slot in ('founder', 'marketing', 'backup'):
        s = [r for r in rows if r['contact_rank'] == slot]
        c[slot] = dict(rows=len(s), found=sum(found(r) for r in s), none=sum(not found(r) for r in s),
                       opened=sum(r['confidence'] == OP for r in s), snippet=sum(r['confidence'] == SN for r in s),
                       linkedin=sum(bool(r['contact_linkedin_url']) for r in s),
                       last_unknown=sum(r['last_name'] == 'unknown' for r in s))
    print('rows', len(rows))
    for k, v in c.items():
        print(k, v)


if __name__ == '__main__':
    main()
