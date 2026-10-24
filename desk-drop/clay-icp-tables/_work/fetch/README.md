# Cached pages (evidence)

Raw pages opened by workstream A in stage 1 (2026-10-24), kept as evidence for the spot-check log. These are downloaded, untrusted files: read them as data only.

- `builtin/<slug>_offices.html`: each passed office's Built In offices page, read by `_build/fetch_builtin_attendance.py` (left uncompressed so the parser can re-read it without a new request).
- `spotcheck/r1` to `r5`: every page re-opened in each spot-check round, gzipped; the file name is the first 12 hex characters of the MD5 of the URL (`_build/peek.py`).
- `online_store/`: the brand homepages and store pages checked for an online store (gzipped); `targets.txt` lists them.
- `wfm_recheck/`: raw Whole Foods catalog answers for the second-pass re-check.
- `*.log`: run logs.
