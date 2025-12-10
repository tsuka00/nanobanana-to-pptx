# ツール一覧

Designer Agent で使用可能なツールの詳細仕様です。

## 背景生成ツール

### text_to_background

テキストプロンプトから背景画像を生成します。

**ファイル**: `agents/tools/text_to_background.py`

**使用モデル**: `gemini-2.5-flash-image`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| prompt | str | 必須 | - | 背景画像のプロンプト |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた画像データ",
  "mime_type": "image/png"
}
```

**仕様**:
- 出力サイズ: 1920x1080（16:9固定）
- 画像内にテキストは含まれません
- Gemini 2.5 Flash Image で生成

**使用例**:

```python
from agents.tools import text_to_background

result = text_to_background._tool_func(
    prompt="青空と白い雲、晴れた夏の日"
)
```

---

### image_to_background

参考画像を元に新しい背景画像を生成します。

**ファイル**: `agents/tools/image_to_background.py`

**使用モデル**: `gemini-2.5-flash-image`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| prompt | str | 必須 | - | 生成指示プロンプト |
| image_base64 | str | 必須 | - | 参考画像のBase64データ |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた画像データ",
  "mime_type": "image/png"
}
```

**仕様**:
- 参考画像のスタイル、構図、雰囲気を参照して新規生成
- 参考画像をそのまま編集するのではなく、新しい画像を生成
- 出力サイズ: 1920x1080（16:9固定）

---

## イラスト描画ツール

### draw_illustration

JSONパラメータから幾何学シェイプを描画します（透過PNG）。

**ファイル**: `agents/tools/draw_illustration.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| shape | dict | 必須 | - | シェイプ定義（後述） |

**シェイプ定義**:

```json
{
  "type": "polygon | rectangle | ellipse | triangle",
  "points": [[x1, y1], [x2, y2], ...],
  "x": 0,
  "y": 0,
  "width": 200,
  "height": 200,
  "fill": {
    "type": "solid | gradient",
    "color": "#RRGGBB",
    "start": "#RRGGBB",
    "end": "#RRGGBB",
    "direction": "vertical | horizontal | diagonal"
  },
  "opacity": 1.0
}
```

**シェイプタイプ別パラメータ**:

| タイプ | 必須パラメータ |
|--------|----------------|
| polygon | points |
| rectangle | x, y, width, height |
| ellipse | x, y, width, height |
| triangle | points（3点） |

**塗りつぶし設定**:

| fill.type | 必須パラメータ |
|-----------|----------------|
| solid | color |
| gradient | start, end, direction |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた透過PNG",
  "mime_type": "image/png"
}
```

**仕様**:
- 出力サイズ: 1920x1080（透過PNG）
- Pillow で描画
- グラデーション対応（縦、横、斜め）
- 不透明度調整可能（0.0〜1.0）

**使用例**:

```python
from agents.tools import draw_illustration

# 緑色のグラデーション三角形
result = draw_illustration._tool_func(shape={
    "type": "polygon",
    "points": [[0, 400], [0, 1080], [600, 1080], [300, 400]],
    "fill": {
        "type": "gradient",
        "start": "#4CAF50",
        "end": "#81C784",
        "direction": "diagonal"
    },
    "opacity": 1.0
})
```

---

## テキスト描画ツール

### text_to_title

タイトルテキストを透過PNGとして描画します。

**ファイル**: `agents/tools/text_to_title.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| text | str | 必須 | - | タイトルテキスト |
| x | int | 任意 | 960 | X座標（テキスト中心） |
| y | int | 任意 | 400 | Y座標（テキスト中心） |
| font_size | int | 任意 | 64 | フォントサイズ |
| color | str | 任意 | "#ffffff" | 文字色 |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた透過PNG",
  "mime_type": "image/png"
}
```

**仕様**:
- 出力サイズ: 1920x1080（透過PNG）
- フォント: Noto Sans CJK JP Regular
- 座標はテキストの中心位置を指定
- Pillow で描画

**使用例**:

```python
from agents.tools import text_to_title

result = text_to_title._tool_func(
    text="Hello World",
    x=960,
    y=400,
    font_size=72,
    color="#ffffff"
)
```

---

### text_to_subtitle

サブタイトルテキストを透過PNGとして描画します。

**ファイル**: `agents/tools/text_to_subtitle.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| text | str | 必須 | - | サブタイトルテキスト |
| x | int | 任意 | 960 | X座標（テキスト中心） |
| y | int | 任意 | 500 | Y座標（テキスト中心） |
| font_size | int | 任意 | 36 | フォントサイズ |
| color | str | 任意 | "#ffffff" | 文字色 |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた透過PNG",
  "mime_type": "image/png"
}
```

**仕様**:
- `text_to_title` と同様の仕様
- デフォルトのフォントサイズとY座標が異なる

---

## 合成ツール

### compose_slide

各要素を合成してスライド画像を生成します。

