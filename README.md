# The Unofficial Guide

Youssef Shaaban · AI201 Project 1 · corpus: **`city_guides`**

> How the starter works, and every command, is in `RUNNING.md`.
> Working measurements and the reasoning behind each decision are in `NOTES.md`.
> The five acceptance criteria are in `criteria.md`.

---

# Unit 1

## What This Does

This is a retrieval-augmented question answering system over `city_guides`, a
set of 14 travel guides covering nine towns in a fictional region plus five
guides that cut across all of them — eating, walking, regional transport,
seasons, and accessibility. You ask a plain question and it answers from those
documents only, naming the file the answer came from.

It handles the kind of question a guidebook index can't: *"What time does the
bakery in Kestrelford sell out?"*, *"How often do Marchwood's trams run on
weekdays?"*, *"Which town is easiest to get around with limited mobility?"* —
questions whose answers are one sentence buried in a section of one document,
sometimes stated once across the whole corpus.

Questions the documents don't cover are refused rather than guessed at. A
relevance gate checks how close the best retrieved chunk actually is before the
model is called at all, so *"What is the capital of Mongolia?"* gets *"I don't
have enough information about that"* instead of a confident answer from the
model's training data.

## Chunking Strategy

**Chunk size:** 700 characters — a **ceiling**, not a target. Actual chunks run
183–661, averaging 317.
**Overlap:** 120 characters, and on this corpus it never fires. See below.

Every document here is Markdown: one `#` title, a short intro, then a run of
`##` sections. There are 98 such sections. The shortest is 23 characters, the
median is 282, the longest is 709. **Not one reaches 800.**

That single measurement decided the strategy. The starter's 800-character
window can never split one of these sections for being too long — so the only
thing it ever does is cut partway through a section and staple the tail onto
the next heading. 98 clean boundaries go in and 51 arbitrary ones come out,
including a 24-character orphan. The corpus is handing me correct boundaries in
its own markup and the starter is throwing them away.

So `chunker.py::split_documents` splits on the `##` headings. One section, one
chunk. The character cap stops deciding boundaries and becomes a guard against
a section too long to be a single thought.

**The part that isn't obvious: every chunk carries a `Document — Section`
header line inside its own text**, not just in its metadata. Two measured
reasons:

1. **`Practical notes` is byte-identical in all nine town guides** — the same
   277 characters about cash, mobile coverage and the nearest hospital. Split
   by section and stored as-is, that is nine chunks with identical text,
   identical embeddings, and no way for retrieval to prefer the right one or
   for a citation to mean anything. With the header line they are nine
   different strings. Counting distinct chunk texts: 9 collisions before, 0
   after.
2. **The nine town guides share all seven headings.** "Buses run four times a
   day" is unusable if nothing in the chunk says Halden Bay — unusable to the
   embedding model, which can't tell which town is being asked about, and to
   the answer model, which can't name the town it just read.

**This is what replaces overlap.** Overlap exists so a boundary doesn't orphan
the context that made a sentence mean something. Here the context that matters
is *which town, which topic*, and repeating that on every chunk carries it
better than 120 shared characters of the previous section would.

Where the two numbers came from:

- **700** because, left whole, section chunks come out 183–758 characters and
  exactly one is over it: `guide_accessibility.md` :: "Straightforward", which
  is three towns in three bold paragraphs. The cap is set where it takes that
  one apart at its paragraph breaks and leaves the other 94 alone — not at a
  round number.
- **120** only reaches the sentence-splitting path, which this corpus never
  enters. Between sibling paragraphs of one over-long section it is
  deliberately **not** applied: those paragraphs are about different towns, and
  carrying the last sentence of the Thornby Wells paragraph into the Marchwood
  chunk would put the wrong town's facts under a header claiming Marchwood.

**I changed my mind about one thing.** I had planned a minimum-size rule to
merge stub chunks into their neighbours, and wrote criterion 4's slack around
the possibility. Once the chunker ran, the smallest chunk was 183 characters
and read as a whole thought, so the rule would have been code that never
executes. I dropped it rather than ship it. The criterion keeps its original
slack, because criteria don't move after the fact.

### Before and after

    $ python app.py index    # starter's chunker
      chunked  51 chunks, 650 characters on average (shortest 24, longest 800),
               produced by chunker.py::fallback_split

    $ python app.py index    # mine
      chunked  95 chunks, 317 characters on average (shortest 183, longest 661),
               produced by chunker.py::split_documents

| | starter (`fallback_split`) | mine (`split_documents`) |
|---|---|---|
| Chunks | 51 | 95 |
| Average characters | 650 | 317 |
| Shortest | 24 | 183 |
| Longest | 800 | 661 |
| Duplicate chunk texts | 9 | 0 |

94 of the 95 are one whole section. The 95th is the second half of
"Straightforward".

## Sample Chunks

Printed by `python app.py chunks -n 5` and pasted unedited.

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility — Overview

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
Corry Vale — Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** — source: `guide_givens_mill.md#3` — produced by: `chunker.py::split_documents`

