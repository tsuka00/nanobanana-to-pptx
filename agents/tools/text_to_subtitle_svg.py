"""
Text-to-Subtitle-SVG ツール
サブタイトルテキストをSVGとして生成（スタイルプリセット対応）
"""

from typing import Optional, Union, Dict
from strands import tool
from .svg_text_styles import generate_styled_text_svg, get_available_styles

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# デフォルトフォントファミリー
DEFAULT_FONT_FAMILY = "Hiragino Sans"


@tool
def text_to_subtitle_svg(
    text: str,
    x: int = 960,
    y: int = 500,
    font_size: int = 36,
    font_family: Optional[str] = None,
    font_weight: str = "normal",
    color: Optional[str] = None,
    style: str = "flat",
    fill: Optional[Union[str, Dict]] = None,
    glow_color: Optional[str] = None,
) -> dict:
    """
    サブタイトルテキストをSVGとして生成します。
    スタイルプリセットでリッチな表現が可能です。

    Args:
        text: サブタイトルテキスト
        x: X座標（テキスト中心）
        y: Y座標（テキスト中心）
        font_size: フォントサイズ。デフォルト: 36
        font_family: フォントファミリー。デフォルト: Hiragino Sans
        font_weight: フォントの太さ（normal, bold, light）。デフォルト: normal
        color: 文字色（flat, outline, embossで使用）。デフォルト: #ffffff
        style: スタイルプリセット名。以下から選択:
            - flat: シンプルな単色
            - shadow: ドロップシャドウ
            - 3d-metallic: 3D風メタリック
            - neon-glow: ネオン発光
            - glass: ガラス風透明感
            - outline: アウトライン
            - gold: ゴールドメタリック
            - silver: シルバーメタリック
            - emboss: エンボス（浮き彫り）
            - gradient: カスタムグラデーション
        fill: グラデーション設定（style="gradient"時に使用）
            {
                "type": "gradient",
                "start": "#開始色",
                "end": "#終了色",
                "direction": "vertical | horizontal | diagonal"
            }
        glow_color: グロー色（style="neon-glow"時に使用）

    Returns:
        dict: 生成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: SVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        font = font_family or DEFAULT_FONT_FAMILY
        text_color = color or "#ffffff"

        # fillからカスタムグラデーション設定を取得
        custom_gradient = None
        if fill and isinstance(fill, dict) and fill.get("type") == "gradient":
            custom_gradient = fill

        # スタイル付きSVGを生成
        svg = generate_styled_text_svg(
            text=text,
            x=x,
            y=y,
            font_size=font_size,
            font_family=font,
            font_weight=font_weight,
            style=style,
            color=text_color,
            custom_gradient=custom_gradient,
            custom_glow_color=glow_color,
        )

        return {
            "success": True,
            "svg": svg
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
