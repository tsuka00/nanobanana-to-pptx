"""
Designer Agent
自然言語の指示からスライドデザインを生成するエージェント

フロー:
1. ユーザープロンプトを分析（Reasoning）
2. 設計JSONを生成
3. 各要素を個別に生成（背景、イラスト）
4. PPTXに統合（テキストは編集可能なテキストボックス）
"""

import os
import json
import base64
import re
import io
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from google import genai  # type: ignore
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool
from PIL import Image

# ツール
from .tools.text_to_image import text_to_image as _text_to_image
from .tools.image_to_pptx import image_to_pptx as _image_to_pptx
from .tools.design_references import get_references_summary, search_references

# プリセットシステム
from .presets import get_preset_summary, LAYOUTS, PALETTES, TONES
from .preset_resolver import resolve_presets, get_prompt_for_preset_selection

# .env.local を読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

# 出力ディレクトリ（セッションIDごとにまとめる）
AGENT_OUTPUT_DIR = Path(__file__).parent.parent / "agent_output"

# 設計フェーズ用のモデル
DESIGN_MODEL = "gemini-3-pro-preview"

# Reasoning フェーズ用プロンプト
REASONING_PROMPT = """あなたは優秀なビジュアルデザイナーです。
ユーザーの指示を深く分析し、最適なデザインを考えてください。

## 分析してください：

1. **意図の理解**
   - ユーザーは何を伝えたいのか？
   - このスライドの目的は？（プレゼン、告知、教育など）

2. **ターゲット**
   - 誰に向けたデザインか？
   - フォーマルか、カジュアルか？

3. **トーンの選択**（以下から1つ選択）
   - `professional`: プロフェッショナル、ビジネス、信頼感
   - `creative`: クリエイティブ、アーティスティック、独創的
   - `tech`: テクノロジー、未来的、先進的
   - `premium`: 高級、ラグジュアリー、洗練
   - `minimal`: ミニマル、シンプル、余白重視
   - `energetic`: エネルギッシュ、活発、ダイナミック
   - `warm`: 温かみ、親しみやすさ、柔らかさ
   - `cool`: クール、洗練、知的
   - `nature`: 自然、オーガニック、サステナブル
   - `playful`: 遊び心、楽しさ、カジュアル

4. **レイアウトの検討**（以下から1つ選択）
   - `center`: 中央配置（デフォルト、バランス重視）
   - `center-middle`: 中央・垂直中央（インパクト重視）
   - `left`: 左寄せ（右に余白、動きのある印象）
   - `right`: 右寄せ（左に余白）
   - `bottom`: 下部配置（背景重視）
   - `top`: 上部配置（安定感）
   - `split-left`: 左半分にテキスト（50:50分割）
   - `split-right`: 右半分にテキスト（50:50分割）
   - `bottom-left`: 左下配置
   - `bottom-right`: 右下配置
   - `overlay`: オーバーレイ（背景画像の上）

5. **配色パレットの選択**（以下から1つ選択）
   - ライト系: `light`, `light-warm`, `light-cool`
   - ダーク系: `dark`, `dark-tech`, `dark-purple`
   - モノクローム: `monochrome`, `monochrome-dark`
   - プレミアム: `premium-gold`, `premium-silver`
   - ビビッド: `vibrant`, `vibrant-gradient`
   - 自然系: `nature`, `ocean`
   - ビジネス: `corporate`, `corporate-dark`

6. **テキストスタイル**（以下から選択）
   - flat: シンプルな単色（ビジネス、フォーマル向け）
   - shadow: ドロップシャドウ付き（可読性重視）
   - **3d-metallic: ホログラム/メタリック/3D風（★推奨：立体感、光沢、虹色反射が必要な場合はこれを使う）**
   - neon-glow: ネオン発光（テクノロジー、エンタメ）
   - glass: ガラス風透明感（洗練、クリーン）
   - outline: アウトライン（カジュアル、ポップ）
   - gold: ゴールドメタリック（高級感、祝い事）
   - silver: シルバーメタリック（クール、先進的）
   - emboss: エンボス/浮き彫り（伝統的、重厚感）
   - gradient: 単純な2色グラデーション

   **重要**: ホログラム、メタリック、チューブ形状、立体的な表現が求められる場合は必ず `3d-metallic` を選択。

7. **推奨アプローチ**
   - 選んだトーン、レイアウト、パレットを明記
   - なぜその組み合わせが最適かの理由

思考過程を詳しく出力してください。最後に「推奨アプローチ」と選んだプリセット（tone, layout, palette）を明記してください。
"""

