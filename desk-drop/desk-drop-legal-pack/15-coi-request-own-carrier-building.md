**Draft for attorney review. Not legal advice.**

# 15 · Certificate of insurance request to our own carrier: a building as additional insured

Version 0.2 · 2026-10-24

**What it is for.** Some Manhattan buildings will not let a vendor deliver until they hold a certificate of insurance naming the building, and often its managing agent, as additional insured (plan, legal table row "General liability insurance"; risk table "Building access and insurance demands"). This file gets the building's exact requirements from the office, asks our carrier or broker for the certificate, and checks it before drop day.

**When it is used.** Only after our general liability policy is bound (plan: bind before the first product arrives; target $1M per occurrence and $2M aggregate, a plan figure, not a quote). Start the moment an office's intake says `coi_required = yes` or `unsure`, and no later than ten business days before that office's first drop. The plan puts certificate-only buildings "on the list for later", so for campaign zero this is used only if a signed office turns out to need it.

**How to fill it in.** Replace the brackets. Copy the building's names and wording exactly as the building gives them; buildings check the names. Our legal name appears once, in the request block, and must match the filed Articles of Organization.

---

## Step 1 · Email to the pantry owner, to get the building's requirements

> **Subject:** Your building's insurance certificate for our delivery
>
> Hi [NAME], you mentioned your building may need a certificate of insurance before we deliver. Could you forward me your building's vendor or certificate requirements? Building management may have a sheet for this. What I need:
>
> 1. The exact names to list as additional insured (usually the building owner and the managing agent)
> 2. Who the certificate holder should be, with the address
> 3. The insurance limits and any wording they require
> 4. Where to send it and how far ahead of the delivery
> 5. Anything else they ask vendors for (for example, workers' compensation or auto insurance)
>
> If it's easier, a contact in building management works too, and I'll ask them directly.
>
> Thanks, [FOUNDER NAME]

Record the answer in the office row (`coi_required`, notes) and keep the building's sheet in the office folder.

## Step 2 · Compare the requirements with our policy before asking

| Building asks for | What to do |
| --- | --- |
| General liability limits at or below our policy's limits | Go to Step 3 |
| Limits above ours, or an umbrella or excess policy | Stop. We cannot meet it without buying more coverage. Tell the office, ask whether the office can receive at another point the building allows, or defer this office. Do not buy coverage without the founder's written yes and a quote |
| Owner and managing agent "as additional insureds" | Normal. Go to Step 3 |
| "Primary and non-contributory" or "waiver of subrogation" | Ask the carrier in Step 3 whether our policy already includes these or needs an endorsement, and at what cost. Stop at any cost and decide |
| Workers' compensation | We have no employees, so we carry no workers' compensation policy. New York's CE-200 exemption certificate can be used only with a government entity, so it is not an answer to a private building. Ask the building whether a signed statement that the company has no employees is acceptable (template below) |
| Auto liability | Relevant only if we drive a vehicle to its loading dock. Ask the carrier whether our policy has hired and non-owned auto coverage and whether it can appear on the certificate |

## Step 3 · Request to our carrier or broker

If the carrier's online portal lets you issue certificates yourself, enter the same facts there and still run the Step 4 check.

> **Subject:** Certificate of insurance request: [BUILDING ADDRESS], needed by [DATE]
>
> **Request for a certificate of insurance and additional-insured endorsement**
>
> **Named insured:** Desk Drop LLC · Policy number [POLICY NUMBER]
>
> **Certificate holder:** [EXACT NAME FROM BUILDING SHEET], [ADDRESS]
>
> **Additional insureds, exactly as the building lists them:** [OWNER ENTITY]; [MANAGING AGENT]; [ANY OTHER NAMES OR "AND THEIR OFFICERS, AGENTS AND EMPLOYEES" WORDING THE BUILDING REQUIRES]
>
> **Description of operations:** Delivery of sealed, packaged snack and beverage products to [TENANT COMPANY], [FLOOR OR SUITE], [BUILDING ADDRESS], for placement in the tenant's pantry. Deliveries on Tuesday or Wednesday mornings, about monthly, starting [FIRST DELIVERY DATE].
>
> **Requirements from the building:** [LIMITS, PRIMARY AND NON-CONTRIBUTORY, WAIVER OF SUBROGATION, OTHER, COPIED FROM THE SHEET]
>
> **Questions before you issue it:**
> 1. Does our policy have a blanket additional-insured endorsement? If it applies only where we have a written contract with the additional insured, note that we have no contract with this building: our agreement is with the tenant. Would you need to add the building by name (for example ISO CG 20 26, Additional Insured – Designated Person or Organization)?
> 2. Does our policy already include each of the building's other requirements listed above? If an endorsement is needed, what does it cost and how long does it take?
> 3. Please send the certificate on your standard form (ACORD 25 is fine) and a copy of the endorsement that adds the additional insureds. We are not asking for any wording on the certificate that the policy does not contain.
> 4. How soon can you issue it? We need it by [DATE], at least two business days before the first delivery on [FIRST DELIVERY DATE].
>
> **Send to:** [FOUNDER NAME], [EMAIL], [PHONE]

## Step 4 · Check the certificate before sending it to the building

- [ ] Named insured is our company exactly as on the Articles of Organization; policy number is right.
- [ ] Certificate holder matches the building's sheet letter for letter.
- [ ] Every additional insured on the building's sheet appears, spelled exactly as on the sheet.
- [ ] Limits meet or exceed every limit on the sheet.
- [ ] Policy dates cover every planned delivery to that building.
- [ ] The "ADDL INSD" column is marked for general liability, and the endorsement copy is attached.
- [ ] Any primary and non-contributory or waiver of subrogation the building requires is shown and backed by the policy.
- [ ] Description of operations names the tenant, floor and address.

Then send it to the building contact, copy the pantry owner, save it as `[BUILDING]-COI-[YYYY-MM-DD].pdf` in the office folder, and put it on your phone for drop day (plan, appendix J: "Certificate of insurance PDF on your phone").

## No-employees statement, if the building accepts one in place of workers' compensation

> [DATE]
> To: [BUILDING MANAGEMENT NAME], [ADDRESS]
> Re: Deliveries to [TENANT COMPANY], [FLOOR OR SUITE]
> The company named on the enclosed certificate of insurance has no employees. Its deliveries to your building are made by its sole member, [FOUNDER NAME], or by an outside courier company; we will ask any courier we use to send you its own certificate if you require one. If the company hires anyone, it will obtain workers' compensation coverage before that person makes a delivery to your building, and send you a certificate.
> [FOUNDER NAME], Member · [PHONE] · [EMAIL]

Attorney to confirm this wording. It must stay true: the plan requires workers' compensation the day anyone is hired, including part-time delivery help.

---

## Sources

- Plan, legal table rows "General liability insurance" ($1M per occurrence, $2M aggregate, keep a certificate template ready, bind before the first product arrives), "Auto exposure" (hired and non-owned auto), "Workers' compensation" (not required with no employees; required the day you hire anyone); Phase 1 targeting rules ("Buildings that require a certificate of insurance for every delivery go on the list for later"); appendix J. plan.md, read 2026-10-23.
- ISO CG 20 26 04 13, Additional Insured – Designated Person or Organization, NYC sample copy, https://www.nyc.gov/assets/mome/pdf/Sample-MOME-ISO-Form-CG-20-26-04-13.pdf (opened and text extracted 2026-10-23): names the additional insured in a schedule; coverage is for liability "caused, in whole or in part, by your acts or omissions" in ongoing operations or premises; not broader than the contract requires.
- ACORD 25 (2014/01) certificate text in a New York City agency sample, https://www.nyc.gov/assets/dycd/downloads/pdf/FY2021_General_Liability_Insurance_Sample.pdf (opened 2026-10-23): "confers no rights upon the certificate holder"; "If the certificate holder is an ADDITIONAL INSURED, the policy(ies) must be endorsed."
- New York Insurance Law section 502, https://www.nysenate.gov/legislation/laws/ISC/502 (opened 2026-10-23): certificates must be on an approved form, cannot add terms the policy lacks, and cannot alter coverage.
- New York Workers' Compensation Board, CE-200 request overview, https://www.wcb.ny.gov/content/ebiz/wc_db_exemptions/requestExemptionOverview.jsp (opened 2026-10-23): available to "entities operating in NY with no employees" and "can only be used to attest to a government entity"; valid only for the specific license, permit or contract.
- Whether any given building accepts a no-employees statement is unknown: ask each building.