```
Givens Mill — Eat and drink

A tearoom attached to the mill, open 10 to 4 daily except Tuesdays, which sells bread made from the flour ground twenty metres away and is the reason most people come. One pub, food served lunchtimes and Thursday to Saturday evenings.
```

**Chunk 4** — source: `guide_kestrelford.md#6` — produced by: `chunker.py::split_documents`

```
Kestrelford — When to go

Late spring and early autumn. The Saturday market runs year-round but is much reduced from November to February. August is busy with walkers. The single-track approach road is genuinely difficult in snow and the town can be cut off for a day or two most winters.
```

**Chunk 5** — source: `guide_regional_transport.md#1` — produced by: `chunker.py::split_documents`

```
Getting around the region — Buses

Three operators run in the region and they do not accept each other's tickets,
which is the single most common source of confusion for visitors. Services
concentrate on weekday daytimes. Sunday service is minimal to non-existent
outside the Brightwater town routes.

The Kestrelford service is hourly on weekdays, two-hourly on Saturdays, and
does not run on Sundays. The Halden Bay coast service runs four times daily
year-round.
```

Reading them against the Milestone 3 test — *could someone answer a question
using only this?* — all five stand alone, and all five name their subject in
the first line. Chunk 1 is the weakest: it says the guide is honest about
difficulty without saying which places are difficult. It is a document intro,
so that is what it is, but it is the chunk I would expect to retrieve for a
question it cannot then answer.

## Sample Answer

> ⚠️ **Incomplete: the generated answer is missing.** Retrieval, the relevance
> gate, and prompt assembly all ran and their real output is below. The
> generation call did not — this environment has no `GEMINI_API_KEY`, and
> `generate.py` stops with `RuntimeError: No GEMINI_API_KEY found.` Rather than
> write an answer by hand and present it as system output, the model's part is
> left blank. To fill it in: put a key in `.env` and run the command below.

**Question:** What time does the bakery in Kestrelford sell out?

    $ python app.py ask "What time does the bakery in Kestrelford sell out?" --show-prompt

Retrieval and the gate, real output:

```
  (best distance 0.341, cutoff 0.7)
```

The assembled prompt, exactly as sent — this is what the answer can be based
on, and note that two independent documents in it carry the answer:

```
Documents:

[from guide_kestrelford.md]
Kestrelford — Eat and drink

Four pubs, two cafés, and a bakery that sells out by 11am. The pubs serve food between 12 and 2 and again between 6 and 8:30, and outside those windows there is nowhere to eat at all. The bakery is the reason most people come back.

[from guide_kestrelford.md]
Kestrelford — When to go

Late spring and early autumn. The Saturday market runs year-round but is much reduced from November to February. August is busy with walkers. The single-track approach road is genuinely difficult in snow and the town can be cut off for a day or two most winters.

[from guide_eating.md]
Eating across the region — Markets

Kestrelford's Saturday market has run since the 1400s and is the region's best,
though much reduced from November to February. Brightwater's Tuesday market
sets up at 7am in the square and is finished by 1pm. Marchwood's covered market
has operated since 1863, runs six days a week, and is at its best on a weekday
morning.

[from guide_eating.md]
Eating across the region — Local specifics

Halden Bay's seafood is genuinely fresh — the two harbour restaurants buy
directly from boats that land in the early morning. Givens Mill's tearoom sells
bread made from flour ground twenty metres away. Kestrelford's bakery sells out
by 11am and is the reason a lot of people return. Thornby Wells does Sunday
lunch as a local institution and it needs booking a week ahead.

[from guide_kestrelford.md]
Kestrelford — Getting around

Everything is within a ten-minute walk of the market square. The town is built on a slope and the walk up from the lower car park is steeper than it looks on a map. There is no local bus service within the town itself.

---

Question: What time does the bakery in Kestrelford sell out?

Answer using only the documents above, and name the file you used.
```

**Answer:**

```
(not produced — no API key in this environment; see the note above)
```

**Sources retrieved:** `guide_eating.md`, `guide_kestrelford.md`

<!-- app.py prints this line after the answer, so it wasn't printed on this
     run. Listed here from the retrieved chunks shown in the prompt above,
     which is the same set app.py builds it from. -->
Both contain the answer, so criterion 5 would pass on this question.

**My relevance cutoff:** **0.70**, set in `config.py`.

I ran my five test questions and the five in `OUT_OF_SCOPE` through
`app.py retrieve` and recorded the best distance for each. All ten rows:

| Question | In corpus? | Best distance |
|---|---|---|
| How often do Marchwood's trams run on weekdays? | yes | 0.2275 |
| How many times a year does the access road to Elder Ness flood? | yes | 0.2807 |
| What time does the bakery in Kestrelford sell out? | yes | 0.3413 |
| Which town in the region is easiest to get around with limited mobility? | yes | 0.3788 |
| Which evening of the week is hardest to find a meal in this region? | yes | 0.4683 |
| What is the capital of Mongolia? | no | 0.8104 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8351 |
| How do I write a for loop in Rust? | no | 0.8614 |
| How do I change the oil in a diesel engine? | no | 0.8809 |
| Who won the 1994 World Cup? | no | 0.9692 |

