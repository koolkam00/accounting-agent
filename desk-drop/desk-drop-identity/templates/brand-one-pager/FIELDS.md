# Brand one-pager: fields

Template: `templates/brand-one-pager/brand-one-pager.html` (v1.1, 2026-10-24). One Letter page. Contents from plan.md: the positioning line, "What brands buy", the price table (from `system/dd-offer.js`), the measurement ladder with how each rung is counted, the seven-point qualification checklist, what the brand supplies, exclusions, no sales guarantee.

| Key | Rule |
| --- | --- |
| `prepared_for` | Optional brand name, printed "Prepared for ..." in the header. |
| `roster_status` | Required. Only what is true today, from the signed offices (count, combined Tuesday headcount, next drop date). Starts as a `[ROSTER STATUS: ...]` slot so it can never go out unfilled. |
| `headline` | The positioning line, verbatim from the brief. |
| `lead`, `includes`, `ladder_note`, `fit`, `excluded`, `send`, `never`, `next` | Copy, editable. One list item per line. `fit` must have seven lines (warns otherwise). Checked for claims words. |

Fixed (not fields): the price table and the ladder rungs (names fixed by CONTRACTS section 2).

```bash
node render/render.js brand-one-pager data.json out.pdf --final
```
