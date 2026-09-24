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

---

## Milestone 4 — distances and the cutoff

`top_k` left at 5. Every one of my five questions puts a chunk containing the
answer at rank 1, so raising it would only have added loosely related material
below a result that was already right.

### The two groups

| # | Question | In corpus? | Best distance |
|---|---|---|---|
| 2 | How often do Marchwood's trams run on weekdays? | yes | 0.2275 |
| 3 | How many times a year does the access road to Elder Ness flood? | yes | 0.2807 |
| 1 | What time does the bakery in Kestrelford sell out? | yes | 0.3413 |
| 4 | Which town is easiest to get around with limited mobility? | yes | 0.3788 |
| 5 | Which evening is hardest to find a meal in this region? | yes | 0.4683 |
| — | What is the capital of Mongolia? | no | 0.8104 |
| — | What is the recommended dosage of ibuprofen for a headache? | no | 0.8351 |
| — | How do I write a for loop in Rust? | no | 0.8614 |
| — | How do I change the oil in a diesel engine? | no | 0.8809 |
| — | Who won the 1994 World Cup? | no | 0.9692 |

Gap: **0.4683 to 0.8104**, 0.342 wide, nothing inside it. Midpoint 0.639.

### The third group, which is the actual finding

The brief asks what I would get wrong at my chosen number. To answer that I had
to ask questions that are neither of the above — about places this corpus does
cover, for facts it does not contain.

| Question | Best distance | Top result |
|---|---|---|
| Which beaches near Halden Bay have lifeguards in August? | 0.3417 | Halden Bay — When to go |
| Is there a cinema in Kestrelford? | 0.3657 | Kestrelford — Where to stay |
| How do I get from Brightwater to Edinburgh? | 0.4205 | Brightwater — Getting there |
| What time does the bakery in Marchwood sell out? | 0.4211 | Marchwood — Eat and drink |
| What is the best restaurant in Paris? | 0.5827 | Kestrelford — Eat and drink |
| How much does a train ticket to the regional hub cost? | 0.6092 | Marchwood — Overview |

These sit **inside the in-corpus band**, not in the gap. "Is there a cinema in
Kestrelford?" is closer than three of my five real questions.

That is not a tuning problem. Distance measures whether the question is about
the same subject matter as some chunk, and these questions are. It cannot
measure whether the chunk contains the answer. No threshold refuses these and
still accepts real questions.

So the gate's real job is narrower than criterion 3 makes it sound: it catches
the far group and nothing else. Which changes how I picked the number.

### The cutoff: 0.70

Not the midpoint. Since the gate provably cannot catch near misses, raising the
cutoff costs almost nothing — the questions a higher cutoff lets through were
getting through anyway — while lowering it risks refusing real questions that
are worded worse than mine. My five in-corpus questions are optimistic: I wrote
them after reading the documents, so they use the corpus's own vocabulary. A
real user's phrasing will score worse.

0.70 gives 0.23 of headroom above my worst real question and keeps 0.11 of
margin below the nearest false accept.

| If my cutoff were | What would happen |
|---|---|
| 0.30 | Refuses Q1, Q4 and Q5 — three questions it has the answers to |
| 0.50 | Accepts all five, but only 0.03 clear of Q5. One badly worded question away from a wrong refusal |
| 0.70 (chosen) | All 5 real questions accepted, all 5 far questions refused. Near misses still get through — they always would |
| 0.85 | Starts accepting "What is the capital of Mongolia?" |

Verified at 0.70: 5 of 5 in-corpus pass, 5 of 5 out-of-corpus refused.

### The grounding layer

`generate.py::GROUNDING_INSTRUCTION` is what has to catch the near misses, and
it already says the right things — use only these documents, say when they
don't cover it, name the file. I read it against the near-miss list and left it
as it is. Tightening a prompt I cannot yet run is guessing; the honest move is
to name it as the untested half and test it in unit 2, where "Is there a cinema
in Kestrelford?" is the first question I will put through it.

---

## Milestone 5 — repo check

`python test.py`: 8 passed, 1 failed, 1 skipped. The failure and the skip are
both the missing `GEMINI_API_KEY` — no `.env` in this environment. Everything
that runs locally passes, including the embedding model and a Chroma cosine
round trip.

`python tools/smoke_test.py`: all checks passed, against the `practice` corpus
and the cross-cutting checks (cosine collection, gate behaviour, cache, budget
guard).

The chunker across all four corpora:

| Corpus | Chunks | Average | Produced by |
|---|---|---|---|
| city_guides | 95 | 317 | `split_documents` |
| campus_life | 88 | 317 | `fallback_split` |
| advice_threads | 27 | 478 | `fallback_split` |
| practice | 41 | 425 | `fallback_split` |

Only `city_guides` uses Markdown `##` headings, so it is the only corpus that
takes the section-aware path. The other three have no structure to split on and
fall through to fixed windows, which is the documented behaviour rather than a
silent failure — a plain-text corpus degrades to the starter's chunking instead
of becoming one chunk per file.

### Still outstanding

The generation stage has never run. Retrieval, the gate, and prompt assembly
are all verified against real output; the model call is not. That means:

- README "Sample Answer" has a real prompt and no answer.
- Criterion 2 (every answer names a source) is untested — `app.py` builds the
  sources line from retrieval metadata, so it should hold, but "should" is not
  a measurement.
- Criterion 5 (sources are correct) is untested for the same reason.
- `GROUNDING_INSTRUCTION` is unexercised, which is the gap that matters most,
  since the near-miss finding in Milestone 4 makes it the only thing standing
  between an uncovered question and a made-up answer.

To close all of these: put a key in `.env` and run

    python app.py ask "What time does the bakery in Kestrelford sell out?" --show-prompt
    python app.py ask "Is there a cinema in Kestrelford?"