Two groups, cleanly separated. The gap runs **0.4683 to 0.8104** — 0.342 wide,
with nothing inside it. Midpoint 0.639.

**I did not pick the midpoint, and the reason is the most useful thing I found
in this project.** The brief asks what you'd get wrong at your chosen number.
To answer that I had to ask a third kind of question: about towns the corpus
*does* cover, for facts it does *not* contain.

| Near-miss question | Best distance |
|---|---|
| Which beaches near Halden Bay have lifeguards in August? | 0.3417 |
| Is there a cinema in Kestrelford? | 0.3657 |
| How do I get from Brightwater to Edinburgh? | 0.4205 |
| What time does the bakery in Marchwood sell out? | 0.4211 |
| What is the best restaurant in Paris? | 0.5827 |
| How much does a train ticket to the regional hub cost? | 0.6092 |

These land **inside the in-corpus band**, not in the gap. *"Is there a cinema in
Kestrelford?"* scores 0.3657 — closer than three of my five real questions.

That isn't a tuning problem. Distance measures whether a question is about the
same subject matter as some chunk, and these are. It cannot measure whether the
chunk contains the answer. **No threshold refuses these and still accepts real
questions.**

So the gate's real job is narrower than it looks: the far group, and nothing
else. Given that, raising the cutoff costs almost nothing — the near misses were
getting through at any usable value — while lowering it risks refusing real
questions worded worse than mine. And mine are optimistic: I wrote them after
reading the documents, so they use the corpus's own vocabulary.

0.70 leaves 0.23 of headroom above my worst real question and 0.11 of margin
below the nearest false accept.

| If my cutoff were | What would happen |
|---|---|
| 0.30 | Refuses Q1, Q4 and Q5 — three questions it has the answers to |
| 0.50 | Accepts all five, but only 0.03 clear of Q5 — one badly worded question from a wrong refusal |
| **0.70 (chosen)** | All 5 real questions accepted, all 5 far questions refused. Near misses still get through — they always would |
| 0.85 | Starts accepting "What is the capital of Mongolia?" |

Verified at 0.70: **5 of 5 in-corpus pass, 5 of 5 out-of-corpus refused.**

Catching the near misses is `GROUNDING_INSTRUCTION`'s job, in `generate.py`. I
read it against the list above and left it unchanged — it already says use only
these documents, admit when they don't cover the question, name the file.
Tightening a prompt I can't yet run would be guessing. It is the untested half
of this system, and *"Is there a cinema in Kestrelford?"* is the first thing I
will put through it in unit 2.

## How I Used AI

I built this in a Claude Code session, so AI was involved throughout. Two
moments where it actually changed the work:

**1. It wrote a confident claim about its own output that was wrong, and
printing the output caught it.**

I asked for the section-aware chunker, describing the strategy and the
`Document — Section` header line. What came back worked, and its docstring
stated that the one over-long section — `guide_accessibility.md` ::
"Straightforward", three towns in three bold paragraphs — would split into
"one chunk per town." Plausible, and it is what I wanted to happen.

It isn't what happens. The packer fills greedily, so Thornby Wells and
Marchwood share the first piece (568 characters) and Brightwater gets the
second (283). I only found it because I printed the split chunks instead of
trusting the description. I corrected the docstring to say 2 pieces and not 3,
and explained why I didn't chase one-town-per-chunk: it would need a rule that
splits on bold lead-ins, and that rule would be fitted to exactly one section
in the corpus. The fix was to the claim, not to the code.

**2. It filled in a measurement before the measurement existed, which is the
specific failure this assignment is built to prevent.**

While drafting `criteria.md` in Milestone 2, the "why this target" under
criterion 3 asks what the two groups of distances looked like — a Milestone 4
question. The draft that came back answered it: in-corpus 0.399–0.652,
out-of-corpus 0.845–1.014, cutoff 0.75. Specific, well-formatted, entirely
invented — Milestone 4 hadn't been run.

The numbers were plausible enough that they'd have survived a skim, which is
what makes this worth writing down. I deleted the block and left a comment
saying Milestone 4 would fill it in. The real numbers, measured two commits
later, are 0.2275–0.4683 and 0.8104–0.9692 with a cutoff of 0.70 — the shape of
the guess was right and every digit was wrong.

The general lesson I took: an AI is useful for the thing it can't do here, which
is decide what a target should be. It will happily produce the *results* of work
it hasn't done, and those are the outputs that need checking against a command I
ran myself.

<!-- No stretch features attempted. -->

---

# Unit 2

<!-- Added next unit. Unit 1 above stays as written. -->

## Run Log — Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks are whole, labelled sections | 9 of 10 |  |  |  |  |
| 5. Sources are correct, not merely present | 5 of 5 |  |  |  |  |

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

## The Improvement

**What I changed:**

**Why I picked it:**

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks are whole, labelled sections | 9 of 10 |  |  |  |  |
| 5. Sources are correct, not merely present | 5 of 5 |  |  |  |  |

**Did it help?**

## What's Still Broken

## What I'd Do Differently
