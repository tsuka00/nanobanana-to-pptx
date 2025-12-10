"""
Text-to-Image ツール
Gemini 2.5 Flash Image によるテキストからの画像生成
"""

import base64
import io
import os
from typing import Optional
from strands import tool
from google import genai  # type: ignore
from google.genai import types
from PIL import Image

MODEL = "gemini-3-pro-image-preview"


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


@tool
def text_to_image(
    prompt: str,
    reference_image_base64: Optional[str] = None
) -> dict:
    """
    テキストプロンプトから新規画像を生成します（16:9固定）。
    参照画像がある場合は、その構造・レイアウト・スタイルを参考にします。

    Args:
        prompt: 画像生成のプロンプト。生成したい画像の内容を詳細に指示します。
        reference_image_base64: 参照画像のBase64データ（オプション）。
                                指定すると、この画像の構造やスタイルを参考に生成します。

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ
            - mime_type: 画像のMIMEタイプ
            - error: エラーメッセージ（失敗時）
    """
    try:
        client = get_client()

        if reference_image_base64:
            # 参照画像がある場合: 構造・スタイルを参考に生成
            full_prompt = f"""添付の画像を参考にして、新しいスライドデザインを生成してください。

参照画像から学ぶべきポイント:
- レイアウト構造（要素の配置、余白のバランス）
- 色使いとカラーパレット
- デザインのトーンと雰囲気
- 装飾的な要素のスタイル

生成する画像の指示:
{prompt}

重要なルール:
- アスペクト比は16:9（横長）で生成してください
- 参照画像の「構造」と「スタイル」を参考にしつつ、新しいデザインを作成してください
- 参照画像のテキストや具体的な要素をそのままコピーしないでください
- 画像内にテキストや文字を一切含めないでください
- 背景とデザイン要素のみで構成してください"""

            # 参照画像をPIL Imageに変換
            image_bytes = base64.b64decode(reference_image_base64)
            reference_image = Image.open(io.BytesIO(image_bytes))

            contents = [full_prompt, reference_image]
        else:
            # 参照画像がない場合: テキストのみで生成
            full_prompt = f"""{prompt}

アスペクト比は16:9（横長）で生成してください。
重要: 画像内にテキストや文字を一切含めないでください。"""

            contents = full_prompt

        # generate_content で画像生成
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
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
