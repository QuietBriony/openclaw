# OpenClaw

OpenClaw is the human-gated session control plane for the QuietBriony music stack.

It does not make sound in v1. It reads contracts, prints safe dry-run steps, and keeps `Music`, `drum-floor`, `chill`, and `namima` in their own lanes.

## Stack Roles

- `Music`: final integrated runtime and internal producer.
- `drum-floor`: pocket candidate generator and inspector.
- `chill`: soft piano / room reference, snapshot only.
- `namima`: GI mood, water interaction, and coarse local trace context.
- `test`: style morph archive, not a runtime connector.

## Quick Start

Run from this directory:

```powershell
python -m openclaw validate sessions/examples/music-stack-session.example.json
python -m openclaw plan sessions/examples/music-stack-session.example.json
python -m openclaw inspect-connectors
python -m openclaw drum-floor-command sessions/examples/music-stack-session.example.json
```

If your Python runtime runs in isolated safe-path mode, use the local shim:

```powershell
python .\openclaw_cli.py validate sessions/examples/music-stack-session.example.json
python .\openclaw_cli.py plan sessions/examples/music-stack-session.example.json
```

The CLI is dry-run oriented. It does not arm live slots, start browser audio, record, upload, or write to GitHub.

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
