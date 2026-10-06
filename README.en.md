# Jev Cookbook · Give your AI agent a "judgment layer"

Mount **Jev** — TypeSafe's small, fast *judgment model* — into your own AI agent: which micro-decisions it should own, how to wire it in, how to validate it, and where it breaks.

> A field handbook from one month of real production use (Chinese & English). Not a concept intro, not an ad — read it and you can wire up your first decision point today.
>
> 中文版 → [README.md](README.md)

## The 30-second version

**What Jev is** — a model that only answers small questions and returns typed answers your code can use directly:

- **noul** — yes/no ("Is this command dangerous?") → probability 0–1
- **choice** — pick one from a set → selected option + per-option probabilities + confidence
- **score** — rate against a rubric → weighted score + confidence

**Why it matters** — an agent makes dozens of micro-decisions per turn (which search result to read first, which memory to keep, whether a command is risky, what to preserve when compacting). Large models are expensive, slow and distracted for those; hard-coded rules are brittle. A tiny judge that *just decides* — cheaply, in parallel, with calibrated probabilities — is the third way.

**What's in this repo** — everything from a month of running it in production:

| File | What |
|---|---|
| `docs/01` | Why a judgment layer (and why it isn't "a bigger model") |
| `docs/02` | Integration guide — 30 minutes to your first decision point |
| `docs/03` | Decision-point checklist — what's worth wiring, what isn't |
| `docs/04` | Shadow mode & per-task-family evaluation — earn trust before auto-acting |
| `docs/05` | Pitfalls — including our own failures |
| `scripts/jev_smoke.py` | Smoke test — verified working (stdlib only, never prints your key) |
| `scripts/jev_key_sweep.py` | Secret-leak surface scanner |
| `AGENTS.md` | Operating instructions for AI agents (let your agent read it) |

## Quick start

```bash
export TYPESAFE_API_KEY=...      # or OPENROUTER_API_KEY
python scripts/jev_smoke.py
```

One request carries a `state` (what to evaluate) plus a map of typed `questions`; each answer comes back structured — no text parsing.

## Six principles we earned the hard way

1. **Fail open** — if the judge is down or slow, behave exactly as if it didn't exist. It's an accessory, not a heart.
2. **Shadow first, autopilot later** — log its calls without acting on them, compare against reality for a week, then trust gradually.
3. **Release per task family** — we measured 90%+ reliability in some families and ~15% in others on the same task. Never one-shot the rollout.
4. **Only cheap questions go to the judge** — direction-setting and long-chain reasoning stay with the big model; red lines stay with the human.
5. **Log every decision** — input, answer, probability — that log is your license to trust it. No log, no rollout.
6. **Hard red lines never enter the judge** — spending, publishing, deleting stay human-gated. Deterministic code, not model discretion.

## Related projects

- **mu (μ)** — a coding agent with a tiny judge wired through its turn loop: <https://github.com/qybaihe/mu>
- **pi-jev** — Jev inside the Pi coding agent: <https://github.com/y0usaf/pi-jev>
- **hermes-jev** — Jev plugin for Hermes Agent: <https://github.com/kerpopule/hermes-jev-skills>
- **TypeSafe docs** — Jev's official documentation: <https://docs.typesafe.ai>

## License

MIT © 2026 zhaoyanan-pixe

> No secrets, no third-party code in this repo. All numbers are observations from one specific environment — treat them as reference, not promises.
