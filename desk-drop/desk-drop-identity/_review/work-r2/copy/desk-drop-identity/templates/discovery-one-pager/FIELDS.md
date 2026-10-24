# Discovery one-pager: fields

Template: `templates/discovery-one-pager/discovery-one-pager.html` (v1.1, 2026-10-24). One Letter page: the idea in five sentences, without selling (plan.md Phase 0, week 1).

| Key | Rule |
| --- | --- |
| `meta` | Small header line. Default "Research stage". |
| `title` | A phrase, not a sentence (warns if it ends like one). |
| `s1` to `s5` | Exactly one sentence each (error otherwise), so the page explains the idea in exactly five. Warns on selling words: a price, "offer", "discount", "limited", "exclusive", "sign up", "founding", "book your", "spots left", "special", "guarantee". `{BRAND_NAME}` prints the name from `brand.json`. |

Samples: `samples/DEFAULT.json` (the shipped five sentences), `samples/SAMPLE-must-warn.json` (proves the two checks fire).

```bash
node render/render.js discovery-one-pager data.json out.pdf --final
```
