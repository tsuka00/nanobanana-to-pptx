"""
Designer Agent
自然言語の指示から画像デザインを生成するエージェント（要素別生成版）
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
from PIL import Image

# Nanobanana 画像生成（前処理）
from .tools.text_to_image import text_to_image as _text_to_image

# Text-to-* ツール（新規生成）
from .tools.text_to_background import text_to_background as _text_to_background
from .tools.text_to_title import text_to_title as _text_to_title
from .tools.text_to_subtitle import text_to_subtitle as _text_to_subtitle

# Image-to-* ツール（既存画像編集）
from .tools.image_to_background import image_to_background as _image_to_background

# イラスト描画ツール（Pillow）
from .tools.draw_illustration import draw_illustration as _draw_illustration

# 合成ツール
from .tools.compose_slide import compose_slide as _compose_slide

# SVGツール
from .tools.image_to_svg import image_to_svg as _image_to_svg
from .tools.text_to_title_svg import text_to_title_svg as _text_to_title_svg
from .tools.text_to_subtitle_svg import text_to_subtitle_svg as _text_to_subtitle_svg
from .tools.draw_illustration_svg import draw_illustration_svg as _draw_illustration_svg
from .tools.compose_slide_svg import compose_slide_svg as _compose_slide_svg

# PPTXツール
from .tools.svg_to_pptx import svg_to_pptx as _svg_to_pptx
from .tools.svg_to_pptx import svg_to_pptx_editable as _svg_to_pptx_editable

# プリセットシステム
from .presets import get_preset_summary, LAYOUTS, PALETTES, TONES
from .preset_resolver import resolve_presets, get_prompt_for_preset_selection

# .env.local を読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

# 出力ディレクトリ
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_SVG_DIR = Path(__file__).parent.parent / "output_svg"
OUTPUT_PARSE_IMAGE_DIR = Path(__file__).parent.parent / "output_parse_image"
OUTPUT_DESIGN_DIR = Path(__file__).parent.parent / "output_design"

# 設計フェーズ用のモデル
DESIGN_MODEL = "gemini-2.0-flash"

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

DESIGN_SYSTEM_PROMPT = """あなたは画像デザインの設計者です。
事前のデザイン分析（Reasoning）の結果を踏まえて、最適な設計JSONを出力してください。
JSONのみを出力し、他のテキストは含めないでください。

キャンバスサイズは 1920x1080 (16:9) です。

## JSON形式

{
  "preset": {
    "layout": "レイアウト名（省略可）",
    "palette": "パレット名（省略可）",
    "tone": "トーン名（省略可）"
  },
  "background": {
    "prompt": "背景画像の生成プロンプト（省略時はパレットのヒントを使用）"
  },
  "illustration": {
    "type": "polygon | rectangle | ellipse | triangle",
    "points": [[x1, y1], [x2, y2], ...],
    "fill": {
      "type": "solid | gradient",
      "color": "#色（solidの場合、省略時はパレットのアクセント色）",
      "start": "#開始色（gradientの場合）",
      "end": "#終了色（gradientの場合）",
      "direction": "vertical | horizontal | diagonal"
    },
    "opacity": 0.0-1.0
  },
  "title": {
    "text": "タイトル",
    "x": "X座標（省略時はレイアウトのデフォルト）",
    "y": "Y座標（省略時はレイアウトのデフォルト）",
    "fontSize": サイズ,
    "fontFamily": "フォント名",
    "fontWeight": "normal | bold | light（省略時はトーンのデフォルト）",
    "style": "flat | shadow | 3d-metallic | neon-glow | glass | outline | gold | silver | emboss | gradient（省略時はパレットの推奨スタイル）",
    "color": "#色（省略時はパレットのtext_primary）",
    "glowColor": "#色（neon-glow用、オプション）",
    "fill": {
      "type": "gradient",
      "start": "#開始色（省略時はパレットのアクセント色）",
      "end": "#終了色（省略時はパレットのtext_primary）",
      "direction": "vertical | horizontal | diagonal"
    }
  },
  "subtitle": {
    "text": "サブタイトル",
    "x": "X座標（省略時はレイアウトのデフォルト）",
    "y": "Y座標（省略時はレイアウトのデフォルト）",
    "fontSize": サイズ,
    "fontFamily": "フォント名",
    "fontWeight": "normal | bold | light（省略時はトーンのデフォルト）",
    "style": "flat | shadow | ... （省略時はflat）",
    "color": "#色（省略時はパレットのtext_secondary）"
  }
}

