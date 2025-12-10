"""
Strands Agent ツール
"""

# Text-to-* ツール（新規生成）
from .text_to_background import text_to_background
from .text_to_title import text_to_title
from .text_to_subtitle import text_to_subtitle

# Image-to-* ツール（既存画像編集）
from .image_to_background import image_to_background

# イラスト描画ツール（Pillow）
from .draw_illustration import draw_illustration

# 合成ツール
from .compose_slide import compose_slide

# SVGツール
from .image_to_svg import image_to_svg
from .text_to_title_svg import text_to_title_svg
from .text_to_subtitle_svg import text_to_subtitle_svg
from .draw_illustration_svg import draw_illustration_svg
from .compose_slide_svg import compose_slide_svg

# PPTXツール
from .svg_to_pptx import svg_to_pptx, svg_to_pptx_editable

# 既存ツール（互換性のため残す）
from .text_to_image import text_to_image
from .image_to_image import image_to_image
from .text_to_illustration import text_to_illustration
from .image_to_illustration import image_to_illustration
from .jp_fonts import jp_fonts, jp_fonts_multi

__all__ = [
    # Text-to-* ツール
    "text_to_background",
    "text_to_title",
    "text_to_subtitle",
    # Image-to-* ツール
    "image_to_background",
    # イラスト描画ツール
    "draw_illustration",
    # 合成ツール
    "compose_slide",
    # SVGツール
    "image_to_svg",
    "text_to_title_svg",
    "text_to_subtitle_svg",
    "draw_illustration_svg",
    "compose_slide_svg",
    # PPTXツール
    "svg_to_pptx",
    "svg_to_pptx_editable",
    # 既存ツール
    "text_to_image",
    "image_to_image",
    "text_to_illustration",
    "image_to_illustration",
    "jp_fonts",
    "jp_fonts_multi",
]
