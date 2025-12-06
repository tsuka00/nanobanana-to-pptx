"""
Designer Agent
自然言語の指示から画像デザインを生成するエージェント（要素別生成版）
"""

import os
import json
import base64
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai

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

# .env.local を読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

# 出力ディレクトリ
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# 設計フェーズ用のモデル
DESIGN_MODEL = "gemini-2.0-flash"

DESIGN_SYSTEM_PROMPT = """あなたは画像デザインの設計者です。
ユーザーの指示を解析し、以下のJSON形式で設計を出力してください。
JSONのみを出力し、他のテキストは含めないでください。

キャンバスサイズは 1920x1080 (16:9) です。

{
  "background": {
    "prompt": "背景画像の生成プロンプト"
  },
  "illustration": {
    "type": "polygon",
    "points": [[x1, y1], [x2, y2], [x3, y3], ...],
    "fill": {
      "type": "gradient",
      "start": "#開始色",
      "end": "#終了色",
      "direction": "diagonal"
    },
    "opacity": 1.0
  },
  "title": {
    "text": "タイトルテキスト",
    "x": X座標（中心基準）,
    "y": Y座標（中心基準）,
    "fontSize": フォントサイズ,
    "color": "文字色"
  },
  "subtitle": {
    "text": "サブタイトルテキスト",
    "x": X座標（中心基準）,
    "y": Y座標（中心基準）,
    "fontSize": フォントサイズ,
    "color": "文字色"
  }
}

重要なルール:
- ユーザーが指示していない要素は null にする
- 背景は必ず指定する（背景なしの場合も白背景を指定）
- タイトル/サブタイトルの座標はテキストの中心位置を指定する
- 座標は 0-1920 (x) と 0-1080 (y) の範囲で指定

illustration（幾何学シェイプ）の指定方法:
- type: "polygon"（多角形）, "rectangle"（矩形）, "triangle"（三角形）, "ellipse"（楕円）
- points: 多角形の頂点座標のリスト [[x1,y1], [x2,y2], ...]
- fill.type: "solid"（単色）または "gradient"（グラデーション）
- fill.color: 単色の場合の色
- fill.start, fill.end: グラデーションの開始色と終了色
- fill.direction: "vertical"（縦）, "horizontal"（横）, "diagonal"（斜め）
- opacity: 不透明度 0.0-1.0

シェイプの例（左下から斜めに覆う形）:
"points": [[0, 400], [0, 1080], [800, 1080], [400, 400]]

座標の目安（1920x1080）:
- 中央: x=960, y=540
- タイトル（中央上部）: x=960, y=400
- サブタイトル（タイトル下）: x=960, y=500
- 左寄せ: x=200
- 右寄せ: x=1720

fontSize の目安:
- メインタイトル: 64-80
- サブタイトル: 36-48
- キャプション: 24-32

color:
- 暗い背景には "#ffffff"（白）
- 明るい背景には "#000000"（黒）
"""


def save_image(image_base64: str, folder: str, session_id: str) -> str:
    """画像を保存してパスを返す"""
    output_path = OUTPUT_DIR / folder / f"{session_id}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_data = base64.b64decode(image_base64)
    with open(output_path, 'wb') as f:
        f.write(image_data)

    return str(output_path)


