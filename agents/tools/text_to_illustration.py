"""
Text-to-Illustration ツール
Gemini 2.5 Flash Image によるイラスト/シェイプ生成
"""

import base64
import os
from strands import tool
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash-image"


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


@tool
def text_to_illustration(prompt: str) -> dict:
    """
    イラストやシェイプを生成します。

    Args:
        prompt: イラストのプロンプト。形状、色、スタイルを指示します。

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        full_prompt = f"""{prompt}

アスペクト比は16:9（1920x1080）の横長で生成してください。
重要: 画像内にテキストや文字を一切含めないでください。図形やイラストのみを生成してください。"""

        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                return {
                    "success": True,
                    "image_base64": base64.b64encode(image_data).decode("utf-8"),
                    "mime_type": part.inline_data.mime_type or "image/png",
                }

        return {"success": False, "error": "No image was generated in response"}

    except Exception as e:
        return {"success": False, "error": str(e)}