**ファイル**: `agents/tools/compose_slide.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| background_base64 | str | 任意 | None | 背景画像のBase64 |
| illustration_base64 | str | 任意 | None | イラスト画像のBase64 |
| illustration_x | int | 任意 | 0 | イラストのX座標（左上） |
| illustration_y | int | 任意 | 0 | イラストのY座標（左上） |
| title_base64 | str | 任意 | None | タイトル画像のBase64 |
| subtitle_base64 | str | 任意 | None | サブタイトル画像のBase64 |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた合成画像",
  "mime_type": "image/png"
}
```

**合成順序**:

1. 白紙キャンバス（1920x1080）
2. 背景画像（リサイズしてフィット）
3. イラスト画像（透過合成）
4. タイトル画像（透過合成）
5. サブタイトル画像（透過合成）

**仕様**:
- 出力サイズ: 1920x1080（RGB、透過なし）
- 要素がない場合はスキップ
- 透過PNG はアルファ合成

---

## SVGツール

### image_to_svg

ラスター画像をSVG内に埋め込みます。

**ファイル**: `agents/tools/image_to_svg.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| image_base64 | str | 必須 | - | 埋め込む画像のBase64データ |
| width | int | 任意 | 1920 | SVGの幅 |
| height | int | 任意 | 1080 | SVGの高さ |

**戻り値**:

```json
{
  "success": true,
  "svg": "<svg>...</svg>"
}
```

**仕様**:
- 画像をそのままSVG内に埋め込み（品質劣化なし）
- 背景画像の再生成で対応するため、ベクター変換は行わない
- `preserveAspectRatio="xMidYMid slice"` でアスペクト比を維持

---

### draw_illustration_svg

幾何学シェイプをSVG要素として描画します。

**ファイル**: `agents/tools/draw_illustration_svg.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| shape | dict | 必須 | - | シェイプ定義（draw_illustrationと同じ形式） |

**戻り値**:

```json
{
  "success": true,
  "svg": "<svg>...</svg>"
}
```

**仕様**:
- ネイティブSVG要素（polygon, rect, ellipse）を出力
- グラデーション対応（linearGradient使用）
- Illustratorで編集可能なベクターシェイプ

---

### text_to_title_svg

タイトルテキストをSVGとして生成します（スタイルプリセット対応）。

**ファイル**: `agents/tools/text_to_title_svg.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| text | str | 必須 | - | タイトルテキスト |
| x | int | 任意 | 960 | X座標（テキスト中心） |
| y | int | 任意 | 400 | Y座標（テキスト中心） |
| font_size | int | 任意 | 64 | フォントサイズ |
| font_family | str | 任意 | "Hiragino Sans" | フォントファミリー |
| font_weight | str | 任意 | "bold" | フォントの太さ |
| color | str | 任意 | "#ffffff" | 文字色 |
| style | str | 任意 | "flat" | スタイルプリセット名 |
| fill | dict/str | 任意 | None | グラデーション設定 |
| glow_color | str | 任意 | None | グロー色（neon-glow用） |

**スタイルプリセット**:

| スタイル | 説明 | 特徴 |
|----------|------|------|
| `flat` | シンプルな単色 | 軽量 |
| `shadow` | ドロップシャドウ | 可読性向上 |
| `3d-metallic` | 3D/メタリック/ホログラム | 立体感、光沢、虹色反射 |
| `neon-glow` | ネオン発光 | 複数レイヤーのグロー |
| `glass` | ガラス風 | 透明感 |
| `outline` | アウトライン | ストロークのみ |
| `gold` | ゴールド | 金色グラデーション |
| `silver` | シルバー | 銀色グラデーション |
| `emboss` | エンボス | 浮き彫り |
| `gradient` | グラデーション | 2色グラデーション |

**戻り値**:

```json
{
  "success": true,
  "svg": "<svg>...</svg>"
}
```

**使用例**:

```python
from agents.tools import text_to_title_svg

# 3Dメタリックスタイル
result = text_to_title_svg._tool_func(
    text="TITLE",
    x=960,
    y=400,
    font_size=100,
    style="3d-metallic",
    fill={
        "type": "gradient",
        "start": "#00FF00",
        "end": "#00FFFF",
        "direction": "diagonal"
    }
)
```

---

### text_to_subtitle_svg

サブタイトルテキストをSVGとして生成します（スタイルプリセット対応）。

**ファイル**: `agents/tools/text_to_subtitle_svg.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| text | str | 必須 | - | サブタイトルテキスト |
| x | int | 任意 | 960 | X座標（テキスト中心） |
| y | int | 任意 | 500 | Y座標（テキスト中心） |
| font_size | int | 任意 | 36 | フォントサイズ |
| font_family | str | 任意 | "Hiragino Sans" | フォントファミリー |
| font_weight | str | 任意 | "normal" | フォントの太さ |
| color | str | 任意 | "#ffffff" | 文字色 |
| style | str | 任意 | "flat" | スタイルプリセット名 |
| fill | dict/str | 任意 | None | グラデーション設定 |
| glow_color | str | 任意 | None | グロー色（neon-glow用） |

