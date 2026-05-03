# Session Runbook

This is the first OpenClaw v1 session loop.

Producer desk routing: [producer-desk-routing.md](producer-desk-routing.md)

## Flow

1. `plan`: validate `SessionManifest v1` and print connector actions.
2. `generate candidates`: print the `drum-floor` command; the human decides whether to run it.
3. `inspect`: inspect the candidate before any manual arm.
4. `human listen`: Music remains the center; decide whether pocket, chill, or namima context helps.
5. `arm/skip`: only the human can arm external gear or live slots.
6. `trace`: keep coarse notes and local snapshot context.
7. `PR tuning`: convert listening observations into small repo-specific PRs.

## First Practical Session

- Open `Music` and start it manually.
- Enable AUTO MIX manually if desired.
- Watch `window.MusicRuntimeState.producerHabits`, `genreTimbreKits`, `signatureCells`, and `humanGroove`.
- Use OpenClaw to print a `drum-floor` candidate command.
- Run `drum-floor inspect` before any manual arm.
- Keep `chill` behind Music as low-density piano room, or skip it.
- Use `namima` as mood and interaction context, not as a raw performance recorder.

## Soft Piano + Raw Drum Drive Session

- `Music` stays the main producer and low-end safety source.
- `chill` selects `soft-melody-piano` when the human wants soft piano answers and memory dots.
- `drum-floor` uses `raw_live_drum_drive` with `raw_live_break_drive` to print a live drum drive candidate.
- OpenClaw only prints generate and inspect commands; any arm, routing, recording, or merge remains human-gated.

## Listening Gate

Pass conditions:

- Music remains the main producer.
- Pocket candidate does not crowd the kick/bass floor.
- Chill piano does not become lead melody unless explicitly chosen.
- Namima trace is coarse context only.
- No bright EDM drift, bass overload, dense repeat fatigue, copied motif, sample, lyric, or dependency drift.

## Merge Gate

Before merging any tuning PR:

- State what was heard.
- Name which connector influenced the change.
- Confirm no `.github/workflows` edit.
- Confirm no audio files, samples, lyrics, or dependencies.
- Prefer small parameter changes over new runtime surfaces.
