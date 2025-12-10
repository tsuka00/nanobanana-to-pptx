# PPTX出力

PowerPointプレゼンテーション（.pptx）出力の詳細仕様です。

## 概要

Designer Agentは、生成したスライドをPowerPointプレゼンテーション形式で出力できます。PPTX出力では、**テキストが編集可能なネイティブテキストボックス**として配置されます。

## 出力先

```
output_pptx/
└── result/
    └── SESSION_ID.pptx
```

例: `output_pptx/result/SYV4-1867.pptx`

## 要素の配置方法

| 要素 | 配置方法 | 編集 |
|------|----------|------|
| 背景 | 画像（フル画面） | 移動・リサイズ可 |
| イラスト | 画像（透過PNG） | 移動・リサイズ可 |
| タイトル | **テキストボックス** | **テキスト編集可能** |
| サブタイトル | **テキストボックス** | **テキスト編集可能** |

## 使用方法

### 自動生成（デフォルト）

`DesignerAgent.generate()` を実行すると、PNG・SVGと共にPPTXも自動生成されます。

```python
from agents.designer_agent import DesignerAgent

agent = DesignerAgent()
result = agent.generate("青空の背景にタイトル「Hello World」")

# 結果にPPTXパスが含まれる
print(result.get("pptx_result_path"))
# -> /path/to/output_pptx/result/XXXX-YYYY.pptx
```

### 個別ツール呼び出し

PPTXツールを直接呼び出すこともできます。

#### svg_to_pptx（画像版・編集不可）

SVG全体を画像としてスライドに配置します。

```python
from agents.tools import svg_to_pptx

result = svg_to_pptx._tool_func(
    svg="<svg>...</svg>",
    session_id="TEST-0001",
    folder="result"
)
```

#### svg_to_pptx_editable（テキスト編集可能版）

背景・イラストを画像、テキストをテキストボックスとして配置します。

```python
from agents.tools import svg_to_pptx_editable

result = svg_to_pptx_editable._tool_func(
    session_id="TEST-0001",
    folder="result",
    background_base64=bg_base64,
    illustration_base64=illust_base64,  # オプション
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
        "text": "サブタイトル\n2行目のテキスト",
        "x": 960,
        "y": 600,
        "fontSize": 48,
        "fontFamily": "Arial",
        "fontWeight": "normal",
        "color": "#CCCCCC"
    }
)
```

## テキスト設定（title_config / subtitle_config）

| プロパティ | 型 | 説明 | デフォルト |
|------------|-----|------|------------|
| text | string | 表示テキスト（`\n`で改行） | - |
| x | number | X座標（テキスト中心） | 960 |
| y | number | Y座標（テキスト中心） | 400/600 |
| fontSize | number | フォントサイズ（pt） | 64/36 |
| fontFamily | string | フォント名 | "Arial" |
| fontWeight | string | "bold" / "normal" | "bold"/"normal" |
| color | string | 文字色（#RRGGBB） | "#FFFFFF" |

## スライド仕様

| 項目 | 値 |
|------|-----|
| スライドサイズ | 1920 x 1080 px（16:9） |
| レイアウト | 空白レイアウト |
| 単位 | EMU（English Metric Units） |

## 制限事項

### SVGスタイルプリセットは適用されない

SVG出力で使用できるスタイルプリセット（3d-metallic、neon-glow等）は、PPTX出力には適用されません。PPTXではシンプルなテキストとして配置されます。

| 設定項目 | SVG | PPTX |
|----------|-----|------|
| style（プリセット） | 適用される | **適用されない** |
| color | 適用される | 適用される |
| fontSize | 適用される | 適用される |
| fontFamily | 適用される | 適用される |
| fontWeight | 適用される | 適用される |
| fill（グラデーション） | 適用される | **適用されない** |

### 背景・イラストは画像

背景とイラストはPNG画像として配置されます。SVGのようなベクター編集はできません。

### フォント互換性

指定したフォントがPowerPointで利用できない場合、代替フォントに置き換えられます。

**推奨フォント（Windows/Mac共通）**:
- Arial
- Helvetica Neue
- Times New Roman

## 比較：SVG vs PPTX

| 用途 | 推奨形式 |
|------|----------|
| Adobe Illustratorで編集 | SVG |
| PowerPointでテキスト編集 | PPTX |
| テキストスタイルを維持 | SVG |
| 最終プレビュー | PNG |

## トラブルシューティング

### テキストが表示されない

`title_config` または `subtitle_config` の `text` プロパティが空でないことを確認してください。

### フォントが正しく表示されない

指定した `fontFamily` がシステムにインストールされていることを確認してください。一般的なフォント（Arial等）を使用することを推奨します。

### 位置がずれる

座標（x, y）はテキストの中心位置を指定します。テキストボックスは自動的にスライド幅の90%に設定され、中央揃えで配置されます。

## 必要なライブラリ

```bash
pip install python-pptx cairosvg
```

| ライブラリ | 用途 |
|------------|------|
| python-pptx | PPTX生成 |
| cairosvg | SVG→PNG変換（svg_to_pptx用） |
