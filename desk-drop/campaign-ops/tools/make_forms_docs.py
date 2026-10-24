#!/usr/bin/env python3
"""Write forms/office-intake-form.md and forms/brand-qualification-form.md from spec/forms.json,
so the build steps always match the tracker's mapping formulas.

  python3 tools/make_forms_docs.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, "spec", "forms.json")))


def letter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


SEND = {"office_intake": "Send the form's link with the agreement (legal pack file 03) when the office says yes, or fill it in yourself during the call.",
        "brand_intake": "Send the form's link to a brand after a first conversation, or fill it in yourself during the qualifying call."}

TYPES = {"short": "Short answer", "paragraph": "Paragraph", "mc": "Multiple choice", "mc_other": "Multiple choice, with 'Other'",
         "checkbox": "Checkboxes", "dropdown": "Dropdown", "scale": "Linear scale"}


def opts(item, cats_col):
    o = item.get("options")
    if o == "CATEGORIES_OFFICE_WITH_ANY":
        return "Any of them; " + "; ".join(c[1] for c in SPEC["categories"])
    if o == "CATEGORIES_BRAND":
        return "; ".join(c[2] for c in SPEC["categories"])
    if isinstance(o, list):
        return "; ".join("%s (writes `%s`)" % (lab, val) if lab != val else lab for lab, val in o)
    return ""


def doc(key, out, intro, extra):
    f = SPEC["forms"][key]
    lines = ["**Draft for attorney review. Not legal advice.** (The form's short notice repeats the website's notice; clear both at the attorney hour.)", "",
             "# %s" % f["file_title"], "", intro, "",
             "Built from `spec/forms.json` by `tools/make_forms_docs.py`. Change the spec, not this page, and rebuild the tracker so its mapping formulas follow.", "",
             "## Build it once [FOUNDER LOGIN: Google]", "",
             "1. forms.google.com, Blank form. Drive file name: `%s` (no company name in a file name)." % f["file_title"],
             "2. Title: `%s`. Description: *%s*" % (f["form_title"], f["description"]),
             "3. Settings > Responses: **Restrict to users in [your domain] and its trusted organizations: OFF.** A Google Workspace form is restricted to your own organization by default, so with this on, an office manager or brand from another company meets a Google sign-in and cannot answer (Google Workspace help, support.google.com/a/users/answer/9303071, opened 2026-10-24: \"By default, access is restricted to people inside your organization\"). Collect email addresses: **Do not collect** (the form asks for a work email as a question instead); Limit to 1 response: off; Allow response editing: off. Presentation: View results summary: off.",
             "4. Add the questions below, in this order. Google writes them in this column order on the response tab, and the tracker reads them by position.",
             "5. Responses > Link to Sheets > Select existing spreadsheet > the tracker. Google adds a new tab. **Delete the tracker's placeholder tab `%s` and rename Google's new tab to exactly `%s`.** The tab `%s` then shows each answer in CONTRACTS 6.3 columns, with `source = founder` and `form_version = %s`." % (
                 f["response_tab"], f["response_tab"], f["target_tab"], f["form_version"]),
             "6. **Test it as an outsider:** open the form's Send link in a private or incognito window, or on a phone signed out of Google. It must open with no sign-in. Signed in to your own Workspace account, the test passes even when outsiders are blocked.",
             "7. " + SEND[key],
             "", "## Questions", "", "| Col | Question | Type | Required | Options | Writes column |", "| --- | --- | --- | --- | --- | --- |"]
    for i, it in enumerate(f["items"]):
        q = it["title"] + ((" · help: *%s*" % it["help"]) if it.get("help") else "")
        if it.get("title_standard"):
            q += " · once the founding tier closes: *%s*" % it["title_standard"]
        lines.append("| %s | %s | %s | %s | %s | `%s` |" % (letter(i + 2), q, TYPES[it["type"]], "Yes" if it["required"] else "No",
                                                         opts(it, None), it["maps_to"]))
    lines += ["", "Column A is Google's Timestamp; it becomes `submitted_at` (text, `YYYY-MM-DDTHH:MM:SS`), the key you copy into the tracker.", ""]
    lines += extra
    open(os.path.join(ROOT, "forms", out), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return out


def main():
    doc("office_intake", "office-intake-form.md",
        "The founder-side copy of the website's office form: the same questions and the same CONTRACTS 6.3 columns (`office_intake`), for offices that sign before the website is public, or when you take intake on a call. The website's own form writes to the tracker's `office_intake` tab directly when its script is bound to the tracker (website/SETUP.md section 3; runbook step 6).",
        ["## Notes", "",
         "- Pantry owner: when the answer is \"Yes, me\", the mapping copies the contact's name and title into `pantry_owner_name` and `pantry_owner_title`, as the website does.",
         "- Categories: \"Any of them\" writes all 14 keys; otherwise the ticked labels become their keys, separated by semicolons, in CONTRACTS order.",
         "- The pantry owner's own phone and email (when the owner is not the contact) are asked in the participation agreement's top table, not here; the outreach workstream passes them as `pantry_owner_phone` and `pantry_owner_email` (HANDOFF.md).",
         "- Retention: the same 12-month promise as the website form. Rows of offices that never sign are deleted from the response tab and from the form (Responses > Individual > Delete)."])
    doc("brand_intake", "brand-qualification-form.md",
        "The founder-side copy of the website's brand application: the seven qualification checks, the same CONTRACTS 6.3 columns (`brand_intake`). Use it before the website is public or during a qualifying call. The seven checks are what the brand says; the tracker's `brands` tab marks `qualified` only when all seven are a plain yes and the product is not excluded, and you still check the certificate (legal pack file 11) and the retailer evidence yourself.",
        ["## Notes", "",
         "- Checks 4 and 6 change wording when the founding tier closes (after the third founding brand): edit those two questions and set `brand_form_version` on the tracker's config tab to `brand-gform-2.0`. The column names stay `q4_can_ship_275_in_10bd` and `q6_contact_can_approve_600`, exactly as on the website (website/HANDOFF.md).",
         "- Website and online store addresses get `https://` added when missing, as on the website.",
         "- \"Not an excluded product\" is one required checkbox; ticking it writes `excluded_category_confirmed = Y`.",
         "- Nutrient wording such as \"10g protein\" is allowed but you review it; structure or function wording such as \"supports gut health\" is a health claim and the brand is excluded (CONTRACTS section 4)."])
    print("wrote forms/office-intake-form.md, forms/brand-qualification-form.md")


if __name__ == "__main__":
    main()
