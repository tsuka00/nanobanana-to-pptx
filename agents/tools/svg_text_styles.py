"""
SVG Text Style Presets
タイトル/サブタイトル用のSVGスタイルプリセット
"""

from typing import Dict, List, Tuple, Optional
import random

# キャンバスサイズ
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


def generate_id(prefix: str = "style") -> str:
    """ユニークなID生成"""
    return f"{prefix}_{random.randint(1000, 9999)}"


# =============================================================================
# スタイルプリセット定義
# =============================================================================

STYLE_PRESETS = {
    # シンプル（デフォルト）
    "flat": {
        "description": "シンプルな単色テキスト",
        "has_filter": False,
        "has_gradient": False,
        "layers": 1,
    },

    # ドロップシャドウ
    "shadow": {
        "description": "ドロップシャドウ付きテキスト",
        "has_filter": True,
        "has_gradient": False,
        "layers": 1,
        "shadow_offset": (4, 4),
        "shadow_blur": 4,
        "shadow_color": "rgba(0,0,0,0.5)",
    },

    # 3D風メタリック
    "3d-metallic": {
        "description": "3D風メタリックグラデーション",
        "has_filter": True,
        "has_gradient": True,
        "layers": 3,
        "gradient_stops": [
            (0, "#e8e8e8"),
            (25, "#ffffff"),
            (50, "#b8b8b8"),
            (75, "#e0e0e0"),
            (100, "#c0c0c0"),
        ],
        "shadow_offset": (6, 6),
        "shadow_blur": 8,
        "highlight_offset": (-2, -2),
    },

    # ネオングロー
    "neon-glow": {
        "description": "ネオン発光エフェクト",
        "has_filter": True,
        "has_gradient": False,
        "layers": 3,
        "glow_blur": 10,
        "glow_color": "#00ffff",
        "inner_color": "#ffffff",
    },

    # ガラス/透明感
    "glass": {
        "description": "ガラス風透明感",
        "has_filter": True,
        "has_gradient": True,
        "layers": 2,
        "gradient_stops": [
            (0, "rgba(255,255,255,0.9)"),
            (50, "rgba(255,255,255,0.6)"),
            (100, "rgba(255,255,255,0.8)"),
        ],
        "blur": 1,
    },

    # アウトライン
    "outline": {
        "description": "アウトライン付きテキスト",
        "has_filter": False,
        "has_gradient": False,
        "layers": 2,
        "stroke_width": 3,
        "stroke_color": "#000000",
    },

    # ゴールド
    "gold": {
        "description": "ゴールドメタリック",
        "has_filter": True,
        "has_gradient": True,
        "layers": 2,
        "gradient_stops": [
            (0, "#f7e98e"),
            (25, "#ffffc8"),
            (50, "#d4a84b"),
            (75, "#f7e98e"),
            (100, "#c9a227"),
        ],
        "shadow_offset": (4, 4),
        "shadow_blur": 6,
    },

    # シルバー
    "silver": {
        "description": "シルバーメタリック",
        "has_filter": True,
        "has_gradient": True,
        "layers": 2,
        "gradient_stops": [
            (0, "#e8e8e8"),
            (25, "#ffffff"),
            (50, "#a8a8a8"),
            (75, "#d8d8d8"),
            (100, "#b8b8b8"),
        ],
        "shadow_offset": (3, 3),
        "shadow_blur": 5,
    },

    # エンボス
    "emboss": {
        "description": "エンボス（浮き彫り）効果",
        "has_filter": True,
        "has_gradient": False,
        "layers": 3,
        "light_offset": (-2, -2),
        "shadow_offset": (2, 2),
    },

    # グラデーション（カスタム用）
    "gradient": {
        "description": "カスタムグラデーション",
        "has_filter": False,
        "has_gradient": True,
        "layers": 1,
    },
}


def get_available_styles() -> List[str]:
    """利用可能なスタイル名のリストを取得"""
    return list(STYLE_PRESETS.keys())


def get_style_description(style_name: str) -> str:
    """スタイルの説明を取得"""
    preset = STYLE_PRESETS.get(style_name, {})
    return preset.get("description", "不明なスタイル")


# =============================================================================
# SVG生成関数
# =============================================================================

