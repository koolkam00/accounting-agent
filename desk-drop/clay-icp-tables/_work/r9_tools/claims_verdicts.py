"""Review round 1 (R1-01): the human verdict on every brand the v2 claims scan flagged, with the quote and the
page it was read on (all opened 2026-10-24 by _build/scan_claims.py). Rule, applied to every brand alike:
  fail   - the brand's own selling copy (homepage, product page or catalog description, About, FAQ, ingredient or
           'why' page) says the product or its ingredients affect a body or mental function or a disease
           (digestion, gut, immunity, heart, blood sugar, cholesterol, inflammation, hormones, mood, calm, stress,
           focus, sleep, weight, metabolism, recovery, skin, bones, teeth), including a testimonial the brand
           publishes about a disease, or the site sells CBD products; brand-level, as for Spring & Mulberry
  review - implied or educational only: blog or 'learn' articles, product tags, 'energy' or 'no crash' wording,
           functional ingredients (adaptogens, mushrooms, L-theanine, valerian) with no claim seen, FDA-style
           disclaimers with no claim found, hemp lines; blocks outreach until the founder clears it
  clear  - not a product claim (Prop 65 warnings, founder stories, charity pages, 'no adaptogens', nutrient content)
Writes _work/claims_verdicts_2026-10-24.csv and appends sourced rows to _work/stage3_corrections.csv
(idempotent: rows it wrote before are replaced). Run: python3 -I clay-icp-tables/_work/r9_tools/claims_verdicts.py
"""
import csv, os
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
V = [
 # row_id, brand, verdict, url, quote
 ("AB-233", "Simply Gum", "fail", "https://www.simplygum.com/products/bubble-gum", "sweetened with xylitol to fight cavities and protect enamel while you chew"),
 ("AB-111", "Harken Sweets", "fail", "https://harkensweets.com/pages/faqs", "dates are high in fiber and antioxidants, with nutritional benefits that help improve gut health, prevent chronic disease, boost brain health; product page: 'Gut-healthy indulgence'"),
 ("AB-070", "Raaka Chocolate", "fail", "https://www.raakachocolate.com/products/functional-gift-bundle", "Reishi supports a calm mood, lion's mane keeps you sharp (functional line: seven adaptogenic herbs and 530mg of mushrooms)"),
 ("AB-249", "Häppy Candy", "fail", "https://eathappycandy.com/pages/faq", "prebiotic fiber, meaning it feeds your good gut bacteria and it also slows down glucose spikes"),
 ("AB-016", "Ella's Flats", "fail", "https://www.ellasflats.com/products/bestseller-variety-3-pack", "gut healthy, blood sugar stabilizing, balancing hormones; About page: seeds 'naturally help balance blood sugar'"),
 ("AB-239", "Hella Cocktail Co.", "fail", "https://hellacocktail.co/products/grapefruit-bitters-soda-buy-more-save-more", "can support healthy digestion by easing gas, bloating, and indigestion.*"),
 ("AB-073", "Seed + Mill", "fail", "https://www.seedandmill.com/pages/about-sesame", "Phytosterols are plant compounds known to help reduce cholesterol; Anti-Inflammatory; supporting skin elasticity"),
 ("AB-084", "Elements Truffles", "fail", "https://www.elementstruffles.com/products/veg-news-protein-launch", "Improves athletic performance, Accelerates post-workout recovery; elsewhere 'Immunity Boosting Chai Spice', ashwagandha 'known for its stress relieving properties'"),
 ("AB-034", "Reelie (formerly Artisan Tropic)", "fail", "https://www.reelie.com/products/sweet-plantain-chips", "nutrient-dense goodness that helps support gut health; cassava chips 'known for its anti-inflammatory benefits'"),
 ("AB-124", "Goodio", "fail", "https://goodiochocolate.com/products/calm-balanced-chocolate-49", "Promote balance and serenity ... carefully crafted to enhance your mood throughout the day (functional bars with ashwagandha, valerian, L-tryptophan)"),
 ("AB-090", "Maxine's Heavenly", "fail", "https://maxinesheavenly.com/pages/our-ingredients", "studies have consistently shown that oats can help reduce cholesterol, reduce the risk of developing high blood pressure"),
 ("AB-220", "Unhinged", "fail", "https://alwaysunhinged.com", "L-theanine ... Paired with caffeine, it smooths the curve, steady focus on the way up, no cliff on the way down"),
 ("AB-117", "GoMacro", "fail", "https://gomacro.com/pages/ingredient-glossary", "a good source of potassium, helping support heart health; raisins 'helping support digestive health'"),
 ("AB-104", "88 Acres", "fail", "https://88acres.com/pages/ingredients", "dark chocolate ... can help to lower blood pressure and reduce the risk of heart disease; cocoa butter 'nutrients that support the immune system'"),
 ("AB-311", "RIND Snacks", "fail", "https://www.rindsnacks.com/products/coconut-crisps", "essential minerals ... to enhance your immune system"),
 ("AB-023", "SuperSeedz", "fail", "https://www.superseedz.com/products/in-the-raw", "Supports heart health, hormone balance, and immune system"),
 ("AB-244", "Kelly's Four Plus Granola", "fail", "https://www.kellysfourplus.com/pages/ingredients", "help reduce the absorption of cholesterol ... This can help reduce risks associated with diabetes"),
 ("AB-042", "Terranean", "fail", "https://terraneanherbs.com/products/sumac", "even regulates blood sugar. It lowers inflammation and can reduce cholesterol"),
 ("AB-011", "Jöey Nordic Seed Crisps", "fail", "https://joeynordicseedcrisps.com/pages/our-7-organic-super-seeds", "these seeds help boost immunity and promote better sleep quality; sunflower seeds 'support heart health'"),
 ("AB-267", "Heartland NY Popcorn", "fail", "https://heartlandnystore.com/products/deer-soul-pine-needle-tea", "the brand's own store sells teas and herbal products with structure/function wording and the FDA disclaimer ('This product is not intended to diagnose, treat, cure, or prevent any disease')"),
 ("AB-271", "Upstate Stock (Birch Sap Seltzer)", "fail", "https://www.upstatestock.com/products/original-100-pute-ny-organic-birch-sap-seltzer", "manganese, along with potassium, calcium, and magnesium, which support bone health and cellular function; the store also lists CBD and THC products"),
 ("AB-184", "nero black coffee", "fail", "https://drinknero.com", "it delivers smooth caffeine power to keep you focused, active, and energized throughout your day"),
 ("AB-066", "Rip Van", "fail", "https://www.ripvan.com/pages/faqs", "feeding and promoting the growth of healthy gut bacteria, supporting a balanced digestive system from the inside out"),
 ("AB-116", "Bobo's", "fail", "https://eatbobos.com/pages/about-us-our-ingredients-1", "Whole grains can help you achieve healthier blood pressure, and contain beneficial bacteria to improve gut health"),
 ("AB-026", "Righteous Felon", "fail", "https://www.righteousfelon.com/products/wild-nature-variety-3-pack", "Supports Immunity, Digestion, and a Smooth Skin & Coat (the brand's jerky treats line)"),
 ("AB-234", "Kim's Magic Pop", "fail", "https://kimsmagicpop.com/products/kims-deli-pop-gluten-free", "Brown Rice (helps improve weight loss) Red Rice (strenghtening metabolism, helps in weight management)"),
 ("AB-261", "Top Seedz", "fail", "https://topseedz.com/pages/why-seeds", "With a high fiber content, seeds are often considered a probiotic and can support healthy digestion"),
 ("AB-044", "Quinn Snacks", "fail", "https://quinnsnacks.com/pages/ingredients", "sorghum flour ... aids digestion while making you feel fuller, longer; sunflower oil 'anti-inflammatory'"),
 ("AB-150", "Harney & Sons (bottled iced tea and juice drinks)", "fail", "https://www.harney.com/products/the-brothers-apothecary", "this unique combination supports joint health, immunity, healthy digestion (the brand's own site sells CBD and hemp shots with the FDA disclaimer)"),
 ("AB-162", "COAQUA", "fail", "https://www.drinkcoaqua.com/pages/about-us", "From boosting hydration to aiding digestion and even improving heart health"),
 ("AB-191", "Pop & Bottle", "fail", "https://www.popandbottle.com/products/wholesale-matcha-oat-milk-latte", "boosted with functional mushrooms to help you reduce your stress levels and support your immune system"),
 ("AB-050", "DANG Foods", "fail", "https://dangfoods.com/pages/why-keto", "we experience improved mental focus, increased energy, reduced inflammation, weight loss, better sleep, and improved mood"),
 ("AB-156", "Slate Milk", "fail", "https://slatemilk.com/pages/our-story", "Our products aid in muscle recovery, strength-building"),
 ("AB-212", "North Fork Potato Chips", "fail", "https://northforkchips.com", "This Heart-Healthy oil is also proven to lower cholesterol levels"),
 ("AB-147", "Mingle Mocktails", "fail", "https://www.minglemocktails.com", "Functional drinks ... Supports calm, focus, and overall wellness"),
 ("AB-297", "DM Snacks (Damn, Man Snacks)", "fail", "https://www.dmsnacks.com/products/cowboy-starter-kit", "Packed with premium beef and roasted nuts to keep you full and focused"),
 ("AB-188", "Loom", "fail", "https://www.drinkloom.com", "a testimonial the brand publishes on its homepage: 'helped my mother specifically with her diabetes management'"),
 ("AB-038", "Gheelish", "fail", "https://www.gheelish.com/pages/why-ghee", "butyrate, a short-chain fatty acid linked to gut health"),
 ("AB-115", "Mast", "fail", "https://mastmarket.com/products/new-york-shuk-harissa-with-preserved-lemon-10oz", "HEALTH BENEFITS: Chili Peppers have Capsaicin which are known to lower blood pressure and can help boost metabolism (a product the brand's own store sells)"),
 ("AB-242", "Baabu Foods", "fail", "https://baabufoods.com/products/chai-biscuits", "fennel seeds support digestion, boost antioxidants, and promote cardiovascular health"),
 ("AB-021", "Tierra Farm", "fail", "https://www.tierrafarm.com/products/organic-br-ayurvedic-immunity-tea-infusion", "Immunity Tea aims to support your immune system and balance your energy; 'Slim Tea aims to curb cravings and promote weight management'"),
 ("AB-109", "Kate's Real Food", "fail", "https://katesrealfood.com/products/coconut-truffle-protein-bar", "15g of plant-based protein that keeps you full and focused without the sugar crash"),
 ("AB-067", "Rule Breaker Snacks", "fail", "https://www.rulebreakersnacks.com/pages/faq", "Prebiotics are naturally occurring compounds in food that help establish and maintain beneficial gut microorganisms"),
 # review: blocking until the founder clears
 ("AB-236", "Goody's Granola", "review", "https://goodysgranola.nyc/blogs/announcements/beyond-the-crunch-why-your-breakfast-choice-is-your-secret-productivity-hack", "blog post: most granolas 'spike your blood sugar and drop you off a cliff an hour later' (blog copy, not pack copy)"),
 ("AB-004", "Daily Crunch", "review", "https://dailycrunchsnacks.com/products/spiced-chai-pear-limited-time-only", "the brand tags its products 'gut healthy' in its own catalog; if that wording is on the pack or a page, it fails"),
 ("AB-222", "Shinzo Matcha", "review", "https://shinzomatcha.com/pages/learn", "a 'learn' hub with articles 'Matcha and Gut Health', 'Matcha for Focus', 'Matcha and Stress', 'Matcha for Sleep'"),
 ("AB-001", "BjornQorn", "review", "https://bjornqorn.com/products/bjornqorn-gift-box-2025", "a gift-box popcorn 'powered by reishi mushrooms' (functional ingredient; no claim seen)"),
 ("AB-072", "Blue Stripes", "review", "https://www.bluestripes.com", "THEOBROMINE Long lasting natural energy; ELECTROLYTES (energy wording)"),
 ("AB-174", "OOSO Sparkling Tea", "review", "https://drinkooso.com", "L-Theanine listed as a feature ('Organic Teas Essential Vitamins L-Theanine'); no claim seen"),
 ("AB-182", "OOZ Birch Water", "review", "https://oozwater.com", "200 bioactive nutrients, light electrolytes ... DEEPER HYDRATION (implied effect)"),
 ("AB-298", "The Maple Brothers", "review", "https://themaplebrothers.com", "Whole grains and real fruit for steady, no-crash energy (energy wording)"),
 ("AB-133", "Halmi", "review", "https://drinkhalmi.com/products/cinnamon-ginger-jujube-persimmon", "inspired by SuJeongGwa, a spiced punch 'brewed for generations to aid digestion' (traditional-use wording)"),
 ("AB-213", "Brooklyn Biltong", "review", "https://www.brooklynbiltong.com", "the site footer carries the FDA disclaimer ('not intended to diagnose, treat, cure, or prevent any disease'); no claim found on the pages read"),
 ("AB-269", "Skinny Earth", "review", "https://skinnyearth.com/products/gluten-free-7-plus-super-food-oatmeal", "an FDA-style disclaimer on a product page ('Statements regarding diet and Dietary Supplements have not been evaluated'); no claim found"),
 ("AB-288", "True North Granola", "review", "https://truenorthgranola.com/pages/faq", "FAQ answers 'Is your granola blood sugar friendly?', 'good for gut health?', 'suitable for GLP-1 users' (framed as customer preference)"),
 ("AB-012", "Vaca Chips", "review", "https://www.vacachips.com/blogs/news/why-beef-tallow-is-the-superfat-your-diet-has-been-missing", "blog posts: tallow 'linked to supporting metabolism', vitamins for 'immune support' (blog copy)"),
 ("AB-176", "Saint James Iced Tea", "review", "https://saintjamesicedtea.com/products/strawberry-tangerine-yerba-mate", "caffeine, theobromine, and polyphenols delivers a steady, no crash lift (energy wording)"),
 ("AB-043", "Unique Snacks (Unique Pretzels)", "review", "https://www.uniquesnacks.com/products/small-diabetic-friendly-gift-basket", "a 'Diabetic Friendly Gift Basket' (suitability wording tied to a disease)"),
 ("AB-178", "Rockaway Soda", "review", "https://drinkrockaway.com/products/lime-mint", "a soda listing ashwagandha and valerian (functional ingredients; check the pack for a Supplement Facts panel or claims)"),
 ("AB-165", "Elmhurst 1925", "review", "https://elmhurst1925.com/pages/faq", "the FAQ says its hemp products 'only contain trace amounts of THC': confirm the SKU offered is not a hemp line"),
 ("AB-061", "Belle's Gourmet Popcorn", "review", "https://bellespopcorn.com", "a coming 'Beauty + Glow' popcorn with collagen peptides, biotin and vitamin E (implied effect)"),
 ("AB-110", "Thunderbird", "review", "https://www.thunderbirdbar.com", "'Energy Bar' line and maca (energy wording, functional ingredient)"),
 ("AB-183", "Taply", "review", "https://drinktaply.com", "'Treelicious Hydration Electrolytes, Antioxidants & Minerals'; a customer review on the homepage mentions 'electrolytes and prebiotics'"),
]
CLEAR = ["AB-210 Treat House (charity story)", "AB-096 Magic Spoon (net-carb explanation)", "AB-062 Marimix (founder story)",
         "AB-159 Hoplark (customer story)", "AB-057 Every Body Eat (Prop 65 note)", "AB-041 BEEST Snacks (founder story)",
         "AB-291 Bixby Chocolate (founder story)", "AB-307 Milene Jardine (sponsorship)", "AB-160 Nixie (charity)",
         "AB-046 Simply 7 (FAQ defers to a doctor)", "AB-028 Saffron Road (animal welfare)", "AB-161 Death Wish Coffee (a jersey)",
         "AB-069 Sweet Loren's (founder story)", "AB-045 The Good Crisp Company (charity)", "AB-010 Mamame (protein digestibility of tempeh)",
         "AB-105 Unreal (inulin as an ingredient)", "AB-118 Good Word Foods (collagen as an ingredient)", "AB-047 Go Raw (another brand's item in a promo box)",
         "AB-169 Banagua, AB-157 JUST Water, AB-179 Ample Hydration, AB-192 Sunbear, AB-158 Vita Coco (electrolyte content)",
         "AB-063 The Hermit, AB-252 Whey Water, AB-029 Vermont Smoke & Cure (collagen content or casing)",
         "AB-164 Luba Libations, AB-202 Spirited Zero Proof, AB-196 Tilden ('no adaptogens')", "AB-205 Kimino (theanine as flavor)"]

