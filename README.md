# rag-from-scratch

Ask questions of any plain-text file from your terminal, and get an answer that cites the passages it came from.

It is a complete retrieval-augmented generation (RAG) pipeline in about 200 lines of Python, built without a framework or a vector database: just NumPy and the OpenAI API. It's small on purpose, so every stage can be read, printed and blamed when an answer goes wrong.

Example (shortened):

```
$ uv run python -m retrieval_app "How many days does it take to form a habit?"
corpus HealthWellnessGuide.txt: 16,206 characters -> 21 chunks
...

Q: How many days does it take to form a habit?

On average, it takes 66 days to form a habit [chunk 12].

Sources:
  [chunk 12] ion Habits are behaviors that become automatic through repetitio... (score 0.526)
  ...
```

## How it works

Five stages, one file each:

| Stage | File | What it does |
|---|---|---|
| 1. Load | `retrieval_app/corpus.py` | reads the `.txt` file into one string |
| 2. Split | `retrieval_app/corpus.py` | cuts it into overlapping chunks (1,000 characters, 200 overlap) |
| 3. Embed | `retrieval_app/index.py` | turns every chunk into a vector with `text-embedding-3-small`, in one API call |
| 4. Search | `retrieval_app/index.py` | embeds the question, scores it against every chunk by cosine similarity, keeps the top `k` |
| 5. Answer | `retrieval_app/answer.py` | sends the top chunks, labelled by chunk number, to `gpt-4.1-mini` with a prompt that says: answer only from this context, cite every fact, and decline if the answer isn't there |

Every answer lists its sources with their scores, and a trace (chunk count, index time, token usage) goes to stderr, so you can always see which chunks an answer came from.

## Setup

Needs Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
echo "OPENAI_API_KEY=sk-..." > .env    # your key; .env is gitignored
```

`data/` ships with a sample corpus, `HealthWellnessGuide.txt` (16,206 characters), so it runs straight away. To ask about your own text, put any UTF-8 `.txt` file in `data/`, ideally 10,000–50,000 characters. Keep one `.txt` there, or pick one with `--corpus`.

## Usage

```bash
uv run python -m retrieval_app "your question"
uv run python -m retrieval_app "your question" -k 5              # retrieve 5 chunks instead of 3
uv run python -m retrieval_app "your question" --show-chunks     # print the retrieved text too
uv run python -m retrieval_app "your question" --corpus data/other.txt   # if data/ holds more than one .txt
```

`run_questions.py` runs a fixed set of 10 test questions and writes the answers, retrieved chunks and top-5 scores to a Markdown file, for before/after comparisons.

## What testing showed

On the sample wellness guide, with 10 hand-written questions (simple lookups, questions whose answer is split across two places, and questions the text can't answer), it got 8/10 right:

- **Both failures were retrieval:** the second half of the answer ranked 4th, just outside the top 3.
- **All 3 unanswerable questions were declined correctly.** The strict prompt handled them, with no score cutoff needed.
- **Cosine scores measure topic, not whether a chunk holds the answer.** An irrelevant chunk once scored 0.424 while a chunk with the right answer scored 0.354, so a single score threshold can't separate them.

Details are in `step3_results.md`, and the change made in response is in `DECISIONS.md`.

## Limitations (deliberate)

- Re-embeds the whole file on every run: nothing is saved to disk.
- Search is a plain loop over every vector, fine for a few hundred chunks.
- Chunks are fixed-size character slices, so they can cut words and sentences in half.
- One file at a time.
