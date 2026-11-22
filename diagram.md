# Pipeline diagram

How one question flows through the app, one stage at a time. Each thin arrow is labelled with the Python type that travels along it. The thick 💲 arrows are paid OpenAI calls, and the arrow leaving each OpenAI box is what the call returns. (Strictly, the reply comes back to the function that made the call, which passes it on. The diagram skips that hop to keep it readable.) ⭐ marks where the Step 4 change (k raised from 3 to 4) sits.

```mermaid
flowchart TD
    Q(["question<br/>typed on the command line"])
    F[("data/HealthWellnessGuide.txt")]

    subgraph CORPUS["corpus.py"]
        L["1 · load_corpus()"]
        S["2 · split_corpus()<br/>chunk_size 1000, overlap 200, step 800"]
    end

    subgraph INDEX["index.py"]
        E["3 · build_index()<br/>calls embed_texts(chunks)"]
        QE["inside search(): embed_texts([question])<br/>same embedding model as the index"]
        C["4 · search()<br/>cosine_similarity against every row,<br/>sort high to low, keep top k"]
    end

    subgraph ANSWER["answer.py"]
        subgraph A5["5 · answer(question: str, hits: list[Hit])"]
            M["build_messages()<br/>called inside answer()<br/>labels each chunk as [chunk N]"]
        end
    end

    OE1{{"💲 OpenAI Embeddings API<br/>text-embedding-3-small<br/>(the chunks)"}}
    OE2{{"💲 OpenAI Embeddings API<br/>text-embedding-3-small<br/>(the question)"}}
    OC{{"💲 OpenAI Chat Completions API<br/>gpt-4.1-mini, temperature 0"}}
    OUT(["printed answer + Sources list<br/>(stdout)"])
    K["⭐ Step 4 change: k = 4 (was 3)<br/>-k default in __main__.py and in search()"]

    F -->|"Path"| L
    L -->|"str, 16,206 characters"| S
    S -->|"list[str], 21 chunks"| E
    E ==>|"💲 sends the 21 chunks, list[str]<br/>paid on every run: nothing is saved"| OE1
    OE1 -->|"21 vectors: np.ndarray, shape (21, 1536)"| C
    S -->|"list[str], same 21 chunks<br/>(looked up by position for each Hit's text)"| C
    Q -->|"str"| QE
    QE ==>|"💲 sends 1 string"| OE2
    OE2 -->|"1 vector: np.ndarray, shape (1536,)"| C
    K -.- C
    C -->|"list[Hit], up to k = 4<br/>each Hit: chunk_id, text, score"| M
    Q -->|"str"| M
    M ==>|"💲 sends list[dict], 2 messages:<br/>1. system: the system prompt (SYSTEM_PROMPT)<br/>2. user: context + question<br/>(context = the text of each Hit, labelled [chunk N])"| OC
    OC -->|"str, the answer with [chunk N] citations"| OUT
    C -->|"list[Hit], printed by __main__.py as the Sources list"| OUT
```

## Reading the diagram

- **Two OpenAI endpoints, three paid calls per question.** The Embeddings API is drawn twice because it's called twice: once for all 21 chunks (because nothing is saved to disk, this happens again on every run) and once for the question. The Chat API is called once, for the answer.
- **The row-to-chunk link.** Row `i` of the `(21, 1536)` matrix belongs to chunk `i`. `search()` uses that position as the `chunk_id`, which is what makes every citation traceable.
- **Where the Step 4 change sits.** Raising `k` only moves the cut-off at the end of `search()`. The scores and their order don't change; one more `Hit` goes to the model.
- **Two arrows reach the output on purpose.** The `[chunk N]` citations inside the answer are written by the model and can be wrong. The Sources list is printed by `__main__.py` straight from the `list[Hit]` that `search()` returned, so it shows what the model was actually sent.
- **No hits, no chat call.** If `search()` returned nothing, `answer()` would return the `DECLINE` sentence without calling the chat model. With k = 4 that never happens on this corpus, so the diagram doesn't draw it.
