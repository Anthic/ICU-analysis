Do not run any new analysis. Do not edit any memory file yet.
Propose the edits below as text only; I will confirm.

1. Source files: in table4, table5 and table7, print the exact script and
   input file names that produced every number (including paired bootstrap CIs).
2. Wording proposals: table4 takeaway: replace "mean improvement is clear" with
   "the mean shift toward nominal 90% is clear for groups with a gap; delta varies
   a lot between splits". table6: remove "catastrophically"; say the survivor
   majority "likely" dominates the threshold (not tested). table7 note: use "Lower
   survivor coverage than White" and add "exploratory; many comparisons; CI is
   an indication only". Variance sentence: "7-50% larger in all groups except
   Other/Unknown insurance (80%)".
3. Add the status line "GENERATED - PENDING REVIEW" to the header of table3..7.
4. Delta set size (Mondrian minus global) is not covered by independent_check.py.
   Extend the script (still no shared helpers) to recompute it, plus Mondrian-marginal
   death coverage (table6), for all 4 age groups and all 4 insurance groups, and show
   PASS/FAIL with tolerance 0.0005. Also print the import lines of
   independent_check.py.
5. Propose the status wording: "Phase 4-5 (noflags, a010): VERIFIED for the groups and
   metrics listed in independent_check.py; all other values GENERATED".
Stop when done and wait for me.