# Producer Desk Routing

This Music chat can act as the producer desk for the whole stack.

The shape is:

1. The human gives musical intent here.
2. OpenClaw turns that intent into a manifest, dry-run commands, and runbook gates.
3. Repo-specific agents make small bounded changes.
4. The human listens, arms, records, merges, or rejects.

The Surface PC can run local candidate export with `openclaw local-generate`,
but only for manifests that explicitly mark a connector with
`generate_enabled: true`. Live runtime sessions stay human-operated in the
browser. The public Pages site stays a readable contract; generated candidates
and traces stay under `.openclaw-local/`.

## Agent Roles

- `Music Agent`: final runtime, producer habits, genre kits, low-end safety, recorder compatibility.
- `Chill Agent`: live trio source of truth: piano, elastic quiet bass, flow director, pressure, local score.
- `Drum-Floor Agent`: raw live drum drive, pocket candidates, MIDI preview, inspect/score loop.
- `Namima Agent`: GI mood, coarse trace, water interaction safety.
- `OpenClaw Agent`: session manifest, connector contract, Pages dashboard, human gates.

## Current Session Direction

`Chill Trio Live` + `Raw Drum Candidate Export`

- `chill` owns the live trio and `window.chillTrioSession.snapshot()`.
- `drum-floor` provides browser drum grammar to chill and raw MIDI candidates to OpenClaw.
- `Music` remains a separate integrated producer session, not the chill trio master.
- `namima` contributes mood context only.
- OpenClaw routes live observe vs candidate export and keeps arm/record/merge manual.

## Rules

- Do not add audio files, samples, lyrics, dependencies, or workflow files.
- Do not auto-arm Ableton, EP-133, browser REC, or live slots.
- Do not copy reference melodies, chord progressions, song structures, or recordings.
- Prefer one small repo-specific PR over a large cross-stack rewrite.
- Listening notes become code changes only after human review.
