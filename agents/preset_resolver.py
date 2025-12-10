"""
プリセット解決モジュール
設計JSONのプリセット指定を具体的な値に展開する
"""

from typing import Optional
from .presets import (
    get_layout, get_palette, get_tone,
    LAYOUTS, PALETTES, TONES,
    CANVAS_WIDTH, CANVAS_HEIGHT
)


def resolve_presets(design: dict) -> dict:
    """
    設計JSONのプリセットを解決し、具体的な値に展開する

    Args:
        design: プリセット指定を含む設計JSON

    Returns:
        dict: プリセットが解決された設計JSON
    """
    resolved = design.copy()

    # presetセクションを取得
    preset = design.get("preset", {})
    layout_name = preset.get("layout", "center")
    palette_name = preset.get("palette", "light")
    tone_name = preset.get("tone")

    # プリセットを取得
    layout = get_layout(layout_name)
    palette = get_palette(palette_name)
    tone = get_tone(tone_name) if tone_name else None

    # 背景の解決
    resolved["background"] = _resolve_background(
        design.get("background"),
        palette,
        tone
    )

    # タイトルの解決
    if design.get("title") and design["title"].get("text"):
        resolved["title"] = _resolve_text_element(
            design["title"],
            layout,
            palette,
            tone,
            is_title=True
        )

    # サブタイトルの解決
    if design.get("subtitle") and design["subtitle"].get("text"):
        resolved["subtitle"] = _resolve_text_element(
            design["subtitle"],
            layout,
            palette,
            tone,
            is_title=False
        )

    # イラストの解決（配色を適用）
    if design.get("illustration"):
        resolved["illustration"] = _resolve_illustration(
            design["illustration"],
            palette,
            layout
        )

    # presetセクションは削除（解決済み）
    if "preset" in resolved:
        del resolved["preset"]

    return resolved


def _resolve_background(
    background: Optional[dict],
    palette: dict,
    tone: Optional[dict]
) -> dict:
    """背景設定を解決"""
    if background is None:
        background = {}

    result = background.copy()

    # promptが未指定または空の場合、パレットのヒントを使用
    if not result.get("prompt"):
        hint = palette.get("background_prompt_hint", "")
        if tone:
            hint += f", {tone.get('reasoning_hint', '')}"
        result["prompt"] = hint

    return result


def _resolve_text_element(
    element: dict,
    layout: dict,
    palette: dict,
    tone: Optional[dict],
    is_title: bool = True
) -> dict:
    """テキスト要素（タイトル/サブタイトル）を解決"""
    result = element.copy()

    # 座標の解決（明示的に指定されていない場合のみ）
    if "x" not in result or result.get("x") is None:
        result["x"] = layout["title_x"] if is_title else layout["subtitle_x"]

    if "y" not in result or result.get("y") is None:
        result["y"] = layout["title_y"] if is_title else layout["subtitle_y"]

    # 色の解決（明示的に指定されていない場合のみ）
    if "color" not in result or result.get("color") is None:
        if is_title:
            result["color"] = palette["text_primary"]
        else:
            result["color"] = palette["text_secondary"]

    # フォントウェイトの解決（トーンがある場合）
    if tone and ("fontWeight" not in result or result.get("fontWeight") is None):
        if is_title:
            result["fontWeight"] = tone.get("font_weight_title", "bold")
        else:
            result["fontWeight"] = tone.get("font_weight_subtitle", "normal")

    # スタイルの解決（明示的に指定されていない場合、パレットの推奨スタイルから選択）
    if "style" not in result or result.get("style") is None:
        recommended = palette.get("recommended_styles", ["flat"])
        # タイトルには最初の推奨スタイル、サブタイトルはflatを使用
        result["style"] = recommended[0] if is_title else "flat"

    # fillのグラデーション色をアクセント色で補完
    if result.get("fill") and isinstance(result["fill"], dict):
        fill = result["fill"].copy()
        if fill.get("type") == "gradient":
            # 開始色・終了色が未指定の場合、パレットから補完
            if not fill.get("start"):
                fill["start"] = palette["accent"]
            if not fill.get("end"):
                fill["end"] = palette["text_primary"]
        result["fill"] = fill

    return result


def _resolve_illustration(
    illustration: dict,
    palette: dict,
    layout: dict
) -> dict:
    """イラスト設定を解決"""
    if illustration is None:
        return None

    result = illustration.copy()

    # fillの色解決
    if result.get("fill"):
        fill = result["fill"].copy()
        if fill.get("type") == "solid" and not fill.get("color"):
            fill["color"] = palette["accent"]
        elif fill.get("type") == "gradient":
            if not fill.get("start"):
                fill["start"] = palette["accent"]
            if not fill.get("end"):
                fill["end"] = palette["text_secondary"]
        result["fill"] = fill

    return result


