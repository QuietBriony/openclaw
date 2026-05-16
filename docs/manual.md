# Music Stack OpenClaw Desk Manual

Music Stack OpenClaw Desk は、Music stack のための「人間確認つき制作卓」です。
Umbrel 常駐 runtime ではなく、Surface PC で Music Stack を見ながら
手元コントロール、live coding 的な試行、SYNC packet 確認、候補生成の
段取りをまとめる入口です。`openclaw-lab` 母艦、finance / LINE 系の共有
OpenClaw 導線そのものではありません。

公開 Pages は見るための入口で、実際の生成や候補確認は Surface PC の
ローカル CLI が行います。音を出す、録音する、armする、live coding する、
mergeする、という最終操作は人間が選びます。

## まず開くページ

- Music Stack OpenClaw Desk: <https://quietbriony.github.io/openclaw/>
- Packet Inspector Quickstart: [packet-inspector-quickstart.md](packet-inspector-quickstart.md)
- Current Stack Alignment: [current-stack-alignment.md](current-stack-alignment.md)
- Music: <https://quietbriony.github.io/Music/>
- chill: <https://quietbriony.github.io/chill/>
- chill trio: <https://quietbriony.github.io/chill/session.html>
- drum-floor: <https://quietbriony.github.io/drum-floor/>

## 役割

- `Music`: 母艦。最終 runtime、音色、producer habits、低域安全。
- `chill`: soft piano / sparse bass / やわらかメロディ / memory dots。
- `drum-floor`: raw live drums / pocket / browser trio drum surface / MIDI candidate。
- `namima`: mood / water interaction / coarse trace。
- `Music Stack OpenClaw Desk`: Surface操作、live coding前の段取り、manifest、local generate、inspect、human gate、repo横断の制作卓。

今のalignmentは [current-stack-alignment.md](current-stack-alignment.md) を基準にします。

## Public と Local

Public Pages に置いてよいもの:

- manifest
- connector registry
- command examples
- local packet inspector UI
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
python .\openclaw_cli.py plan sessions\examples\chill-trio-live.example.json
```

raw drum candidate export の流れを見る:

```powershell
python .\openclaw_cli.py plan sessions\examples\raw-drum-candidate-export.example.json
```

Music packet board の流れを見る:

```powershell
python .\openclaw_cli.py plan sessions\examples\music-orchestra-mission-board.example.json
```

repo harvest をPagesで見る:

1. Music Stack OpenClaw Desk を開く。
2. `Repo Harvest` までスクロールする。
3. `chill / test / namima-lab` のカードで、`拾う` と `拾わない` を見る。
4. 良さそうなら `このネタで次PR` を押し、コピーされた文をこのチャットへ貼る。
5. `JSON` はMusic側のreview-only sidecar、`Surface CLI` はローカル確認用。

repo harvest sidecar を見る:

```powershell
python .\openclaw_cli.py harvest-inspect ..\Music\docs\examples\repo-harvest-sidecars\chill.sidecar.json
python .\openclaw_cli.py harvest-inspect ..\Music\docs\examples\repo-harvest-sidecars\test.sidecar.json
python .\openclaw_cli.py harvest-inspect ..\Music\docs\examples\repo-harvest-sidecars\namima-lab.sidecar.json
```

これは「何を拾うか」「何をコピーしないか」「どのrepoへ渡すか」を読むだけです。
code、dependency、audio、sample、workflowはimportしません。

Music で `SYNC` した packet を読む:

Pagesで簡単に見る:

1. Music Stack OpenClaw Desk を開く。
2. Music Pagesで `SYNC` 済みなら latest packet が自動表示される。
3. `drum-floorへ` / `namimaへ` / `chillへ` / `OpenClaw` の review-only translation を読む。
4. Hazama FM から `SYNC` した場合は `Hazama FM cue` を読み、`techno balance` / `piano foreground` などの短い聴感タスクを次PR候補として扱う。
5. Surface CLIへ渡す時は `Surfaceへ保存` を押し、Downloadsへpacketを保存する。
6. JSON file chooser と貼り付け欄は、localhostの別portなどでSYNCが届かない時だけ使う。

Surface PC の CLI で見る:

```powershell
python .\openclaw_cli.py packet-import --latest-download
python .\openclaw_cli.py packet-inspect --latest
```

`packet-import` は最新のMusic packetをDownloadsから探し、
`.openclaw-local/inbox/latest-music-session-packet.json` と
`.openclaw-local/inbox/history/` にコピーします。`.openclaw-local/` はgitに載せません。

直接ファイルを指定するfallback:

```powershell
python .\openclaw_cli.py packet-import "$env:USERPROFILE\Downloads\<music-session-packet>.json"
python .\openclaw_cli.py packet-inspect "$env:USERPROFILE\Downloads\<music-session-packet>.json"
```

これは drum-floor / namima / chill への翻訳を表示するだけで、ブラウザ音声、録音、
候補生成、arm、upload は実行しません。

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

raw drum candidate を生成する:

```powershell
python .\openclaw_cli.py local-generate sessions\examples\raw-drum-candidate-export.example.json --candidate-id raw-drive-001 --execute --python $py
```

生成物はここに出ます:

```text
.openclaw-local/candidates/
```

## 聴く流れ

1. Music Stack OpenClaw Desk でセッションを選ぶ。
2. `plan` を読む。
3. `local-generate --execute` で候補を作る。
4. `preview.txt` と `drums.mid` を確認する。
5. Music / chill / drum-floor / namima を手動で開く。
6. 人間が聴いて、arm / skip / record / merge を決める。
7. このチャットで「もっとこう」と言う。
8. 必要な repo だけ小さく磨いて commit / push / Pages 確認する。

## 今の推奨セッション

`Chill Piano Bass Drum Trio`

- `chill`: main piano, elastic quiet bass, flow director, pressure, local score
- `drum-floor`: browser soft pocket follows chill `sessionShape`
- `OpenClaw`: plan, routing, observe-only human gates
- console: `window.chillTrioSession.snapshot()`

`Raw Drum Candidate Export`

- `OpenClaw`: `local-generate` and inspect
- `drum-floor`: `raw_live_drum_drive` + `raw_live_break_drive`
- output: `.openclaw-local/candidates/`
- no Ableton / EP-133 / chill transport auto-arm

`Music Orchestra Mission Board`

- `Music`: human clicks `SYNC` and reviews metadata-only packet
- `drum-floor`: translates `routing.drum_floor` to preview controls
- `namima`: translates `routing.namima` to family-safe mood
- `chill`: translates `routing.chill` to quiet piano/bass/trio stance
- no local-generate; use raw drum export only after human review

## drum-floor の3役

- `drum-floor standalone`: drum-floor Pagesで合成ドラムを手動previewする。Music SYNCでcontrolsが寄り、`再生` は人間が押す。
- `chill DRUMS`: chill/session内のsoft pocket。chillがピアノ、ベース、flow、START/PANICを所有する。
- `OpenClaw raw candidate`: Surface CLIでMIDI候補を生成/inspectする別導線。live arm、録音、uploadはしない。

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

Music Stack OpenClaw Desk は候補を作れますが、公開や録音や arm はしません。

## Safety

- No audio files.
- No samples.
- No lyrics.
- No copied melodies, chords, structures, or recordings.
- No secrets in public repos.
- No automatic upload.
- No workflow edits unless explicitly requested.