## プリセットシステム

### レイアウトプリセット（preset.layout）
| 名前 | 説明 | タイトル位置 |
|------|------|------------|
| center | 中央配置（デフォルト） | (960, 400) |
| center-middle | 中央・垂直中央 | (960, 480) |
| left | 左寄せ | (200, 400) |
| right | 右寄せ | (1720, 400) |
| bottom | 下部配置 | (960, 800) |
| top | 上部配置 | (960, 200) |
| split-left | 左半分（50:50分割） | (480, 450) |
| split-right | 右半分（50:50分割） | (1440, 450) |
| bottom-left | 左下配置 | (200, 800) |
| bottom-right | 右下配置 | (1720, 800) |
| overlay | オーバーレイ | (960, 480) |

### 配色パレット（preset.palette）
| 名前 | 背景 | 用途 |
|------|------|------|
| light | #ffffff | 明るい、ビジネス |
| light-warm | #faf8f5 | 温かみ |
| light-cool | #f5f9fc | クール |
| dark | #1a1a1a | モダン |
| dark-tech | #0a0a0a | テック、サイバー |
| dark-purple | #1a0a2e | クリエイティブ |
| monochrome | #f5f5f5 | ミニマル |
| monochrome-dark | #121212 | ダークミニマル |
| premium-gold | #1a1a1a | 高級感・ゴールド |
| premium-silver | #1a1a2e | 高級感・シルバー |
| vibrant | #ffffff | エネルギッシュ |
| vibrant-gradient | #667eea | グラデーション背景 |
| nature | #f5f5dc | 自然・エコ |
| ocean | #e3f2fd | 海・青系 |
| corporate | #f8f9fa | 企業向け |
| corporate-dark | #1e2a3a | 企業向けダーク |

### トーンプリセット（preset.tone）
| 名前 | 説明 | 推奨パレット |
|------|------|------------|
| professional | ビジネス、信頼感 | corporate, light |
| creative | アーティスティック | vibrant, dark-purple |
| tech | 未来的、先進的 | dark-tech, dark |
| premium | 高級、ラグジュアリー | premium-gold, premium-silver |
| minimal | シンプル、余白重視 | monochrome, light |
| energetic | 活発、ダイナミック | vibrant, vibrant-gradient |
| warm | 温かみ、親しみ | light-warm, nature |
| cool | クール、知的 | light-cool, ocean |
| nature | 自然、オーガニック | nature, ocean |
| playful | 遊び心、楽しさ | vibrant, light-warm |

## ルール

- Reasoningで推奨されたプリセット（tone, layout, palette）をpresetセクションに指定
- **座標や色は省略可能** - プリセットから自動解決される
- 明示的に指定した値はプリセットより優先される
- ユーザーが指示していない要素は null にする
- 背景のpromptは省略可能（パレットのヒントから生成）
- illustrationは単一のオブジェクトとして返す

## スタイル選択ガイド

| ユーザーの要望 | 選ぶべきstyle |
|--------------|--------------|
| ホログラム、メタリック、3D、立体 | **3d-metallic** |
| 発光、ネオン、サイバー | neon-glow |
| 高級感、ゴールド | gold |
| クール、シルバー | silver |
| シンプル、ビジネス | flat |

## プリセット活用の例

### 例1: テック系プレゼン
```json
{
  "preset": { "tone": "tech", "layout": "center", "palette": "dark-tech" },
  "title": { "text": "AI革命", "fontSize": 100, "style": "3d-metallic" },
  "subtitle": { "text": "未来を創る技術" }
}
```
→ 座標・色はプリセットから自動解決

### 例2: 高級感のある告知
```json
{
  "preset": { "tone": "premium", "layout": "center-middle", "palette": "premium-gold" },
  "title": { "text": "GRAND OPENING", "fontSize": 120, "style": "gold" },
  "subtitle": { "text": "特別なひとときを" }
}
```

