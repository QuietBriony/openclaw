# Current Music Stack Alignment

This is the current operating map for the Music Stack. OpenClaw reads the stack
as metadata, routes the next listening task, and keeps every runtime
human-gated.

## Current Sources

- `Music`: integrated producer and packet source. Hazama FM is at v172 groove
  conversation, and Band Room has PWA/lifecycle, timeline seek, source-derived
  part agents, and Drum Floor handoff.
- `Hazama FM`: live listening surface. It exposes genre/source/role,
  `review_cue`, listening trace, and v172 internal groove conversation for
  human review. Other repos receive metadata only, not audio or melodies.
- `Band Room`: album/stem room. It can hand a current song/frame to Drum Floor
  as a manual preview packet. It should not wake Namima unless Music explicitly
  routes to `namima`.
- `drum-floor`: manual synthetic drum preview, raw candidate CLI, and chill
  soft-pocket adapter. It never arms Ableton, EP-133, or browser audio by
  itself.
- `chill`: quiet piano trio surface. START, BASS, DRUMS, AUTO, PANIC remain
  owned by chill and by the human.
- `namima`: public-friendly ambient surface. It translates safe mood, water,
  garden, transparent evening, and soft sleep from Music metadata.
- `OpenClaw`: conductor desk. It validates packets, reads routing, writes local
  candidates only under `.openclaw-local/`, and turns listening notes into small
  repo-specific changes.

## Routing Rules

- `SYNC` is metadata-only.
- Browser/PWA receivers may adjust controls or visible mood, but audio starts
  only after human action.
- `review_cue` from Hazama FM becomes a next listening task, not an automatic
  PR.
- Band Room drum handoff targets Drum Floor unless Music explicitly says
  otherwise.
- Namima must stay family-safe: no dark glitch, low-end pressure, raw trace,
  samples, lyrics, or uploads.

## Recommended Passes

1. Music or Hazama FM: listen and click `SYNC`.
2. OpenClaw: read latest packet and choose one repo target.
3. Target repo: make one small change, then run local browser/static checks.
4. Commit and push per repo.
5. Confirm all Music Stack target repos are clean and open PR count is zero.
