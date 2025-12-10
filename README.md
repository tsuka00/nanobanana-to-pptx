# Nanobanana to PPTX

Nanobanana（Gemini画像生成）で作成した高品質画像を、編集可能なPowerPointプレゼンテーションに変換するAIエージェントシステムです。

## 概要

このシステムは、Nanobanana（Gemini 3 Pro Image）が生成した高品質な画像を分析し、要素を識別して編集可能なPPTXに変換します。

### ワークフロー

```
ユーザー入力（プロンプト + 参照画像）
       │
       ▼
┌─────────────────────────────────┐
│ Phase 0: Nanobanana 前処理      │
│ Gemini 3 Pro Image で高品質画像生成 │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Phase 1: 画像分析               │
│ Gemini 3 Pro で要素を識別       │
│ - テキスト要素 → SVG生成        │
│ - 非テキスト要素 → bbox取得     │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Phase 2: PPTX生成               │
│ - 背景/イラスト → 元画像から切り出し │
│ - テキスト → SVG→PNG変換        │
│ - 全要素をPPTXに配置            │
└─────────────────────────────────┘
       │
       ▼
   agent_output/{session_id}/
   ├── nanobanana.png    # 前処理画像
   ├── design.json       # 設計JSON
   ├── {session_id}.pptx # 出力PPTX
   ├── background.png    # 背景
   ├── text_*.svg/png    # テキスト要素
   └── ...
```

## 環境構築

### 必要条件

- Python 3.12+
- Google API Key（Gemini API）

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

# 出力先
print(result.get("pptx_result_path"))  # PPTXファイルパス
```

## 出力

生成されたファイルはセッションIDごとにまとめて保存されます：

```
agent_output/
└── {session_id}/
    ├── nanobanana.png      # Nanobanana前処理画像
    ├── result.png          # 結果画像
    ├── design.json         # 設計JSON（プリセット情報含む）
    ├── {session_id}.pptx   # 最終PPTX
    ├── background.png      # 背景画像（元画像から切り出し）
    ├── text_1.svg          # テキストSVG
    ├── text_1.png          # テキストPNG（SVG変換後）
    ├── illustration_*.png  # イラスト（元画像から切り出し）
    └── ...
```

セッションIDは `XXXX-YYYY` 形式（例: `SYV4-1867`）で自動生成されます。

## ツール

| ツール | 説明 |
|--------|------|
| `text_to_image` | Nanobanana前処理（Gemini 3 Pro Imageで画像生成） |
| `analyze_image` | 画像分析（Gemini 3 Proで要素識別・SVG生成） |
| `image_to_pptx` | PPTX生成（要素配置） |

## ドキュメント

詳細なドキュメントは `docs/` フォルダを参照してください：

- [システム概要](docs/overview.md) - アーキテクチャと処理フロー
- [ツール一覧](docs/tools.md) - 各ツールの詳細仕様
- [JSONスキーマ](docs/json-schema.md) - 設計JSONの仕様（プリセットシステム）

## ディレクトリ構成

```
nanobanana-to-pptx/
├── agents/
│   ├── designer_agent.py    # メインエージェント
│   ├── test_agent.py        # テスト用スクリプト
│   ├── presets.py           # プリセット定義
│   ├── preset_resolver.py   # プリセット解決
│   ├── fonts/               # フォントファイル
│   │   └── NotoSansCJKjp-Regular.otf
│   └── tools/
│       ├── text_to_image.py    # Nanobanana前処理
│       ├── analyze_image.py    # 画像分析（Gemini 3 Pro）
│       └── image_to_pptx.py    # PPTX生成
├── agent_output/            # 出力ディレクトリ（セッションIDごと）
├── tests/                   # テストスクリプト
└── docs/                    # ドキュメント
```

## 技術スタック

- **Google Gemini API**
  - Gemini 3 Pro Image: 高品質画像生成（Nanobanana前処理）
  - Gemini 3 Pro: 画像分析・SVG生成・設計解析
- **Pillow**: 画像処理（切り出し、合成）
- **cairosvg**: SVG→PNG変換
- **python-pptx**: PowerPoint出力

## ライセンス

MIT License
