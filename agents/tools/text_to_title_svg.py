"""
Text-to-Title-SVG ツール
タイトルテキストをSVGとして生成
"""

import os
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# フォントファミリー（SVG用）
# Illustrator互換性のため、シンプルなフォント名を使用
FONT_FAMILY = "Hiragino Sans"


def escape_xml(text: str) -> str:
    """XML特殊文字をエスケープ"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


@tool
def text_to_title_svg(
    text: str,
    x: int = 960,
    y: int = 400,
    font_size: int = 64,
    color: str = "#ffffff",
    font_family: str = None
) -> dict:
    """
    タイトルテキストをSVGとして生成します。

    Args:
        text: タイトルテキスト
        x: X座標（テキスト中心）
        y: Y座標（テキスト中心）
        font_size: フォントサイズ。デフォルト: 64
        color: 文字色。デフォルト: "#ffffff"
        font_family: フォントファミリー。デフォルト: Noto Sans CJK JP

    Returns:
        dict: 生成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: SVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        font = font_family or FONT_FAMILY
        escaped_text = escape_xml(text)

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">
  <text x="{x}" y="{y}"
        font-family="{font}"
        font-size="{font_size}"
        font-weight="bold"
        fill="{color}"
        text-anchor="middle"
        dominant-baseline="middle">{escaped_text}</text>
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