def generate_styled_text_svg(
    text: str,
    x: int,
    y: int,
    font_size: int,
    font_family: str,
    font_weight: str,
    style: str = "flat",
    color: str = "#ffffff",
    custom_gradient: Optional[Dict] = None,
    custom_glow_color: Optional[str] = None,
) -> str:
    """
    スタイル付きテキストSVGを生成

    Args:
        text: テキスト内容
        x: X座標（中心）
        y: Y座標（中心）
        font_size: フォントサイズ
        font_family: フォントファミリー
        font_weight: フォントウェイト
        style: スタイルプリセット名
        color: 基本色（flatやoutlineで使用）
        custom_gradient: カスタムグラデーション設定
        custom_glow_color: カスタムグロー色（neon-glow用）

    Returns:
        SVG文字列
    """
    escaped_text = escape_xml(text)
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["flat"])

    defs_content = ""
    text_elements = ""
    uid = generate_id(style)

    # スタイル別のSVG生成
    if style == "flat":
        text_elements = _generate_flat_text(
            escaped_text, x, y, font_size, font_family, font_weight, color
        )

    elif style == "shadow":
        defs_content, text_elements = _generate_shadow_text(
            escaped_text, x, y, font_size, font_family, font_weight, color, uid
        )

    elif style == "3d-metallic":
        defs_content, text_elements = _generate_3d_metallic_text(
            escaped_text, x, y, font_size, font_family, font_weight, uid
        )

    elif style == "neon-glow":
        glow_color = custom_glow_color or preset.get("glow_color", "#00ffff")
        defs_content, text_elements = _generate_neon_glow_text(
            escaped_text, x, y, font_size, font_family, font_weight, glow_color, uid
        )

    elif style == "glass":
        defs_content, text_elements = _generate_glass_text(
            escaped_text, x, y, font_size, font_family, font_weight, uid
        )

    elif style == "outline":
        text_elements = _generate_outline_text(
            escaped_text, x, y, font_size, font_family, font_weight, color, uid
        )

    elif style == "gold":
        defs_content, text_elements = _generate_metallic_text(
            escaped_text, x, y, font_size, font_family, font_weight,
            STYLE_PRESETS["gold"]["gradient_stops"], uid
        )

    elif style == "silver":
        defs_content, text_elements = _generate_metallic_text(
            escaped_text, x, y, font_size, font_family, font_weight,
            STYLE_PRESETS["silver"]["gradient_stops"], uid
        )

    elif style == "emboss":
        text_elements = _generate_emboss_text(
            escaped_text, x, y, font_size, font_family, font_weight, color, uid
        )

    elif style == "gradient":
        if custom_gradient:
            defs_content, text_elements = _generate_gradient_text(
                escaped_text, x, y, font_size, font_family, font_weight,
                custom_gradient, uid
            )
        else:
            text_elements = _generate_flat_text(
                escaped_text, x, y, font_size, font_family, font_weight, color
            )

    else:
        # フォールバック
        text_elements = _generate_flat_text(
            escaped_text, x, y, font_size, font_family, font_weight, color
        )

    # SVG組み立て
    defs_section = f"  <defs>\n{defs_content}  </defs>\n" if defs_content else ""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">
{defs_section}{text_elements}</svg>'''

    return svg


# =============================================================================
# スタイル別生成関数
# =============================================================================

def _generate_flat_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, color: str
) -> str:
    """シンプルなテキスト"""
    return f'''  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="{color}"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''


