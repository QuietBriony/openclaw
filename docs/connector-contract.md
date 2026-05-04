# Connector Contract

OpenClaw v1 uses a minimal connector contract. The control plane can validate,
plan, and print safe commands, but it does not take over audio runtime control.

## Common API Shape

- `capabilities()`: describe the connector surface.
- `prepare(sessionManifest)`: validate intent and safety.
- `generate(intent)`: create a candidate only where the connector explicitly allows it.
- `inspect(candidateId)`: read-only safety check.
- `start/update/stop`: reserved for future browser runtime work and still human-gated.
- `snapshot()`: read runtime state without mutating sound.

## Music

`Music` is the final integrated runtime. OpenClaw may inspect:

- `window.MusicRuntimeState`
- `window.MusicSessionPacket.build()`
- `window.MusicSessionPacket.download()`
- `producerHabits`
- `genreTimbreKits`
- `referenceMorph`
- `signatureCells`
- `humanGroove`

OpenClaw v1 must not click `START`, `STOP`, `REC`, alter `OUTPUT`, or mutate the recorder.
The packet is local metadata only and remains a review sidecar until the human
chooses a repo-specific next step.

## Drum-Floor

Safe command references:

```powershell
python -m drum_floor generate --style <profile-id> --frame <optional-frame-id> --bpm <40-240> --bars <1-128> --energy <0-100> --seed <int> --out live/candidates/<candidate-id>
python -m drum_floor inspect live/candidates/<candidate-id>
```

OpenClaw only calls `local-generate` for a connector with:

- `generate_enabled: true`
- `intent.style`

Live browser manifests such as `Chill Trio Live` are observe-only and should
route candidate export to `sessions/examples/raw-drum-candidate-export.example.json`.

Allowed write area:

- `live/candidates/`
- `live/logs/`

Forbidden automatic write areas:

- `live/armed/`
- `live/archive/`
- Ableton project files
- EP-133 device state
- audio recordings or samples
- `.github/workflows`

Browser trio surface:

- `createDrumFloorSessionAdapter().snapshot()`
- `createDrumFloorSessionAdapter().applyMusicSessionPacket(packet)`
- `window.DrumFloorMusicSessionAdapter.translateMusicSessionPacket(packet)`
- `createDrumFloorSessionAdapter().previewBar()`
- `createDrumFloorSessionAdapter().diagnostics.previewSession()`

This surface is loaded by `chill/session.html` for manual trio audition. OpenClaw
may document and inspect it, but v1 must not use it to start browser audio, arm
drums, record, or bypass the human listening gate.

## Chill

OpenClaw may snapshot:

- `window.chillTrioSession.snapshot()`
- `window.chillAdapter.getRuntimeConfig()`
- `window.chillAdapter.session.previewBassBar()`
- `window.chillAdapter.diagnostics.previewEventStream()`
- `window.chillAdapter.diagnostics.runDeterminismCheck()`
- `chill:session:v1`
- `chill:recipe:v1`
- `chill:lastSeed`

OpenClaw v1 must not call `setIntent`, `setReference`, `schedule`,
`scheduleBassBar`, direct generator mutation, UI clicks, or Tone
transport/audio calls.

## Namima

OpenClaw may snapshot:

- `window.AudioEngine.started`
- `window.AudioEngine.mood`
- `window.AudioEngine.auto`
- `window.NamimaMusicSessionAdapter.translateMusicSessionPacket(packet)`
- `window.namimaAdapter.snapshot()`
- `profiles/mood-profiles.json`
- `namima:session-trace:v1` if present

OpenClaw v1 must not call `start`, `onTap`, `updateEnergy`, `setMood`, `setMoodProfile`, or `setAuto`.
Music packet translation is allowed as review context, but applying a mood in a
live browser remains a human-reviewed action.

If trace storage is added, it should remain local, capped, and coarse: mood,
visual mode, auto state, touch energy bands, x-position bands, and listening
notes. It must not store audio, microphone input, raw pointer streams, or exact
gesture captures.
