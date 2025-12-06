"""
Image-to-Image ツール
Gemini 2.5 Flash Image による既存画像の編集
"""

import base64
import io
import os
from strands import tool
from google import genai
from PIL import Image

MODEL = "gemini-2.5-flash-image"


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


@tool
def image_to_image(prompt: str, image_base64: str, mime_type: str = "image/png") -> dict:
    """
    既存の画像を編集します（テキストは含めません）。

    Args:
        prompt: 画像編集のプロンプト。編集内容を詳細に指示します。
        image_base64: 元画像のBase64エンコードされたデータ
        mime_type: 画像のMIMEタイプ（デフォルト: image/png）

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        # 背景生成プロンプト（テキスト生成を明示的に禁止）
        full_prompt = f"""この画像を編集してください: {prompt}

重要: 画像内にテキストや文字を一切含めないでください。背景のみを生成してください。"""

        # 元画像をPIL Imageに変換
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        # generate_content で画像編集
        response = client.models.generate_content(
            model=MODEL,
            contents=[full_prompt, image],
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
