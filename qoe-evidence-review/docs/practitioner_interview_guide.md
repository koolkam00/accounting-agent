# QoE Evidence Review: practitioner interview guide

This guide is for transaction-advisory professionals: associates, seniors and managers, current or former. It has two parts, run in this order:

- **Part 1: workflow discovery (30 minutes).** This happens *before* the participant has seen the tool. The aim is to learn how add-back review actually works and what the participant would need before trusting help with it.
- **Part 2: tool walkthrough (15 minutes).** A scripted walkthrough of the Streamlit app with observation prompts.

After each interview, fill in the one-page synthesis (the end of this guide) within 24 hours.

> **If the person is also a benchmark participant** (`benchmark_protocol.md`), run Part 1 before their session 0 and Part 2 only **after** their last scored session. Part 2 uses the Meridian package (D1). Walking a participant through D1 before they are scored on it contaminates the benchmark.

---

## Confidentiality (read this aloud before starting)

> "Everything we look at today is synthetic. Please don't tell me anything that could identify a client, a target, a deal or a counterparty: no names, no deal values, no sector-plus-geography combinations that give it away. If one slips out, I won't write it down. I'm interested in how the work is done, not in whom it was done for. If your firm has rules about taking part in research like this, those rules come first, and it's fine to skip any question. I'd like to record audio so I can take accurate notes. The recording stays off the project repository and is deleted once my notes are written up. Is that OK?"

**Ground rules for the interviewer:**

- **No client data, ever.** Use synthetic packages only. Real engagement data can be used only with written authorisation from the data owner (the client) *and* the practitioner's firm. Even then, it is outside the scope of this guide and of the benchmark.
- **Don't ask for firm documents.** That includes methodology manuals, databook templates and review checklists. Ask the participant to *describe* them in general terms.
- **Anonymise as you take notes.** The participant ID is `I01`, `I02` and so on, or their `P0n` ID if they are also a benchmark participant. The firm type is bucketed as Big-4, national, regional/boutique, or in-house/PE.
- **Where recordings live.** Store recordings outside the repo, and delete them after the synthesis is written. Only the anonymised synthesis goes into `reports/interviews/`.

---

## Interview technique

- **Ask about the last real instance**, not about hypotheticals. "Walk me through the last add-back schedule you reviewed" gets you what happened. "How would you review add-backs?" gets you what the manual says.
- **Don't pitch, don't describe the tool, don't lead.** Before Part 2, don't mention AI, evidence links, flags or automation unless the participant brings them up.
- **Follow the time and the pain.** When they mention a step, ask how long it took and what made it slow.
- **Capture verbatims.** Put exact phrases in quotes in your notes, especially about trust and refusal. These are the most useful lines in the synthesis.
- **Silence is fine.** Count to five before offering a follow-up.

---

## Part 1: workflow discovery (30 minutes)

| Time | Section |
| --- | --- |
| 0:00–0:03 | Confidentiality, consent, purpose |
| 0:03–0:06 | Background |
| 0:06–0:11 | Where add-back review takes time |
| 0:11–0:16 | Support standards by adjustment type |
| 0:16–0:20 | Documenting conclusions and open items |
| 0:20–0:23 | Trust and what they won't delegate |
| 0:23–0:27 | Tools, templates, data-room realities |
| 0:27–0:30 | Measuring success, wrap-up |

### 0:00–0:03: Purpose

> "I'm trying to understand how management's EBITDA adjustments get reviewed in a QoE: where the hours go, what evidence you insist on, and what you'd never hand to a tool or a junior. There are no right answers, and I'm not assessing you."

### 0:03–0:06: Background

1. What's your current or most recent role in transaction services, and roughly how many years have you done QoE work?
2. What sectors and deal sizes do you usually see? Buckets are fine.
3. On a typical QoE, who reviews management's adjustments: associate, senior, manager? Who signs off?

### 0:06–0:11: Where add-back review takes time