def main():
    rows = [dict(row_id=a, brand=b, verdict=v, url=u, quote=q, opened="2026-10-24") for a, b, v, u, q in V]
    with open(os.path.join(W, 'claims_verdicts_2026-10-24.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        for c in CLEAR:
            w.writerow(dict(row_id='', brand=c, verdict='clear', url='', quote='not a product claim', opened='2026-10-24'))
    p = os.path.join(W, 'stage3_corrections.csv')
    cur = list(csv.DictReader(open(p, encoding='utf-8')))
    cur = [r for r in cur if 'Claims scan v2' not in r['reason']]
    for r in rows:
        if r['verdict'] == 'fail':
            cur.append(dict(table='brands', key=r['brand'], field='excluded', new_value='Y', source_url=r['url'],
                            source_date='2026-10-24', reason='Claims scan v2 2026-10-24 (review round 1, R1-01)'))
            cur.append(dict(table='brands', key=r['brand'], field='exclusion_reason',
                            new_value=f"explicit health claim in the brand's own copy (opened 2026-10-24): '{r['quote']}' ({r['url']})",
                            source_url=r['url'], source_date='2026-10-24', reason='Claims scan v2 2026-10-24 (review round 1, R1-01)'))
        else:
            cur.append(dict(table='brands', key=r['brand'], field='founder_review_reason',
                            new_value=f"(append) Claims review 2026-10-24: {r['quote']} ({r['url']}); decide before outreach, and the tent card must not repeat it",
                            source_url=r['url'], source_date='2026-10-24', reason='Claims scan v2 2026-10-24 (review round 1, R1-01)'))
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['table', 'key', 'field', 'new_value', 'source_url', 'source_date', 'reason'])
        w.writeheader(); w.writerows(cur)
    print(sum(1 for r in rows if r['verdict'] == 'fail'), 'fail,', sum(1 for r in rows if r['verdict'] == 'review'), 'review')

if __name__ == '__main__':
    main()
