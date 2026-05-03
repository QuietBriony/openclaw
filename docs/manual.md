# OpenClaw Manual

OpenClaw は、Music stack のための「人間確認つき制作卓」です。

公開 Pages は見るための入口で、実際の生成は Surface PC のローカル CLI が行います。

## まず開くページ

- OpenClaw Main Desk: <https://quietbriony.github.io/openclaw/>
- Music: <https://quietbriony.github.io/Music/>
- chill: <https://quietbriony.github.io/chill/>
- chill trio: <https://quietbriony.github.io/chill/session.html>
- drum-floor: <https://quietbriony.github.io/drum-floor/>

## 役割

- `Music`: 母艦。最終 runtime、音色、producer habits、低域安全。
- `chill`: soft piano / sparse bass / やわらかメロディ / memory dots。
- `drum-floor`: raw live drums / pocket / browser trio drum surface / MIDI candidate。
- `namima`: mood / water interaction / coarse trace。
- `OpenClaw`: manifest、local generate、inspect、human gate、repo横断の制作卓。

## Public と Local

Public Pages に置いてよいもの:

- manifest
- connector registry
- command examples
- docs
- manual

Surface PC だけに置くもの:

- `.openclaw-local/candidates/`
- `.openclaw-local/runs/`
- generated MIDI
- inspect logs
- listening notes before PR

Pages に secrets、録音、生成履歴、private trace は置きません。

## 基本操作

Surface PC の terminal で:

```powershell
cd C:\workspace\github-inventory\music-stack\openclaw
```

最初に doctor で環境を確認:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
python .\openclaw_cli.py doctor --python $py
```

ここで確認できること:

- repo-local OpenClaw CLI があるか
- `Music / drum-floor / chill / namima` が揃っているか
- `drum-floor` CLI が呼べるか
- 外部 `openclaw` CLI が PATH にあるか
- `OPENCLAW_API_KEY / OPENCLAW_TOKEN / OPENAI_API_KEY` が存在するか

secret の値は表示しません。

セッションの流れを見る:

```powershell
python .\openclaw_cli.py plan sessions\examples\soft-piano-raw-drum-drive.example.json
```

chill trio の流れを見る:

```powershell
python .\openclaw_cli.py plan sessions\examples\chill-piano-bass-drum-trio.example.json
```

候補を生成して inspect する:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
python .\openclaw_cli.py local-generate sessions\examples\soft-piano-raw-drum-drive.example.json --execute --python $py
```

すでに同じ candidate がある場合は上書きしません。既存候補を見る:

```powershell
python .\openclaw_cli.py local-list
```

新しい出力名で生成する:

```powershell
python .\openclaw_cli.py local-generate sessions\examples\soft-piano-raw-drum-drive.example.json --candidate-id raw-drive-002 --execute --python $py
```

chill trio 用に生成する:

```powershell
python .\openclaw_cli.py local-generate sessions\examples\chill-piano-bass-drum-trio.example.json --candidate-id trio-drive-001 --execute --python $py
```

生成物はここに出ます:

```text
.openclaw-local/candidates/
```

## 聴く流れ

1. OpenClaw Main Desk でセッションを選ぶ。
2. `plan` を読む。
3. `local-generate --execute` で候補を作る。
4. `preview.txt` と `drums.mid` を確認する。
5. Music / chill / drum-floor / namima を手動で開く。
6. 人間が聴いて、arm / skip / record / merge を決める。
7. このチャットで「もっとこう」と言う。
8. 必要な repo だけ小さく磨いて commit / push / Pages 確認する。

## 今の推奨セッション

`Chill Piano Bass Drum Trio`

- `chill`: main piano and sparse bass
- `drum-floor`: browser soft pocket plus local raw drum candidate
- `OpenClaw`: plan, local-generate, inspect, human gates
- console: `window.chillTrioSession.snapshot()`

`Soft Piano + Raw Drums`

- `Music`: main producer
- `chill`: `soft-melody-piano`
- `drum-floor`: `raw_live_drum_drive` + `raw_live_break_drive`
- `namima`: mood context only

## 各 repo を磨く時

このチャットで方向を言えば、そのまま repo ごとに切れます。

例:

- 「chillをもっとピアノ専門に」
- 「drum-floorをもっと生ドラムで荒く」
- 「Musicがdrum-floor候補を受けやすいmixに」
- 「OpenClawのmanifestをセッション別に増やして」

基本方針:

- 1 repo 1 役割。
- 小さい PR / commit に分ける。
- 生成物や listening trace は public に出さない。

## Human Gates

必ず人間が決めるもの:

- Ableton / EP-133 / live slot arm
- Music REC
- recording
- upload
- merge
- release

OpenClaw は候補を作れますが、公開や録音や arm はしません。

## Safety

- No audio files.
- No samples.
- No lyrics.
- No copied melodies, chords, structures, or recordings.
- No secrets in public repos.
- No automatic upload.
- No workflow edits unless explicitly requested.
