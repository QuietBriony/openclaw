# SYNC最短手順

Music の `SYNC` は音ではありません。今の Music の状態を、drum-floor、
namima、chill、OpenClaw に渡すための短い地図です。

## いちばん簡単な使い方

1. Music を開く: <https://quietbriony.github.io/Music/>
2. `START` して、良い瞬間まで聴く。
3. Music の `SYNC` を押す。
4. OpenClaw を開く: <https://quietbriony.github.io/openclaw/>
5. `Packet Inspector` に latest SYNC が自動表示される。
6. `drum-floorへ`、`namimaへ`、`chillへ` のどれで遊ぶか決める。
7. 行き先を開いて、音を出すボタンだけ押す。
   - drum-floor: `AI Live / 再生`
   - namima: `Tap to start`
   - chill: `START`

JSONファイル選択と貼り付け欄は、localhostの別portなどでSYNCが届かない時のfallbackです。

## 結果の見方

- `Musicの今`: その瞬間の energy、void、haze、micro。まずここで雰囲気を見る。
- `drum-floorへ`: ドラムに渡すなら profile、frame、kit、bpm がどうなるか。
- `namimaへ`: 水面/庭/家族向け ambient に渡すなら mood がどうなるか。
- `chillへ`: ピアノ/ベース/trioに渡すなら reference、Touch、Phrase、Room がどうなるか。
- `Next`: 次に人間が何を頼むか。
- `このチャットへ投げる`: そのまま貼れる指示文。

## このチャットで言うこと

Music を磨くなら:

```text
このpacketの方向で、Musicをもう少し音色広げて
```

drum-floor に渡すなら:

```text
このpacketで、drum-floorを候補生成できる形にして
```

namima に渡すなら:

```text
このpacketのmoodで、namimaをfamily-safeに寄せて
```

chill に渡すなら:

```text
このpacketで、chillのピアノ/ベース/trioを柔らかく磨いて
```

OpenClaw に任せるなら:

```text
このpacketで次PR切って。生成や録音はまだしないで
```

画面上では、上のような文を `指示文をコピー` で作れます。

## やらないこと

- JSONをアップロードしない。
- 音声、録音、サンプル、歌詞を保存しない。
- Music REC、Ableton、EP-133、live slot を自動操作しない。
- 生成やmergeは、人間が確認してから。
