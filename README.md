# Epistemic Marketplace

Submit a claim. Fourteen philosophers argue about it for three rounds. The
output is not an answer — it is a map of where the disagreement actually is.

Most multi-agent systems are built to converge. This one is built to show you
what survives when people who reason differently look at the same thing, and
to be honest about the fact that they do not agree.

---

## The agents

Each philosopher exists for a test none of the others makes.

| | The first move it makes |
|---|---|
| **Hume** | Which impression does this trace back to? Where did it leap from *is* to *ought*? |
| **Kant** | What must already be true for this to be thinkable at all? |
| **Aristotle** | Define the term before judging it. What is the thing *for*? |
| **Nietzsche** | Not whether it is true — who does it serve, and what was made unthinkable to hold it? |
| **Wittgenstein** | Is this a question, or a knot in language that dissolves on inspection? |
| **Nagarjuna** | Run the tetralemma. Do these terms have any nature of their own? |
| **Spinoza** | Nothing is contingent. Is this an adequate idea or a passion speaking? |
| **Marx** | What mode of production does this belong to? Whose interest does it serve? |
| **Jung** | What does the position disown? What is it compensating for? |
| **Adler** | Not what caused it — what is it *for*, in the life of whoever holds it? |
| **Kierkegaard** | What would it cost to actually live by this? |
| **Dostoevsky** | Put it in a person and follow it. Can it be lived? |
| **Weil** | Was this formed by looking at the people inside it, or reached over their heads? |
| **James** | What concrete difference would its truth make? |

Every one of them also declares, in its own prompt, **where its method
systematically fails** — Nietzsche that genealogy is a genetic fallacy waiting
to happen, Jung that his framework can absorb any evidence, Dostoevsky that a
vivid counter-example is not a refutation. That is not decoration. An agent
with no declared blind spot argues its corner forever and adds nothing to a
marketplace of positions, and there is a test that will not let one be added
without one.

## How a debate runs

**Round 1 — independent.** Each agent sees only the claim. No contact.

**Round 2 — cross-challenge.** Each agent sees every other position *and the
cruxes behind them*, issues named challenges, and restates where it stands.

**Round 3 — synthesis.** Each agent receives **the challenges addressed to it**
and its own track so far, answers them, and gives a final position.

## Two numbers, not one

Every position carries two:

- **`probability_true`** — the plain shared scale, identical in meaning from
  every agent. This is what gets averaged, charted and compared.
- **`belief_score`** — that agent's own verdict, in whatever its method
  actually weighs.

They are separate because they measure different things. Dostoevsky scores
whether a claim survives being *lived*; Hume a degree of expectation from
experience; Spinoza how *adequate* the idea is. Averaging those would add
quantities that are not the same quantity. Where the two diverge is usually
the most interesting thing on the card.

## The ranking

After each debate, three philosophers who **took no part in it** read the full
transcript and score every participant on four criteria:

- **Method** — did it reason the way its own declared method requires?
- **Engagement** — did it answer what was actually said, or a convenient version?
- **Cruxes** — was what it said would change its mind a real condition that could fail?
- **Responsiveness** — did it move when given reason, and hold when not? Both
  stubbornness and drift score low.

The means become pairwise results inside the debate and move an Elo from 1500.

Judges score **craft, not agreement** — asking philosophers who was *right*
would measure how many of the other schools happen to be sympathetic to
yours. That narrows the bias without removing it, so judge severity is
published on the ranking page rather than hidden.

**Nothing here measures being right.** There is no ground truth for most of
these claims, and deciding one would mean appointing someone to declare it.

### Ranked and exhibition debates

Only debates marked `ranked` feed the Elo and the per-agent statistics. A
visitor gets the whole experience — the rounds, the jury, the scores, all
stored and readable — but an open deployment would otherwise let whoever runs
the most debates reshape the ranking, and the corpus is only meaningful
because participation is balanced. Set `ALLOW_RANKED_DEBATES=true` to build
the corpus; leave it off in public.

## Running it

```bash
# Postgres and Redis
brew services start postgresql@17
redis-server /opt/homebrew/etc/redis.conf --daemonize yes

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # DATABASE_URL, REDIS_URL, GEMINI_API_KEY
alembic upgrade head          # the app does NOT create tables
uvicorn app.main:app --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

A free key from [Google AI Studio](https://aistudio.google.com/apikey) is
enough. The debates run on `gemini-3.8-live` rather than the regular endpoint,
which allows only about twenty requests a day on the free tier — one debate.

```bash
cd backend && pytest        # 98 tests, no database, no model calls
```

## Built with

FastAPI · SQLAlchemy 2.0 async · PostgreSQL (Neon) · Alembic · Redis pub/sub ·
WebSockets · Next.js · D3 · Recharts

The chart palette is not Tailwind's. The obvious choice fails a colourblindness
check against this app's surface — blue and cyan land below the discrimination
floor for *normal* vision, and emerald and rose collapse under deuteranopia.
The set in `frontend/src/lib/agentColors.ts` passes every check, and colour is
assigned per debate because there are more agents than validated slots.

## Balancing a corpus

The twelve debates in the current corpus use **complementary partitions**: for
each claim the fourteen agents split into two halves of seven, and each half
argues it separately. Every agent debates every claim exactly once, every
agent participates the same number of times, and all 91 possible pairs meet —
so the Elo is not confounded by which topics an agent happened to draw.
