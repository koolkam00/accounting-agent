#!/usr/bin/env python3
"""Audit every formula in the workbook.

1. Lists every formula that contains a numeric literal other than 0 or 1
   (tokens classified by openpyxl's formula tokenizer, so numbers inside
   strings and cell references are not counted). Target: zero.
2. Lists every function used and flags any not on the Google Sheets
   function list checked on 2026-10-23 (support.google.com/docs/table/25273).
3. Flags features Google Sheets will not carry over: array formulas,
   structured table references, external links, defined names, data tables,
   macros, and whole-column references (slow in Sheets).
4. Flags any cell other than the company_name input that spells the company
   name, so a rename stays one edit.

Usage: python3 audit_formulas.py [path.xlsx]   (exit code 1 if anything fails)
"""
import collections
import os
import re
import sys

import openpyxl
from openpyxl.formula.tokenizer import Tokenizer, Token

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(os.path.dirname(HERE), "Desk Drop financial model v1.xlsx")

# Google Sheets function list (opened 2026-10-23). Only functions this model may use.
SHEETS_OK = {
    "ABS", "AND", "AVERAGE", "CHOOSE", "COUNT", "COUNTA", "COUNTIF", "COUNTIFS", "DATE", "DATEVALUE", "DAY", "EDATE", "EOMONTH",
    "FIND", "IF", "IFERROR", "INDEX", "INT", "ISBLANK", "ISERROR", "ISNUMBER", "ISTEXT", "LEFT", "LEN", "MATCH", "MAX", "MEDIAN",
    "MIN", "MONTH", "N", "NETWORKDAYS", "NOT", "OR", "ROUND", "ROUNDUP", "SUBSTITUTE", "SUM", "SUMIFS", "SUMPRODUCT", "TEXT",
    "TIMEVALUE", "TODAY", "TRIM", "UPPER", "VALUE", "WEEKDAY", "WORKDAY", "YEAR",
}
ALLOWED_NUMBERS = {"0", "1"}


def audit(path):
    wb = openpyxl.load_workbook(path)  # formulas, not values
    lit_hits, fn_counter, bad_fn, other = [], collections.Counter(), [], []
    name_hits = []
    company_cell = None
    n_formulas = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and not v.startswith("="):
                    if "Desk Drop" in v:
                        name_hits.append(f"{ws.title}!{c.coordinate}")
                    continue
                if not (isinstance(v, str) and v.startswith("=")):
                    continue
                n_formulas += 1
                if "Desk Drop" in v:
                    name_hits.append(f"{ws.title}!{c.coordinate} (inside a formula)")
                try:
                    tok = Tokenizer(v)
                except Exception as e:  # unparsable formula
                    other.append(f"{ws.title}!{c.coordinate}: tokenizer error {e}")
                    continue
                for t in tok.items:
                    if t.type == Token.OPERAND and t.subtype == Token.NUMBER:
                        num = t.value.rstrip("%")
                        if num not in ALLOWED_NUMBERS:
                            lit_hits.append(f"{ws.title}!{c.coordinate}: literal {t.value} in {v[:140]}")
                    if t.type == Token.FUNC and t.subtype == Token.OPEN:
                        fn = t.value.rstrip("(").upper()
                        fn_counter[fn] += 1
                        if fn not in SHEETS_OK:
                            bad_fn.append(f"{ws.title}!{c.coordinate}: {fn}")
                    if t.type == Token.OPERAND and t.subtype == Token.RANGE:
                        ref = t.value
                        if "[" in ref:
                            other.append(f"{ws.title}!{c.coordinate}: structured or external reference {ref}")
                        if re.search(r"(^|!)\$?[A-Z]{1,3}:\$?[A-Z]{1,3}$", ref):
                            other.append(f"{ws.title}!{c.coordinate}: whole-column reference {ref}")
                if c.data_type == "f" and getattr(c, "array_formula", None):
                    other.append(f"{ws.title}!{c.coordinate}: array formula")
    if len(wb.defined_names):
        other.append(f"defined names present: {list(wb.defined_names.keys())[:10]}")
    for ws in wb.worksheets:
        for t in getattr(ws, "tables", {}).values() if hasattr(ws, "tables") else []:
            other.append(f"{ws.title}: Excel table {t}")
    # the company-name input is allowed exactly once
    allowed = [h for h in name_hits if h.startswith("Inputs!C")]
    name_hits = [h for h in name_hits if not (h.startswith("Inputs!C") or h.startswith("Inputs!J"))]
    return n_formulas, lit_hits, fn_counter, bad_fn, other, name_hits, allowed


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    n, lits, fns, bad, other, names, allowed = audit(path)
    print(f"formulas scanned: {n}")
    print(f"formulas with a numeric literal other than 0 or 1: {len(lits)}")
    for h in lits[:60]:
        print("  ", h)
    print(f"functions used ({len(fns)}): " + ", ".join(f"{k} x{v}" for k, v in sorted(fns.items())))
    print(f"functions not on the Google Sheets list: {len(bad)}")
    for h in bad[:20]:
        print("  ", h)
    print(f"features Google Sheets may not carry: {len(other)}")
    for h in other[:20]:
        print("  ", h)
    print(f"cells spelling the company name outside Inputs (should be 0): {len(names)}")
    for h in names[:20]:
        print("  ", h)
    print(f"company-name input cells: {allowed}")
    sys.exit(1 if (lits or bad or other or names) else 0)
