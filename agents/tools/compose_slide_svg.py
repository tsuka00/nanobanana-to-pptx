"""
Compose Slide SVG ツール
各SVG要素を合成して1枚のSVGを生成
"""

import re
from typing import Optional
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


def extract_svg_dimensions(svg: str) -> tuple[float, float]:
    """
    SVGからwidth/heightを抽出

    Returns:
        tuple: (width, height) デフォルトは (CANVAS_WIDTH, CANVAS_HEIGHT)
    """
    width_match = re.search(r'<svg[^>]*\swidth="(\d+(?:\.\d+)?)"', svg)
    height_match = re.search(r'<svg[^>]*\sheight="(\d+(?:\.\d+)?)"', svg)

    width = float(width_match.group(1)) if width_match else CANVAS_WIDTH
    height = float(height_match.group(1)) if height_match else CANVAS_HEIGHT

    return width, height


def extract_svg_content(svg: str) -> tuple[str, str]:
    """
    SVGから<defs>とコンテンツ部分を抽出

    Returns:
        tuple: (defs部分, コンテンツ部分)
    """
    # <defs>...</defs> を抽出
    defs_match = re.search(r'<defs>.*?</defs>', svg, re.DOTALL)
    defs = defs_match.group(0) if defs_match else ""

    # <svg>タグの中身を抽出（<defs>を除く）
    inner_match = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.DOTALL)
    if inner_match:
        content = inner_match.group(1)
        # <defs>を削除
        content = re.sub(r'<defs>.*?</defs>', '', content, flags=re.DOTALL)
        return defs, content.strip()

    return defs, ""


def make_unique_ids(svg: str, prefix: str) -> str:
    """
    SVG内のIDを一意にするためにプレフィックスを追加
    """
    # id="xxx" を id="prefix_xxx" に置換
    svg = re.sub(r'id="([^"]+)"', f'id="{prefix}_\\1"', svg)
    # url(#xxx) を url(#prefix_xxx) に置換
    svg = re.sub(r'url\(#([^)]+)\)', f'url(#{prefix}_\\1)', svg)
    return svg


@tool
def compose_slide_svg(
    background_svg: Optional[str] = None,
    illustration_svg: Optional[str] = None,
    title_svg: Optional[str] = None,
    subtitle_svg: Optional[str] = None
) -> dict:
    """
    各SVG要素を合成して1枚のSVGを生成します。
    合成順序: 背景 → イラスト → タイトル → サブタイトル

    Args:
        background_svg: 背景SVG文字列
        illustration_svg: イラストSVG文字列
        title_svg: タイトルSVG文字列
        subtitle_svg: サブタイトルSVG文字列

    Returns:
        dict: 合成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: 合成されたSVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        all_defs = []
        all_contents = []

        # 各レイヤーを順番に処理
        layers = [
            ("bg", background_svg, True),       # 背景はスケーリングが必要
            ("illust", illustration_svg, False),
            ("title", title_svg, False),
            ("subtitle", subtitle_svg, False)
        ]

        for prefix, svg, needs_scaling in layers:
            if svg:
                # IDを一意にする
                unique_svg = make_unique_ids(svg, prefix)

                # 元のSVGサイズを取得
                src_width, src_height = extract_svg_dimensions(unique_svg)

                defs, content = extract_svg_content(unique_svg)
                if defs:
                    all_defs.append(defs.replace("<defs>", "").replace("</defs>", ""))

                if content:
                    # スケーリングが必要な場合（背景など）
                    if needs_scaling and (src_width != CANVAS_WIDTH or src_height != CANVAS_HEIGHT):
                        scale_x = CANVAS_WIDTH / src_width
                        scale_y = CANVAS_HEIGHT / src_height
                        transform = f'transform="scale({scale_x:.6f}, {scale_y:.6f})"'
                        all_contents.append(f"  <!-- {prefix} layer (scaled from {src_width}x{src_height}) -->\n  <g {transform}>{content}</g>")
                    else:
                        all_contents.append(f"  <!-- {prefix} layer -->\n  <g>{content}</g>")

        # 合成SVGを組み立て
        defs_section = ""
        if all_defs:
            defs_section = f"  <defs>\n    {''.join(all_defs)}\n  </defs>\n"

        content_section = "\n".join(all_contents)

        composed_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">
{defs_section}{content_section}
</svg>'''

        return {
            "success": True,
            "svg": composed_svg
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
