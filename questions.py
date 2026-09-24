"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.

────────────────────────────────────────────────────────────────────────────
MY FIVE (corpus: city_guides)

Written in Milestone 2, before I replaced the chunker and before I had seen a
single retrieval result.

Every `expects` phrase below is a string that appears verbatim in at least one
document, so a unit 2 substring scorer has something exact to match rather than
something I have to re-judge by eye each run.

Q1-Q4 are each answered explicitly in two documents — the town's own guide and
one of the five cross-cutting guides. Q5 is answered in exactly one sentence in
exactly one document, which is why criterion 1 in criteria.md says 4 of 5 and
not 5 of 5.
────────────────────────────────────────────────────────────────────────────
"""

QUESTIONS = [
    {
        # guide_kestrelford.md :: Eat and drink — "a bakery that sells out by 11am"
        # guide_eating.md :: Local specifics — "Kestrelford's bakery sells out by 11am"
        "question": "What time does the bakery in Kestrelford sell out?",
        "expects": "11am",
    },
    {
        # guide_marchwood.md :: Getting around — "running every 8 minutes on weekdays"
        # guide_accessibility.md :: Straightforward — "every 8 minutes on weekdays"
        "question": "How often do Marchwood's trams run on weekdays?",
        "expects": "8 minutes",
    },
    {
        # guide_elder_ness.md :: Getting there — "roughly six times a year"
        # guide_walking.md :: Serious — "about six times a year"
        "question": "How many times a year does the access road to Elder Ness flood?",
        "expects": "six",
    },
    {
        # guide_accessibility.md :: Straightforward — "Thornby Wells is the easiest
        #   town in the region"
        # guide_walking.md :: Easy — "the region's most accessible town on foot"
        "question": "Which town in the region is easiest to get around with limited mobility?",
        "expects": "Thornby Wells",
    },
    {
        # guide_eating.md :: Opening hours — "Sunday evening is the hardest meal to
        #   find anywhere except Marchwood and Thornby Wells". One sentence, one
        #   document. This is the question I expect to be hardest to retrieve, and
        #   the reason criterion 1 is 4 of 5.
        "question": "Which evening of the week is hardest to find a meal in this region?",
        "expects": "Sunday",
    },
]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
#
# Kept as shipped. They are the right shape for what criterion 3 measures — the
# gate catching questions from a different world — and swapping in five of my
# own invention would have tested the same thing with less evidence behind it.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
