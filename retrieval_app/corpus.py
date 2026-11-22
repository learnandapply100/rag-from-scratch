"""Stage 1 and 2: load the source text, and split it into chunks.
"""

from pathlib import Path


def load_corpus(path: Path) -> str:
    """Reads a .txt file and returns its entire contents as one string.

    Args:
        path: the .txt file to read, whichever corpus the app was pointed at.

    Returns:
        The whole file as a single string.
    """
    return Path(path).read_text(encoding="utf-8")


def split_corpus(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Splits one long string into a list of overlapping chunks.

    Args:
        text: the whole corpus, from load_corpus().
        chunk_size: how many characters in each chunk.
        chunk_overlap: how many characters each chunk repeats from the last one.

    Returns:
        A list of strings i.e. chunks

   Why does the step subtract the overlap rather than add it?
   If you add the overlap, every pair of neighbouring chunks has a gap of chunk_overlap characters between them, 
   and those characters end up in no chunk at all.
    """
    
    #If the overlap is as big as the chunk or bigger, the function stops immediately with an error
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


    #'step' here is how far each chunk starts after the previous one. In this case the default is 1000 chars for chunk_size and 200 chars
    # for chunk_overlap. This means each chunk will start 800 (1000 - 200) characters after the previous chunk. There will be an overlap of 200 chars
    # between neighbouring chunks
    step = chunk_size - chunk_overlap
    chunks = []

    #'for' loop in Python iterates over the start positions that range() produces (0, 800, 1600, …), slicing the text in each iteration. Each slice has
    # 800 chars from the start position of that iteration. The last iteration stops before the len(text) is reached so last slice may be shorter.
    # Each slice is added to the end of the list
    for start in range(0, len(text), step):
        chunks.append(text[start : start + chunk_size])
    return chunks