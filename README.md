# OpenClaw

OpenClaw is the human-gated session control plane for the QuietBriony music stack.

It does not make sound in v1. It reads contracts, prints safe dry-run steps, and keeps `Music`, `drum-floor`, `chill`, and `namima` in their own lanes.

Pages dashboard: <https://quietbriony.github.io/openclaw/>

The dashboard includes a local Packet Inspector: choose a Music `JSON` download
to review drum-floor / namima routing without upload, recording, arm, or generate.

Manual: [docs/manual.md](docs/manual.md)

Music Orchestra Mission Board: [docs/music-orchestra-mission-board.md](docs/music-orchestra-mission-board.md)

## Stack Roles

- `Music`: final integrated runtime and internal producer.
- `drum-floor`: pocket candidate generator, inspector, and trio drum surface.
- `chill`: soft piano / sparse bass / room reference, snapshot only from OpenClaw.
- `namima`: GI mood, water interaction, and coarse local trace context.
- `test`: style morph archive, not a runtime connector.

## Quick Start

Run from this directory:

```powershell
python -m openclaw validate sessions/examples/music-stack-session.example.json
python -m openclaw doctor
python -m openclaw plan sessions/examples/music-stack-session.example.json
python -m openclaw plan sessions/examples/music-orchestra-mission-board.example.json
python -m openclaw packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
python -m openclaw inspect-connectors
python -m openclaw drum-floor-command sessions/examples/music-stack-session.example.json
python -m openclaw plan sessions/examples/soft-piano-raw-drum-drive.example.json
python -m openclaw plan sessions/examples/chill-trio-live.example.json
python -m openclaw plan sessions/examples/raw-drum-candidate-export.example.json
python -m openclaw local-generate sessions/examples/soft-piano-raw-drum-drive.example.json --execute
```

If your Python runtime runs in isolated safe-path mode, use the local shim:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
python .\openclaw_cli.py validate sessions/examples/music-stack-session.example.json
python .\openclaw_cli.py doctor --python $py
python .\openclaw_cli.py plan sessions/examples/music-stack-session.example.json
python .\openclaw_cli.py plan sessions/examples/music-orchestra-mission-board.example.json
python .\openclaw_cli.py packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
python .\openclaw_cli.py plan sessions/examples/soft-piano-raw-drum-drive.example.json
python .\openclaw_cli.py plan sessions/examples/chill-trio-live.example.json
python .\openclaw_cli.py plan sessions/examples/raw-drum-candidate-export.example.json
python .\openclaw_cli.py local-list
python .\openclaw_cli.py local-generate sessions/examples/raw-drum-candidate-export.example.json --candidate-id raw-drive-001 --execute --python $py
```

The CLI is dry-run oriented. It does not arm live slots, start browser audio, record, upload, or write to GitHub.

Use `doctor` first when checking this Surface setup. It confirms the local
producer path and reports whether a separate external OpenClaw CLI or token is
visible without printing secret values.

`local-generate` is only enabled for manifests with a connector marked
`generate_enabled: true` and an `intent.style`. It writes generated candidates
and run traces under `.openclaw-local/`, which is ignored by git. It still does
not arm, record, upload, or push.

`packet-inspect` reads a Music `JSON` download and prints review-only
drum-floor / namima routing translations. It does not execute the translations.

## V1 Contract

The v1 manifest is documented in `schemas/session-manifest.v1.schema.json`.

Required gates:

- `before_arm`
- `before_record`
- `before_merge`

Required connectors:

- `music`
- `drumFloor`
- `chill`
- `namima`

## Safety

- No audio files.
- No samples.
- No lyrics.
- No dependencies.
- No workflow files.
- No automatic Ableton, EP-133, Music REC, or browser transport control.
- No copied reference melodies, chords, structures, or sample gestures.

OpenClaw is a conductor desk, not a hidden performer.

## Chill Trio

`sessions/examples/chill-trio-live.example.json` treats `chill` as the
piano/bass/flow source of truth and `drum-floor` as the browser drum surface.

- Open <https://quietbriony.github.io/chill/session.html>
- Use `START`, `BASS`, `DRUMS`, `AUTO`, and `PANIC` manually.
- Check `window.chillTrioSession.snapshot()` in the browser console.
- Use `sessions/examples/raw-drum-candidate-export.example.json` for local drum candidates under `.openclaw-local/`.
