"""
Image-to-SVG ツール
vtracer によるラスター画像のベクター変換
"""

import base64
import io
import vtracer
from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


def trace_image_to_svg(
    image_bytes: bytes,
    colormode: str = "color",
    hierarchical: str = "stacked",
    mode: str = "polygon",
    filter_speckle: int = 4,
    color_precision: int = 6,
    layer_difference: int = 16,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
    max_iterations: int = 10,
    splice_threshold: int = 45,
    path_precision: int = 3
) -> str:
    """
    vtracer を使って画像をSVGにトレース変換

    Args:
        image_bytes: 画像のバイナリデータ
        colormode: "color" または "binary"
        hierarchical: "stacked"（重ね）または "cutout"（切り抜き）
        mode: "polygon" または "spline"
        filter_speckle: ノイズ除去（小さいピクセル群を無視）
        color_precision: 色の精度（1-8、大きいほど色数が多い）
        layer_difference: レイヤー分割の閾値
        corner_threshold: 角の検出閾値
        length_threshold: パスの長さ閾値
        max_iterations: 最大反復回数
        splice_threshold: スプライス閾値
        path_precision: パス座標の精度

    Returns:
        str: SVG文字列
    """
    svg = vtracer.convert_raw_image_to_svg(
        image_bytes,
        img_format="png",
        colormode=colormode,
        hierarchical=hierarchical,
        mode=mode,
        filter_speckle=filter_speckle,
        color_precision=color_precision,
        layer_difference=layer_difference,
        corner_threshold=corner_threshold,
        length_threshold=length_threshold,
        max_iterations=max_iterations,
        splice_threshold=splice_threshold,
        path_precision=path_precision
    )
    return svg


@tool
def image_to_svg(
    image_base64: str,
    colormode: str = "color",
    quality: str = "balanced"
) -> dict:
    """
    ラスター画像（Base64）をSVGにトレース変換します。
    vtracer を使用してベクターパスに変換するため、編集可能なSVGが生成されます。

    Args:
        image_base64: 画像のBase64データ
        colormode: "color"（フルカラー）または "binary"（2値）
        quality: 変換品質
            - "fast": 高速、低精度（プレビュー用）
            - "balanced": バランス（デフォルト）
            - "high": 高精度、低速（最終出力用）

    Returns:
        dict: 生成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: SVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        # Base64をバイナリにデコード
        image_bytes = base64.b64decode(image_base64)

        # 品質設定
        quality_settings = {
            "fast": {
                "filter_speckle": 8,
                "color_precision": 4,
                "layer_difference": 32,
                "path_precision": 2
            },
            "balanced": {
                "filter_speckle": 4,
                "color_precision": 6,
                "layer_difference": 16,
                "path_precision": 3
            },
            "high": {
                "filter_speckle": 2,
                "color_precision": 8,
                "layer_difference": 8,
                "path_precision": 4
            }
        }

        settings = quality_settings.get(quality, quality_settings["balanced"])

        # トレース変換
        svg = trace_image_to_svg(
            image_bytes,
            colormode=colormode,
            **settings
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
