"""
デザイン参照ツール
トレーニング画像データセットから参考デザインを検索・取得
将来的にはDBに移行予定
"""

import json
import base64
from pathlib import Path
from typing import Optional, List

# データセットのパス
DATASET_PATH = Path(__file__).parent.parent.parent / "traning-img" / "dataset.json"
IMAGES_DIR = Path(__file__).parent.parent.parent / "traning-img"


def _load_dataset() -> dict:
    """データセットを読み込む"""
    if not DATASET_PATH.exists():
        return {"images": [], "design_patterns": {}}

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_references(
    category: Optional[str] = None,
    taste: Optional[List[str]] = None,
    palette: Optional[List[str]] = None,
    limit: int = 5
) -> dict:
    """
    条件に合う参考デザインを検索

    Args:
        category: カテゴリ（商品サムネイル、技術資料サムネイル、SNS広告バナー等）
        taste: テイストタグのリスト（かっこいい、かわいい、高級感等）
        palette: 配色のリスト（ブルー、パープル、グラデーション等）
        limit: 取得件数

    Returns:
        dict: {
            "success": bool,
            "references": list,  # マッチした参照リスト
            "count": int
        }
    """
    try:
        dataset = _load_dataset()
        images = dataset.get("images", [])

        results = []

        for img in images:
            score = 0

            # カテゴリマッチ
            if category and category in img.get("category", ""):
                score += 10

            # テイストマッチ
            if taste:
                img_taste = img.get("taste", [])
                matches = len(set(taste) & set(img_taste))
                score += matches * 5

            # パレットマッチ
            if palette:
                img_palette = img.get("palette", [])
                matches = len(set(palette) & set(img_palette))
                score += matches * 3

            # スコアがあれば追加
            if score > 0 or (not category and not taste and not palette):
                results.append({
                    **img,
                    "_score": score
                })

        # スコア順にソート
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # スコアを削除してlimit件返す
        for r in results:
            r.pop("_score", None)

        return {
            "success": True,
            "references": results[:limit],
            "count": len(results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "references": []
        }


def get_design_patterns() -> dict:
    """
    デザインパターン一覧を取得

    Returns:
        dict: {
            "success": bool,
            "patterns": dict  # パターン名 -> 特徴
        }
    """
    try:
        dataset = _load_dataset()
        patterns = dataset.get("design_patterns", {})

        return {
            "success": True,
            "patterns": patterns
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "patterns": {}
        }


def get_reference_image(image_id: str, include_base64: bool = False) -> dict:
    """
    特定の参照画像の詳細を取得

    Args:
        image_id: 画像ID
        include_base64: Base64データを含めるか

    Returns:
        dict: {
            "success": bool,
            "image": dict,  # 画像情報
            "image_base64": str  # include_base64=Trueの場合
        }
    """
    try:
        dataset = _load_dataset()
        images = dataset.get("images", [])

        for img in images:
            if img.get("id") == image_id:
                result = {
                    "success": True,
                    "image": img
                }

                if include_base64:
                    img_path = IMAGES_DIR / img.get("filename", "")
                    if img_path.exists():
                        with open(img_path, "rb") as f:
                            result["image_base64"] = base64.b64encode(f.read()).decode()

                return result

        return {
            "success": False,
            "error": f"Image not found: {image_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_references_summary() -> str:
    """
    参照データセットのサマリーをテキストで取得（プロンプト用）

    Returns:
        str: サマリーテキスト
    """
    try:
        dataset = _load_dataset()
        images = dataset.get("images", [])
        patterns = dataset.get("design_patterns", {})

        lines = ["## 参照デザインパターン\n"]

        for pattern_name, pattern_info in patterns.items():
            palette = ", ".join(pattern_info.get("palette", []))
            features = ", ".join(pattern_info.get("features", []))
            lines.append(f"### {pattern_name}")
            lines.append(f"- 配色: {palette}")
            lines.append(f"- 特徴: {features}")
            lines.append("")

        lines.append("## 参照画像一覧\n")
        for img in images:
            taste = ", ".join(img.get("taste", [])[:3])
            lines.append(f"- **{img.get('category')}**: {taste} ({img.get('comment', '')})")

        return "\n".join(lines)

    except Exception:
        return ""
