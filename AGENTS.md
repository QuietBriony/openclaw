# AGENTS.md — openclaw repo operating contract

この repo を触る agent (claude code / codex / 他) が **最初に読む** ルール。
music-stack 全体の自走開発エンジンは `Music/docs/autonomy/` にある。

---

## この repo の役割

music-stack の **control desk / session planner**。Surface PC 上の
**human-gated production desk** で、自分は音を鳴らさない。

- Music `SYNC` packet の inspection
- `drum-floor` / `chill` / `namima` への drum-floor candidate planning と routing
- safe next-step routing — packet を読み routing option を表示し、人間が叩く
  CLI command を組み立てる

review 専用。実行・arm・record・merge の判断は人間が持つ。

---

## Hard rules（絶対守る）

openclaw 固有の境界:

1. **arm / record / merge を自動実行しない。** v1 gate は `before_arm` /
   `before_record` / `before_merge` で、常に人間が通す。
2. **Ableton / EP-133 / browser playback / Music REC を自動操作しない。**
3. **review とコマンド提示のみ。** 実行は人間。CLI は dry-run 指向。
4. **external API 呼び出し・upload・GitHub への write をしない。**

共通ルール（music-stack 全 repo):

5. **音源 / サンプル / 歌詞を repo に追加しない**。reference melody・chord・
   structure もコピーしない。
6. **dependency を勝手に足さない**（CLI は Python stdlib のみ）。
7. **GitHub Actions（workflow file）を勝手に足さない** — 追加は人間承認必須。
8. **archive / delete / settings を触らない。**

main runtime ファイル（変更時は特に慎重に）:

- `openclaw/` package — `cli.py` / `planner.py` / `connectors.py` /
  `contracts.py` / `packet_inspector.py` / `harvest_inspector.py` /
  `local_runner.py` / `surface_inbox.py` / `doctor.py`（routing 本体）
- `openclaw_cli.py` — safe-path shim entry
- `index.html` — dashboard PWA shell
- `sw.js` / `manifest.webmanifest` — PWA service worker / manifest
- `schemas/session-manifest.v1.schema.json` — v1 manifest 契約
- `connectors/registry.json` — connector registry

---

## Integrity gate

commit 前に repo root から **両方を 0 終了** で通す:

```
node scripts/check-pwa-static.mjs
python -m pytest tests/ -q
```

`0 BAD` / 全 pass の状態でのみ commit する。
5 repo 一括検証は Music repo root の `node scripts/stack-check.mjs`。

---

## Cache buster discipline

`sw.js` の cache version 変数は `const VERSION = \`${CACHE_PREFIX}-v3\`;`
（`CACHE_PREFIX = "openclaw-pwa"`、現在値 `openclaw-pwa-v3`）。

UI（`index.html` 等）や precache 対象を変えたら:

1. `sw.js` の `VERSION` を `v3 → v4` のように bump（`PRECACHE_URLS` も更新）。
2. `scripts/check-pwa-static.mjs` は `VERSION` の値を pin 検証するので、
   その assert 文字列も同じ値に揃える。
3. `node scripts/check-pwa-static.mjs` を 0 終了で確認。

---

## Branch & PR convention

| 状況 | 推奨 |
|---|---|
| docs only | main 直 push 可 |
| 非 runtime コード（test / script の微修正等） | feature branch → PR |
| runtime / routing / schema を変える（`openclaw/` package・`index.html`・`sw.js`・`schemas/`） | feature branch → PR → 人間レビュー |

作業前に **必ず `git pull --ff-only origin main`** で最新化する。

---

## Autonomous development

自走開発の入口・待ち行列・記録は `Music/docs/autonomy/`:

- `STACK-INDEX.md` — 5 repo の構造マップ（最初に読む）
- `BACKLOG.md` — 優先度付き作業待ち行列
- `SESSION-LEDGER.md` — 追記専用のセッション台帳
- `AUTONOMOUS-RUN.md` — 自律ランのプレイブック

自律ランの安全上限:

- ✅ docs は main 直 push 可
- ✅ 非 runtime コードは feature branch + PR まで（merge は人間）
- ❌ runtime / routing / schema は人間レビュー必須
- ❌ 無人 merge は不可
- ❌ arm / record / 実行系の自動操作・GitHub Actions 追加・dependency 追加・
  archive 操作は不可

詳細は `Music/docs/autonomy/AUTONOMOUS-RUN.md` を参照。
