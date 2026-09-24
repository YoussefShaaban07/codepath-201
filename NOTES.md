# Working notes

Scratch observations made while building. Not part of the submission checklist —
kept because the README asks me to point at things I noticed, and this is where
I noticed them.

---

## Milestone 1 — reading the corpus

Corpus: **`city_guides`**. 14 documents, 28,958 characters, ~2,068 characters
per document.

Nine of the fourteen are town guides (Brightwater, Corry Vale, Elder Ness,
Givens Mill, Halden Bay, Kestrelford, Marchwood, Pellew Sands, Thornby Wells).
The other five cut across all of them: eating, walking, regional transport,
seasons, accessibility.

### Shape

Every document is Markdown: one `#` title, a short intro paragraph, then a run
of `##` sections. The nine town guides use an identical seven-heading template:

    Getting there · Getting around · Eat and drink · What to see ·
    Where to stay · When to go · Practical notes

Measured over the whole corpus (`##` sections, plus each document's
title+intro, counted as one unit each):

| | |
|---|---|
| Sections | 98 |
| Shortest | 23 characters |
| Median | 282 characters |
| Mean | 292 characters |
| Longest | 709 characters (`guide_accessibility.md` :: "Straightforward") |
| Over 500 characters | 5 |
| Under 200 characters | 10 |

**Every section in this corpus fits inside 800 characters.** That is the fact
Milestone 3 turns on.

### What the starter's chunker does to that

    $ python app.py --corpus city_guides index
      loaded   14 documents, 28,958 characters, ~2,068 characters per document
      chunked  51 chunks, 650 characters on average (shortest 24, longest 800),
               produced by chunker.py::fallback_split

98 natural sections go in and 51 fixed windows come out. Because no section is
as long as the 800-character window, the window never splits a section for
being too big — it only ever cuts in an arbitrary place partway through one and
staples the tail onto whatever heading came next. The 24-character chunk is the
leftover tail of a document that didn't divide evenly.

So the damage is not "chunks too big" or "chunks too small". It is that the
boundaries are in the wrong places entirely, and the corpus hands me the right
ones for free in its own markup.

### Two things I found that change the design

**1. `Practical notes` is byte-identical in all nine town guides.**

The same 277 characters — cash, mobile coverage, nearest hospital — appear at
the bottom of every town guide. Chunked naively by section, that is nine chunks
with identical text and therefore identical embeddings. Retrieval would order
them arbitrarily and cite whichever one came back first, which is a citation
that means nothing.

This is the reason my chunker prepends a `Document › Section` breadcrumb to
every chunk's **text**, not just to its metadata. Once the text reads
"Kestrelford › Practical notes: …" the nine chunks are nine different strings
that embed differently, and the model sees which town it is reading about.

It matters for the ordinary sections too. "Buses run four times a day" is an
unusable chunk if nothing in it says Halden Bay.

**2. The corpus contradicts itself about the nearest hospital.**

`guide_accessibility.md` :: Practical says *"The nearest full hospital is in
Marchwood."* The `Practical notes` block repeated in all nine town guides says
*"The nearest full hospital is in Brightwater."*

Not something I should fix — the job is to answer from the documents, not to
correct them. Noting it because it is exactly the kind of question where a
grounded system should end up citing a source and a confident ungrounded one
would just pick one. Deliberately not one of my five test questions: it has no
single right answer, so it fails the "specific enough to have a right answer"
bar in Milestone 2.

---

## Milestone 1 — the number to write down

Asked for separately in the brief, regardless of corpus choice:

    $ python app.py --corpus advice_threads chunks -n 1
    26 chunks total.

**26.**

---

## Milestone 3 — after the swap

    $ python app.py index
      loaded   14 documents, 28,958 characters, ~2,068 characters per document
      chunked  95 chunks, 317 characters on average (shortest 183, longest 661),
               produced by chunker.py::split_documents

| | starter (`fallback_split`) | mine (`split_documents`) |
|---|---|---|
| Chunks | 51 | 95 |
| Average | 650 | 317 |
| Shortest | 24 | 183 |
| Longest | 800 | 661 |
| Duplicate chunk texts | 9 | 0 |

94 of the 95 are one whole `##` section. The 95th exists because
`guide_accessibility.md` :: "Straightforward" is 758 characters with the header
line and splits into two pieces at a paragraph break.

The 24-character chunk is gone, because nothing is now cut at a position that
can leave a 24-character remainder.

The nine byte-identical `Practical notes` blocks are now nine distinct strings.
Checked directly rather than assumed: counting distinct chunk texts gives 95 out
of 95, against 9 collisions before.

The minimum-size merge I hedged against in criterion 4 never came up — the
smallest chunk is 183 characters and reads as a whole thought — so I did not
write one. The criterion keeps its slack as written.
