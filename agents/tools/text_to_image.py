"""
Text-to-Image ツール
Gemini 2.5 Flash Image によるテキストからの画像生成
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
def text_to_image(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """
    テキストプロンプトから新規画像を生成します。

    Args:
        prompt: 画像生成のプロンプト。生成したい画像の内容を詳細に指示します。
        aspect_ratio: アスペクト比（デフォルト: 16:9）。例: "1:1", "4:3", "16:9", "9:16"

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        # テキスト生成を禁止するプロンプト
        full_prompt = f"""{prompt}

重要: 画像内にテキストや文字を一切含めないでください。"""

        # generate_content でテキストから画像生成
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )

        # レスポンスから画像を抽出
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
