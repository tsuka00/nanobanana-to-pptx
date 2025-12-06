"""
Designer Agent
自然言語の指示から画像デザインを生成するエージェント
"""

import os
import json
import base64
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .tools.nanobanana import nanobanana as _nanobanana
from .tools.jp_fonts import jp_fonts as _jp_fonts, jp_fonts_multi as _jp_fonts_multi

# .env.local を読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

# 設計フェーズ用のモデル
DESIGN_MODEL = "gemini-2.0-flash"

DESIGN_SYSTEM_PROMPT = """あなたは画像デザインの設計者です。
ユーザーの指示を解析し、以下のJSON形式で設計を出力してください。
JSONのみを出力し、他のテキストは含めないでください。

{
  "background": {
    "action": "generate" または "keep",
    "prompt": "背景生成プロンプト（actionがgenerateの場合のみ）"
  },
  "texts": [
    {
      "text": "表示するテキスト",
      "position": "配置位置",
      "fontSize": フォントサイズ（数値）,
      "color": "文字色"
    }
  ]
}

重要なルール:
- ユーザーが明示的に指示していないことはJSONに含めない
- テキスト追加の指示がなければ texts は空配列 []
- 背景変更の指示がなければ background.action は "keep"
- background.action が "keep" の場合、prompt は不要

position の選択肢:
- center-top: メインタイトル向け
- center-bottom: サブタイトル向け
- center: 中央
- top, bottom: 上部/下部
- top-left, top-right, bottom-left, bottom-right: 四隅

fontSize の目安:
- メインタイトル: 64
- サブタイトル: 36
- キャプション: 24

color:
- 暗い背景には "#ffffff"（白）
- 明るい背景には "#000000"（黒）
"""


class DesignerAgent:
    """画像デザインを生成するエージェント"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self.client = genai.Client(api_key=self.api_key)

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

    def _execute_design(self, design: dict, image_base64: str) -> dict:
        """設計JSONに基づいてツールを実行"""
        current_image = image_base64
        steps = []

        # Phase 1: 背景生成
        bg = design.get("background", {})
        if bg.get("action") == "generate" and bg.get("prompt"):
            print(f"  [Step 1] 背景生成: {bg['prompt'][:50]}...")
            result = _nanobanana._tool_func(
                prompt=bg["prompt"],
                image_base64=current_image,
                mime_type="image/png"
            )
            if result.get("success"):
                current_image = result["image_base64"]
                steps.append("背景を生成しました")
            else:
                error = result.get("error", "不明なエラー")
                print(f"  [Error] 背景生成失敗: {error}")
                steps.append(f"背景生成に失敗: {error}")
        else:
            print("  [Step 1] 背景: 変更なし")
            steps.append("背景は変更なし")

        # Phase 2: テキスト追加
        texts = design.get("texts", [])
        if texts:
            print(f"  [Step 2] テキスト追加: {len(texts)}個")
            result = _jp_fonts_multi._tool_func(
                image_base64=current_image,
                texts=texts
            )
            if result.get("success"):
                current_image = result["image_base64"]
                steps.append(f"{len(texts)}個のテキストを追加しました")
            else:
                error = result.get("error", "不明なエラー")
                print(f"  [Error] テキスト追加失敗: {error}")
                steps.append(f"テキスト追加に失敗: {error}")
        else:
            print("  [Step 2] テキスト: 追加なし")

        return {
            "success": True,
            "image_base64": current_image,
            "steps": steps
        }

    def generate(self, user_prompt: str, image_base64: str = None, mime_type: str = "image/png") -> dict:
        """
        ユーザーの指示から画像を生成

        Args:
            user_prompt: ユーザーの自然言語指示
            image_base64: 元画像のBase64データ
            mime_type: 画像のMIMEタイプ

        Returns:
            dict: 生成結果
        """
        try:
            if not image_base64:
                return {"success": False, "error": "画像が指定されていません"}

            # Phase 1: 設計
            print("\n[Phase 1] プロンプトを解析中...")
            design = self._parse_design(user_prompt)
            print(f"  設計JSON: {json.dumps(design, ensure_ascii=False, indent=2)}")

            # Phase 2: 実行
            print("\n[Phase 2] 設計を実行中...")
            result = self._execute_design(design, image_base64)

            return {
                "success": True,
                "design": design,
                "steps": result.get("steps", []),
                "image_base64": result.get("image_base64"),
                "response": "\n".join(result.get("steps", []))
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
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
    result = agent.generate(
        user_prompt=params.get("userPrompt", ""),
        image_base64=params.get("imageBase64"),
        mime_type=params.get("mimeType", "image/png")
    )

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
