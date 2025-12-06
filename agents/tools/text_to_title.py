"""
Text-to-Title ツール
Pillow によるタイトル画像生成（透過PNG）
"""

import base64
import io
import os
from PIL import Image, ImageDraw, ImageFont
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# フォントディレクトリ
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
FONT_PATH = os.path.join(FONTS_DIR, "NotoSansCJKjp-Regular.otf")


def get_font(size: int = 64) -> ImageFont.FreeTypeFont:
    """フォントオブジェクトを取得"""
    return ImageFont.truetype(FONT_PATH, size)


def image_to_base64(image: Image.Image) -> str:
    """PIL Image を Base64 文字列に変換"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@tool
def text_to_title(
    text: str,
    x: int = 960,
    y: int = 400,
    font_size: int = 64,
    color: str = "#ffffff"
) -> dict:
    """
    タイトルテキスト画像を生成します（透過PNG、1920x1080）。

    Args:
        text: タイトルテキスト
        x: X座標（テキスト中心）
        y: Y座標（テキスト中心）
        font_size: フォントサイズ。デフォルト: 64
        color: 文字色。デフォルト: "#ffffff"

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ（透過PNG）
            - error: エラーメッセージ（失敗時）
    """
    try:
        # 透過キャンバスを作成
        image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # フォントを取得
        font = get_font(font_size)

        # テキストサイズを計算
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 中心座標から左上座標を計算
        draw_x = x - text_width // 2
        draw_y = y - text_height // 2

        # テキストを描画
        draw.text((draw_x, draw_y), text, font=font, fill=color)

        return {
            "success": True,
            "image_base64": image_to_base64(image),
            "mime_type": "image/png"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
