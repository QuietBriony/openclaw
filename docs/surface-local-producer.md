# Surface Local Producer

The public Music Stack OpenClaw Desk Pages site is a dashboard and contract surface. The actual
producer run can live on this Surface PC.

This repo is not the Umbrel OpenClaw runtime. It is the Surface-side desk for
manual control, live-coding-style exploration, Music `SYNC` packet review, and
local candidate generation before a human decides what to play, arm, record, or
merge.

## Public vs Local

Public:

- `https://quietbriony.github.io/openclaw/`
- manifests
- connector docs
- dry-run command examples
- human gates

Local only:

- `.openclaw-local/inbox/latest-music-session-packet.json`
- `.openclaw-local/inbox/history/`
- `.openclaw-local/candidates/`
- `.openclaw-local/runs/`
- generated MIDI candidates
- inspect results
- listening notes before PR

## Import The Latest Music Packet

From OpenClaw Pages, click `Surfaceへ保存` after Music `SYNC`.
Then import the newest valid packet from Downloads:

```powershell
python .\openclaw_cli.py packet-import --latest-download
python .\openclaw_cli.py packet-inspect --latest
```

This copies metadata only. It does not start browser audio, record, upload,
arm gear, or call an external OpenClaw subscription.

## Generate A Candidate

From `C:\workspace\music-stack\openclaw`:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
python .\openclaw_cli.py local-generate sessions\examples\raw-drum-candidate-export.example.json --candidate-id raw-drive-001 --execute --python $py
```

This runs `drum-floor generate`, then `drum-floor inspect`, and writes a local
run log. It does not arm Ableton, EP-133, Music REC, or any live slot.

`local-generate` only works when a manifest has a connector with
`generate_enabled: true` and `intent.style`. `chill-trio-live.example.json` is
observe-only; open `chill/session.html` for that live session.

## Human Gates

After a local generate:

1. Inspect stdout and local preview.
2. Listen manually.
3. Decide arm or skip.
4. Record only from Music/chill/drum-floor by human action.
5. Convert useful listening notes into small repo-specific PRs.

## Safety

- No secrets in public repos.
- No generated traces committed.
- No automatic upload.
- No audio files or samples added.
- No reference melody, chord progression, or recording copy.
