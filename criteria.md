# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Corpus:** `city_guides` — 14 documents, 28,958 characters.
**Test questions:** the five in `QUESTIONS` in `questions.py`.
**Out-of-corpus questions:** the five in `OUT_OF_SCOPE` in the same file.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Four of my five questions are answered explicitly in two documents each — the
town's own guide and one of the five cross-cutting guides. Q1 (the Kestrelford
bakery) is in `guide_kestrelford.md` and `guide_eating.md`; Q2 (Marchwood's
trams) is in `guide_marchwood.md` and `guide_accessibility.md`; and so on. Two
independent chances at `top_k=5` is a lot of margin, so those four should
land.

Q5 is the reason this is 4 of 5 and not 5 of 5. "Which evening is hardest to
find a meal" is answered in one sentence in one document —
`guide_eating.md` :: Opening hours — and the word "Sunday" appears in eight
other documents attached to bus timetables and shop closures. I expect the
question to pull Sunday-flavoured chunks about opening hours in general and to
have to be lucky to get the one sentence that actually answers it. Setting this
to 5 of 5 would mean claiming I had solved that before measuring it.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
All five and not four because this one is structural rather than probabilistic.
`app.py` prints a `Sources retrieved:` line from the retrieved chunks' metadata
on every answer that gets past the gate, so it does not depend on the model
choosing to cooperate. For this to come out below 5 of 5, something would have
to be genuinely broken — a chunk stored without its `source` metadata, or the
pipeline answering from something it didn't retrieve. Either of those is a
defect I want the criterion to catch, which is why I am not giving it slack.

Note that this criterion is deliberately the weak version: it asks whether a
source is *named*, not whether the named source is the *right* one. Criterion 5
is the strong version.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. -->

**Why this target:**
Written in Milestone 2, before measuring: 4 of 5 rather than 5 of 5 because the
cutoff is a single number doing a job that a single number can only mostly do.
My five out-of-corpus questions are not equally far away. "How do I write a for
loop in Rust?" shares no vocabulary with a travel guide at all, but "What is
the recommended dosage of ibuprofen for a headache?" contains health vocabulary
and my corpus talks about minor injuries units and hospitals in nine documents.
I expect that one to sit closest to the cutoff, and I would rather name a
target that survives one near-miss than a perfect score I then have to explain
away.

<!-- Milestone 4 fills in what the two groups of distances actually looked like,
     directly underneath. The target above does not move. -->

---

## 4. Chunks are whole, labelled sections

At least 9 of 10 chunks I sample read as a complete thought: the chunk begins at
the start of a section and ends at the end of one, no sentence is cut in half at
either end, and the name of the town or guide the chunk describes appears inside
the chunk's own text rather than only in its metadata.

**Why this target:**
The starter's chunker turns 98 natural sections into 51 fixed 800-character
windows. No section in this corpus reaches 800 characters, so the window never
splits a section for being too long — it only ever cuts partway through one and
staples the tail onto the next heading. Whole sections are therefore available
for free in the markup, and a chunker that can't reach 9 of 10 is not doing the
one thing it exists to do.

Not 10 of 10, for two reasons I can point at. One section in the corpus
(`guide_accessibility.md` :: "Straightforward", 709 characters) is long enough
that a future cap could split it mid-paragraph. And ten sections are under 200
characters, short enough that merging them into a neighbour to avoid stub chunks
would produce a chunk covering two headings — which is a chunk I would have to
count as failing this criterion even though merging was the right call.

The "names the town in its own text" half is not decoration. `Practical notes`
is byte-identical in all nine town guides — the same 277 characters about cash,
mobile coverage and the nearest hospital. Split by section and stored as-is,
that is nine chunks with identical text, identical embeddings, and no way for
retrieval to prefer the right one or for the model to know which town it is
reading about.

---

## 5. Sources are correct, not merely present

For all 5 of my test questions, the source document named alongside the answer
is a document that actually contains the answer — not merely a document that
happened to be retrieved.

**Why this target:**
Criterion 2 is satisfied by a system that names a source at random, and on this
corpus that is a live risk rather than a theoretical one: the nine identical
`Practical notes` blocks mean a naive pipeline can cite `guide_pellew_sands.md`
for a fact it actually read in `guide_kestrelford.md`, with a perfectly
reasonable-looking source line. A citation that is confidently wrong is worse
than no citation, because it survives a spot check.

All 5 and not 4 because every one of my questions is answered in a named
document I can point at, so a wrong attribution is a defect rather than bad
luck — and because this is the thing the whole breadcrumb design in my chunker
is supposed to buy. If it can't hold 5 of 5, that design didn't work and I want
the criterion to say so out loud.

I check it by hand: for each question, read the `Sources retrieved:` line, open
the file it names, and confirm the answer is in there.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
