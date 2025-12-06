"""
Text-to-Subtitle-SVG ツール
サブタイトルテキストをSVGとして生成
"""

from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# フォントファミリー（SVG用）
FONT_FAMILY = "Noto Sans CJK JP, Noto Sans JP, sans-serif"


def escape_xml(text: str) -> str:
    """XML特殊文字をエスケープ"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


@tool
def text_to_subtitle_svg(
    text: str,
    x: int = 960,
    y: int = 500,
    font_size: int = 36,
    color: str = "#ffffff",
    font_family: str = None
) -> dict:
    """
    サブタイトルテキストをSVGとして生成します。

    Args:
        text: サブタイトルテキスト
        x: X座標（テキスト中心）
        y: Y座標（テキスト中心）
        font_size: フォントサイズ。デフォルト: 36
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
