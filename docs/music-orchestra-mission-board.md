# Music Stack Orchestra Mission Board

OpenClaw treats the music stack as a human-gated orchestra board. It does not
perform audio in v1. It reads metadata packets, prints safe routes, and turns
listening results into repo-specific PRs.

## Inputs

- `Music` emits a metadata-only `music-session-packet` through browser `SYNC`.
- `drum-floor` translates `routing.drum_floor` into groove controls with
  `translateMusicSessionPacket(packet)`.
- `namima` translates `routing.namima` into a family-safe mood with
  `translateMusicSessionPacket(packet)`.
- `chill` remains the live trio source of truth and is observed through
  `window.chillTrioSession.snapshot()`.

## Board Flow

1. Human opens Music and listens.
2. Human clicks `SYNC` in Music. No audio, recording, samples, or lyrics are
   sent.
3. Human opens the OpenClaw Pages `Packet Inspector`. The latest packet appears
   automatically when it was synced on `quietbriony.github.io`. JSON file
   selection and CLI `packet-inspect <packet.json>` remain Surface/localhost
   fallbacks.
4. `drum-floor` and `namima` can preview translations from the packet.
5. Human listens, chooses arm/skip/record manually, and writes notes.
6. Approved changes become small PRs in the owning repo.

## Review-Only Rules

Surface command:

```powershell
python .\openclaw_cli.py packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
```

- No automatic browser `START`, `STOP`, `REC`, OUTPUT, or mood control.
- No automatic Ableton, EP-133, MIDI arm, live slot, or upload.
- No audio files, samples, lyrics, raw microphone, or raw pointer streams.
- No copyrighted melody, chord sequence, sample reference, or song form copying.
- Generated local candidates stay under `.openclaw-local/` unless intentionally
  promoted as examples.

## Promotion

Promotion means "make a small repo-specific PR after human listening." It does
not mean automatic runtime mutation. A promotion note should name:

- packet/session id
- repo owner (`Music`, `drum-floor`, `namima`, `chill`, or `openclaw`)
- listening reason
- safety check
- rollback path

Rollback is standard git revert of the owning PR. OpenClaw keeps the board
boring on purpose: metadata in, human judgment, scoped PR out.