def suggest_presets_for_prompt(user_prompt: str) -> dict:
    """
    ユーザープロンプトから推奨プリセットを提案する

    Args:
        user_prompt: ユーザーの自然言語指示

    Returns:
        dict: 推奨プリセット {"layout": ..., "palette": ..., "tone": ...}
    """
    prompt_lower = user_prompt.lower()

    # トーンの推定
    tone = "professional"  # デフォルト

    tone_keywords = {
        "tech": ["テック", "技術", "ai", "tech", "digital", "デジタル", "未来", "future", "cyber", "サイバー"],
        "premium": ["高級", "ラグジュアリー", "premium", "luxury", "エレガント", "elegant", "上質"],
        "creative": ["クリエイティブ", "アート", "creative", "art", "デザイン", "独創"],
        "minimal": ["ミニマル", "シンプル", "minimal", "simple", "余白"],
        "energetic": ["エネルギー", "活発", "ダイナミック", "energy", "dynamic", "bold"],
        "warm": ["温かい", "warm", "親しみ", "friendly", "柔らか"],
        "cool": ["クール", "cool", "洗練", "知的", "intellectual"],
        "nature": ["自然", "nature", "エコ", "eco", "オーガニック", "organic", "緑"],
        "playful": ["楽しい", "fun", "カジュアル", "casual", "遊び"],
    }

    for tone_name, keywords in tone_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            tone = tone_name
            break

    # トーンから推奨を取得
    tone_preset = get_tone(tone)

    # 推奨からランダムではなく最初のものを選択
    recommended_layouts = tone_preset["recommended_layouts"]
    recommended_palettes = tone_preset["recommended_palettes"]

    return {
        "layout": recommended_layouts[0] if recommended_layouts else "center",
        "palette": recommended_palettes[0] if recommended_palettes else "light",
        "tone": tone
    }


def get_prompt_for_preset_selection() -> str:
    """
    LLMがプリセットを選択するためのプロンプト文字列を生成

    Returns:
        str: プリセット選択用のシステムプロンプト
    """
    lines = []

    lines.append("## 利用可能なプリセット\n")

    lines.append("### レイアウト (layout)")
    lines.append("| 名前 | 説明 |")
    lines.append("|------|------|")
    layout_descriptions = {
        "center": "中央配置（デフォルト）",
        "center-middle": "中央・垂直中央（インパクト重視）",
        "left": "左寄せ（右に余白）",
        "right": "右寄せ（左に余白）",
        "bottom": "下部配置（背景重視）",
        "top": "上部配置",
        "split-left": "左半分にテキスト（50:50分割）",
        "split-right": "右半分にテキスト（50:50分割）",
        "bottom-left": "左下配置",
        "bottom-right": "右下配置",
        "overlay": "オーバーレイ（背景画像の上）",
    }
    for name in LAYOUTS.keys():
        desc = layout_descriptions.get(name, "")
        lines.append(f"| `{name}` | {desc} |")

    lines.append("\n### 配色パレット (palette)")
    lines.append("| 名前 | 背景 | 推奨用途 |")
    lines.append("|------|------|----------|")
    palette_descriptions = {
        "light": "明るい背景、ビジネス向け",
        "light-warm": "温かみのある明るい背景",
        "light-cool": "クールな明るい背景",
        "dark": "暗い背景、モダン",
        "dark-tech": "テック風ダーク（サイバー）",
        "dark-purple": "紫系ダーク（クリエイティブ）",
        "monochrome": "モノクローム（ミニマル）",
        "monochrome-dark": "ダークモノクローム",
        "premium-gold": "ゴールド系高級感",
        "premium-silver": "シルバー系高級感",
        "vibrant": "ビビッド（エネルギッシュ）",
        "vibrant-gradient": "グラデーション背景",
        "nature": "自然・エコ系",
        "ocean": "海・青系",
        "corporate": "企業向け",
        "corporate-dark": "企業向けダーク",
    }
    for name, palette in PALETTES.items():
        desc = palette_descriptions.get(name, "")
        lines.append(f"| `{name}` | {palette['background']} | {desc} |")

    lines.append("\n### トーン (tone)")
    lines.append("| 名前 | 説明 |")
    lines.append("|------|------|")
    for name, tone in TONES.items():
        lines.append(f"| `{name}` | {tone['description']} |")

    return "\n".join(lines)
