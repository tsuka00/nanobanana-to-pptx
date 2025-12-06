"""
@jp_fonts ツール
Pillow を使用した日本語テキスト描画（完全 Python 実装）
"""

import base64
import io
import os
from PIL import Image, ImageDraw, ImageFont
from strands import tool

# フォントディレクトリ
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")

FONTS = {
    "noto-sans-jp": {
        "name": "Noto Sans CJK JP",
        "file": os.path.join(FONTS_DIR, "NotoSansCJKjp-Regular.otf"),
    }
}

DEFAULT_FONT = "noto-sans-jp"


def get_font(font_key: str = DEFAULT_FONT, size: int = 48) -> ImageFont.FreeTypeFont:
    """フォントオブジェクトを取得"""
    font_info = FONTS.get(font_key)
    if not font_info:
        raise ValueError(f"Font not found: {font_key}")
    return ImageFont.truetype(font_info["file"], size)


def calculate_text_position(
    image_size: tuple,
    text_size: tuple,
    position: str,
    padding: int = 20
) -> tuple:
    """テキストの配置位置を計算"""
    img_width, img_height = image_size
    text_width, text_height = text_size

    center_x = (img_width - text_width) // 2
    center_y = (img_height - text_height) // 2

    positions = {
        "top": (center_x, padding),
        "top-left": (padding, padding),
        "top-right": (img_width - text_width - padding, padding),
        "center": (center_x, center_y),
        "center-top": (center_x, center_y - text_height - padding),
        "center-bottom": (center_x, center_y + text_height + padding),
        "bottom": (center_x, img_height - text_height - padding),
        "bottom-left": (padding, img_height - text_height - padding),
        "bottom-right": (img_width - text_width - padding, img_height - text_height - padding),
    }

    x, y = positions.get(position, positions["bottom"])
    return max(0, x), max(0, y)


def image_to_base64(image: Image.Image) -> str:
    """PIL Image を Base64 文字列に変換"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def base64_to_image(image_base64: str) -> Image.Image:
    """Base64 文字列を PIL Image に変換"""
    image_data = base64.b64decode(image_base64)
    return Image.open(io.BytesIO(image_data)).convert("RGBA")


@tool
def jp_fonts(
    image_base64: str,
    text: str,
    font_size: int = 48,
    color: str = "#ffffff",
    position: str = "bottom",
    padding: int = 20
) -> dict:
    """
    画像に日本語テキストをオーバーレイします。

    Args:
        image_base64: 元画像のBase64エンコードされたデータ
        text: 描画するテキスト
        font_size: フォントサイズ（ピクセル）。デフォルト: 48
        color: 文字色（例: "#ffffff"）。デフォルト: 白
        position: テキストの配置位置。以下から選択:
            - "top": 上部中央
            - "top-left": 左上
            - "top-right": 右上
            - "center": 中央
            - "center-top": 中央やや上
            - "center-bottom": 中央やや下
            - "bottom": 下部中央
            - "bottom-left": 左下
            - "bottom-right": 右下
        padding: 端からの余白（ピクセル）。デフォルト: 20

    Returns:
        dict: 結果を含む辞書
            - success: 成功したかどうか
            - image_base64: テキストがオーバーレイされた画像のBase64データ
            - error: エラーメッセージ（失敗時）
    """
    try:
        # 画像を読み込み
        image = base64_to_image(image_base64)

        # フォントを取得
        font = get_font(DEFAULT_FONT, font_size)

        # 描画用オブジェクトを作成
        draw = ImageDraw.Draw(image)

        # テキストサイズを計算
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 配置位置を計算
        x, y = calculate_text_position(
            image.size, (text_width, text_height), position, padding
        )

        # テキストを描画
        draw.text((x, y), text, font=font, fill=color)

        # 結果を返す
        return {
            "success": True,
            "image_base64": image_to_base64(image)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def jp_fonts_multi(
    image_base64: str,
    texts: list
) -> dict:
    """
    画像に複数の日本語テキストをオーバーレイします。

    Args:
        image_base64: 元画像のBase64エンコードされたデータ
        texts: テキスト設定のリスト。各要素は以下のキーを持つ辞書:
            - text: 描画するテキスト
            - fontSize: フォントサイズ（ピクセル）
            - color: 文字色（例: "#ffffff"）
            - position: 配置位置
            - padding: 余白（オプション）

    Returns:
        dict: 結果を含む辞書
            - success: 成功したかどうか
            - image_base64: テキストがオーバーレイされた画像のBase64データ
            - error: エラーメッセージ（失敗時）
    """
    try:
        # 画像を読み込み
        image = base64_to_image(image_base64)
        draw = ImageDraw.Draw(image)

        for text_config in texts:
            text = text_config.get("text", "")
            font_size = text_config.get("fontSize", 48)
            color = text_config.get("color", "#ffffff")
            position = text_config.get("position", "bottom")
            padding = text_config.get("padding", 20)

            # フォントを取得
            font = get_font(DEFAULT_FONT, font_size)

            # テキストサイズを計算
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 配置位置を計算
            x, y = calculate_text_position(
                image.size, (text_width, text_height), position, padding
            )

            # テキストを描画
            draw.text((x, y), text, font=font, fill=color)

        # 結果を返す
        return {
            "success": True,
            "image_base64": image_to_base64(image)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
