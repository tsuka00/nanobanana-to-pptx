"""
Draw Illustration ツール
Pillow による幾何学シェイプ描画（透過PNG対応）
"""

import base64
import io
from PIL import Image, ImageDraw
from strands import tool


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    """HEXカラーをRGBAタプルに変換"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def interpolate_color(color1: tuple, color2: tuple, t: float) -> tuple:
    """2色間を補間"""
    return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))


def create_gradient_image(width: int, height: int, start_color: str, end_color: str, direction: str = "vertical") -> Image.Image:
    """グラデーション画像を生成"""
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    c1 = hex_to_rgba(start_color)
    c2 = hex_to_rgba(end_color)

    if direction == "vertical":
        for y in range(height):
            t = y / height
            color = interpolate_color(c1, c2, t)
            draw.line([(0, y), (width, y)], fill=color)
    elif direction == "horizontal":
        for x in range(width):
            t = x / width
            color = interpolate_color(c1, c2, t)
            draw.line([(x, 0), (x, height)], fill=color)
    elif direction == "diagonal":
        # 対角線グラデーション
        for y in range(height):
            for x in range(width):
                t = (x + y) / (width + height)
                color = interpolate_color(c1, c2, t)
                draw.point((x, y), fill=color)

    return gradient


def image_to_base64(image: Image.Image) -> str:
    """PIL Image を Base64 文字列に変換"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@tool
def draw_illustration(shape: dict) -> dict:
    """
    JSONパラメータからイラスト/シェイプを描画します（透過PNG）。

    Args:
        shape: シェイプの定義
            - type: "polygon", "rectangle", "ellipse", "triangle"
            - points: [[x1, y1], [x2, y2], ...] (polygonの場合)
            - x, y, width, height: (rectangle/ellipseの場合)
            - fill: {
                "type": "solid" または "gradient",
                "color": "#RRGGBB" (solidの場合),
                "start": "#RRGGBB", "end": "#RRGGBB", "direction": "vertical/horizontal/diagonal" (gradientの場合)
              }
            - opacity: 0.0-1.0 (オプション、デフォルト1.0)

    Returns:
        dict: 生成された画像のBase64データを含む辞書
            - success: 成功したかどうか
            - image_base64: 生成された画像のBase64データ（透過PNG）
            - error: エラーメッセージ（失敗時）
    """
    try:
        # キャンバスサイズ（シェイプに合わせて後でクロップも可能）
        canvas_width = 1920
        canvas_height = 1080

        # 透過キャンバスを作成
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        shape_type = shape.get("type", "polygon")
        fill_config = shape.get("fill", {"type": "solid", "color": "#00796B"})
        opacity = int(shape.get("opacity", 1.0) * 255)

        # シェイプの領域を計算
        if shape_type == "polygon":
            points = shape.get("points", [])
            if not points:
                return {"success": False, "error": "Points are required for polygon"}
            points = [tuple(p) for p in points]

            # バウンディングボックスを計算
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            shape_width = max_x - min_x
            shape_height = max_y - min_y

        elif shape_type == "rectangle":
            x = shape.get("x", 0)
            y = shape.get("y", 0)
            w = shape.get("width", 200)
            h = shape.get("height", 200)
            points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            min_x, min_y = x, y
            shape_width, shape_height = w, h

        elif shape_type == "triangle":
            # 三角形: 3点を指定
            points = shape.get("points", [[100, 0], [0, 200], [200, 200]])
            points = [tuple(p) for p in points]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            shape_width = max_x - min_x
            shape_height = max_y - min_y

        elif shape_type == "ellipse":
            x = shape.get("x", 0)
            y = shape.get("y", 0)
            w = shape.get("width", 200)
            h = shape.get("height", 200)
            min_x, min_y = x, y
            shape_width, shape_height = w, h
        else:
            return {"success": False, "error": f"Unknown shape type: {shape_type}"}

        # 塗りつぶし
        if fill_config.get("type") == "gradient":
            # グラデーション塗りつぶし
            start_color = fill_config.get("start", "#00796B")
            end_color = fill_config.get("end", "#A5D6A7")
            direction = fill_config.get("direction", "diagonal")

            # グラデーション画像を生成
            gradient = create_gradient_image(canvas_width, canvas_height, start_color, end_color, direction)

            # マスクを作成
            mask = Image.new("L", (canvas_width, canvas_height), 0)
            mask_draw = ImageDraw.Draw(mask)

            if shape_type == "ellipse":
                mask_draw.ellipse([min_x, min_y, min_x + shape_width, min_y + shape_height], fill=opacity)
            else:
                mask_draw.polygon(points, fill=opacity)

            # グラデーションをマスクで切り抜いてキャンバスに合成
            canvas.paste(gradient, (0, 0), mask)

        else:
            # ソリッド塗りつぶし
            color = fill_config.get("color", "#00796B")
            fill_color = hex_to_rgba(color, opacity)

            draw = ImageDraw.Draw(canvas)

            if shape_type == "ellipse":
                draw.ellipse([min_x, min_y, min_x + shape_width, min_y + shape_height], fill=fill_color)
            else:
                draw.polygon(points, fill=fill_color)

        return {
            "success": True,
            "image_base64": image_to_base64(canvas),
            "mime_type": "image/png"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