4. "Think of the last management adjusted-EBITDA schedule you worked on. Walk me through what you did, from receiving the schedule to having a view on each adjustment."
   - *Probe:* What did you do first: the GL, the documents, or management?
   - *Probe:* How long did the add-back work take in total, and per adjustment? Which adjustment took the longest, and why?
   - *Probe:* How much of that was **getting data into shape** (GL exports, pivots, mapping, tying the GL to the P&L) versus **forming a view**?
5. Which part of that work would you most like never to do again?
6. Where does the budget usually blow up? Probe for GL problems, waiting on management, back-and-forth on support, and manager review comments.

### 0:11–0:16: Support standards by adjustment type

7. "For each of these, what's the minimum support you'd need before carrying the adjustment, and what's the red flag that makes you push back?" Go through the list quickly, spending time only where they have strong views.

| Adjustment type | Minimum support they insist on | Red flags they look for |
| --- | --- | --- |
| Litigation / legal fees | | |
| Severance | | |
| Owner compensation normalisation | | |
| Owner personal / discretionary expenses | | |
| Transaction-related professional fees | | |
| "One-time" projects (IT, implementation) | | |
| Casualty loss / insurance | | |
| Out-of-period items / true-ups | | |
| Relocation / facility moves | | |
| Inventory write-offs | | |
| Bad debt / customer bankruptcy | | |
| Pro forma / run-rate savings | | |

   - *Probe:* When is a GL detail listing enough, and when do you need the invoice? When do you need the contract or engagement letter?
   - *Probe:* How do you test "non-recurring"? How many prior periods do you look back?
   - *Probe:* How do you check whether two adjustments count the same cost twice? Whether management left the recovery in? Whether the cost is already below EBITDA?

### 0:16–0:20: Documenting conclusions and open items

8. How do you document your conclusion on an adjustment? Ask them to describe the support schedule: columns, tickmarks, how evidence is referenced, and how facts are separated from your own view.
9. How do open items and questions for management get tracked, and how do the answers get back into the workpaper?
10. What do manager or director review notes on add-back work typically say? What do they send back most often?

### 0:20–0:23: Trust and what they won't delegate

11. "Suppose someone, or something, hands you a finished support schedule for an adjustment. What would you check before you'd put your name on it?"
    - *Probe:* What would make you trust it more: links to GL rows, quotes from documents, reperforming a sample, a track record?
    - *Probe:* What single thing would make you stop trusting it altogether?
12. Which parts of add-back review would you refuse to delegate, to a junior or to a tool? Why?
13. Have you used a general AI assistant on this kind of work, or been told you can't? What happened?

### 0:23–0:27: Tools, templates, data-room realities

14. What tools and templates do you use today: Excel templates, Power Query, Alteryx, IDEA, firm-proprietary databook tools? What do they do well and badly?
15. Data-room realities:
    - Which GL export formats do you actually receive (QuickBooks, NetSuite, Xero, Sage Intacct, Dynamics, others)? How often do you get a full GL rather than a TB and P&L only?
    - How often are months missing, or does the GL not tie to the P&L or TB? What do you do then?
    - How much of the support comes as scanned PDFs, emails or spreadsheets? How often is it simply missing?
    - Have you dealt with multiple entities, a mid-period system conversion, or top-side entries outside the GL?

### 0:27–0:30: Measuring success, wrap-up

16. "If a tool claimed to help with add-back review, how would you judge whether it worked on your next engagement?"
    - *Probe:* How much time would it need to save to be worth learning? What error rate is acceptable, and which errors aren't acceptable at any rate?
    - *Probe:* How many engagements would it take before you trusted it?
17. Is there anything I should have asked but didn't?
18. May I follow up with one or two clarifying questions by email?

---

## Part 2: tool walkthrough (15 minutes)

**Setup (before the participant joins):**