**仕様**:
- `text_to_title_svg` と同じスタイルプリセットに対応
- デフォルトのフォントサイズ、Y座標、font_weightが異なる

---

### compose_slide_svg

各SVG要素を合成して1枚のSVGを生成します（Illustrator互換）。

**ファイル**: `agents/tools/compose_slide_svg.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| background_svg | str | 任意 | None | 背景SVG文字列 |
| illustration_svg | str | 任意 | None | イラストSVG文字列 |
| title_svg | str | 任意 | None | タイトルSVG文字列 |
| subtitle_svg | str | 任意 | None | サブタイトルSVG文字列 |

**戻り値**:

```json
{
  "success": true,
  "svg": "<?xml version=\"1.0\"?>..."
}
```

**合成順序（レイヤー順）**:

1. background（最背面）
2. illustration
3. title
4. subtitle（最前面）

**仕様**:
- 各レイヤーに `id` 属性を付与（Illustratorでレイヤー名として認識）
- XML宣言と xmlns:xlink 名前空間を含む
- 背景SVGは自動的にキャンバスサイズ（1920x1080）にスケーリング
- 各要素の `<defs>` セクションを統合

**出力例**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="1920" height="1080"
     viewBox="0 0 1920 1080">
  <defs>
    <!-- 統合されたグラデーション定義など -->
  </defs>
  <g id="background">
    <!-- 背景コンテンツ -->
  </g>
  <g id="illustration">
    <!-- イラストコンテンツ -->
  </g>
  <g id="title">
    <!-- タイトルコンテンツ -->
  </g>
  <g id="subtitle">
    <!-- サブタイトルコンテンツ -->
  </g>
</svg>
```

---

## PPTXツール

### svg_to_pptx

SVGをPowerPointプレゼンテーションに変換します（画像として埋め込み）。

**ファイル**: `agents/tools/svg_to_pptx.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| svg | str | 必須 | - | SVG文字列 |
| session_id | str | 必須 | - | セッションID（ファイル名） |
| folder | str | 任意 | "result" | 保存先フォルダ名 |

**戻り値**:

```json
{
  "success": true,
  "file_path": "/path/to/output_pptx/result/SESSION_ID.pptx"
}
```

**仕様**:
- SVGをPNGにレンダリング後、画像としてスライドに配置
- 編集不可（1枚の画像として配置）
- スライドサイズ: 1920x1080（16:9）

---

### svg_to_pptx_editable

個別の要素からPowerPointプレゼンテーションを生成します（テキスト編集可能）。

**ファイル**: `agents/tools/svg_to_pptx.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| session_id | str | 必須 | - | セッションID（ファイル名） |
| folder | str | 任意 | "result" | 保存先フォルダ名 |
| background_base64 | str | 任意 | None | 背景画像のBase64 |
| illustration_base64 | str | 任意 | None | イラスト画像のBase64 |
| title_config | dict | 任意 | None | タイトル設定 |
| subtitle_config | dict | 任意 | None | サブタイトル設定 |

**title_config / subtitle_config の形式**:

```json
{
  "text": "テキスト",
  "x": 960,
  "y": 400,
  "fontSize": 64,
  "fontFamily": "Arial",
  "fontWeight": "bold",
  "color": "#FFFFFF"
}
```

**戻り値**:

```json
{
  "success": true,
  "file_path": "/path/to/output_pptx/result/SESSION_ID.pptx"
}
```

**仕様**:
- 背景・イラスト: 画像として配置（移動・リサイズ可能）
- タイトル・サブタイトル: ネイティブテキストボックスとして配置（**編集可能**）
- スライドサイズ: 1920x1080（16:9）
- テキストは中央揃え

**使用例**:

```python
from agents.tools import svg_to_pptx_editable

result = svg_to_pptx_editable._tool_func(
    session_id="TEST-0001",
    folder="result",
    background_base64=bg_base64,
    title_config={
        "text": "タイトル",
        "x": 960,
        "y": 400,
        "fontSize": 100,
        "fontFamily": "Arial",
        "fontWeight": "bold",
        "color": "#FFFFFF"
    },
    subtitle_config={
        "text": "サブタイトル\n2行目",
        "x": 960,
        "y": 600,
        "fontSize": 48,
        "fontFamily": "Arial",
        "fontWeight": "normal",
        "color": "#CCCCCC"
    }
)
```

---

## 互換性ツール（レガシー）

以下のツールは互換性のために残されています：

| ツール名 | 説明 |
|----------|------|
| text_to_image | 汎用画像生成（Nanobanana前処理用） |
| image_to_image | 汎用画像編集 |
| text_to_illustration | イラスト生成（旧） |
| image_to_illustration | イラスト編集（旧） |
| jp_fonts | 日本語フォント一覧 |
| jp_fonts_multi | 複数フォント一覧 |

新規開発では上記の要素別ツールを使用してください。