# Web Research フェーズ用プロンプト
WEB_RESEARCH_PROMPT = """あなたはデザインリサーチャーです。
ユーザーの指示を分析し、より良いデザインを作成するために必要な情報をWeb検索してください。

## 検索すべき情報（必要に応じて）
1. **デザイントレンド**: 関連する最新のデザイントレンド、配色トレンド
2. **参考事例**: 類似のプレゼンテーションやスライドデザインの事例
3. **業界スタイル**: 特定の業界（テック、金融、教育等）のデザイン慣習

## 指示
- 検索が不要と判断した場合は「検索不要」と返答してください
- 検索した場合は、得られた情報を以下の形式でまとめてください：

### 検索結果
- **トレンド**: ...
- **推奨配色**: ...
- **参考スタイル**: ...
- **注意点**: ...

## ユーザーの指示
{user_prompt}
"""

DESIGN_SYSTEM_PROMPT = """あなたはプロフェッショナルなスライドデザイナーです。
ユーザーの指示とデザイン分析（Reasoning）に基づいて、高品質なスライド設計JSONを出力してください。

## 重要: 動的elements配列方式

必要な要素を自由に追加できます。固定の要素数に縛られません。
デザインに必要な要素をすべてelements配列に含めてください。

キャンバスサイズ: 1920x1080 (16:9)

## JSON形式

```json
{
  "meta": {
    "theme": "テーマ名（tech, business, creative, premium, casual等）",
    "mood": "雰囲気（energetic, calm, professional, playful等）",
    "color_scheme": {
      "primary": "#主要色",
      "secondary": "#補助色",
      "accent": "#アクセント色",
      "background": "#背景色"
    }
  },
  "elements": [
    // 必要な要素を自由に追加
  ]
}
```

## 要素タイプ

### 1. background（背景）- 必須、1つのみ
```json
{
  "type": "background",
  "prompt": "背景の詳細な叙述的説明。場面を描写するように書く。",
  "style": {
    "lighting": "照明の説明（studio-lit, soft diffused, dramatic等）",
    "color_tone": "色調（warm, cool, neutral等）",
    "texture": "質感（smooth gradient, subtle noise, geometric patterns等）"
  }
}
```

### 2. image（生成画像）- 複数可
```json
{
  "type": "image",
  "id": "一意のID",
  "prompt": "画像の詳細な叙述的説明",
  "position": {"x": 0, "y": 0, "width": 400, "height": 400},
  "style": {
    "type": "illustration | icon | photo | abstract",
    "details": "スタイルの詳細説明"
  }
}
```

### 3. text（テキスト）- 複数可
```json
{
  "type": "text",
  "id": "一意のID",
  "content": "表示するテキスト",
  "position": {"x": 960, "y": 400, "width": 1600, "height": 200},
  "style": {
    "fontSize": 80,
    "fontWeight": "bold | normal | light",
    "fontStyle": "normal | italic",
    "color": "#FFFFFF",
    "align": "center | left | right",
    "verticalAlign": "top | middle | bottom"
  }
}
```

## 背景プロンプトの書き方（重要）

キーワード羅列NG。場面を叙述的に描写してください。

### 悪い例
```
"prompt": "青いグラデーション、テック、モダン"
```

### 良い例
```
"prompt": "A sleek, modern tech background with a deep blue to purple gradient flowing diagonally across the canvas. Subtle geometric shapes float in the background with soft, diffused lighting creating depth. The overall mood is professional and futuristic, with clean lines and minimal visual noise. Studio-quality finish with smooth color transitions."
```

## 配色パターン例

| テーマ | primary | secondary | accent | background |
|--------|---------|-----------|--------|------------|
| tech-dark | #3B82F6 | #8B5CF6 | #06B6D4 | #0F172A |
| business | #1E40AF | #3B82F6 | #F59E0B | #F8FAFC |
| creative | #EC4899 | #8B5CF6 | #F59E0B | #1F2937 |
| premium | #D4AF37 | #C0C0C0 | #FFD700 | #1A1A1A |
| nature | #059669 | #10B981 | #FBBF24 | #ECFDF5 |

## デザイン例

### 例1: テック系セミナー告知
```json
{
  "meta": {
    "theme": "tech",
    "mood": "professional",
    "color_scheme": {
      "primary": "#3B82F6",
      "secondary": "#8B5CF6",
      "accent": "#06B6D4",
      "background": "#0F172A"
    }
  },
  "elements": [
    {
      "type": "background",
      "prompt": "A sophisticated dark tech background featuring a smooth gradient from deep navy blue (#0F172A) to rich purple (#1E1B4B). Abstract geometric shapes - hexagons and flowing lines - subtly emerge from the darkness with a soft cyan glow. The lighting is dramatic yet professional, with highlights creating depth. Clean, modern aesthetic suitable for a technology presentation.",
      "style": {
        "lighting": "dramatic with soft cyan accents",
        "color_tone": "cool, dark",
        "texture": "smooth gradient with subtle geometric patterns"
      }
    },
    {
      "type": "text",
      "id": "title",
      "content": "AI時代のエンジニアリング",
      "position": {"x": 960, "y": 380, "width": 1600, "height": 150},
      "style": {
        "fontSize": 72,
        "fontWeight": "bold",
        "color": "#FFFFFF",
        "align": "center"
      }
    },
    {
      "type": "text",
      "id": "subtitle",
      "content": "最新技術トレンドと実践的アプローチ",
      "position": {"x": 960, "y": 520, "width": 1400, "height": 80},
      "style": {
        "fontSize": 36,
        "fontWeight": "normal",
        "color": "#94A3B8",
        "align": "center"
      }
    },
    {
      "type": "text",
      "id": "date",
      "content": "2025.01.15 | 19:00 - 21:00",
      "position": {"x": 960, "y": 650, "width": 600, "height": 50},
      "style": {
        "fontSize": 24,
        "fontWeight": "normal",
        "color": "#06B6D4",
        "align": "center"
      }
    },
  ]
}
```

**重要**: shape要素は使用しない。装飾が必要な場合は背景画像生成時にプロンプトで指定する。

### 例2: 商品プロモーション
```json
{
  "meta": {
    "theme": "premium",
    "mood": "luxurious",
    "color_scheme": {
      "primary": "#D4AF37",
      "secondary": "#1A1A1A",
      "accent": "#FFD700",
      "background": "#0D0D0D"
    }
  },
  "elements": [
    {
      "type": "background",
      "prompt": "An elegant, luxurious dark background with rich black (#0D0D0D) as the base. Subtle golden light rays emanate from the center, creating a premium feel. Soft bokeh effects in warm gold tones add depth and sophistication. The texture is smooth with a slight metallic sheen, suggesting high-end quality. Professional studio lighting with dramatic shadows.",
      "style": {
        "lighting": "dramatic golden accents",
        "color_tone": "warm, dark, premium",
        "texture": "smooth with subtle metallic sheen"
      }
    },
    {
      "type": "image",
      "id": "product-visual",
      "prompt": "An abstract golden geometric shape, like a stylized crown or premium emblem, rendered in 3D with metallic gold finish and soft reflections",
      "position": {"x": 960, "y": 300, "width": 300, "height": 300},
      "style": {
        "type": "abstract",
        "details": "3D metallic gold, premium feel"
      }
    },
    {
      "type": "text",
      "id": "brand",
      "content": "PREMIUM",
      "position": {"x": 960, "y": 550, "width": 800, "height": 120},
      "style": {
        "fontSize": 96,
        "fontWeight": "bold",
        "color": "#D4AF37",
        "align": "center"
      }
    },
    {
      "type": "text",
      "id": "tagline",
      "content": "Exclusive Collection 2025",
      "position": {"x": 960, "y": 680, "width": 600, "height": 60},
      "style": {
        "fontSize": 28,
        "fontWeight": "light",
        "color": "#FFFFFF",
        "align": "center"
      }
    }
  ]
}
```

## ルール

1. **elements配列に必要な要素をすべて含める** - 背景、テキスト、画像、図形を自由に追加
2. **背景プロンプトは叙述的に** - キーワード羅列ではなく、場面を描写
3. **位置は具体的に** - x, y, width, heightをピクセルで指定
4. **配色は統一感を** - meta.color_schemeで定義した色を各要素で使用
5. **IDは一意に** - 各要素のidは重複しないようにする

JSONのみを出力してください。
"""

