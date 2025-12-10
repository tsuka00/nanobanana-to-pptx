# ツール一覧

Designer Agent で使用可能なツールの詳細仕様です。

## text_to_image（Nanobanana前処理）

Nanobanana（Gemini 3 Pro Image）でユーザーの指示から高品質画像を生成します。

**ファイル**: `agents/tools/text_to_image.py`

**使用モデル**: `gemini-3-pro-image`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| prompt | str | 必須 | - | 画像生成プロンプト |
| reference_image_base64 | str | 任意 | None | 参照画像のBase64データ |

**戻り値**:

```json
{
  "success": true,
  "image_base64": "base64エンコードされた画像データ",
  "mime_type": "image/png"
}
```

**仕様**:
- 出力サイズ: 1920x1080（16:9）または参照画像に依存
- 高品質なスタイリングされた画像を生成
- 参照画像がある場合はスタイル・構図を参照

**使用例**:

```python
from agents.tools import text_to_image

# text-to-image モード
result = text_to_image(
    prompt="ズートピア2の感想会サムネイル、映画のシーンと配信者のリアクション"
)

# image-to-image モード
result = text_to_image(
    prompt="この画像のスタイルで新しいサムネイルを生成",
    reference_image_base64=reference_base64
)
```

---

## analyze_image（画像分析）

Gemini 3 Pro で画像を分析し、要素を識別します。テキスト要素にはSVGを生成します。

**ファイル**: `agents/tools/analyze_image.py`

**使用モデル**: `gemini-3-pro-preview`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| image_base64 | str | 必須 | - | 分析する画像のBase64データ |
| api_key | str | 任意 | 環境変数 | Google API Key |

**戻り値**:

```json
{
  "success": true,
  "elements": [
    {
      "id": "background",
      "type": "background",
      "label": "背景の説明",
      "bbox": {"x": 0, "y": 0, "width": 1920, "height": 1080}
    },
    {
      "id": "text_1",
      "type": "text",
      "label": "テキストの説明",
      "content": "テキスト内容",
      "bbox": {"x": 100, "y": 200, "width": 500, "height": 100},
      "svg": "<svg>...</svg>"
    },
    {
      "id": "illustration_1",
      "type": "illustration",
      "label": "イラストの説明",
      "bbox": {"x": 800, "y": 300, "width": 400, "height": 400}
    }
  ],
  "image_size": {"width": 1920, "height": 1080}
}
```

**要素タイプ**:

| タイプ | SVG生成 | 説明 |
|--------|---------|------|
| background | なし | 背景画像（全画面） |
| text | あり | テキスト要素（SVGで再現） |
| illustration | なし | イラスト・アイコン |
| image | なし | 写真・画像 |

**SVG生成の仕様**:
- フォント: `Noto Sans CJK JP`
- グラデーション対応（linearGradient）
- 基本的なテキストスタイル（フォントサイズ、太さ、色）
- bbox（x, y, width, height）は元画像のピクセル座標

**注意事項**:
- 複雑なテキストスタイル（3D、影、縁取り、ホログラムなど）の完全な再現は困難
- 生成されるSVGは元の見た目を「近似」するもの

**使用例**:

```python
from agents.tools import analyze_image

result = analyze_image(image_base64=nanobanana_image)

if result["success"]:
    elements = result["elements"]
    for elem in elements:
        print(f"{elem['id']}: {elem['type']}")
        if elem.get("svg"):
            print(f"  SVG generated")
```

---

## image_to_pptx（PPTX生成）

分析された要素リストと元画像からPowerPointプレゼンテーションを生成します。

**ファイル**: `agents/tools/image_to_pptx.py`

**引数**:

| 引数名 | 型 | 必須 | デフォルト | 説明 |
|--------|-----|------|------------|------|
| elements | list | 必須 | - | 要素リスト（analyze_imageの出力） |
| original_image_base64 | str | 必須 | - | 元画像のBase64データ |
| session_id | str | 必須 | - | セッションID（ファイル名） |
| output_dir | Path | 任意 | agent_output/{session_id} | 出力ディレクトリ |

**戻り値**:

```json
{
  "success": true,
  "file_path": "/path/to/agent_output/{session_id}/{session_id}.pptx",
  "element_files": [
    "/path/to/background.png",
    "/path/to/text_1.svg",
    "/path/to/text_1.png",
    "/path/to/illustration_1.png"
  ]
}
```

**処理フロー**:

1. **背景要素**: 元画像から切り出し → 全画面配置
2. **テキスト要素**: SVG → PNG変換（cairosvg） → bbox位置に配置
3. **イラスト要素**: 元画像から切り出し → bbox位置に配置

**SVG→PNG変換**:
- cairosvgを使用
- フォント置換: Arial Black, Impact, sans-serif → Noto Sans CJK JP
- フォントパス: `agents/fonts/NotoSansCJKjp-Regular.otf`

**スライド仕様**:
- サイズ: 1920 x 1080 px（16:9）
- レイアウト: 空白スライド
- 配置順: 背景 → その他の要素（z-indexを維持）

**使用例**:

```python
from agents.tools import image_to_pptx

result = image_to_pptx(
    elements=analyze_result["elements"],
    original_image_base64=nanobanana_image,
    session_id="TEST-0001"
)

if result["success"]:
    print(f"PPTX: {result['file_path']}")
    print(f"要素ファイル: {len(result['element_files'])}個")
```

---

## 座標計算

### 元画像座標 → PPTX座標

```python
# スケール計算
scale_x = SLIDE_WIDTH / img_width   # 1920 / 元画像幅
scale_y = SLIDE_HEIGHT / img_height # 1080 / 元画像高さ

# PPTX座標計算（EMU単位）
x = Emu(int(bbox_x * scale_x) * 914400 // 96)
y = Emu(int(bbox_y * scale_y) * 914400 // 96)
width = Emu(int(bbox_width * scale_x) * 914400 // 96)
height = Emu(int(bbox_height * scale_y) * 914400 // 96)
```

### EMU（English Metric Units）

python-pptxで使用される単位：
- 1インチ = 914400 EMU
- 96 DPI で計算

---

## 必要なライブラリ

```bash
pip install google-genai pillow python-pptx cairosvg
```

| ライブラリ | 用途 |
|------------|------|
| google-genai | Gemini API（画像生成・分析） |
| pillow | 画像処理（切り出し） |
| python-pptx | PPTX生成 |
| cairosvg | SVG→PNG変換 |

---

## フォント

SVG→PNG変換で使用するフォント：

**パス**: `agents/fonts/NotoSansCJKjp-Regular.otf`

**フォント置換マッピング**:
- Arial Black → Noto Sans CJK JP
- Impact → Noto Sans CJK JP
- sans-serif → Noto Sans CJK JP
