# Nanobanana Designer Agent

自然言語の指示から画像デザインを生成するAIエージェントシステムです。Strands Agents フレームワークと Google Gemini API を使用しています。

## 概要

このシステムは、ユーザーの自然言語指示を解析し、以下の要素を個別に生成・合成してスライド画像を作成します：

- **背景（Background）**: Gemini による画像生成
- **イラスト（Illustration）**: 幾何学シェイプ描画（SVG / Pillow）
- **タイトル（Title）**: テキスト描画（SVG / Pillow）
- **サブタイトル（Subtitle）**: テキスト描画（SVG / Pillow）

## 出力形式

PNG画像とSVGの両方を出力します：

- **PNG出力**: 最終合成画像（編集不可）
- **SVG出力**: 編集可能なベクター形式（Adobe Illustrator対応）

SVG出力により、AI生成後もIllustratorで個別要素の編集が可能です。

## 動作モード

1. **text-to-image**: プロンプトのみで新規画像を生成
2. **image-to-image**: 参考画像を元に新規画像を生成（参考画像のスタイルや構図を参照）

## 環境構築

### 必要条件

- Python 3.12+
- Node.js v22+ (オプション)

### セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.local.example .env.local
# .env.local に GOOGLE_API_KEY を設定
```

### 環境変数

`.env.local` に以下を設定：

```env
GOOGLE_API_KEY=your-google-genai-key  # Gemini API キー（必須）
```

## 使用方法

### インタラクティブモード

```bash
python -m agents.test_agent
```

プロンプトを入力すると、text-to-image モードで画像を生成します。
画像パス付きで入力すると、image-to-image モードで生成します。

### プログラムからの使用

```python
from agents.designer_agent import DesignerAgent

agent = DesignerAgent()

# text-to-image モード
result = agent.generate("青空の背景にタイトル「Hello World」を配置")

# image-to-image モード（参考画像あり）
import base64
with open("reference.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

result = agent.generate(
    "この画像のスタイルで新しい背景を生成",
    image_base64=image_base64
)
```

## 出力

生成されたファイルは以下のフォルダに保存されます：

```
output/                 # PNG画像
  background/           # 背景画像
  illustration/         # イラスト（透過PNG）
  title/                # タイトル（透過PNG）
  subtitle/             # サブタイトル（透過PNG）
  result/               # 最終合成画像

output_svg/             # SVGファイル（編集可能）
  background/           # 背景SVG（vtracer変換）
  illustration/         # イラストSVG
  title/                # タイトルSVG
  subtitle/             # サブタイトルSVG
  result/               # 最終合成SVG（Illustrator対応）
```

各ファイルはセッションID（例: `SYV4-1867.png`、`SYV4-1867.svg`）で管理されます。

## ドキュメント

詳細なドキュメントは `docs/` フォルダを参照してください：

- [システム概要](docs/overview.md) - アーキテクチャと処理フロー
- [ツール一覧](docs/tools.md) - 各ツールの詳細仕様
- [JSONスキーマ](docs/json-schema.md) - 設計JSONの仕様

## ディレクトリ構成

```
nanobanana-to-pptx/
  agents/
    designer_agent.py    # メインエージェント
    test_agent.py        # テスト用スクリプト
    tools/
      # PNG生成ツール
      text_to_background.py   # 背景生成（text-to-image）
      image_to_background.py  # 背景生成（image-to-image）
      draw_illustration.py    # イラスト描画（Pillow）
      text_to_title.py        # タイトル描画
      text_to_subtitle.py     # サブタイトル描画
      compose_slide.py        # PNG合成ツール
      jp_fonts.py             # 日本語フォント設定
      # SVG生成ツール
      image_to_svg.py         # 画像→SVG変換（vtracer）
      draw_illustration_svg.py # イラストSVG生成
      text_to_title_svg.py    # タイトルSVG生成
      text_to_subtitle_svg.py # サブタイトルSVG生成
      compose_slide_svg.py    # SVG合成（Illustrator対応）
  output/                # PNG画像の出力先
  output_svg/            # SVGファイルの出力先
  docs/                  # ドキュメント
```

## 技術スタック

- **Strands Agents**: エージェントフレームワーク
- **Google Gemini API**: 画像生成（gemini-2.5-flash-image）、設計解析（gemini-2.0-flash）
- **Pillow**: テキスト描画、シェイプ描画、画像合成（PNG）
- **vtracer**: ラスター画像→SVGベクター変換
- **SVG**: 編集可能なベクター出力（Adobe Illustrator対応）

## ライセンス

MIT License
