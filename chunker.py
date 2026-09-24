"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.

────────────────────────────────────────────────────────────────────────────
MILESTONE 3 — what I replaced it with, and why
(corpus: city_guides. Measurements are in NOTES.md.)

Every document in this corpus is Markdown with one `#` title, a short intro,
and a run of `##` sections. There are 98 such sections. The shortest is 23
characters, the median is 282, and the longest is 709. **Not one of them
reaches 800.**

That is the whole argument. The starter's 800-character window can never split
one of these sections for being too long, so the only thing it ever does is cut
partway through a section and staple the tail onto the next heading. 98 clean
boundaries go in; 51 arbitrary ones come out. The corpus is handing me the
right boundaries in its own markup and the starter is throwing them away.

So: **split on the headings, not on a character count.** One section, one
chunk. The character cap stops being the thing that decides boundaries and
becomes a ceiling that catches sections too long to be one thought.

The part that is not obvious from "split on headings":

  Every chunk carries a `Document — Section` header line in its own TEXT, not
  just in its metadata. Two reasons, both measured rather than assumed.

  1. `Practical notes` is byte-identical in all nine town guides — the same 277
     characters about cash, mobile coverage and the nearest hospital. Split by
     section and stored as-is, those are nine chunks with identical text and
     therefore identical embeddings. Retrieval orders them arbitrarily and
     cites whichever came back first, which is a citation that means nothing.
     With the header line they are nine different strings that embed
     differently.

  2. The nine town guides share all seven headings. "Buses run four times a
     day" is a useless chunk if nothing inside it says Halden Bay — useless to
     the embedding model, which cannot tell which town is being asked about,
     and useless to the answer model, which cannot name the town it just read.

  This is also what replaces overlap. Overlap exists to stop a boundary from
  orphaning the context that made a sentence mean something. Here the context
  that matters is "which town, which topic", and repeating that on every chunk
  carries it better than 120 shared characters of the previous section would.

Numbers, and where they came from:

  CHUNK_SIZE = 700        A ceiling, not a target. Left whole, section chunks
                          come out 183–758 characters, and exactly one is over
                          700: `guide_accessibility.md` :: "Straightforward",
                          which is three towns in three bold paragraphs. The
                          cap is set where it takes that one apart and leaves
                          everything else alone, rather than at a round number.

                          It splits into 2 pieces, not 3 — the packer fills
                          greedily, so Thornby Wells and Marchwood share the
                          first chunk (568 chars) and Brightwater gets the
                          second (283). Both pieces are whole paragraphs and
                          both carry the header line, which is what the
                          criterion asks for; one-town-per-chunk would need a
                          rule that splits on bold leads, and that rule would
                          be fitted to this single section.

  CHUNK_OVERLAP = 120     Only reaches the sentence-splitting path, which this
                          corpus never enters (see `_split_long_section`).
                          Between sibling paragraphs of one section it is
                          deliberately NOT applied: those paragraphs are about
                          different towns, and carrying the last sentence of
                          the Thornby Wells paragraph into the Marchwood one
                          would put the wrong town's facts in the chunk the
                          header line claims is about Marchwood.

  No minimum-size merge. The smallest chunk this produces is 183 characters and
  reads as a whole thought, so a merge rule would be code that never runs. If a
  future corpus needs one, this is where it would go.
────────────────────────────────────────────────────────────────────────────
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# A `## Heading` line, used to cut a document into sections.
_SECTION = re.compile(r"(?m)^##[ \t]+(.+?)[ \t]*$")

# A blank line between paragraphs.
_PARAGRAPH = re.compile(r"\n[ \t]*\n")

# End of a sentence: .!? followed by whitespace. Good enough for prose; it will
# split on "e.g." and there is nothing in this corpus for it to get wrong.
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _title_of(doc: Document) -> str:
    """The document's `# Title`, or its filename if it hasn't got one."""
    first = doc.text.lstrip().split("\n", 1)[0]
    if first.startswith("# "):
        return first[2:].strip()
    return doc.source


def _sections(doc: Document) -> list[tuple[str, str]]:
    """
    Cut a document into (heading, body) pairs on its `##` lines.

    Whatever sits above the first `##` — the title line and the intro
    paragraph — comes back as a section called "Overview", because on these
    documents it is the paragraph that says what the town actually is.

    Returns [] for a document with no `##` headings at all, which is the
    signal to fall back to fixed windows.
    """
    matches = list(_SECTION.finditer(doc.text))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []

    intro = doc.text[: matches[0].start()]
    # Drop the `# Title` line; it goes on every chunk as the header instead.
    intro = re.sub(r"(?m)\A#[ \t]+.*$", "", intro).strip()
    if intro:
        sections.append(("Overview", intro))

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(doc.text)
        body = doc.text[match.end() : end].strip()
        if body:
            sections.append((match.group(1).strip(), body))

    return sections


