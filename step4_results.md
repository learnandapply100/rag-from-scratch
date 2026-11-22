# Step 4: raise k from 3 to 4

**The change:** the default for `-k` in `retrieval_app/__main__.py` went from 3 to 4 (the default in `search()` in `index.py` was changed to match). Everything else is the same as Step 3: chunk_size 1000, chunk_overlap 200 (21 chunks), text-embedding-3-small, gpt-4.1-mini, temperature 0.

**The failures it targeted:** Q6 and Q7. In both, the chunk with the missing fact ranked 4th, just outside k=3.

Full answers, retrieved chunks and top-5 scores: `results_before.md` (k=3) and `results_after.md` (k=4).

## Before / after

| # | Question | k=3 | k=4 | What changed, where |
|---|----------|:---:|:---:|---------------------|
| 1 | Aerobic activity per week? | ✅ | ✅ | no change. 4th chunk (5, meal planning) added and ignored |
| 2 | Bedroom temperature for sleep? | ✅ | ✅ | no change. now cites only chunk 8, the one with the full F and C line |
| 3 | Days to form a habit? | ✅ | ✅ | no change |
| 4 | Cat-Cow repetitions? | ✅ | ✅ | no change |
| 5 | Morning and evening routine? | ✅ | ✅ | no change. answer word-for-word the same |
| 6 | Box breathing vs deep breathing? | ❌ | ✅ | **fixed, retrieval:** chunk 18 (0.355, holds the Appendix "4 in, 4 hold, 4 out, 4 hold" line) now comes back 4th. The model cites it instead of filling in from outside knowledge |
| 7 | How long before bed to stop screens? | ❌ | ❌ | **still failing, but the stage moved from retrieval to generation:** chunk 19 (Sleep Checklist, "No screens 1 hour before bed") now comes back, and the model still gives only "1-2 hours". It also cites [chunk 8], which wasn't retrieved and has no screen line: a made-up citation |
| 8 | Ibuprofen dose for a migraine? | ✅ | ✅ | still declines, **but the decline sentence is now reworded** ("...about the dose of ibuprofen for a migraine in the provided context") instead of the exact DECLINE text |
| 9 | Melatonin dose for jet lag? | ✅ | ✅ | still declines, **same rewording regression** as Q8 |
| 10 | Keto meal plan for type 2 diabetes? | ✅ | ✅ | still declines. reworded in both runs, so no change |

**Score: 8/10 -> 9/10.**

## What the numbers say

- **One fix (Q6):** The fact was ranked 4th, k=4 brought it in, and the model used it. Fixing retrieval also fixed Q6's second bug: with box breathing in the context, the model no longer needed outside knowledge.
- **One failure moved stage (Q7):** k=4 fixed the retrieval issue from previous run with k=3. Both screen-time facts (chunk 7 and chunk 19) are in the context now and sent to the model with top 4 retrieval. The model still reports only one of them. This is a generation bug, and a bigger k won't fix it. The next fix should be in the prompt (for example, "if the context gives different values, report all of them"), not in retrieval.
- **Regressions, none of which change the score:**
  - Exact decline wording: 1/3 decline questions reworded the DECLINE sentence at k=3, and 3/3 do at k=4. The refusals are still correct, but any code that checks `reply == DECLINE` would now miss all three. The extra chunk changed the model's input, and that was enough to change its wording.
  - Q7 cites a chunk that was never sent to the model. Citations are only useful if they point at text the model actually saw.
- **Rankings didn't move.** The top-5 scores match between runs to within 0.002, so k=4 only added the next chunk in line and didn't change the order. That's expected, since k only decides where the list is cut off.
- **Cost:** every question now sends 4 chunks instead of 3, about 1,000 more characters of context per question. This run didn't record token counts, so the exact cost isn't measured here.

## Vibe check
Does it *feel* better? 
Q6 reads much better: it's short and cited, where before it explained box breathing from memory. Q7 looks unchanged, even though under the hood its failure moved from retrieval to generation. It also made up a citation for chunk 8 which it never received as it wasn't part of top 4. Q8 and Q9 no longer use the exact decline sentence, but to a user they still read as correct refusals. Overall the results *feel* the same or marginally better with the change. That roughly matches the numbers: the score rose by one point, from 8 to 9, and Q6 is the only change a user would notice. The score hides the regressions though: reworded refusals and a made-up citation. These would break an automated reply == DECLINE check and make citations less trustworthy.
