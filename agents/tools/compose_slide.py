"""
Compose Slide ツール
各要素を合成してスライド画像を生成
"""

import base64
import io
from typing import Optional
from PIL import Image
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


def base64_to_image(image_base64: str) -> Image.Image:
    """Base64 文字列を PIL Image に変換"""
    image_data = base64.b64decode(image_base64)
    return Image.open(io.BytesIO(image_data)).convert("RGBA")


def image_to_base64(image: Image.Image) -> str:
    """PIL Image を Base64 文字列に変換"""
    buffer = io.BytesIO()
    # 最終出力はRGBで保存（透過なし）
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@tool
def compose_slide(
    background_base64: Optional[str] = None,
    illustration_base64: Optional[str] = None,
    illustration_x: int = 0,
    illustration_y: int = 0,
    title_base64: Optional[str] = None,
    subtitle_base64: Optional[str] = None
) -> dict:
    """
    各要素を合成してスライド画像を生成します。
    合成順序: 白紙キャンバス → 背景 → イラスト → タイトル → サブタイトル

    Args:
        background_base64: 背景画像のBase64データ
        illustration_base64: イラスト画像のBase64データ
        illustration_x: イラストのX座標（左上）
        illustration_y: イラストのY座標（左上）
        title_base64: タイトル画像のBase64データ（透過PNG）
        subtitle_base64: サブタイトル画像のBase64データ（透過PNG）

    Returns:
        dict: 合成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 合成された画像のBase64データ
            - error: エラーメッセージ（失敗時）
    """
    try:
        # 白紙キャンバスを作成（RGBA）
        canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 255))

        # 1. 背景を配置
        if background_base64:
            bg_image = base64_to_image(background_base64)
            # リサイズしてキャンバスにフィット
            bg_image = bg_image.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
            canvas.paste(bg_image, (0, 0))

        # 2. イラストを配置
        if illustration_base64:
            illust_image = base64_to_image(illustration_base64)
            # 透過がある場合はアルファ合成
            if illust_image.mode == "RGBA":
                canvas.paste(illust_image, (illustration_x, illustration_y), illust_image)
            else:
                canvas.paste(illust_image, (illustration_x, illustration_y))

        # 3. タイトルを配置（透過PNG）
        if title_base64:
            title_image = base64_to_image(title_base64)
            canvas.paste(title_image, (0, 0), title_image)

        # 4. サブタイトルを配置（透過PNG）
        if subtitle_base64:
            subtitle_image = base64_to_image(subtitle_base64)
            canvas.paste(subtitle_image, (0, 0), subtitle_image)

        return {
            "success": True,
            "image_base64": image_to_base64(canvas),
            "mime_type": "image/png"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
