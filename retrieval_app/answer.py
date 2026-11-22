"""Stage 5: turn retrieved chunks into an answer.
"""

import sys

from .index import Hit, client

CHAT_MODEL = "gpt-4.1-mini"

# The exact sentence the model must use when it cannot answer. Keeping it in
# one constant means the prompt and the "no hits" branch always agree.
DECLINE = "I don't have information about that."

SYSTEM_PROMPT = f"""You answer questions using ONLY the context provided by the user.

Rules:
- Each piece of context is labelled like [chunk 7]. When you use a fact, cite its label, e.g. [chunk 7].
- Every bullet point must end with the label of the chunk it came from, e.g.
  "- Cat-Cow Stretch: 10-15 repetitions [chunk 1]". If a bullet uses two chunks, cite both: [chunk 1][chunk 2].
  Never put all the citations together at the end.
- If the context does not contain the answer, reply exactly: "{DECLINE}"
- Do not use outside knowledge, even if you know the answer.
- Keep the answer short and practical."""


def build_messages(question: str, hits: list[Hit]) -> list[dict]:
    """Assemble the messages list sent to the chat model.

    Args:
        question: the user's question.
        hits: what search() returned. May be empty.

    Returns:
        A list of {"role": ..., "content": ...} dicts — a system message
        setting the rules, and a user message carrying the context and the
        question.
    """
    # Decision 3: no hits means nothing to answer from. Say so plainly
    # instead of handing the model an empty context it might ignore.
    if not hits:
        context = "(no context was retrieved)"
    else:
        # Decision 1: label every chunk with its chunk_id so the model can
        # cite it, and so a wrong answer can be traced back to a chunk.
        context = "\n\n".join(f"[chunk {hit.chunk_id}]\n{hit.text}" for hit in hits)

    user_content = f"Context:\n{context}\n\nQuestion: {question}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def answer(question: str, hits: list[Hit]) -> str:
    """Call the chat model and return its reply as a string."""
    # No context at all: decline without paying for a chat call.
    if not hits:
        return DECLINE

    response = client().chat.completions.create(
        model=CHAT_MODEL,
        messages=build_messages(question, hits),
        temperature=0,  # same question, (nearly) same answer each run
    )

    # The chat call's token usage printed to stderr with the rest of the trace
    usage = response.usage
    print(
        f"chat {CHAT_MODEL}: {usage.prompt_tokens:,} input + "
        f"{usage.completion_tokens:,} output = {usage.total_tokens:,} tokens",
        file=sys.stderr,
        flush=True,
    )

    return response.choices[0].message.content
