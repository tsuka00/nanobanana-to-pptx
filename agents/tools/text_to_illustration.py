"""
Text-to-Illustration ツール
Gemini 2.5 Flash Image によるイラスト/シェイプ生成（透過PNG対応）
"""

import base64
import io
import os
from strands import tool
from google import genai
from google.genai import types
from rembg import remove, new_session

# CPUモードで初期化（GPU検出エラー回避）
REMBG_SESSION = new_session("u2net", providers=["CPUExecutionProvider"])
from PIL import Image

MODEL = "gemini-2.5-flash-image"


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


def remove_background(image_data: bytes) -> bytes:
    """rembgで背景を除去して透過PNGに変換"""
    input_image = Image.open(io.BytesIO(image_data))
    output_image = remove(input_image, session=REMBG_SESSION)

    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    return buffer.getvalue()


@tool
def text_to_illustration(prompt: str) -> dict:
    """
    イラストやシェイプを生成します（透過PNG）。

    Args:
        prompt: イラストのプロンプト。形状、色、スタイルを指示します。

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ（透過PNG）
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        full_prompt = f"""{prompt}

重要: 画像内にテキストや文字を一切含めないでください。図形やイラストのみを生成してください。
背景はシンプルな単色（白または薄いグレー）にしてください。"""

        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                # 背景除去して透過PNGに変換
                image_data = remove_background(part.inline_data.data)
                return {
                    "success": True,
                    "image_base64": base64.b64encode(image_data).decode("utf-8"),
                    "mime_type": "image/png",
                }

        return {"success": False, "error": "No image was generated in response"}

    except Exception as e:
        return {"success": False, "error": str(e)}
