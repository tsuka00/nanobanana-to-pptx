"""
デザインプリセット定義
レイアウト、配色パレット、トーンのプリセットを定義
"""

from typing import Optional, TypedDict

# キャンバスサイズ
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080


# =============================================================================
# レイアウトプリセット
# =============================================================================

class LayoutPositions(TypedDict):
    """レイアウトの座標定義"""
    title_x: int
    title_y: int
    subtitle_x: int
    subtitle_y: int
    title_align: str  # "center", "left", "right"
    content_area: Optional[dict]  # イラスト/画像用の領域


LAYOUTS: dict[str, LayoutPositions] = {
    # 中央配置（デフォルト）
    "center": {
        "title_x": 960,
        "title_y": 400,
        "subtitle_x": 960,
        "subtitle_y": 520,
        "title_align": "center",
        "content_area": None,
    },
    # 中央・垂直中央
    "center-middle": {
        "title_x": 960,
        "title_y": 480,
        "subtitle_x": 960,
        "subtitle_y": 600,
        "title_align": "center",
        "content_area": None,
    },
    # 左寄せ
    "left": {
        "title_x": 200,
        "title_y": 400,
        "subtitle_x": 200,
        "subtitle_y": 520,
        "title_align": "left",
        "content_area": {"x": 1200, "y": 200, "width": 600, "height": 680},
    },
    # 右寄せ
    "right": {
        "title_x": 1720,
        "title_y": 400,
        "subtitle_x": 1720,
        "subtitle_y": 520,
        "title_align": "right",
        "content_area": {"x": 100, "y": 200, "width": 600, "height": 680},
    },
    # 下部配置
    "bottom": {
        "title_x": 960,
        "title_y": 800,
        "subtitle_x": 960,
        "subtitle_y": 920,
        "title_align": "center",
        "content_area": {"x": 0, "y": 0, "width": 1920, "height": 700},
    },
    # 上部配置
    "top": {
        "title_x": 960,
        "title_y": 200,
        "subtitle_x": 960,
        "subtitle_y": 320,
        "title_align": "center",
        "content_area": {"x": 0, "y": 400, "width": 1920, "height": 680},
    },
    # 左半分（50:50分割）
    "split-left": {
        "title_x": 480,
        "title_y": 450,
        "subtitle_x": 480,
        "subtitle_y": 580,
        "title_align": "center",
        "content_area": {"x": 960, "y": 0, "width": 960, "height": 1080},
    },
    # 右半分（50:50分割）
    "split-right": {
        "title_x": 1440,
        "title_y": 450,
        "subtitle_x": 1440,
        "subtitle_y": 580,
        "title_align": "center",
        "content_area": {"x": 0, "y": 0, "width": 960, "height": 1080},
    },
    # 左下
    "bottom-left": {
        "title_x": 200,
        "title_y": 800,
        "subtitle_x": 200,
        "subtitle_y": 920,
        "title_align": "left",
        "content_area": None,
    },
    # 右下
    "bottom-right": {
        "title_x": 1720,
        "title_y": 800,
        "subtitle_x": 1720,
        "subtitle_y": 920,
        "title_align": "right",
        "content_area": None,
    },
    # オーバーレイ（背景画像の上に中央配置、暗いオーバーレイ推奨）
    "overlay": {
        "title_x": 960,
        "title_y": 480,
        "subtitle_x": 960,
        "subtitle_y": 620,
        "title_align": "center",
        "content_area": None,
    },
}


# =============================================================================
# 配色パレット
# =============================================================================

class ColorPalette(TypedDict):
    """配色パレットの定義"""
    background: str  # 背景色（単色の場合）
    text_primary: str  # メインテキスト色
    text_secondary: str  # サブテキスト色
    accent: str  # アクセント色
    background_prompt_hint: str  # 背景生成時のヒント
    recommended_styles: list[str]  # 推奨テキストスタイル