class DesignerAgent:
    """画像デザインを生成するエージェント（要素別生成版）"""

    def __init__(self, api_key: str = None, session_id: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self.client = genai.Client(api_key=self.api_key)
        self.session_id = session_id or self._generate_session_id()

    def _generate_session_id(self) -> str:
        """セッションIDを生成"""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=4)) + '-' + ''.join(random.choices(string.digits, k=4))

    def _parse_design(self, user_prompt: str) -> dict:
        """ユーザーのプロンプトをJSON設計に変換"""
        prompt = DESIGN_SYSTEM_PROMPT + "\n\nユーザーの指示: " + user_prompt

        response = self.client.models.generate_content(
            model=DESIGN_MODEL,
            contents=prompt
        )

        text = response.text

        # JSONを抽出
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            raise ValueError(f"Failed to parse design JSON: {text}")

        return json.loads(json_match.group())

    def _execute_design(self, design: dict, input_image: str = None) -> dict:
        """設計JSONに基づいて各要素を生成

        Args:
            design: 設計JSON
            input_image: 入力画像のBase64データ（オプション）
        """
        steps = []
        elements = {}
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
            else:
                print(f"  [Error] 背景生成失敗: {result.get('error')}")
                steps.append(f"背景生成に失敗: {result.get('error')}")
        else:
            print("  [Step 1] 背景: スキップ")

        # 2. イラスト生成（Pillow描画）
        illust = design.get("illustration")
        if illust and illust.get("type"):
            shape_type = illust.get("type", "polygon")
            print(f"  [Step 2] イラスト生成: {shape_type}...")
            result = _draw_illustration._tool_func(shape=illust)

            if result.get("success"):
                elements["illustration"] = result["image_base64"]
                path = save_image(result["image_base64"], "illustration", self.session_id)
                steps.append(f"イラストを生成: {path}")
            else:
                print(f"  [Error] イラスト生成失敗: {result.get('error')}")
                steps.append(f"イラスト生成に失敗: {result.get('error')}")
        else:
            print("  [Step 2] イラスト: スキップ")

        # 3. タイトル生成
        title = design.get("title")
        if title and title.get("text"):
            print(f"  [Step 3] タイトル生成: {title['text'][:30]}...")
            result = _text_to_title._tool_func(
                text=title["text"],
                x=title.get("x", 960),
                y=title.get("y", 400),
                font_size=title.get("fontSize", 64),
                color=title.get("color", "#ffffff")
            )
            if result.get("success"):
                elements["title"] = result["image_base64"]
                path = save_image(result["image_base64"], "title", self.session_id)
                steps.append(f"タイトルを生成: {path}")
            else:
                print(f"  [Error] タイトル生成失敗: {result.get('error')}")
                steps.append(f"タイトル生成に失敗: {result.get('error')}")
        else:
            print("  [Step 3] タイトル: スキップ")

        # 4. サブタイトル生成
        subtitle = design.get("subtitle")
        if subtitle and subtitle.get("text"):
            print(f"  [Step 4] サブタイトル生成: {subtitle['text'][:30]}...")
            result = _text_to_subtitle._tool_func(
                text=subtitle["text"],
                x=subtitle.get("x", 960),
                y=subtitle.get("y", 500),
                font_size=subtitle.get("fontSize", 36),
                color=subtitle.get("color", "#ffffff")
            )
            if result.get("success"):
                elements["subtitle"] = result["image_base64"]
                path = save_image(result["image_base64"], "subtitle", self.session_id)
                steps.append(f"サブタイトルを生成: {path}")
            else:
                print(f"  [Error] サブタイトル生成失敗: {result.get('error')}")
                steps.append(f"サブタイトル生成に失敗: {result.get('error')}")
        else:
            print("  [Step 4] サブタイトル: スキップ")

        # 5. 合成
        print("  [Step 5] 合成中...")
        result = _compose_slide._tool_func(
            background_base64=elements.get("background"),
            illustration_base64=elements.get("illustration"),
            illustration_x=0,  # 座標は描画済みなので(0,0)に配置
            illustration_y=0,
            title_base64=elements.get("title"),
            subtitle_base64=elements.get("subtitle")
        )

        if result.get("success"):
            path = save_image(result["image_base64"], "result", self.session_id)
            steps.append(f"合成完了: {path}")
            return {
                "success": True,
                "image_base64": result["image_base64"],
                "result_path": path,
                "steps": steps
            }
        else:
            print(f"  [Error] 合成失敗: {result.get('error')}")
            steps.append(f"合成に失敗: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "steps": steps
            }

    def generate(self, user_prompt: str, image_base64: str = None) -> dict:
        """
        ユーザーの指示から画像を生成

        Args:
            user_prompt: ユーザーの自然言語指示
            image_base64: 入力画像のBase64データ（オプション）
                          指定すると image-to-image モードで動作

        Returns:
            dict: 生成結果
        """
        try:
            # Phase 1: 設計
            print("\n[Phase 1] プロンプトを解析中...")
            design = self._parse_design(user_prompt)
            print(f"  設計JSON: {json.dumps(design, ensure_ascii=False, indent=2)}")

            # Phase 2: 実行
            print("\n[Phase 2] 設計を実行中...")
            result = self._execute_design(design, input_image=image_base64)

            return {
                "success": result.get("success", False),
                "session_id": self.session_id,
                "design": design,
                "steps": result.get("steps", []),
                "image_base64": result.get("image_base64"),
                "result_path": result.get("result_path"),
                "response": "\n".join(result.get("steps", []))
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "session_id": self.session_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }


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