def _generate_shadow_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, color: str, uid: str
) -> Tuple[str, str]:
    """ドロップシャドウ付きテキスト"""
    filter_id = f"shadow_{uid}"

    defs = f'''    <filter id="{filter_id}" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="4" dy="4" stdDeviation="3" flood-color="rgba(0,0,0,0.5)"/>
    </filter>
'''

    elements = f'''  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="{color}"
        filter="url(#{filter_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def _generate_3d_metallic_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, uid: str
) -> Tuple[str, str]:
    """3D風ホログラフィックメタリックテキスト"""
    # グラデーションID
    holo_gradient_id = f"holo_grad_{uid}"
    holo_gradient_h_id = f"holo_grad_h_{uid}"
    stroke_gradient_id = f"stroke_grad_{uid}"
    highlight_gradient_id = f"highlight_grad_{uid}"

    # フィルターID
    bevel_filter_id = f"bevel_{uid}"
    glow_filter_id = f"glow_{uid}"
    specular_filter_id = f"specular_{uid}"

    # ストローク幅（フォントサイズに比例）
    stroke_width = max(font_size // 8, 4)

    defs = f'''    <!-- ホログラフィック縦グラデーション（メイン塗り） -->
    <linearGradient id="{holo_gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#88ffaa"/>
      <stop offset="15%" stop-color="#aaffcc"/>
      <stop offset="30%" stop-color="#66dd88"/>
      <stop offset="50%" stop-color="#44aa66"/>
      <stop offset="70%" stop-color="#66cc88"/>
      <stop offset="85%" stop-color="#88eebb"/>
      <stop offset="100%" stop-color="#55bb77"/>
    </linearGradient>

    <!-- ホログラフィック横グラデーション（虹色反射） -->
    <linearGradient id="{holo_gradient_h_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(100, 200, 255, 0.3)"/>
      <stop offset="25%" stop-color="rgba(200, 100, 255, 0.2)"/>
      <stop offset="50%" stop-color="rgba(255, 150, 200, 0.3)"/>
      <stop offset="75%" stop-color="rgba(100, 255, 200, 0.2)"/>
      <stop offset="100%" stop-color="rgba(150, 200, 255, 0.3)"/>
    </linearGradient>

    <!-- ストローク用グラデーション（チューブの輪郭） -->
    <linearGradient id="{stroke_gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#aaddbb"/>
      <stop offset="30%" stop-color="#55aa77"/>
      <stop offset="70%" stop-color="#338855"/>
      <stop offset="100%" stop-color="#226644"/>
    </linearGradient>

    <!-- ハイライトグラデーション -->
    <linearGradient id="{highlight_gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(255,255,255,0.9)"/>
      <stop offset="30%" stop-color="rgba(255,255,255,0.4)"/>
      <stop offset="50%" stop-color="rgba(255,255,255,0.1)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
    </linearGradient>

    <!-- ベベル/エンボスフィルター -->
    <filter id="{bevel_filter_id}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="blur"/>
      <feOffset in="blur" dx="-2" dy="-2" result="offsetLight"/>
      <feOffset in="blur" dx="2" dy="2" result="offsetShadow"/>
      <feComposite in="offsetLight" in2="SourceAlpha" operator="arithmetic" k1="0" k2="1" k3="-1" k4="0" result="lightDiff"/>
      <feComposite in="offsetShadow" in2="SourceAlpha" operator="arithmetic" k1="0" k2="1" k3="-1" k4="0" result="shadowDiff"/>
      <feFlood flood-color="white" flood-opacity="0.6" result="lightColor"/>
      <feFlood flood-color="black" flood-opacity="0.4" result="shadowColor"/>
      <feComposite in="lightColor" in2="lightDiff" operator="in" result="lightEffect"/>
      <feComposite in="shadowColor" in2="shadowDiff" operator="in" result="shadowEffect"/>
      <feMerge>
        <feMergeNode in="shadowEffect"/>
        <feMergeNode in="SourceGraphic"/>
        <feMergeNode in="lightEffect"/>
      </feMerge>
    </filter>

    <!-- スペキュラーライティングフィルター -->
    <filter id="{specular_filter_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="4" result="blur"/>
      <feSpecularLighting in="blur" surfaceScale="5" specularConstant="0.8" specularExponent="25" lighting-color="#ffffff" result="specular">
        <fePointLight x="{x - 200}" y="{y - 300}" z="400"/>
      </feSpecularLighting>
      <feComposite in="specular" in2="SourceAlpha" operator="in" result="specularIn"/>
      <feComposite in="SourceGraphic" in2="specularIn" operator="arithmetic" k1="0" k2="1" k3="0.8" k4="0"/>
    </filter>

    <!-- グローフィルター -->
    <filter id="{glow_filter_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur"/>
      <feColorMatrix in="blur" type="matrix" values="0 0 0 0 0.4  0 0 0 0 0.9  0 0 0 0 0.6  0 0 0 0.5 0" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
