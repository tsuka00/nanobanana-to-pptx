"""
Image-to-SVG ツール
画像をSVG内にラスター埋め込み
"""

import base64
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


@tool
def image_to_svg(
    image_base64: str,
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT
) -> dict:
    """
    ラスター画像（Base64）をSVG内に埋め込みます。
    画像はそのまま埋め込まれるため、品質の劣化はありません。

    Args:
        image_base64: 画像のBase64データ
        width: SVGの幅（デフォルト: 1920）
        height: SVGの高さ（デフォルト: 1080）

    Returns:
        dict: 生成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: SVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <image href="data:image/png;base64,{image_base64}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice"/>
</svg>'''

        return {
            "success": True,
            "svg": svg
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
