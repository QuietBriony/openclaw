# Surface Local Producer

The public OpenClaw Pages site is a dashboard and contract surface. The actual
producer run can live on this Surface PC.

## Public vs Local

Public:

- `https://quietbriony.github.io/openclaw/`
- manifests
- connector docs
- dry-run command examples
- human gates

Local only:

- `.openclaw-local/candidates/`
- `.openclaw-local/runs/`
- generated MIDI candidates
- inspect results
- listening notes before PR

## Generate A Candidate

From `C:\workspace\github-inventory\music-stack\openclaw`:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
python .\openclaw_cli.py local-generate sessions\examples\soft-piano-raw-drum-drive.example.json --execute --python $py
```

This runs `drum-floor generate`, then `drum-floor inspect`, and writes a local
run log. It does not arm Ableton, EP-133, Music REC, or any live slot.

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