def _pack(pieces: list[str], budget: int, overlap: int = 0) -> list[str]:
    """
    Greedily fill chunks of at most `budget` characters from `pieces`.

    `pieces` are already whole units — paragraphs, or sentences — so a unit is
    never broken. If one unit is on its own larger than the budget it gets its
    own oversized chunk rather than being cut; the caller decides whether to
    take it apart further.

    `overlap` repeats the tail of the previous chunk at the front of the next.
    It is applied in whole pieces, so it never cuts a sentence in half.
    """
    chunks: list[str] = []
    current: list[str] = []
    size = 0

    for piece in pieces:
        addition = len(piece) + (2 if current else 0)
        if current and size + addition > budget:
            chunks.append("\n\n".join(current))
            carried: list[str] = []
            carried_size = 0
            for previous in reversed(current):
                if overlap and carried_size + len(previous) <= overlap:
                    carried.insert(0, previous)
                    carried_size += len(previous) + 2
                else:
                    break
            current = carried
            size = carried_size
            addition = len(piece) + (2 if current else 0)
        current.append(piece)
        size += addition

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _split_long_section(body: str, budget: int, overlap: int) -> list[str]:
    """
    Break a section that is longer than the budget, largest unit first.

    Paragraphs first, with NO overlap between them — in this corpus the
    paragraphs of an over-long section are about different towns, and carrying
    one town's sentence into the next town's chunk is exactly the confusion the
    header line exists to prevent.

    Only if a single paragraph is still over budget does this fall to
    sentences, and that path does use the overlap, because there the pieces
    really are continuous prose. Nothing in `city_guides` reaches it.
    """
    paragraphs = [p.strip() for p in _PARAGRAPH.split(body) if p.strip()]
    pieces = _pack(paragraphs, budget, overlap=0)

    out: list[str] = []
    for piece in pieces:
        if len(piece) <= budget:
            out.append(piece)
            continue
        sentences = [s.strip() for s in _SENTENCE.split(piece) if s.strip()]
        out.extend(_pack(sentences, budget, overlap=overlap))
    return out


def _pieces_for(body: str, header: str, budget: int, overlap: int) -> list[str]:
    """
    Split one section's body so that header + piece always fits the budget.

    The subtlety is that a section which splits is labelled
    `header (part n of m)`, not `header` — so the room left for the body
    depends on how many pieces there turn out to be, and how many pieces there
    turn out to be depends on the room. Reserving nothing for the suffix is
    what produced 703-character chunks against a 700 budget.

    Resolved by iterating to a fixed point: split, see how many pieces came
    out, reserve for that many, split again. Piece count only ever rises as
    room shrinks, so this converges; the cap is belt and braces.

    One case this does not fix, deliberately: a heading longer than the whole
    budget leaves no room for a body at all, and the chunk goes over. No
    splitting strategy fixes that — the header alone doesn't fit — and a
    heading of several hundred characters is corrupt input rather than a
    document. Truncating it would mean a code path that never runs on a real
    corpus, which is the same reason there is no minimum-size merge rule.
    """
    count = 1
    pieces = [body]

    for _ in range(4):
        suffix = len(f" (part {count} of {count})") if count > 1 else 0
        # max(..., 1) keeps room positive if a document has a heading so long
        # that it fills the budget on its own.
        room = max(budget - len(header) - suffix - 2, 1)

        pieces = [body] if len(body) <= room else _split_long_section(body, room, overlap)
        if len(pieces) == count:
            return pieces
        count = len(pieces)

    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents into chunks on their Markdown section headings.

    One `##` section becomes one chunk, prefixed with a `Document — Section`
    header line so the chunk names its own subject in the text the embedding
    model reads and the answer model quotes. A section longer than
    `config.CHUNK_SIZE` is broken at paragraph boundaries — never mid-sentence
    — and each piece keeps the header, numbered `(part n of m)`.

    A document with no `##` headings has no structure to use, so it goes
    through `fallback_split` instead. That does not happen in `city_guides`;
    it is there so that pointing CORPUS at a folder of plain text degrades to
    the starter's behaviour rather than producing one chunk per file.

    The long argument for all of this is at the top of the file.
    """
    budget = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP

    chunks: list[Chunk] = []
    unstructured: list[Document] = []

    for doc in documents:
        sections = _sections(doc)
        if not sections:
            unstructured.append(doc)
            continue

        title = _title_of(doc)
        index = 0

        for heading, body in sections:
            header = f"{title} — {heading}"
            pieces = _pieces_for(body, header, budget, overlap)

            for part, piece in enumerate(pieces, 1):
                label = header
                if len(pieces) > 1:
                    label = f"{header} (part {part} of {len(pieces)})"
                chunks.append(
                    Chunk(
                        text=f"{label}\n\n{piece}",
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    if unstructured:
        for chunk in fallback_split(unstructured):
            chunks.append(chunk)

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
