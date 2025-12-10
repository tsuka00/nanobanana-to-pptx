"""
画像分析ツール
Gemini 3 Proで画像を分析し、要素を識別してテキストはSVGを生成
"""

import os
import json
import re
from typing import Optional
from google import genai
from PIL import Image
from io import BytesIO
import base64

MODEL = "gemini-3-pro-preview"

PROMPT_TEMPLATE = """この画像を分析し、編集可能なPowerPointスライドを作成するために、全ての要素を識別してください。

## タスク
1. 画像内の全ての要素を識別する
2. 各要素のbbox（位置・サイズ）を取得する
3. テキスト要素は内容とスタイル情報を抽出する（SVGは生成しない）

## 出力形式（JSON）
```json
{{
  "elements": [
    {{
      "id": "background",
      "type": "background",
      "label": "背景の説明",
      "bbox": {{"x": 0, "y": 0, "width": {width}, "height": {height}}}
    }},
    {{
      "id": "text_1",
      "type": "text",
      "label": "テキストの説明",
      "content": "テキスト内容",
      "bbox": {{"x": 0, "y": 0, "width": 100, "height": 50}},
      "style": {{
        "fontSize": 48,
        "fontWeight": "bold",
        "fontStyle": "italic",
        "color": "#FFFFFF",
        "align": "center"
      }}
    }},
    {{
      "id": "illustration_1",
      "type": "illustration",
      "label": "イラストの説明",
      "bbox": {{"x": 0, "y": 0, "width": 100, "height": 100}}
    }}
  ]
}}
```

## ルール
- 全ての要素（背景、イラスト、テキスト）についてbbox情報を出力
- bboxは元画像のピクセル座標で指定（この画像は{width}x{height}）
- type="text" の要素には必ず content と style を含める
- style には fontSize, fontWeight, fontStyle, color, align を含める
- fontWeight: "normal" または "bold"
- fontStyle: "normal" または "italic"
- align: "left", "center", "right" のいずれか
- colorは最も目立つ色をHEXで指定
- SVGは生成しない（画像から切り出すため）

JSONのみを出力してください。"""


def analyze_image(
    image_base64: str,
    api_key: Optional[str] = None
) -> dict:
    """
    画像を分析して要素リストを返す

    Args:
        image_base64: 画像のBase64データ
        api_key: Google API Key（省略時は環境変数から取得）

    Returns:
        dict: {
            "success": bool,
            "elements": list,  # 要素リスト
            "error": str  # エラー時のみ
        }
    """
    try:
        # API Key
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            return {"success": False, "error": "GOOGLE_API_KEY is required"}

        client = genai.Client(api_key=key)

        # Base64からPIL Imageに変換
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        width, height = image.size

        # プロンプト生成
        prompt = PROMPT_TEMPLATE.format(width=width, height=height)

        # Gemini呼び出し
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt, image]
        )

        # レスポンスからテキストを取得
        text = ""
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text += part.text

        if not text:
            return {"success": False, "error": "No response from API"}

        # JSONを抽出
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            result = json.loads(json_match.group(1))
        else:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return {"success": False, "error": f"Failed to parse JSON: {text[:500]}"}

        return {
            "success": True,
            "elements": result.get("elements", []),
            "image_size": {"width": width, "height": height}
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ツール関数のラッパー
class _tool_func:
    @staticmethod
    def __call__(**kwargs):
        return analyze_image(**kwargs)

_tool_func = _tool_func()
