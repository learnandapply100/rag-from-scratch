# Decisions

One entry per decision: what changed, why, and what would change it back.

## Retrieval, week 1

**What I changed**

I raised the number of retrieved chunks, `k`, from 3 to 4. This is the default for `-k` in `retrieval_app/__main__.py`, and the default in `search()` in `index.py` matches it.

**Why**

It targeted the two Step 3 failures, Q6 (box breathing vs deep breathing) and Q7 (screens before bed). These questions are 'Needs 2 chunks' kind of questions. In both, the second chunk holding the missing fact ranked 4th, just outside k=3. A score threshold wasn't an option here, because cosine scores don't separate right from wrong here: an irrelevant chunk in Q10 (0.424) scored higher than the correct chunk in Q1 (0.354).

Score: **8/10 at k=3 -> 9/10 at k=4** (details in `step4_results.md`).
- Q6 is fixed. The box-breathing chunk (chunk 18) now comes back, and the model cites it instead of answering from its own knowledge.
- Q7 still fails, but at a different stage. Both screen-time facts now reach the model, and it still reports only one, so it's now a generation bug, not a retrieval one.
- Regressions that don't change the score: all 3 decline questions now reword the exact `DECLINE` sentence (1 of 3 did at k=3), and Q7 cites chunk 8, which was never sent to the model.

**What would change my mind**

I would go back to k=3 if:
- decline questions started getting answered from the extra, irrelevant 4th chunk, or
- after a prompt fix, the extra chunk turned out to be the reason the model keeps rewording `DECLINE` or making up citations, or
- on a bigger corpus or at higher traffic, the cost of a 4th chunk on every question outweighed fixing one question in ten.

If a "needs 2 chunks" question had its missing fact ranked 5th or lower, I would stop raising k and try a different chunking technique or change what gets searched (splitting the question into parts or rewriting it before searching or search with a model-written draft answer), because each extra chunk adds cost and noise for every question.