### 例3: カジュアルなイベント
```json
{
  "preset": { "tone": "playful", "layout": "left", "palette": "vibrant" },
  "title": { "text": "夏祭り開催！", "fontSize": 80 },
  "subtitle": { "text": "8月15日 みんなで楽しもう" }
}
```

## フォントファミリー

| フォント | 用途 |
|----------|------|
| Hiragino Sans | モダン、クリーン（デフォルト） |
| Hiragino Mincho | フォーマル、伝統的 |
| Hiragino Maru Gothic | 親しみやすい、カジュアル |
| Helvetica Neue | 欧文、モダン |
| Arial | 欧文、汎用 |
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


def save_image(image_base64: str, folder: str, session_id: str) -> str:
    """画像を保存してパスを返す"""
    output_path = OUTPUT_DIR / folder / f"{session_id}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_data = base64.b64decode(image_base64)
    with open(output_path, 'wb') as f:
        f.write(image_data)

    return str(output_path)


def save_design(design: dict, session_id: str, reasoning: Optional[str] = None) -> str:
    """設計JSONを保存してパスを返す"""
    output_path = OUTPUT_DESIGN_DIR / f"{session_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 設計JSONとreasoningをまとめて保存
    data = {
        "session_id": session_id,
        "design": design,
        "reasoning": reasoning
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(output_path)


def load_design(session_id: str) -> Optional[dict]:
    """保存された設計JSONを読み込む"""
    design_path = OUTPUT_DESIGN_DIR / f"{session_id}.json"
    if not design_path.exists():
        return None

    with open(design_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_svg(svg_content: str, folder: str, session_id: str) -> str:
    """SVGを保存してパスを返す"""
    output_path = OUTPUT_SVG_DIR / folder / f"{session_id}.svg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    return str(output_path)


def save_parse_image(image_base64: str, session_id: str) -> str:
    """前処理画像を保存してパスを返す"""
    output_path = OUTPUT_PARSE_IMAGE_DIR / f"{session_id}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_data = base64.b64decode(image_base64)
    with open(output_path, 'wb') as f:
        f.write(image_data)

    return str(output_path)


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

    def _reason(
        self,
        user_prompt: str,
        input_image: Optional[str] = None,
        nanobanana_image: Optional[str] = None
    ) -> str:
        """ユーザーのプロンプトを深く分析してデザイン方針を決定

        Args:
            user_prompt: ユーザーの自然言語指示
            input_image: ユーザー入力画像のBase64（オプション）
            nanobanana_image: nanobanana前処理で生成した画像のBase64（オプション）

        Returns:
            str: 分析結果（reasoning）
        """
        contents: List = []

        text_prompt = REASONING_PROMPT + "\n\n## ユーザーの指示\n" + user_prompt

        # 画像がある場合は参照情報を追加
        if input_image or nanobanana_image:
            text_prompt += "\n\n## 参考画像あり\n画像も考慮してデザインを検討してください。"

        contents.append(text_prompt)

        # 画像をコンテンツに追加
        if input_image:
            contents.append(self._base64_to_pil(input_image))
        if nanobanana_image:
            contents.append(self._base64_to_pil(nanobanana_image))

        response = self.client.models.generate_content(
            model=DESIGN_MODEL,
            contents=contents
        )

        return response.text

    def _parse_design(
        self,
        user_prompt: str,
        reasoning: Optional[str] = None,
        input_image: Optional[str] = None,
        nanobanana_image: Optional[str] = None
    ) -> dict:
        """ユーザーのプロンプトをJSON設計に変換（マルチモーダル対応）

        Args:
            user_prompt: ユーザーの自然言語指示
            reasoning: 事前のデザイン分析結果
            input_image: ユーザー入力画像のBase64（オプション）
            nanobanana_image: nanobanana前処理で生成した画像のBase64（オプション）
        """
        # コンテンツリストを構築
        contents: List = []

        # システムプロンプト + ユーザー指示
        text_prompt = DESIGN_SYSTEM_PROMPT + "\n\n## ユーザーの指示\n" + user_prompt

        # Reasoning結果がある場合は追加
        if reasoning:
            text_prompt += "\n\n## デザイン分析（Reasoning）\n" + reasoning

        # 画像がある場合は参照情報を追加
        image_descriptions = []
        if input_image:
            image_descriptions.append("【ユーザー提供画像】この画像をベースに設計してください。")
        if nanobanana_image:
            image_descriptions.append("【AI生成参照画像】この画像のスタイルや雰囲気を参考にしてください。")

        if image_descriptions:
            text_prompt += "\n\n" + "\n".join(image_descriptions)

        contents.append(text_prompt)

        # 画像をコンテンツに追加
        if input_image:
            contents.append(self._base64_to_pil(input_image))
        if nanobanana_image:
            contents.append(self._base64_to_pil(nanobanana_image))

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

    def _execute_design(self, design: dict, input_image: Optional[str] = None) -> dict:
        """設計JSONに基づいて各要素を生成

        Args:
            design: 設計JSON
            input_image: 入力画像のBase64データ（オプション）
        """
        steps = []
        elements = {}      # PNG用
        svg_elements = {}  # SVG用
        mode = "image-to-image" if input_image else "text-to-image"
        print(f"  モード: {mode}")

        # 1. 背景生成
        bg = design.get("background")
        if bg and bg.get("prompt"):
            print(f"  [Step 1] 背景生成: {bg['prompt'][:50]}...")
            if input_image:
                result = _image_to_background._tool_func(
                    prompt=bg["prompt"],
                    image_base64=input_image
                )
            else:
                result = _text_to_background._tool_func(prompt=bg["prompt"])

            if result.get("success"):
                elements["background"] = result["image_base64"]
                path = save_image(result["image_base64"], "background", self.session_id)
                steps.append(f"背景を生成: {path}")

                # SVG変換（Base64埋め込み）
                svg_result = _image_to_svg._tool_func(image_base64=result["image_base64"])
                if svg_result.get("success"):
                    svg_elements["background"] = svg_result["svg"]
                    svg_path = save_svg(svg_result["svg"], "background", self.session_id)
                    steps.append(f"背景SVGを生成: {svg_path}")
            else:
                print(f"  [Error] 背景生成失敗: {result.get('error')}")
                steps.append(f"背景生成に失敗: {result.get('error')}")
        else:
            print("  [Step 1] 背景: スキップ")

        # 2. イラスト生成（Pillow描画 + SVG）
        illust_data = design.get("illustration")

        # 配列の場合は最初の要素を使用（後方互換性）
        # TODO: 将来的には複数イラストレーションの合成に対応
        if isinstance(illust_data, list):
            illust = illust_data[0] if illust_data else None
            if len(illust_data) > 1:
                print(f"  [Note] {len(illust_data)}個のイラストが指定されましたが、現在は最初の1つのみ使用します")
        else:
            illust = illust_data

        if illust and isinstance(illust, dict) and illust.get("type"):
            shape_type = illust.get("type", "polygon")
            print(f"  [Step 2] イラスト生成: {shape_type}...")

            # PNG版
            result = _draw_illustration._tool_func(shape=illust)
            if result.get("success"):
                elements["illustration"] = result["image_base64"]
                path = save_image(result["image_base64"], "illustration", self.session_id)
                steps.append(f"イラストを生成: {path}")

            # SVG版（直接生成）
            svg_result = _draw_illustration_svg._tool_func(shape=illust)
            if svg_result.get("success"):
                svg_elements["illustration"] = svg_result["svg"]
                svg_path = save_svg(svg_result["svg"], "illustration", self.session_id)
                steps.append(f"イラストSVGを生成: {svg_path}")
            else:
                print(f"  [Error] イラスト生成失敗: {result.get('error')}")
                steps.append(f"イラスト生成に失敗: {result.get('error')}")
        else:
            print("  [Step 2] イラスト: スキップ")

        # 3. タイトル生成
        title = design.get("title")
        if title and title.get("text"):
            print(f"  [Step 3] タイトル生成: {title['text'][:30]}...")

            # fillの処理（後方互換性: colorも受け付ける）
            title_fill = title.get("fill")
            if title_fill is None and title.get("color"):
                title_fill = title.get("color")

            # PNG版（単色のみ対応）
            title_color = "#ffffff"
            if isinstance(title_fill, str):
                title_color = title_fill
            elif isinstance(title_fill, dict):
                title_color = title_fill.get("color", title_fill.get("start", "#ffffff"))

            result = _text_to_title._tool_func(
                text=title["text"],
                x=title.get("x", 960),
                y=title.get("y", 400),
                font_size=title.get("fontSize", 64),
                color=title_color
            )
            if result.get("success"):
                elements["title"] = result["image_base64"]
                path = save_image(result["image_base64"], "title", self.session_id)
                steps.append(f"タイトルを生成: {path}")

            # SVG版（スタイルプリセット対応）
            title_style = title.get("style", "flat")
            svg_result = _text_to_title_svg._tool_func(
                text=title["text"],
                x=title.get("x", 960),
                y=title.get("y", 400),
                font_size=title.get("fontSize", 64),
                font_family=title.get("fontFamily"),
                font_weight=title.get("fontWeight", "bold"),
                color=title.get("color", title_color),
                style=title_style,
                fill=title_fill,
                glow_color=title.get("glowColor")
            )
            if svg_result.get("success"):
                svg_elements["title"] = svg_result["svg"]
                svg_path = save_svg(svg_result["svg"], "title", self.session_id)
                steps.append(f"タイトルSVGを生成 (style={title_style}): {svg_path}")
            else:
                print(f"  [Error] タイトル生成失敗: {svg_result.get('error')}")
                steps.append(f"タイトル生成に失敗: {svg_result.get('error')}")
        else:
            print("  [Step 3] タイトル: スキップ")

        # 4. サブタイトル生成
        subtitle = design.get("subtitle")
        if subtitle and subtitle.get("text"):
            print(f"  [Step 4] サブタイトル生成: {subtitle['text'][:30]}...")

            # fillの処理（後方互換性: colorも受け付ける）
            subtitle_fill = subtitle.get("fill")
            if subtitle_fill is None and subtitle.get("color"):
                subtitle_fill = subtitle.get("color")

            # PNG版（単色のみ対応）
            subtitle_color = "#ffffff"
            if isinstance(subtitle_fill, str):
                subtitle_color = subtitle_fill
            elif isinstance(subtitle_fill, dict):
                subtitle_color = subtitle_fill.get("color", subtitle_fill.get("start", "#ffffff"))

            result = _text_to_subtitle._tool_func(
                text=subtitle["text"],
                x=subtitle.get("x", 960),
                y=subtitle.get("y", 500),
                font_size=subtitle.get("fontSize", 36),
                color=subtitle_color
            )
            if result.get("success"):
                elements["subtitle"] = result["image_base64"]
                path = save_image(result["image_base64"], "subtitle", self.session_id)
                steps.append(f"サブタイトルを生成: {path}")

            # SVG版（スタイルプリセット対応）
            subtitle_style = subtitle.get("style", "flat")
            svg_result = _text_to_subtitle_svg._tool_func(
                text=subtitle["text"],
                x=subtitle.get("x", 960),
                y=subtitle.get("y", 500),
                font_size=subtitle.get("fontSize", 36),
                font_family=subtitle.get("fontFamily"),
                font_weight=subtitle.get("fontWeight", "normal"),
                color=subtitle.get("color", subtitle_color),
                style=subtitle_style,
                fill=subtitle_fill,
                glow_color=subtitle.get("glowColor")
            )
            if svg_result.get("success"):
                svg_elements["subtitle"] = svg_result["svg"]
                svg_path = save_svg(svg_result["svg"], "subtitle", self.session_id)
                steps.append(f"サブタイトルSVGを生成 (style={subtitle_style}): {svg_path}")
            else:
                print(f"  [Error] サブタイトル生成失敗: {svg_result.get('error')}")
                steps.append(f"サブタイトル生成に失敗: {svg_result.get('error')}")
        else:
            print("  [Step 4] サブタイトル: スキップ")

        # 5. PNG合成
        print("  [Step 5] PNG合成中...")
        result = _compose_slide._tool_func(
            background_base64=elements.get("background"),
            illustration_base64=elements.get("illustration"),
            illustration_x=0,  # 座標は描画済みなので(0,0)に配置
            illustration_y=0,
            title_base64=elements.get("title"),
            subtitle_base64=elements.get("subtitle")
        )

        result_path = None
        if result.get("success"):
            result_path = save_image(result["image_base64"], "result", self.session_id)
            steps.append(f"PNG合成完了: {result_path}")
        else:
            print(f"  [Error] PNG合成失敗: {result.get('error')}")
            steps.append(f"PNG合成に失敗: {result.get('error')}")

        # 6. SVG合成
        print("  [Step 6] SVG合成中...")
        svg_result = _compose_slide_svg._tool_func(
            background_svg=svg_elements.get("background"),
            illustration_svg=svg_elements.get("illustration"),
            title_svg=svg_elements.get("title"),
            subtitle_svg=svg_elements.get("subtitle")
        )

        svg_result_path = None
        if svg_result.get("success"):
            svg_result_path = save_svg(svg_result["svg"], "result", self.session_id)
            steps.append(f"SVG合成完了: {svg_result_path}")
        else:
            print(f"  [Error] SVG合成失敗: {svg_result.get('error')}")
            steps.append(f"SVG合成に失敗: {svg_result.get('error')}")

        # 7. PPTX生成（編集可能版）
        pptx_result_path = None
        print("  [Step 7] PPTX生成中（編集可能）...")

        # タイトル・サブタイトルの設定を取得
        title = design.get("title")
        subtitle = design.get("subtitle")

        title_config = None
        if title and title.get("text"):
            # fillからcolorを取得（後方互換性）
            title_color = title.get("color", "#FFFFFF")
            title_fill = title.get("fill")
            if isinstance(title_fill, str):
                title_color = title_fill
            elif isinstance(title_fill, dict):
                title_color = title_fill.get("color", title_fill.get("start", title_color))

            title_config = {
                "text": title["text"],
                "x": title.get("x", 960),
                "y": title.get("y", 400),
                "fontSize": title.get("fontSize", 64),
                "fontFamily": title.get("fontFamily", "Arial"),
                "fontWeight": title.get("fontWeight", "bold"),
                "color": title_color
            }

        subtitle_config = None
        if subtitle and subtitle.get("text"):
            # fillからcolorを取得（後方互換性）
            subtitle_color = subtitle.get("color", "#FFFFFF")
            subtitle_fill = subtitle.get("fill")
            if isinstance(subtitle_fill, str):
                subtitle_color = subtitle_fill
            elif isinstance(subtitle_fill, dict):
                subtitle_color = subtitle_fill.get("color", subtitle_fill.get("start", subtitle_color))

            subtitle_config = {
                "text": subtitle["text"],
                "x": subtitle.get("x", 960),
                "y": subtitle.get("y", 500),
                "fontSize": subtitle.get("fontSize", 36),
                "fontFamily": subtitle.get("fontFamily", "Arial"),
                "fontWeight": subtitle.get("fontWeight", "normal"),
                "color": subtitle_color
            }

        pptx_result = _svg_to_pptx_editable._tool_func(
            session_id=self.session_id,
            folder="result",
            background_base64=elements.get("background"),
            illustration_base64=elements.get("illustration"),
            title_config=title_config,
            subtitle_config=subtitle_config
        )
        if pptx_result.get("success"):
            pptx_result_path = pptx_result["file_path"]
            steps.append(f"PPTX生成完了（編集可能）: {pptx_result_path}")
        else:
            print(f"  [Error] PPTX生成失敗: {pptx_result.get('error')}")
            steps.append(f"PPTX生成に失敗: {pptx_result.get('error')}")

        if result.get("success"):
            return {
                "success": True,
                "image_base64": result["image_base64"],
                "svg": svg_result.get("svg") if svg_result.get("success") else None,
                "result_path": result_path,
                "svg_result_path": svg_result_path,
                "pptx_result_path": pptx_result_path,
                "steps": steps
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "steps": steps
            }

    def generate(
        self,
        user_prompt: str,
        image_base64: Optional[str] = None,
        use_nanobanana: bool = True,
        use_reasoning: bool = True
    ) -> dict:
        """
        ユーザーの指示から画像を生成

        Args:
            user_prompt: ユーザーの自然言語指示
            image_base64: 入力画像のBase64データ（オプション）
                          指定すると image-to-image モードで動作
            use_nanobanana: nanobanana前処理を使用するか（デフォルト: True）
            use_reasoning: reasoningフェーズを使用するか（デフォルト: True）

        Returns:
            dict: 生成結果
        """
        try:
            steps = []
            nanobanana_image: Optional[str] = None
            reasoning: Optional[str] = None

            # Phase 0: Nanobanana 前処理
            if use_nanobanana:
                print("\n[Phase 0] Nanobanana 前処理...")
                print(f"  プロンプト: {user_prompt[:50]}...")
                if image_base64:
                    print("  参照画像あり: 構造・スタイルを参考に生成")

                # 参照画像がある場合は一緒に渡す
                nanobanana_result = _text_to_image._tool_func(
                    prompt=user_prompt,
                    reference_image_base64=image_base64
                )

                if nanobanana_result.get("success"):
                    nanobanana_image = nanobanana_result["image_base64"]
                    # 前処理画像を保存
                    nanobanana_path = save_parse_image(nanobanana_image, self.session_id)
                    steps.append(f"Nanobanana前処理画像を生成: {nanobanana_path}")
                    print(f"  前処理画像を生成: {nanobanana_path}")
                else:
                    print(f"  [Warning] Nanobanana前処理に失敗: {nanobanana_result.get('error')}")
                    steps.append(f"Nanobanana前処理に失敗（続行）: {nanobanana_result.get('error')}")

            # Phase 1a: Reasoning（デザイン分析）
            if use_reasoning:
                print("\n[Phase 1a] デザイン分析（Reasoning）...")
                reasoning = self._reason(
                    user_prompt,
                    input_image=image_base64,
                    nanobanana_image=nanobanana_image
                )
                print(f"  分析結果:\n{reasoning[:500]}..." if len(reasoning) > 500 else f"  分析結果:\n{reasoning}")
                steps.append("デザイン分析完了")

            # Phase 1b: 設計（マルチモーダル）
            print("\n[Phase 1b] 設計JSON生成中...")
            design = self._parse_design(
                user_prompt,
                reasoning=reasoning,
                input_image=image_base64,
                nanobanana_image=nanobanana_image
            )
            print(f"  設計JSON（プリセット解決前）: {json.dumps(design, ensure_ascii=False, indent=2)}")

            # Phase 1c: プリセット解決
            print("\n[Phase 1c] プリセット解決中...")
            preset_info = design.get("preset", {})
            if preset_info:
                print(f"  プリセット: layout={preset_info.get('layout')}, palette={preset_info.get('palette')}, tone={preset_info.get('tone')}")
            resolved_design = resolve_presets(design)
            print(f"  設計JSON（プリセット解決後）: {json.dumps(resolved_design, ensure_ascii=False, indent=2)}")
            steps.append(f"プリセット解決完了: layout={preset_info.get('layout', 'center')}, palette={preset_info.get('palette', 'light')}, tone={preset_info.get('tone', '-')}")

            # 設計JSONを保存（解決後のデザインを保存）
            design_path = save_design(resolved_design, self.session_id, reasoning)
            steps.append(f"設計JSONを保存: {design_path}")

            # Phase 2: 実行
            print("\n[Phase 2] 設計を実行中...")
            result = self._execute_design(resolved_design, input_image=image_base64)

            # ステップをマージ
            all_steps = steps + result.get("steps", [])

            return {
                "success": result.get("success", False),
                "session_id": self.session_id,
                "design": resolved_design,
                "design_raw": design,  # プリセット解決前の生のJSON
                "preset": preset_info,
                "reasoning": reasoning,
                "steps": all_steps,
                "nanobanana_image": nanobanana_image,
                "image_base64": result.get("image_base64"),
                "svg": result.get("svg"),
                "result_path": result.get("result_path"),
                "svg_result_path": result.get("svg_result_path"),
                "pptx_result_path": result.get("pptx_result_path"),
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

            # 実行
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
                "svg": result.get("svg"),
                "result_path": result.get("result_path"),
                "svg_result_path": result.get("svg_result_path"),
                "pptx_result_path": result.get("pptx_result_path"),
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
