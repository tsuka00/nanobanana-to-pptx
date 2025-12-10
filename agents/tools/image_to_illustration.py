"""
Image-to-Illustration ツール
Gemini 2.5 Flash Image による既存画像からイラスト/シェイプへの変換（透過PNG対応）
"""

import base64
import io
import os
from strands import tool
from google import genai
from rembg import remove, new_session

# CPUモードで初期化（GPU検出エラー回避）
REMBG_SESSION = new_session("u2net", providers=["CPUExecutionProvider"])
from PIL import Image

MODEL = "gemini-3-pro-image-preview"


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
def image_to_illustration(prompt: str, image_base64: str) -> dict:
    """
    既存の画像を参考にしてイラスト/シェイプを生成します（透過PNG）。

    Args:
        prompt: イラスト編集のプロンプト。編集内容を詳細に指示します。
        image_base64: 参考画像のBase64エンコードされたデータ

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ（透過PNG）
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        full_prompt = f"""添付の画像を参考にして、新しいイラスト/シェイプ画像を生成してください。

参考画像のスタイル、色使い、デザインを参考にしつつ、以下の指示に従って新しい画像を作成してください:
{prompt}

重要: 画像内にテキストや文字を一切含めないでください。図形やイラストのみを生成してください。
背景はシンプルな単色（白または薄いグレー）にしてください。
参考画像をそのまま使わず、新しい画像を生成してください。"""

        # 参考画像をPIL Imageに変換
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        response = client.models.generate_content(
            model=MODEL,
            contents=[full_prompt, image],
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