PALETTES: dict[str, ColorPalette] = {
    # ライト系
    "light": {
        "background": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#666666",
        "accent": "#2196F3",
        "background_prompt_hint": "clean white or light gray background, minimal, professional",
        "recommended_styles": ["flat", "shadow", "outline"],
    },
    "light-warm": {
        "background": "#faf8f5",
        "text_primary": "#3d3d3d",
        "text_secondary": "#757575",
        "accent": "#ff9800",
        "background_prompt_hint": "warm cream or beige background, soft, inviting",
        "recommended_styles": ["flat", "shadow"],
    },
    "light-cool": {
        "background": "#f5f9fc",
        "text_primary": "#1a3a5c",
        "text_secondary": "#5a7a9a",
        "accent": "#00bcd4",
        "background_prompt_hint": "light blue tinted background, clean, fresh",
        "recommended_styles": ["flat", "glass", "shadow"],
    },

    # ダーク系
    "dark": {
        "background": "#1a1a1a",
        "text_primary": "#ffffff",
        "text_secondary": "#aaaaaa",
        "accent": "#00bcd4",
        "background_prompt_hint": "dark background, subtle texture or gradient, modern",
        "recommended_styles": ["flat", "shadow", "neon-glow"],
    },
    "dark-tech": {
        "background": "#0a0a0a",
        "text_primary": "#ffffff",
        "text_secondary": "#888888",
        "accent": "#00ffff",
        "background_prompt_hint": "dark futuristic background, subtle grid or particles, tech atmosphere, cyber aesthetic",
        "recommended_styles": ["3d-metallic", "neon-glow", "glass"],
    },
    "dark-purple": {
        "background": "#1a0a2e",
        "text_primary": "#ffffff",
        "text_secondary": "#b39ddb",
        "accent": "#e040fb",
        "background_prompt_hint": "deep purple dark background, mystical, creative atmosphere",
        "recommended_styles": ["neon-glow", "glass", "gradient"],
    },

    # モノクローム
    "monochrome": {
        "background": "#f5f5f5",
        "text_primary": "#000000",
        "text_secondary": "#555555",
        "accent": "#000000",
        "background_prompt_hint": "pure white or light gray background, minimalist, no color",
        "recommended_styles": ["flat", "outline", "emboss"],
    },
    "monochrome-dark": {
        "background": "#121212",
        "text_primary": "#ffffff",
        "text_secondary": "#9e9e9e",
        "accent": "#ffffff",
        "background_prompt_hint": "pure black background, minimalist, high contrast",
        "recommended_styles": ["flat", "outline"],
    },

    # プレミアム系
    "premium-gold": {
        "background": "#1a1a1a",
        "text_primary": "#ffffff",
        "text_secondary": "#d4af37",
        "accent": "#ffd700",
        "background_prompt_hint": "elegant dark background with subtle gold accents, luxury, sophisticated",
        "recommended_styles": ["gold", "3d-metallic", "emboss"],
    },
    "premium-silver": {
        "background": "#1a1a2e",
        "text_primary": "#ffffff",
        "text_secondary": "#c0c0c0",
        "accent": "#e8e8e8",
        "background_prompt_hint": "dark navy background with metallic silver hints, modern luxury, sleek",
        "recommended_styles": ["silver", "3d-metallic", "glass"],
    },

    # ビビッド系
    "vibrant": {
        "background": "#ffffff",
        "text_primary": "#1a1a1a",
        "text_secondary": "#666666",
        "accent": "#ff4081",
        "background_prompt_hint": "white background with vibrant color accents, energetic, bold",
        "recommended_styles": ["gradient", "neon-glow", "flat"],
    },
    "vibrant-gradient": {
        "background": "#667eea",
        "text_primary": "#ffffff",
        "text_secondary": "#e0e0ff",
        "accent": "#f093fb",
        "background_prompt_hint": "vibrant gradient background from purple to pink, dynamic, modern",
        "recommended_styles": ["flat", "glass", "shadow"],
    },

    # 自然系
    "nature": {
        "background": "#f5f5dc",
        "text_primary": "#2e4a2e",
        "text_secondary": "#5a7a5a",
        "accent": "#4caf50",
        "background_prompt_hint": "natural, organic background, soft green tones, earthy, sustainable",
        "recommended_styles": ["flat", "shadow"],
    },
    "ocean": {
        "background": "#e3f2fd",
        "text_primary": "#0d47a1",
        "text_secondary": "#1976d2",
        "accent": "#00bcd4",
        "background_prompt_hint": "ocean-inspired background, blue gradient, calm, serene",
        "recommended_styles": ["flat", "glass", "gradient"],
    },

    # ビジネス系
    "corporate": {
        "background": "#f8f9fa",
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "accent": "#0056b3",
        "background_prompt_hint": "professional corporate background, clean, trustworthy, business-like",
        "recommended_styles": ["flat", "shadow"],
    },
    "corporate-dark": {
        "background": "#1e2a3a",
        "text_primary": "#ffffff",
        "text_secondary": "#a0aec0",
        "accent": "#3182ce",
        "background_prompt_hint": "dark professional background, corporate, modern business",
        "recommended_styles": ["flat", "shadow", "glass"],
    },
}


# =============================================================================
# トーンプリセット
# =============================================================================

class TonePreset(TypedDict):
    """トーンプリセットの定義"""
    description: str
    recommended_layouts: list[str]
    recommended_palettes: list[str]
    recommended_styles: list[str]
    font_weight_title: str
    font_weight_subtitle: str
    reasoning_hint: str  # Reasoning時のヒント


