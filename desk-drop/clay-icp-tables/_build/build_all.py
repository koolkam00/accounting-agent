#!/usr/bin/env python3
"""Rebuild both tables from the inputs. Run from anywhere:
    python3 -B clay-icp-tables/_build/build_all.py
The Built In attendance fetch (fetch_builtin_attendance.py) is separate: it reads
offices.csv to find the rows that passed the gates, so run it after a first build and
then rebuild. Its results are cached in _work/attendance_builtin.csv.
"""
import os
import runpy
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
for script in ("build_offices.py", "build_brands.py", "stage3_merge.py", "build_xlsx.py"):
    print("==", script)
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")
