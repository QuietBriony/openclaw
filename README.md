# OpenClaw

OpenClaw は QuietBriony music stack のための、人間確認つき制作卓です。

v1では音を鳴らしません。Music の `SYNC` を読み、`drum-floor` / `namima`
へ渡す制作判断を整理し、必要ならローカルCLIの予備手順も出します。

Pages dashboard: <https://quietbriony.github.io/openclaw/>

Pages dashboard では、Music で `SYNC` した最新packetを自動で読み、
drum-floor / namima / chill へのroutingを確認できます。Hazama FM から
`SYNC` した場合は、`techno balance` や `piano foreground` のような
review cue も次の聴感タスクとして表示します。アップロード、録音、arm、
生成はしません。JSON選択はlocalhostなどでSYNCが届かない時のfallbackです。

Manual: [docs/manual.md](docs/manual.md)

Packet Inspector Quickstart: [docs/packet-inspector-quickstart.md](docs/packet-inspector-quickstart.md)

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
python -m openclaw packet-import --latest-download
python -m openclaw packet-inspect --latest
python -m openclaw packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
python -m openclaw harvest-inspect ..\Music\docs\examples\repo-harvest-sidecars\chill.sidecar.json
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
python .\openclaw_cli.py packet-import --latest-download
python .\openclaw_cli.py packet-inspect --latest
python .\openclaw_cli.py packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
python .\openclaw_cli.py harvest-inspect ..\Music\docs\examples\repo-harvest-sidecars\chill.sidecar.json
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

`packet-inspect` is the Surface CLI fallback for a downloaded Music packet.
The usual browser flow is `MusicでSYNC -> OpenClawを開く -> latestを自動表示`.
Neither path executes the translations.

`harvest-inspect` reads a repo harvest sidecar, such as the examples under
`../Music/docs/examples/repo-harvest-sidecars/`, and prints what to harvest,
what not to copy, target repos, safety flags, and the next small PR. It is
review-only and does not import code, dependencies, audio, samples, or workflows.

Use `Surfaceへ保存` on the Pages inspector, then import it locally:

```powershell
python .\openclaw_cli.py packet-import --latest-download
python .\openclaw_cli.py packet-inspect --latest
```

Imported packets are copied to `.openclaw-local/inbox/`, which is ignored by
git. The latest pointer is `.openclaw-local/inbox/latest-music-session-packet.json`.

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
