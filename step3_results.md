# Step 3: 10 questions, what fails?

Run with defaults: chunk_size 1000, chunk_overlap 200 (21 chunks), k=3, text-embedding-3-small, gpt-4.1-mini, temperature 0. Full answers, retrieved chunks and top-5 scores are in `results_before.md`.

| # | Question | ✅/❌ | What went wrong, where |
|---|----------|------|------------------------|
| 1 | Aerobic activity per week? | ✅ | retrieval ranked the answer chunk 0 second (0.354) behind chunk 3, the workout schedule (0.370); passed only because k=3 |
| 2 | Bedroom temperature for sleep? | ✅ | top chunks 7 and 8 both contain the Chapter 8 temperature line (chunk 7 cuts it off before the Celsius part). clean |
| 3 | Days to form a habit? | ✅ | top chunk 12 (Chapter 13), clear gap (0.526 vs 0.388). clean |
| 4 | Cat-Cow repetitions? | ✅ | top chunk 1 (Chapter 2). clean |
| 5 | Morning and evening routine? | ✅ | chunks 12 + 13 cover Chapter 14 and Chapter 15; chunk 13 starts mid-word ("ke at a consistent time") but the 200-char overlap kept the list whole |
| 6 | Box breathing vs deep breathing? | ❌ | retrieval: box-breathing chunk 18 ranked 4th (0.355), so k=3 missed it; generation: model then filled in box breathing from outside knowledge despite the prompt |
| 7 | How long before bed to stop screens? | ❌ | retrieval: got Chapter 8 "1-2 hours" (chunk 7) but the Sleep Checklist "1 hour" (chunk 19) ranked 4th; answer gives only half |
| 8 | Ibuprofen dose for a migraine? | ✅ | retrieval returned 3 irrelevant chunks (top 0.197, headaches); prompt held and the model declined |
| 9 | Melatonin dose for jet lag? | ✅ | retrieval returned sleep chunks 8 and 7 (0.321, 0.304); prompt held and the model declined |
| 10 | Keto meal plan for type 2 diabetes? | ✅ | refusal correct; generation: reworded the DECLINE sentence instead of using it exactly (would break any `reply == DECLINE` check); irrelevant top chunk scored 0.424, higher than Q1's correct chunk (0.354) |

**Score: 8/10.** Both failures are retrieval missing the 4th-ranked chunk, so `k=3` is too small for questions whose facts sit far apart. Q6 also shows a second, separate bug in generation: given incomplete context, the model answered from its own knowledge instead of declining that part.

**For Step 4:** a score threshold can't separate good from bad here. An irrelevant chunk (Q10, 0.424) outscores a correct one (Q1, 0.354). Raising `k` targets the two failures directly: the missing chunk was 4th in both Q6 and Q7.
