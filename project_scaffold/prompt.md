I authorize ONLY these edits to .agent/project_memory.md and
paper/project_memory.md. Do not change anything else.

1. Phase 3 status: add "Noflags, alpha 0.05, class-conditional": coverage
   0.9508 for deaths and 0.9503 for survivors, mean set size 1.431, 43.14%
   of sets are {0,1}; marginal sets at alpha 0.05 still cover only 55.4% of
   deaths.

2. Replace "due to finite test-sample variation" with: "because overall
   coverage varies across random splits (test and calibration sampling), e.g.
   0.9456 in some splits, which allows death coverage near 0.518". Also write
   the bound as (0.95 - 0.8935) / 0.1065 = 0.5305 (assumes survivors fully
   covered; a mean-level bound, not a per-split one).

3. Replace "Seed-0 gain leaders included ..." with: "In the primary noflags
   model (seed 0) the highest-ranked features by gain were BUN, lactate, GCS,
   respiratory rate, bicarbonate and sodium; intubation ranked 12th and age
   13th." State which XGBoost importance_type the script exports.

4. Add: "Percentiles and SDs reported for the 100 runs describe split-to-split
   variability (random train/calibration/test splits), not confidence
   intervals for the true coverage."

5. Resolve duplicates: the zero-gain decision appears around lines 156-157
   and 183. Keep one decision row. Text: "Zero gain for all *_measured flags
   confirmed in seeds 0-9 of the 100-seed run; seeds 10-99 pending." Move
   "seeds 10-99" to open items only.

6. After editing, print (a) lines containing "Methods wording (approved)"
   through the end of that section, and (b) a check that no non-English or
   garbled word appears anywhere in the file. Also show the output of the unit
   tests (including the exact-rank test) by running them now.


   ৪. একটা সতর্কতা

Memory ফাইল এখন প্রায় paper-এর রেকর্ড হয়ে যাচ্ছে। প্রতিটা সংখ্যার পাশে কোন ফাইল থেকে এসেছে (যেমন phase3_baseline_metrics_noflags_a010.json) লিখে রাখা ভালো, যাতে paper-এ বসানোর সময় যাচাই করা যায়। Agent-কে পরের আপডেটে এটা যোগ করতে বলতে পারো।--Likhe rakhba