# システム概要

## アーキテクチャ

Nanobanana Designer Agent は、自然言語の指示から画像デザインを生成する2フェーズ構成のAIエージェントシステムです。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Designer Agent                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────────┐   │
│  │ ユーザー入力  │───▶│ Phase 1: 設計 │───▶│ Phase 2: 実行      │   │
│  │ (自然言語)    │    │ (Gemini 2.0)  │    │ (各ツール呼び出し)  │   │
│  └──────────────┘    └───────────────┘    └────────────────────┘   │
│                             │                        │              │
│                             ▼                        ▼              │
│                      ┌───────────┐           ┌─────────────────┐   │
│                      │ 設計JSON  │           │ PNG + SVG 出力   │   │
│                      └───────────┘           └─────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 処理フロー

### Phase 1: 設計フェーズ

ユーザーの自然言語指示を Gemini 2.0 Flash で解析し、構造化された設計JSONを生成します。

**入力例:**
```
背景は青空、左下に緑色の三角形シェイプを配置、
タイトルは「Hello World」を中央上部に白文字で表示
```

**出力例（設計JSON）:**
```json
{
  "background": {
    "prompt": "青空、晴れた日の空、雲が浮かぶ"
  },
  "illustration": {
    "type": "polygon",
    "points": [[0, 400], [0, 1080], [600, 1080]],
    "fill": {
      "type": "solid",
      "color": "#4CAF50"
    },
    "opacity": 1.0
  },
  "title": {
    "text": "Hello World",
    "x": 960,
    "y": 400,
    "fontSize": 64,
    "color": "#ffffff"
  },
  "subtitle": null
}
```

### Phase 2: 実行フェーズ

設計JSONに基づいて各要素を順番に生成し、最終的に合成します。

```
Step 1: 背景生成
   │
   ├── text-to-image モード: text_to_background ツール
   │   └── Gemini 2.5 Flash Image で背景画像を生成
   │
   └── image-to-image モード: image_to_background ツール
       └── 参考画像のスタイルを参照して新規背景を生成
   │
   ▼
Step 2: イラスト生成
   │
   └── draw_illustration ツール
       └── Pillow で幾何学シェイプを透過PNGとして描画
   │
   ▼
Step 3: タイトル生成
   │
   └── text_to_title ツール
       └── Pillow でテキストを透過PNGとして描画
   │
   ▼
Step 4: サブタイトル生成
   │
   └── text_to_subtitle ツール
       └── Pillow でテキストを透過PNGとして描画
   │
   ▼
Step 5: PNG合成
   │
   └── compose_slide ツール
       └── 全要素を重ね合わせて最終PNG画像を生成
   │
   ▼
Step 6: SVG合成
   │
   └── compose_slide_svg ツール
       └── 全SVG要素を合成して編集可能なSVGを生成
       └── Adobe Illustrator で各レイヤーを個別編集可能
```

### SVG生成の詳細

各要素は PNG と並行して SVG としても生成されます：

| 要素 | PNG生成 | SVG生成 | 編集 |
|------|---------|---------|------|
| 背景 | Gemini生成画像 | ラスター埋め込み | 再生成で対応 |
| イラスト | draw_illustration（Pillow） | ネイティブSVG | 編集可能 |
| タイトル | text_to_title（Pillow） | SVGテキスト | 編集可能 |
| サブタイトル | text_to_subtitle（Pillow） | SVGテキスト | 編集可能 |

**背景のSVG**:
- 画像をそのままSVG内に埋め込み（品質劣化なし）
- 変更が必要な場合は再生成で対応

**テキスト・シェイプのSVG**:
- ネイティブSVG要素として出力（編集可能）
- フォント: Hiragino Sans（Illustrator互換）

## キャンバス仕様

- **サイズ**: 1920 x 1080 ピクセル（16:9）
- **座標系**: 左上が (0, 0)、右下が (1920, 1080)
- **テキスト座標**: 中心基準で指定

### 座標の目安

| 位置 | X座標 | Y座標 |
|------|-------|-------|
| 中央 | 960 | 540 |
| 左上 | 200 | 200 |
| 右上 | 1720 | 200 |
| 左下 | 200 | 880 |
| 右下 | 1720 | 880 |
| タイトル位置 | 960 | 400 |
| サブタイトル位置 | 960 | 500 |

## 動作モード

### text-to-image モード

プロンプトのみで新規画像を生成します。

```python
agent = DesignerAgent()
result = agent.generate("青空の背景にタイトル「Hello」")
```

### image-to-image モード

参考画像を元に新規画像を生成します。参考画像のスタイル、構図、雰囲気を参照しつつ、新しい画像を生成します。

```python
agent = DesignerAgent()
result = agent.generate(
    "この画像のスタイルで新しいデザインを作成",
    image_base64=reference_image_base64
)
```

**重要**: image-to-image モードでは、参考画像をそのまま編集するのではなく、参考画像のスタイルを参照して新規に生成します。

## 出力ファイル構成

```
output/                     # PNG画像
├── background/             # 背景画像
│   └── SESSION_ID.png
├── illustration/           # イラスト（透過PNG）
│   └── SESSION_ID.png
├── title/                  # タイトル（透過PNG）
│   └── SESSION_ID.png
├── subtitle/               # サブタイトル（透過PNG）
│   └── SESSION_ID.png
└── result/                 # 最終合成画像
    └── SESSION_ID.png

output_svg/                 # SVGファイル
├── background/             # 背景SVG（ラスター埋め込み）
│   └── SESSION_ID.svg
├── illustration/           # イラストSVG
│   └── SESSION_ID.svg
├── title/                  # タイトルSVG
│   └── SESSION_ID.svg
├── subtitle/               # サブタイトルSVG
│   └── SESSION_ID.svg
└── result/                 # 最終合成SVG
    └── SESSION_ID.svg
```

セッションIDは `XXXX-YYYY` 形式（例: `SYV4-1867`）で自動生成されます。

### SVG出力の特徴

- **編集可能**: Illustrator で各レイヤーを個別に編集可能
- **レイヤー構造**: background / illustration / title / subtitle の4レイヤー
- **ID属性**: 各レイヤーに id 属性を付与（Illustrator でレイヤー名として認識）
- **スケーリング**: 背景SVGは自動的にキャンバスサイズにスケーリング

## 使用モデル

| 用途 | モデル |
|------|--------|
| 設計解析 | gemini-2.0-flash |
| 背景画像生成 | gemini-2.5-flash-image |

## エラーハンドリング

各ツールはエラー時に以下の形式でレスポンスを返します：

```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

エージェントはエラーが発生しても処理を継続し、生成可能な要素のみで合成を試みます。