'''

    # 多層テキスト構成
    elements = f'''  <!-- レイヤー1: 外側グロー -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{holo_gradient_id})"
        filter="url(#{glow_filter_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー2: 影（奥行き感） -->
  <text x="{x + 6}" y="{y + 6}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="rgba(0,50,30,0.4)"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー3: ストローク（チューブの輪郭） -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="none"
        stroke="url(#{stroke_gradient_id})"
        stroke-width="{stroke_width}"
        stroke-linejoin="round"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー4: メインボディ（ベベル効果付き） -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{holo_gradient_id})"
        filter="url(#{bevel_filter_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー5: スペキュラーハイライト -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{holo_gradient_id})"
        filter="url(#{specular_filter_id})"
        opacity="0.7"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー6: 虹色オーバーレイ -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{holo_gradient_h_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>

  <!-- レイヤー7: トップハイライト -->
  <text x="{x}" y="{y - 2}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{highlight_gradient_id})"
        opacity="0.6"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def _generate_neon_glow_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, glow_color: str, uid: str
) -> Tuple[str, str]:
    """ネオングローテキスト"""
    filter_id = f"neon_{uid}"

    defs = f'''    <filter id="{filter_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur1"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur2"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur3"/>
      <feMerge>
        <feMergeNode in="blur1"/>
        <feMergeNode in="blur2"/>
        <feMergeNode in="blur3"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
'''

    # 多層グロー効果
    elements = f'''  <!-- 外側グロー -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="{glow_color}"
        filter="url(#{filter_id})"
        opacity="0.8"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- 内側（白） -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="#ffffff"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def _generate_glass_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, uid: str
) -> Tuple[str, str]:
    """ガラス風テキスト"""
    gradient_id = f"glass_{uid}"
    filter_id = f"glass_filter_{uid}"

    defs = f'''    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(255,255,255,0.95)"/>
      <stop offset="45%" stop-color="rgba(255,255,255,0.7)"/>
      <stop offset="55%" stop-color="rgba(255,255,255,0.5)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.8)"/>
    </linearGradient>
    <filter id="{filter_id}">
      <feGaussianBlur in="SourceGraphic" stdDeviation="0.5"/>
    </filter>
'''

    elements = f'''  <!-- 影 -->
  <text x="{x + 2}" y="{y + 2}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="rgba(0,0,0,0.2)"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- ガラス本体 -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{gradient_id})"
        filter="url(#{filter_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def _generate_outline_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, color: str, uid: str
) -> str:
    """アウトライン付きテキスト"""
    return f'''  <!-- アウトライン -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="none"
        stroke="#000000"
        stroke-width="4"
        stroke-linejoin="round"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- 塗り -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="{color}"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''


def _generate_metallic_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str,
    gradient_stops: List[Tuple[int, str]], uid: str
) -> Tuple[str, str]:
    """メタリック（ゴールド/シルバー）テキスト"""
    gradient_id = f"metallic_{uid}"
    filter_id = f"metallic_shadow_{uid}"

    stops = "\n".join([
        f'      <stop offset="{offset}%" stop-color="{color}"/>'
        for offset, color in gradient_stops
    ])

    defs = f'''    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">
{stops}
    </linearGradient>
    <filter id="{filter_id}" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="3" dy="3" stdDeviation="3" flood-color="rgba(0,0,0,0.4)"/>
    </filter>
'''

    elements = f'''  <!-- 影 -->
  <text x="{x + 3}" y="{y + 3}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="rgba(0,0,0,0.25)"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- メタリック本体 -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{gradient_id})"
        filter="url(#{filter_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def _generate_emboss_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str, color: str, uid: str
) -> str:
    """エンボス効果テキスト"""
    return f'''  <!-- 光（左上） -->
  <text x="{x - 2}" y="{y - 2}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="rgba(255,255,255,0.5)"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- 影（右下） -->
  <text x="{x + 2}" y="{y + 2}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="rgba(0,0,0,0.5)"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
  <!-- 本体 -->
  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="{color}"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''


def _generate_gradient_text(
    text: str, x: int, y: int, font_size: int,
    font_family: str, font_weight: str,
    gradient_config: Dict, uid: str
) -> Tuple[str, str]:
    """カスタムグラデーションテキスト"""
    gradient_id = f"custom_gradient_{uid}"

    start_color = gradient_config.get("start", "#ffffff")
    end_color = gradient_config.get("end", "#888888")
    direction = gradient_config.get("direction", "vertical")

    if direction == "vertical":
        x1, y1, x2, y2 = "0%", "0%", "0%", "100%"
    elif direction == "diagonal":
        x1, y1, x2, y2 = "0%", "0%", "100%", "100%"
    else:  # horizontal
        x1, y1, x2, y2 = "0%", "0%", "100%", "0%"

    defs = f'''    <linearGradient id="{gradient_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">
      <stop offset="0%" stop-color="{start_color}"/>
      <stop offset="100%" stop-color="{end_color}"/>
    </linearGradient>
'''

    elements = f'''  <text x="{x}" y="{y}"
        font-family="{font_family}"
        font-size="{font_size}"
        font-weight="{font_weight}"
        fill="url(#{gradient_id})"
        text-anchor="middle"
        dominant-baseline="middle">{text}</text>
'''
    return defs, elements


def escape_xml(text: str) -> str:
    """XML特殊文字をエスケープ"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
