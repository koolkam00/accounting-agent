# Short links and QR codes

Two short links per office per campaign, made by formulas on the tracker's `links` tab and by `tools/make_links.py`. The QR printed on the tent card is one of them; the Slack or email post uses the other. A QR scan is counted only from the card's link, so a Slack link preview or a click in the post is never called a scan (the ladder's "scanned" stays a QR scan). `make_links.py` makes links only for offices that said yes to that brand (approvals close at T-10); the `links` tab also lists a declined office's pair, which is never imported or printed.

## The scheme

| Part | Rule | Example (campaign CMP-003, office O-007) |
| --- | --- | --- |
| Card code | `<campaign_id>.<office_id>`. Nothing about a person. | `CMP-003.O-007` |
| QR link (on the card) | `https://<short_link_domain>/c<campaign number>-o<office number>-q` | `https://go.[DOMAIN]/c003-o007-q` |
| Post link (Slack or email) | the same with `-p` | `https://go.[DOMAIN]/c003-o007-p` |
| Destination | the campaign's survey pre-filled link with `CARDCODE` replaced by the card code, plus labels | `https://docs.google.com/forms/d/e/<FORM ID>/viewform?usp=pp_url&entry.<QUESTION ID>=CMP-003.O-007&utm_source=office-pantry&utm_medium=qr&utm_campaign=cmp-003&utm_content=o-007` |
| QR image | the QR link, error correction M, made offline with segno; the tent card draws the same link itself | `qr/c003-o007-q.png` |

Rules:
- **No company name in a back-half, a tag or a label** (`utm_source=office-pantry`, never the name). `make_links.py` refuses a back-half that contains it. The domain is a config value (`short_link_domain`): after a rename you change one cell and print new cards; printed cards keep the old domain.
- SAMPLE links start with `SAMPLE-` and use the reserved `go.example.com`, so a test card can never point at a real survey.
- The `utm_` labels are inert on a Google Form (it ignores them). They make each destination readable in the link tool's list and carry over if the survey ever moves to a web page that reads them. The brand's own landing link, on the survey's thank-you screen, carries `utm_source=office-pantry&utm_medium=survey&utm_campaign=<campaign>` so the brand's analytics can see visits from the campaign (forms/survey-form.md, Part 2, step 3).

## Worked example, from the SAMPLE dry run

From `dry-run/zero/links/links-SAMPLE-DRP-001.csv` (campaign zero, SAMPLE Brightside at SAMPLE office 001):

```
campaign_id      SAMPLE-CMP-001
office_id        SAMPLE-O-001
link_type        qr
slug             SAMPLE-c001-o001-q
short_url        https://go.example.com/SAMPLE-c001-o001-q
card_code        SAMPLE-CMP-001.SAMPLE-O-001
destination_url  https://docs.google.com/forms/d/e/SAMPLE-CMP-001-FORM/viewform?usp=pp_url&entry.1000001=SAMPLE-CMP-001.SAMPLE-O-001&utm_source=office-pantry&utm_medium=qr&utm_campaign=sample-cmp-001&utm_content=sample-o-001
```

What happens when an employee scans it: the phone opens `go.example.com/SAMPLE-c001-o001-q`; the link tool redirects to the destination; the form opens with "Card code (filled in for you): SAMPLE-CMP-001.SAMPLE-O-001" and the question "Did you try SAMPLE Brightside?"; the answer lands in the tracker's `SAMPLE-CMP-001` tab with that code in column B; the tracker counts it for office A because the code matches and the time is inside the window.

How scans are counted: you read each link's total in the link tool and log it on the `scans` tab. In the dry run: baseline 1 (your own test scan, read at T-1), mid 7 at T+2, close 15 at T+4, so the report shows **14 QR scans** for office A (close minus baseline). Readings after T+4 are logged as `late` and never reach the report.

How every QR was proved right in the dry runs: `tools/make_kit.py` rasterizes every printed tent card, decodes both faces' QR codes and checks each against its office and campaign (`dry-run/*/kit/qr-check.txt`: all OK); `tests/test_links.py` then follows every short link through a local copy of the redirects and checks that it lands on that campaign's form with that office's card code.

## Which link tool (prices opened 2026-10-24)

| Tool | Free plan | Fits? |
| --- | --- | --- |
| **Short.io** (default) | 1,000 branded links for the account's lifetime, 50,000 tracked clicks a month, up to 5 custom domains, unlimited redirects (short.io/pricing). A drop uses 2 links x offices x brands: 20 for campaign zero, 60 for a 3-brand, 10-office drop, so about 260 in the first six months. Destinations can be changed after printing (the pricing page says so; whether the free table includes it is unverified, founder to confirm) | Yes, $0 |
| Bitly | 5 links and 2 QR codes a month, no redirect editing; Core $10 a month billed yearly ($120) (bitly.com/pages/pricing) | No on free. Core only with your written yes |
| Your own domain on Cloudflare Pages | `make_links.py` writes `redirects-<drop>.txt` in Cloudflare's `_redirects` format; free and unlimited, but it gives **no click counts**, so "scanned" would be unmeasured | Fallback only: QR links would work, scans would not be counted |
| Dub.co, TinyURL | Dub's pricing page showed no free plan (cheapest $90 a month); TinyURL's page did not load (unverified) | No |

Privacy (legal pack file 13, D11): the link tool sees technical details of each click under its own policy. Use only its totals, read from its dashboard; never export or keep per-click logs. The tracker stores totals only.

## Steps

**Once [FOUNDER LOGIN: Short.io, and your DNS at the registrar or Cloudflare]:**
1. Sign up at short.io (free plan). Stop if it asks for a card: the free plan should not.
2. Add the domain `go.[DOMAIN]` as a custom domain and create the DNS record Short.io shows you (a CNAME) where your domain's DNS lives (Cloudflare, if the website workstream's steps were followed). Wait until Short.io shows it as connected.
3. Put `go.[DOMAIN]` into the tracker's config tab, `short_link_domain`.
4. Domain age: some office firewalls block domains registered in the last 32 days (runbook step 10 has the source). `go.[DOMAIN]` carries the age of `[DOMAIN]`, so `[DOMAIN]` must be registered by Mon 2026-12-07 for the Tue 2027-01-12 drop.

**Each drop, at T-4, after every campaign's survey form exists [FOUNDER LOGIN: Short.io]:**
1. Download the tracker (File > Download > .xlsx) and run `python3 tools/make_links.py tracker.xlsx DRP-002 out/links`.
2. In Short.io: your domain > Import links (CSV), choose `out/links/shortio-import-DRP-002.csv`, map `path` to the short link path and `original_url` to the destination (column names at import are unverified, founder to confirm; Short.io's blog describes the import as "upload the file and map its columns").
3. Open three of them on your phone. Each must open the right brand's survey with the right card code.
4. Print the cards (`tools/make_kit.py`); `qr-check.txt` must say OK on every line.
5. T-1: after your test scans, read every link's total and log it on `scans` as `baseline`. T+2 `mid`, T+4 end of day `close`.

**If Short.io stops being free or fails on drop day:** the cards cannot change, but a destination can: in Short.io, edit the link. If the tool itself is gone, put the `redirects-<drop>.txt` lines into the website's `_redirects` file on Cloudflare Pages and point `go.[DOMAIN]` at the site (the QR links keep working; scans are then not counted, and the report must say so).