# 修正フェーズ用プロンプト
REFINE_PROMPT = """あなたは画像デザインの設計者です。
既存の設計JSONに対して、ユーザーのフィードバックを反映した修正版を出力してください。

## 現在の設計
{current_design}

## ユーザーのフィードバック
{feedback}

## 指示

1. フィードバックを分析し、どの要素を変更すべきか特定してください
2. 変更が必要な要素のみ更新し、他はそのまま維持してください
3. 修正後の完全なJSONを出力してください（変更箇所だけでなく全体を出力）

JSONのみを出力してください。
"""


def get_session_output_dir(session_id: str) -> Path:
    """セッション用の出力ディレクトリを取得"""
    output_dir = AGENT_OUTPUT_DIR / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_image(image_base64: str, filename: str, session_id: str) -> str:
    """画像を保存してパスを返す"""
    output_dir = get_session_output_dir(session_id)
    output_path = output_dir / f"{filename}.png"

    image_data = base64.b64decode(image_base64)
    with open(output_path, 'wb') as f:
        f.write(image_data)

    return str(output_path)


def save_design(
    design: dict,
    session_id: str,
    reasoning: Optional[str] = None,
    web_research: Optional[dict] = None
) -> str:
    """設計JSONを保存してパスを返す"""
    output_dir = get_session_output_dir(session_id)
    output_path = output_dir / "design.json"

    # 設計JSON、reasoning、web_researchをまとめて保存
    data = {
        "session_id": session_id,
        "design": design,
        "reasoning": reasoning,
        "web_research": web_research
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(output_path)


def load_design(session_id: str) -> Optional[dict]:
    """保存された設計JSONを読み込む"""
    output_dir = get_session_output_dir(session_id)
    design_path = output_dir / "design.json"
    if not design_path.exists():
        return None

    with open(design_path, 'r', encoding='utf-8') as f:
        return json.load(f)




class DesignerAgent:
    """画像デザインを生成するエージェント（要素別生成版）"""

    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None):
        self.api_key: str = api_key or os.environ.get("GOOGLE_API_KEY") or ""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self.client = genai.Client(api_key=self.api_key)
        self.session_id: str = session_id or self._generate_session_id()

    def _generate_session_id(self) -> str:
        """セッションIDを生成"""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=4)) + '-' + ''.join(random.choices(string.digits, k=4))

    def _base64_to_pil(self, image_base64: str) -> Image.Image:
        """Base64画像をPIL Imageに変換"""
        image_bytes = base64.b64decode(image_base64)
        return Image.open(io.BytesIO(image_bytes))

    def _web_research(
        self,
        user_prompt: str,
        input_image: Optional[str] = None
    ) -> Optional[dict]:
        """
        Web検索でデザイン参考情報を収集（エージェントが自律判断）

        Args:
            user_prompt: ユーザーの自然言語指示
            input_image: 参照画像のBase64（オプション）

        Returns:
            dict | None: 検索結果（検索不要の場合はNone）
                - research: 検索結果のテキスト
                - grounding: メタデータ（検索クエリ、ソースURL等）
        """
        try:
            contents: List = []

            prompt = WEB_RESEARCH_PROMPT.format(user_prompt=user_prompt)
            contents.append(prompt)

            # 参照画像がある場合は追加
            if input_image:
                contents.append(self._base64_to_pil(input_image))

            # Google Search ツールを有効化
            config = GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())]
            )

            response = self.client.models.generate_content(
                model=DESIGN_MODEL,
                contents=contents,
                config=config
            )

            result_text = response.text or ""

            # 検索不要の場合
            if not result_text or "検索不要" in result_text:
                return None

            # グラウンディングメタデータを抽出
            grounding_metadata = None
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                grounding_metadata = {
                    "search_queries": list(metadata.web_search_queries) if metadata.web_search_queries else [],
                    "sources": [
                        {"uri": chunk.web.uri, "title": chunk.web.title}
                        for chunk in (metadata.grounding_chunks or [])
                        if chunk.web
                    ]
                }

            return {
                "research": result_text,
                "grounding": grounding_metadata
            }

        except Exception as e:
            print(f"  [Warning] Web Research failed: {str(e)}")
            return None

    def _reason(
        self,
        user_prompt: str,
        input_image: Optional[str] = None,
        web_research: Optional[dict] = None
    ) -> str:
        """ユーザーのプロンプトを深く分析してデザイン方針を決定

        Args:
            user_prompt: ユーザーの自然言語指示
            input_image: 参照画像のBase64（オプション）
            web_research: Webリサーチ結果（オプション）

        Returns:
            str: 分析結果（reasoning）
        """
        contents: List = []

        text_prompt = REASONING_PROMPT + "\n\n## ユーザーの指示\n" + user_prompt

        # デザイン参照情報を追加
        references_summary = get_references_summary()
        if references_summary:
            text_prompt += "\n\n" + references_summary

        # Web Research 結果を追加
        if web_research:
            text_prompt += "\n\n## Webリサーチ結果\n" + web_research["research"]
            if web_research.get("grounding", {}).get("sources"):
                text_prompt += "\n\n### 参照ソース:\n"
                for src in web_research["grounding"]["sources"][:5]:
                    text_prompt += f"- [{src['title']}]({src['uri']})\n"

        # 画像がある場合は参照情報を追加
        if input_image:
            text_prompt += "\n\n## 参考画像あり\n画像も考慮してデザインを検討してください。"
            contents.append(text_prompt)
            contents.append(self._base64_to_pil(input_image))
        else:
            contents.append(text_prompt)

        response = self.client.models.generate_content(
            model=DESIGN_MODEL,
            contents=contents
        )

        return response.text

    def _parse_design(
        self,
        user_prompt: str,
        reasoning: Optional[str] = None,
        input_image: Optional[str] = None
    ) -> dict:
        """ユーザーのプロンプトをJSON設計に変換

        Args:
            user_prompt: ユーザーの自然言語指示
            reasoning: 事前のデザイン分析結果
            input_image: 参照画像のBase64（オプション）
        """
        contents: List = []

        # システムプロンプト + ユーザー指示
        text_prompt = DESIGN_SYSTEM_PROMPT + "\n\n## ユーザーの指示\n" + user_prompt

        # Reasoning結果がある場合は追加
        if reasoning:
            text_prompt += "\n\n## デザイン分析（Reasoning）\n" + reasoning

        # 画像がある場合は参照情報を追加
        if input_image:
            text_prompt += "\n\n【参考画像】この画像のスタイルや雰囲気を参考に設計してください。"
            contents.append(text_prompt)
            contents.append(self._base64_to_pil(input_image))
        else:
            contents.append(text_prompt)

        response = self.client.models.generate_content(
            model=DESIGN_MODEL,
            contents=contents
        )

        text = response.text

        # JSONを抽出
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            raise ValueError(f"Failed to parse design JSON: {text}")

        return json.loads(json_match.group())

    def _execute_design(self, design: dict) -> dict:
        """設計JSONに基づいて動的に要素を生成し、PPTXに統合

        新形式: design.elements配列を順に処理
        - background: 背景画像を生成
        - image: イラスト/アイコン等を生成
        - text: テキストボックスとして配置
        - shape: 図形として配置

        Args:
            design: 設計JSON（elements配列を含む）
        """
        from .tools.text_to_image import generate_image

        steps = []
        pptx_elements = []  # PPTX生成用の要素リスト

        # elements配列を取得
        elements = design.get("elements", [])
        meta = design.get("meta", {})
        color_scheme = meta.get("color_scheme", {})

        if not elements:
            return {
                "success": False,
                "error": "No elements found in design",
                "steps": steps
            }

        print(f"  処理する要素数: {len(elements)}")
        image_count = 0

        for i, elem in enumerate(elements):
            elem_type = elem.get("type")
            elem_id = elem.get("id", f"{elem_type}_{i}")

            print(f"  [{i+1}/{len(elements)}] {elem_type}: {elem_id}")

            if elem_type == "background":
                # 背景画像を生成
                prompt = elem.get("prompt", "")
                style = elem.get("style", {})

                if prompt:
                    style_desc = self._build_style_description(style, color_scheme)
                    result = generate_image(
                        prompt=prompt,
                        style_description=style_desc,
                        aspect_ratio="16:9",
                        image_size="2K",
                        no_text=True
                    )

                    if result.get("success"):
                        bg_path = save_image(result["image_base64"], "background", self.session_id)
                        pptx_elements.append({
                            "id": elem_id,
                            "type": "background",
                            "image_base64": result["image_base64"],
                            "file_path": bg_path
                        })
                        steps.append(f"背景画像を生成: {bg_path}")
                        print(f"      → 生成成功: {bg_path}")
                    else:
                        print(f"      → 生成失敗: {result.get('error')}")
                        steps.append(f"背景生成失敗: {result.get('error')}")

            elif elem_type == "image":
                # イラスト/アイコン等を生成
                prompt = elem.get("prompt", "")
                position = elem.get("position", {})
                style = elem.get("style", {})

                if prompt:
                    image_count += 1
                    style_desc = f"Style: {style.get('type', 'illustration')}. {style.get('details', '')}"
                    result = generate_image(
                        prompt=prompt,
                        style_description=style_desc,
                        aspect_ratio="1:1",  # イラストは正方形
                        image_size="1K",
                        no_text=True
                    )

                    if result.get("success"):
                        img_path = save_image(result["image_base64"], f"image_{image_count}", self.session_id)
                        pptx_elements.append({
                            "id": elem_id,
                            "type": "image",
                            "image_base64": result["image_base64"],
                            "file_path": img_path,
                            "bbox": {
                                "x": position.get("x", 0),
                                "y": position.get("y", 0),
                                "width": position.get("width", 400),
                                "height": position.get("height", 400)
                            }
                        })
                        steps.append(f"画像を生成: {elem_id}")
                        print(f"      → 生成成功: {img_path}")
                    else:
                        print(f"      → 生成失敗: {result.get('error')}")
                        steps.append(f"画像生成失敗 ({elem_id}): {result.get('error')}")

            elif elem_type == "text":
                # テキスト要素（PPTXでテキストボックスとして配置）
                content = elem.get("content", "")
                position = elem.get("position", {})
                style = elem.get("style", {})

                if content:
                    pptx_elements.append({
                        "id": elem_id,
                        "type": "text",
                        "content": content,
                        "bbox": {
                            "x": position.get("x", 960),
                            "y": position.get("y", 400),
                            "width": position.get("width", 1600),
                            "height": position.get("height", 100)
                        },
                        "style": {
                            "fontSize": style.get("fontSize", 48),
                            "fontWeight": style.get("fontWeight", "normal"),
                            "fontStyle": style.get("fontStyle", "normal"),
                            "color": style.get("color", "#FFFFFF"),
                            "align": style.get("align", "center")
                        }
                    })
                    steps.append(f"テキスト: {content[:30]}...")
                    print(f"      → テキスト追加: {content[:30]}...")

            elif elem_type == "shape":
                # 図形要素は無視（画像生成で対応）
                print(f"      → スキップ: shape要素は非対応")

        # PPTX生成
        print(f"  PPTX生成中... ({len(pptx_elements)}要素)")
        pptx_result = _image_to_pptx(
            elements=pptx_elements,
            session_id=self.session_id
        )

        pptx_result_path = None
        if pptx_result.get("success"):
            pptx_result_path = pptx_result["file_path"]
            steps.append(f"PPTX生成完了: {pptx_result_path}")
            print(f"      → PPTX: {pptx_result_path}")
        else:
            print(f"      → PPTX生成失敗: {pptx_result.get('error')}")
            steps.append(f"PPTX生成に失敗: {pptx_result.get('error')}")

        # 結果画像は背景画像を使用
        result_image = None
        result_path = None
        for elem in pptx_elements:
            if elem.get("type") == "background" and elem.get("image_base64"):
                result_image = elem["image_base64"]
                result_path = elem["file_path"]
                break

        return {
            "success": pptx_result.get("success", False),
            "image_base64": result_image,
            "elements": pptx_elements,
            "result_path": result_path,
            "pptx_result_path": pptx_result_path,
            "element_files": pptx_result.get("element_files", []),
            "steps": steps
        }

    def _build_style_description(self, style: dict, color_scheme: dict) -> str:
        """スタイル情報から叙述的な説明を生成"""
        parts = []

        if style.get("lighting"):
            parts.append(f"Lighting: {style['lighting']}")
        if style.get("color_tone"):
            parts.append(f"Color tone: {style['color_tone']}")
        if style.get("texture"):
            parts.append(f"Texture: {style['texture']}")

        if color_scheme:
            colors = []
            if color_scheme.get("primary"):
                colors.append(f"primary {color_scheme['primary']}")
            if color_scheme.get("secondary"):
                colors.append(f"secondary {color_scheme['secondary']}")
            if color_scheme.get("accent"):
                colors.append(f"accent {color_scheme['accent']}")
            if colors:
                parts.append(f"Color palette: {', '.join(colors)}")

        return ". ".join(parts) if parts else ""

    def generate(
        self,
        user_prompt: str,
        reference_image_base64: Optional[str] = None,
        use_reasoning: bool = True,
        use_web_research: bool = True
    ) -> dict:
        """
        ユーザーの指示からスライドを生成

        Args:
            user_prompt: ユーザーの自然言語指示
            reference_image_base64: 参照画像のBase64データ（オプション）
                                    スタイルや構成の参考にする
            use_reasoning: reasoningフェーズを使用するか（デフォルト: True）
            use_web_research: webリサーチを使用するか（デフォルト: True）

        Returns:
            dict: 生成結果
        """
        try:
            steps = []
            reasoning: Optional[str] = None
            web_research: Optional[dict] = None

            # Phase 1: Web Research（エージェントが自律判断）
            if use_web_research:
                print("\n[Phase 1] Web Research...")
                web_research = self._web_research(user_prompt, input_image=reference_image_base64)
                if web_research:
                    research_preview = web_research['research'][:200] + "..." if len(web_research['research']) > 200 else web_research['research']
                    print(f"  検索結果: {research_preview}")
                    steps.append("Webリサーチ完了")
                    grounding = web_research.get("grounding")
                    if grounding and grounding.get("sources"):
                        sources = grounding["sources"]
                        steps.append(f"  参照ソース: {len(sources)}件")
                else:
                    print("  → 検索不要と判断")
                    steps.append("Webリサーチ: 不要と判断")

            # Phase 2: Reasoning（デザイン分析）
            if use_reasoning:
                print("\n[Phase 2] デザイン分析（Reasoning）...")
                reasoning = self._reason(
                    user_prompt,
                    input_image=reference_image_base64,
                    web_research=web_research
                )
                print(f"  分析結果:\n{reasoning[:500]}..." if len(reasoning) > 500 else f"  分析結果:\n{reasoning}")
                steps.append("デザイン分析完了")

            # Phase 3: 設計JSON生成
            print("\n[Phase 3] 設計JSON生成中...")
            design = self._parse_design(
                user_prompt,
                reasoning=reasoning,
                input_image=reference_image_base64
            )
            print(f"  設計JSON（プリセット解決前）: {json.dumps(design, ensure_ascii=False, indent=2)}")

            # Phase 4: プリセット解決
            print("\n[Phase 4] プリセット解決中...")
            preset_info = design.get("preset", {})
            if preset_info:
                print(f"  プリセット: layout={preset_info.get('layout')}, palette={preset_info.get('palette')}, tone={preset_info.get('tone')}")
            resolved_design = resolve_presets(design)
            print(f"  設計JSON（プリセット解決後）: {json.dumps(resolved_design, ensure_ascii=False, indent=2)}")
            steps.append(f"プリセット解決完了: layout={preset_info.get('layout', 'center')}, palette={preset_info.get('palette', 'light')}, tone={preset_info.get('tone', '-')}")

            # 設計JSONを保存
            design_path = save_design(resolved_design, self.session_id, reasoning, web_research)
            steps.append(f"設計JSONを保存: {design_path}")

            # Phase 5: 実行（各要素を生成 → PPTX統合）
            print("\n[Phase 5] 設計を実行中...")
            result = self._execute_design(resolved_design)

            # ステップをマージ
            all_steps = steps + result.get("steps", [])

            return {
                "success": result.get("success", False),
                "session_id": self.session_id,
                "design": resolved_design,
                "design_raw": design,
                "preset": preset_info,
                "reasoning": reasoning,
                "web_research": web_research,
                "steps": all_steps,
                "image_base64": result.get("image_base64"),
                "elements": result.get("elements"),
                "result_path": result.get("result_path"),
                "pptx_result_path": result.get("pptx_result_path"),
                "element_files": result.get("element_files"),
                "response": "\n".join(all_steps)
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "session_id": self.session_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def refine(
        self,
        feedback: str,
        session_id: Optional[str] = None
    ) -> dict:
        """
        既存の設計を修正して再生成

        Args:
            feedback: ユーザーのフィードバック（修正指示）
            session_id: 修正対象のセッションID（省略時は現在のセッション）

        Returns:
            dict: 生成結果
        """
        try:
            target_session = session_id or self.session_id
            steps = []

            # 既存の設計を読み込み
            print(f"\n[Refine] セッション {target_session} の設計を読み込み中...")
            saved_data = load_design(target_session)

            if not saved_data:
                return {
                    "success": False,
                    "error": f"セッション {target_session} の設計が見つかりません"
                }

            current_design = saved_data.get("design", {})
            print(f"  現在の設計: {json.dumps(current_design, ensure_ascii=False)[:200]}...")

            # フィードバックを元に設計を更新
            print(f"\n[Refine] フィードバックを反映中...")
            print(f"  フィードバック: {feedback}")

            refine_prompt = REFINE_PROMPT.format(
                current_design=json.dumps(current_design, ensure_ascii=False, indent=2),
                feedback=feedback
            )

            response = self.client.models.generate_content(
                model=DESIGN_MODEL,
                contents=[refine_prompt]
            )

            # JSONを抽出
            text = response.text
            json_match = re.search(r'\{[\s\S]*\}', text)
            if not json_match:
                return {
                    "success": False,
                    "error": f"修正後のJSONを解析できませんでした: {text}"
                }

            new_design = json.loads(json_match.group())
            print(f"  修正後の設計（プリセット解決前）: {json.dumps(new_design, ensure_ascii=False, indent=2)}")

            # プリセット解決
            preset_info = new_design.get("preset", {})
            if preset_info:
                print(f"  プリセット: layout={preset_info.get('layout')}, palette={preset_info.get('palette')}, tone={preset_info.get('tone')}")
            resolved_design = resolve_presets(new_design)
            print(f"  修正後の設計（プリセット解決後）: {json.dumps(resolved_design, ensure_ascii=False, indent=2)}")

            # 変更された要素を特定
            changes = self._detect_changes(current_design, resolved_design)
            print(f"  変更された要素: {changes}")
            steps.append(f"変更を検出: {', '.join(changes) if changes else 'なし'}")

            # 新しいセッションIDで保存（修正版）
            self.session_id = self._generate_session_id()
            design_path = save_design(resolved_design, self.session_id, reasoning=None)
            steps.append(f"修正後の設計を保存: {design_path}")

            # 実行（各要素を生成 → PPTX統合）
            print("\n[Refine] 修正後の設計を実行中...")
            result = self._execute_design(resolved_design)

            all_steps = steps + result.get("steps", [])

            return {
                "success": result.get("success", False),
                "session_id": self.session_id,
                "previous_session_id": target_session,
                "design": resolved_design,
                "design_raw": new_design,
                "preset": preset_info,
                "changes": changes,
                "steps": all_steps,
                "image_base64": result.get("image_base64"),
                "elements": result.get("elements"),
                "result_path": result.get("result_path"),
                "pptx_result_path": result.get("pptx_result_path"),
                "element_files": result.get("element_files"),
                "response": "\n".join(all_steps)
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "session_id": self.session_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _detect_changes(self, old_design: dict, new_design: dict) -> List[str]:
        """設計の変更点を検出"""
        changes = []
        elements = ["background", "illustration", "title", "subtitle"]

        for element in elements:
            old_val = old_design.get(element)
            new_val = new_design.get(element)

            if old_val != new_val:
                changes.append(element)

        return changes


def main():
    """CLI エントリーポイント"""
    import sys

    input_data = sys.stdin.read()

    try:
        params = json.loads(input_data)
    except json.JSONDecodeError:
        print(json.dumps({"success": False, "error": "Invalid JSON input"}))
        sys.exit(1)

    agent = DesignerAgent()
    result = agent.generate(user_prompt=params.get("userPrompt", ""))

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