- Generate and run Meridian (D1) in a **scratch** workpaper folder, so the walkthrough's decisions don't go into a review log that feeds evals.
- Start the app with `uv run streamlit run qoe/ui.py`.
- Clear the review log and show the adjustment list.
- Have Excel running.

**Rules for the interviewer:**

- Give tasks, not tours. Ask them to think aloud.
- Don't help unless they have been stuck for more than 60 seconds. Log every assist.
- Note the **first click** for every task.

| Time | Task you give | What to observe and record |
| --- | --- | --- |
| 0:00–0:02 | "This is a synthetic QoE package with fourteen management adjustments. The tool has already run. We're testing the tool, not you. Please think aloud." | — |
| 0:02–0:04 | "Which adjustment would you look at first, and why?" | Do they go for the largest amount, the CRITICAL flags, or the schedule order? Do they read the treatment colours? |
| 0:04–0:08 | "Take M-01, the legal fees. Would you carry management's number? Show me why or why not." | Do they open the GL links, the documents, or the quote? Do they **open the source document to check a quote**? Do they notice the two matters and the FY2024 comparable? Do they read *Documented facts* and *Judgment questions* differently? Note where they hesitate and what words they use for any doubt. |
| 0:08–0:10 | "Record your decision." | Do they understand treatment vs amounts vs correction type? Do they override? What rationale do they type? Do they look for a field that isn't there? |
| 0:10–0:12 | "Find anything else here that you'd raise with your manager." | Unprompted discoveries (M-08 overlap, M-09 recovery, data-quality items). Are they drawn to flags or to amounts? |
| 0:12–0:14 | "Export it and show me where this would go in your databook." | Reactions to the workbook: formulas vs values, the blue/black convention, tickmarks, support sheets, and the Open Questions sheet. Would they rebuild it? |
| 0:14–0:15 | "What would you check by hand before trusting this? What's missing? What would you never let it do?" | Verbatims. |

**Observation prompts**, to note throughout:

- Every time they leave the tool to check a source file or the GL, what did they check, and did it agree?
- Moments of distrust ("hm", "that can't be right", or re-adding numbers themselves). What triggered each one?
- Terminology they misread: flag codes, "traced" vs "documented" vs "proposed", correction types.
- Features they reach for that don't exist.
- Whether they treat the tool's proposal as a starting point or as an answer. Automation bias shows up as fast agreement with no source checks.

---

## One-page synthesis template

Copy this for each interview and keep it to one page. Save it as `reports/interviews/<id>.md`, with no names and no client details.

```markdown
# Interview synthesis: <I0n / P0n>   Date: <YYYY-MM-DD>   Interviewer: <initials>

**Profile:** <title bucket> · <years> yrs · <firm type bucket> · <sectors> · AI-use: <none/occasional/daily>

## Where the time goes (top 3)
1. <step> — <how long> — "<verbatim>"
2.
3.
Prep vs review split, as they describe it: <e.g. "half the time is getting the GL usable">

## Support standards they insist on
| Type | Minimum support | Red flag |
| --- | --- | --- |
| | | |

## How they document
Support-schedule layout: <…>  Open-items tracking: <…>  Most common review note: "<…>"

## Trust
Would check before signing: <…>
Would lose trust instantly if: "<verbatim>"
Won't delegate: <…>

## Tools and data-room realities
Tools/templates today: <…>  GL formats seen: <…>
Missing periods / GL-P&L breaks / scans: <how often, what they do>

## How they'd measure success
<time saved threshold, acceptable errors, engagements to trust>

## Walkthrough observations (Part 2)
First click (task 2): <…>   M-01 conclusion: <carry / revise / reject + amount>, time: <mm:ss>
Checked sources? <yes/no — which>   Assists given: <n — what>
Confusions: <terms/UI>   Missing features they reached for: <…>
Best verbatim: "<…>"

## Contradicts our assumptions
<what surprised us>

## Implications
Keep: <…>  Change: <…>  Drop: <…>  Follow-up: <…>
```
