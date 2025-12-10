"""
Text-to-Image ツール
Gemini 3 Pro Image (Nano Banana Pro) による高品質画像生成
"""

import base64
import io
import os
from typing import Optional, List
from google import genai  # type: ignore
from google.genai import types
from PIL import Image

MODEL = "gemini-3-pro-image-preview"

# 対応アスペクト比
ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]

# 対応解像度
IMAGE_SIZES = ["1K", "2K", "4K"]


def get_client():
    """Google GenAI クライアントを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


def generate_image(
    prompt: str,
    reference_images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    image_size: str = "2K",
    style_description: Optional[str] = None,
    no_text: bool = True
) -> dict:
    """
    高品質な画像を生成します。

    Args:
        prompt: 画像生成のプロンプト。場面を叙述的に描写してください。
        reference_images: 参照画像のBase64リスト（最大14枚）。スタイル参考用。
        aspect_ratio: アスペクト比 ("16:9", "1:1", "9:16", "4:3", "3:4")
        image_size: 解像度 ("1K", "2K", "4K")
        style_description: スタイルの詳細説明（照明、色調、雰囲気など）
        no_text: テキストを含めない場合True

    Returns:
        dict: {
            "success": bool,
            "image_base64": str,
            "mime_type": str,
            "error": str (失敗時)
        }
    """
    try:
        client = get_client()
        contents: List = []

        # 叙述的なプロンプトを構築
        full_prompt = _build_descriptive_prompt(
            prompt=prompt,
            style_description=style_description,
            aspect_ratio=aspect_ratio,
            no_text=no_text
        )
        contents.append(full_prompt)

        # 参照画像を追加（最大14枚）
        if reference_images:
            for i, img_base64 in enumerate(reference_images[:14]):
                try:
                    image_bytes = base64.b64decode(img_base64)
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    contents.append(pil_image)
                except Exception:
                    continue

        # 画像生成設定
        config = types.GenerateContentConfig(
            response_modalities=["image", "text"],
        )

        # generate_content で画像生成
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
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


def _build_descriptive_prompt(
    prompt: str,
    style_description: Optional[str] = None,
    aspect_ratio: str = "16:9",
    no_text: bool = True
) -> str:
    """叙述的なプロンプトを構築"""

    parts = []

    # メインの場面描写
    parts.append(f"Create a high-quality, professional image:\n\n{prompt}")

    # スタイル詳細
    if style_description:
        parts.append(f"\nVisual Style:\n{style_description}")

    # 品質指示
    parts.append("""
Quality Requirements:
- High-quality, professional finish
- Sharp details and clean edges
- Balanced composition with proper visual hierarchy
- Studio-quality lighting and color grading""")

    # アスペクト比
    aspect_map = {
        "16:9": "wide landscape format (16:9 aspect ratio), suitable for presentations",
        "1:1": "square format (1:1 aspect ratio), suitable for social media",
        "9:16": "vertical portrait format (9:16 aspect ratio), suitable for mobile",
        "4:3": "standard format (4:3 aspect ratio)",
        "3:4": "vertical standard format (3:4 aspect ratio)",
    }
    aspect_desc = aspect_map.get(aspect_ratio, aspect_map["16:9"])
    parts.append(f"\nFormat: {aspect_desc}")

    # テキストなし指示（肯定的に記述）
    if no_text:
        parts.append("""
Content: Focus purely on visual elements - backgrounds, shapes, gradients, illustrations, and decorative elements.
The image should be a clean canvas ready for text overlay in post-production.""")

    return "\n".join(parts)


# 後方互換性のためのラッパー
def text_to_image(
    prompt: str,
    reference_image_base64: Optional[str] = None
) -> dict:
    """後方互換性のためのラッパー関数"""
    reference_images = [reference_image_base64] if reference_image_base64 else None
    return generate_image(
        prompt=prompt,
        reference_images=reference_images,
        aspect_ratio="16:9",
        image_size="2K",
        no_text=True
    )


# Strands tool用のデコレーター付きバージョン
try:
    from strands import tool

    @tool
    def text_to_image_tool(
        prompt: str,
        reference_image_base64: Optional[str] = None
    ) -> dict:
        """テキストから画像を生成するツール"""
        return text_to_image(prompt, reference_image_base64)
except ImportError:
    pass
