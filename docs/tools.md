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

## 互換性ツール（レガシー）

以下のツールは互換性のために残されています：

| ツール名 | 説明 |
|----------|------|
| text_to_image | 汎用画像生成 |
| image_to_image | 汎用画像編集 |
| text_to_illustration | イラスト生成（旧） |
| image_to_illustration | イラスト編集（旧） |
| jp_fonts | 日本語フォント一覧 |
| jp_fonts_multi | 複数フォント一覧 |

新規開発では上記の要素別ツールを使用してください。
