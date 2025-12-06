"""
Draw Illustration SVG ツール
幾何学シェイプをSVGとして生成
"""

from strands import tool

# キャンバスサイズ（16:9）
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


def create_gradient_def(gradient_id: str, fill_config: dict) -> str:
    """SVGグラデーション定義を生成"""
    start_color = fill_config.get("start", "#00796B")
    end_color = fill_config.get("end", "#A5D6A7")
    direction = fill_config.get("direction", "diagonal")

    if direction == "vertical":
        x1, y1, x2, y2 = "0%", "0%", "0%", "100%"
    elif direction == "horizontal":
        x1, y1, x2, y2 = "0%", "0%", "100%", "0%"
    else:  # diagonal
        x1, y1, x2, y2 = "0%", "0%", "100%", "100%"

    return f'''  <defs>
    <linearGradient id="{gradient_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">
      <stop offset="0%" stop-color="{start_color}"/>
      <stop offset="100%" stop-color="{end_color}"/>
    </linearGradient>
  </defs>'''


def points_to_svg_points(points: list) -> str:
    """座標リストをSVGのpoints属性形式に変換"""
    return " ".join(f"{p[0]},{p[1]}" for p in points)


@tool
def draw_illustration_svg(shape: dict) -> dict:
    """
    JSONパラメータからイラスト/シェイプをSVGとして生成します。

    Args:
        shape: シェイプの定義
            - type: "polygon", "rectangle", "ellipse", "triangle"
            - points: [[x1, y1], [x2, y2], ...] (polygon/triangleの場合)
            - x, y, width, height: (rectangle/ellipseの場合)
            - fill: {
                "type": "solid" または "gradient",
                "color": "#RRGGBB" (solidの場合),
                "start": "#RRGGBB", "end": "#RRGGBB", "direction": "vertical/horizontal/diagonal" (gradientの場合)
              }
            - opacity: 0.0-1.0 (オプション、デフォルト1.0)

    Returns:
        dict: 生成されたSVGを含む辞書
            - success: 成功したかどうか
            - svg: SVG文字列
            - error: エラーメッセージ（失敗時）
    """
    try:
        shape_type = shape.get("type", "polygon")
        fill_config = shape.get("fill", {"type": "solid", "color": "#00796B"})
        opacity = shape.get("opacity", 1.0)

        # グラデーション定義
        defs = ""
        if fill_config.get("type") == "gradient":
            gradient_id = "shapeGradient"
            defs = create_gradient_def(gradient_id, fill_config)
            fill_value = f"url(#{gradient_id})"
        else:
            fill_value = fill_config.get("color", "#00796B")

        # シェイプ要素を生成
        if shape_type == "polygon" or shape_type == "triangle":
            points = shape.get("points", [])
            if not points:
                return {"success": False, "error": "Points are required for polygon/triangle"}
            points_str = points_to_svg_points(points)
            shape_element = f'  <polygon points="{points_str}" fill="{fill_value}" opacity="{opacity}"/>'

        elif shape_type == "rectangle":
            x = shape.get("x", 0)
            y = shape.get("y", 0)
            w = shape.get("width", 200)
            h = shape.get("height", 200)
            shape_element = f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill_value}" opacity="{opacity}"/>'

        elif shape_type == "ellipse":
            x = shape.get("x", 0)
            y = shape.get("y", 0)
            w = shape.get("width", 200)
            h = shape.get("height", 200)
            cx = x + w / 2
            cy = y + h / 2
            rx = w / 2
            ry = h / 2
            shape_element = f'  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill_value}" opacity="{opacity}"/>'

        else:
            return {"success": False, "error": f"Unknown shape type: {shape_type}"}

        # SVG全体を組み立て
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">
{defs}
{shape_element}
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
