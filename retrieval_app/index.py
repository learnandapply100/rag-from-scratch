"""Stage 3 and 4: embed the chunks, store them, and search them.

`Hit` and the OpenAI client are already provided by AI Makerspace.
`embed_texts`, `cosine_similarity`, `build_index`
and `search` have been implemented here.
"""
import sys
from dataclasses import dataclass

import numpy as np
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

_cached: OpenAI | None = None


def client() -> OpenAI:
    """The OpenAI client, built on first use and reused after that.

    It is built lazily, not at import time, so that .env has already been
    loaded by the time it looks for OPENAI_API_KEY.
    """
    global _cached
    if _cached is None:
        _cached = OpenAI()
    return _cached


@dataclass
class Hit:
    """One retrieved chunk, and everything you need to cite it.

    `chunk_id` is what makes an answer traceable: when an answer is wrong this is how you find out which chunk caused it.
    """

    chunk_id: int
    text: str
    score: float

    def citation(self) -> str:
        """A short, human-readable label for this chunk. Printed under answers."""
        preview = " ".join(self.text.split())[:60]
        return f"[chunk {self.chunk_id}] {preview}... (score {self.score:.3f})"


def embed_texts(texts: list[str]) -> np.ndarray:
    """Turn a list of strings into a matrix of embedding vectors.

    Args:
        texts: the strings to embed. One API call can take many at once —
            do NOT loop and call once per chunk.

    Returns:
        An array of shape (len(texts), 1536), one row per input string,
        in the same order as `texts`.

    `client().embeddings.create(input=texts, model=EMBEDDING_MODEL)`.
    The response has a `.data` list; each item has an `.embedding`. Wrap the
    result in np.array(). Print `response.usage` once — knowing what a corpus
    costs to embed is the number that decides architecture at scale.
    """
    response = client().embeddings.create(input=texts, model=EMBEDDING_MODEL)

    # Goes to stderr with the rest of the trace, so it never mixes into the answer
    print(f"embedded {len(texts)} text(s): {response.usage.total_tokens:,} tokens", file=sys.stderr, flush=True)

    # Each item carries .index (its position in `texts`). Sorting by it
    # guarantees row i matches texts[i], which the citations depend on.
    items = sorted(response.data, key=lambda item: item.index)
    return np.array([item.embedding for item in items])

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """How similar are two vectors? 1.0 is identical, 0.0 is unrelated.

    The dot product, divided by the product of the two norms.
    NumPy has `np.dot` and `np.linalg.norm`.
    """
    norms = np.linalg.norm(a) * np.linalg.norm(b)
    if norms == 0:
        return 0.0  # an all-zero vector has no direction, so it matches nothing
    return float(np.dot(a, b) / norms)


def build_index(chunks: list[str]) -> np.ndarray:
    """Embed every chunk once, and return the matrix to search against.

    Args:
        chunks: from corpus.split_corpus().

    Returns:
        The embedding matrix. Row i corresponds to chunks[i] — that
        correspondence is the only thing holding your citations together,
        so do not sort or filter one without the other.

    Call to embed_texts() happens once per process, and that a fresh process has no memory of the last one.
    """
    if not chunks:
        raise ValueError("No chunks to index: is the corpus file empty?")
    return embed_texts(chunks)


def search(query: str, chunks: list[str], matrix: np.ndarray, k: int = 3) -> list[Hit]:
    """Find the k chunks most similar to the query.

    Args:
        query: the user's question, as typed.
        chunks: the chunk texts.
        matrix: the embedding matrix from build_index().
        k: how many hits to return.

    Returns:
        Up to k Hits, most similar first.

      - Embedding the query with the SAME model  the index was built with. A query
        embedded by a different model is not comparable, and the failure is
        silent — you get plausible-looking nonsense, not an error.
      - Score the query against every row, then sort.
      - Read the signature again: it says "up to k". Nothing here forces it to
        return exactly k. That tuning is the whole of Step 4's threshold option.
    """
    if len(chunks) != len(matrix):
        raise ValueError(f"{len(chunks)} chunks but {len(matrix)} vectors: citations would be wrong")
    
    # Same function, so same model as build_index used
    query_vector = embed_texts([query])[0]

    # Score every chunk: the "plain Python loop over every vector".
    scores = [cosine_similarity(query_vector, row) for row in matrix]

    # Chunk positions sorted by highest score first, keeping the top k.
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    return [Hit(chunk_id=i, text=chunks[i], score=scores[i]) for i in ranked]