TONES: dict[str, TonePreset] = {
    "professional": {
        "description": "プロフェッショナル、ビジネス、信頼感",
        "recommended_layouts": ["center", "left", "split-left"],
        "recommended_palettes": ["corporate", "light", "monochrome"],
        "recommended_styles": ["flat", "shadow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Clean, trustworthy design. Avoid flashy effects. Prioritize readability and professionalism.",
    },
    "creative": {
        "description": "クリエイティブ、アーティスティック、独創的",
        "recommended_layouts": ["left", "right", "bottom-left", "split-right"],
        "recommended_palettes": ["vibrant", "vibrant-gradient", "dark-purple"],
        "recommended_styles": ["gradient", "glass", "neon-glow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Expressive and artistic design. Use dynamic layouts and bold color choices.",
    },
    "tech": {
        "description": "テクノロジー、未来的、先進的",
        "recommended_layouts": ["center", "split-left", "overlay"],
        "recommended_palettes": ["dark-tech", "dark", "premium-silver"],
        "recommended_styles": ["3d-metallic", "neon-glow", "glass"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Futuristic, cutting-edge design. Dark backgrounds with glowing accents. Tech-forward aesthetic.",
    },
    "premium": {
        "description": "高級、ラグジュアリー、洗練",
        "recommended_layouts": ["center", "center-middle", "overlay"],
        "recommended_palettes": ["premium-gold", "premium-silver", "monochrome-dark"],
        "recommended_styles": ["gold", "silver", "3d-metallic", "emboss"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "light",
        "reasoning_hint": "Elegant and luxurious design. Rich colors, metallic effects, generous whitespace.",
    },
    "minimal": {
        "description": "ミニマル、シンプル、余白重視",
        "recommended_layouts": ["center", "center-middle", "left"],
        "recommended_palettes": ["monochrome", "light", "monochrome-dark"],
        "recommended_styles": ["flat", "outline"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "light",
        "reasoning_hint": "Less is more. Maximum whitespace, minimal elements, clean typography.",
    },
    "energetic": {
        "description": "エネルギッシュ、活発、ダイナミック",
        "recommended_layouts": ["left", "right", "bottom", "split-left"],
        "recommended_palettes": ["vibrant", "vibrant-gradient", "dark-tech"],
        "recommended_styles": ["neon-glow", "gradient", "3d-metallic"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "bold",
        "reasoning_hint": "High energy design. Bold colors, dynamic compositions, strong visual impact.",
    },
    "warm": {
        "description": "温かみ、親しみやすさ、柔らかさ",
        "recommended_layouts": ["center", "left", "bottom"],
        "recommended_palettes": ["light-warm", "nature", "corporate"],
        "recommended_styles": ["flat", "shadow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Warm and inviting design. Soft colors, friendly typography, approachable feel.",
    },
    "cool": {
        "description": "クール、洗練、知的",
        "recommended_layouts": ["center", "split-left", "right"],
        "recommended_palettes": ["light-cool", "ocean", "dark"],
        "recommended_styles": ["flat", "glass", "shadow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Cool and sophisticated design. Blue tones, clean lines, intellectual feel.",
    },
    "nature": {
        "description": "自然、オーガニック、サステナブル",
        "recommended_layouts": ["center", "bottom", "overlay"],
        "recommended_palettes": ["nature", "ocean", "light-warm"],
        "recommended_styles": ["flat", "shadow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Nature-inspired design. Earthy colors, organic shapes, environmental consciousness.",
    },
    "playful": {
        "description": "遊び心、楽しさ、カジュアル",
        "recommended_layouts": ["left", "bottom-left", "split-right"],
        "recommended_palettes": ["vibrant", "light-warm", "vibrant-gradient"],
        "recommended_styles": ["outline", "gradient", "neon-glow"],
        "font_weight_title": "bold",
        "font_weight_subtitle": "normal",
        "reasoning_hint": "Fun and playful design. Bright colors, casual typography, lighthearted feel.",
    },
}


# =============================================================================
# ヘルパー関数
# =============================================================================

def get_layout(name: str) -> LayoutPositions:
    """レイアウトプリセットを取得（存在しない場合はcenterを返す）"""
    return LAYOUTS.get(name, LAYOUTS["center"])


def get_palette(name: str) -> ColorPalette:
    """配色パレットを取得（存在しない場合はlightを返す）"""
    return PALETTES.get(name, PALETTES["light"])


def get_tone(name: str) -> TonePreset:
    """トーンプリセットを取得（存在しない場合はprofessionalを返す）"""
    return TONES.get(name, TONES["professional"])


def list_layouts() -> list[str]:
    """利用可能なレイアウト一覧"""
    return list(LAYOUTS.keys())


def list_palettes() -> list[str]:
    """利用可能なパレット一覧"""
    return list(PALETTES.keys())


def list_tones() -> list[str]:
    """利用可能なトーン一覧"""
    return list(TONES.keys())


def get_preset_summary() -> str:
    """プリセット一覧のサマリー文字列を生成（プロンプト用）"""
    lines = []

    lines.append("## レイアウトプリセット")
    for name, layout in LAYOUTS.items():
        lines.append(f"- `{name}`: タイトル位置({layout['title_x']}, {layout['title_y']}), 配置={layout['title_align']}")

    lines.append("\n## 配色パレット")
    for name, palette in PALETTES.items():
        lines.append(f"- `{name}`: 背景={palette['background']}, テキスト={palette['text_primary']}, アクセント={palette['accent']}")
        lines.append(f"  推奨スタイル: {', '.join(palette['recommended_styles'])}")

    lines.append("\n## トーンプリセット")
    for name, tone in TONES.items():
        lines.append(f"- `{name}`: {tone['description']}")
        lines.append(f"  推奨レイアウト: {', '.join(tone['recommended_layouts'])}")
        lines.append(f"  推奨パレット: {', '.join(tone['recommended_palettes'])}")

    return "\n".join(lines)
