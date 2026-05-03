# Producer Desk Routing

This Music chat can act as the producer desk for the whole stack.

The shape is:

1. The human gives musical intent here.
2. OpenClaw turns that intent into a manifest, dry-run commands, and runbook gates.
3. Repo-specific agents make small bounded changes.
4. The human listens, arms, records, merges, or rejects.

## Agent Roles

- `Music Agent`: final runtime, producer habits, genre kits, low-end safety, recorder compatibility.
- `Chill Agent`: soft piano, gentle melody, memory dots, quiet recovery.
- `Drum-Floor Agent`: raw live drum drive, pocket candidates, MIDI preview, inspect/score loop.
- `Namima Agent`: GI mood, coarse trace, water interaction safety.
- `OpenClaw Agent`: session manifest, connector contract, Pages dashboard, human gates.

## Current Session Direction

`Soft Piano + Raw Drum Drive`

- `Music` remains the main producer.
- `chill` specializes in `soft-melody-piano`.
- `drum-floor` provides `raw_live_drum_drive` candidates.
- `namima` contributes mood context only.
- OpenClaw prints commands and keeps arm/record/merge manual.

## Rules

- Do not add audio files, samples, lyrics, dependencies, or workflow files.
- Do not auto-arm Ableton, EP-133, browser REC, or live slots.
- Do not copy reference melodies, chord progressions, song structures, or recordings.
- Prefer one small repo-specific PR over a large cross-stack rewrite.
- Listening notes become code changes only after human review.
