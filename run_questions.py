"""Step 3 / Step 4 helper: run the 10 test questions through the app's own stages.

    uv run python run_questions.py                 # results -> results_before.md
    uv run python run_questions.py --out results_after.md

Like the app itself, it builds the index again for EVERY question, so each
question pays to embed the whole guide (21 chunks) plus the question.
For every question it records the answer, the chunks that came back and
their scores (the top 5 scores too, so you can see the gap a threshold
would sit in).
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from retrieval_app import answer as answer_stage
from retrieval_app import corpus as corpus_stage
from retrieval_app import index as index_stage

HERE = Path(__file__).resolve().parent

# (kind, question, what a correct answer looks like)
QUESTIONS = [
    ("Lookup", "How many minutes of moderate aerobic activity should adults get per week?", "150 minutes (Ch 1)"),
    ("Lookup", "What temperature should my bedroom be for sleep?", "65-68 F / 18-20 C (Ch 8, Sleep Checklist)"),
    ("Lookup", "On average, how many days does it take to form a habit?", "66 days (Ch 13)"),
    ("Lookup", "How many repetitions of the Cat-Cow stretch should I do?", "10-15 (Ch 2)"),
    ("Needs 2 chunks", "What should my morning and evening routine look like?", "Ch 14 morning list AND Ch 15 evening list"),
    ("Needs 2 chunks", "How is box breathing different from the deep breathing technique for immediate stress relief?", "Ch 11: 4-4-4 vs Appendix: 4-4-4-4 (extra hold)"),
    ("Needs 2 chunks", "How long before bed should I stop using screens?", "Ch 8 says 1-2 hours, Sleep Checklist says 1 hour: should mention both"),
    ("Decline", "What dose of ibuprofen should I take for a migraine?", "refusal (guide has no drug doses)"),
    ("Decline", "How much melatonin should I take for jet lag?", "refusal (guide never mentions melatonin or jet lag)"),
    ("Decline", "What is a good keto meal plan for someone with type 2 diabetes?", "refusal (no keto, no diabetes)"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--out", default="results_before.md")
    args = parser.parse_args()

    load_dotenv(HERE / ".env")
    text = corpus_stage.load_corpus(HERE / "data" / "HealthWellnessGuide.txt")
    chunks = corpus_stage.split_corpus(text)

    lines = [f"# Results ({args.out}), k={args.k}\n"]
    for n, (kind, question, expected) in enumerate(QUESTIONS, start=1):
        # Embed the guide again for this question, as a fresh app run would.
        matrix = index_stage.build_index(chunks)

        # Raw top-5 scores, computed outside search(), so they show the gap
        # even after a threshold is added to search().
        qv = index_stage.embed_texts([question])[0]
        raw = sorted(((index_stage.cosine_similarity(qv, row), i) for i, row in enumerate(matrix)), reverse=True)[:5]
        top5 = ", ".join(f"chunk {i}: {s:.3f}" for s, i in raw)

        hits = index_stage.search(question, chunks, matrix, k=args.k)
        reply = answer_stage.answer(question, hits)
        print(f"[{n}/10] done", file=sys.stderr)

        lines.append(f"## {n}. ({kind}) {question}\n")
        lines.append(f"**Expected:** {expected}\n")
        lines.append(f"**Answer:**\n\n{reply}\n")
        lines.append(f"**Top 5 raw scores:** {top5}\n")
        lines.append("**Retrieved (what search() returned):**\n")
        if not hits:
            lines.append("- (none)\n")
        for hit in hits:
            preview = " ".join(hit.text.split())[:150]
            lines.append(f"- chunk {hit.chunk_id}, score {hit.score:.3f}: {preview}...")
        lines.append("")

    (HERE / args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
