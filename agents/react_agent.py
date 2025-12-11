"""
ReAct Designer Agent
思考(Thought) → 行動(Action) → 観察(Observation) のループで
自律的にツールを選択・実行するエージェント
"""

import os
import json
import base64
import re
import io
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool as GeminiTool
from PIL import Image

# ツール
from .tools.text_to_image import generate_image
from .tools.image_to_pptx import image_to_pptx
from .tools.design_references import search_references, get_reference_image

# プリセット
from .preset_resolver import resolve_presets

# トレーシング
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from langfuse.tracing import AgentTracer, estimate_tokens

# .env.local を読み込み
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

# 出力ディレクトリ
AGENT_OUTPUT_DIR = Path(__file__).parent.parent / "agent_output"

# モデル
AGENT_MODEL = "gemini-3-pro-preview"

# ReActシステムプロンプト
REACT_SYSTEM_PROMPT = """あなたはプロフェッショナルなスライドデザイナーエージェントです。
ユーザーの指示に基づいて、高品質なスライドを作成します。

## 動作方式: ReAct (Reasoning + Acting)

以下のループで動作します：
1. Thought: 現状を分析し、次に何をすべきか考える
2. Action: ツールを実行する
3. Observation: ツールの結果を確認する
4. (繰り返し)
5. Final Answer: 最終結果を出力

## 利用可能なツール

### 1. web_search
最新のデザイントレンドや参考情報をWeb検索する。
- 使用場面: トレンド調査が必要な時、特定の業界スタイルを調べたい時
- 不要な場面: シンプルな指示で十分な情報がある時
```
Action: web_search
Action Input: {"query": "2025年 SNS広告 デザイントレンド"}
```

### 2. reference_search
内部データセットから参考デザインを検索する。
- 使用場面: 類似デザインを参考にしたい時
- パラメータ: category, taste, palette
```
Action: reference_search
Action Input: {"category": "SNS広告バナー", "taste": ["かっこいい", "高級感"], "palette": ["ブルー"]}
```

### 3. design
デザイン設計JSONを生成する。
- 必須: 必ず実行する
- reasoning: これまでの思考・調査結果をまとめる
```
Action: design
Action Input: {"user_prompt": "ユーザーの元の指示", "reasoning": "これまでの分析結果"}
```

### 4. generate
設計JSONに基づいて画像生成・PPTX作成を実行する。
- 必須: designの後に必ず実行する
```
Action: generate
Action Input: {"design": {設計JSON}}
```

### 5. ask_feedback
ユーザーにフィードバックを聞く。
- 使用場面: 生成完了後、ユーザーの確認を得たい時
- 必須: generate後に必ず実行する
```
Action: ask_feedback
Action Input: {"question": "生成結果を確認してください。修正点はありますか？"}
```

### 6. regenerate_background
背景画像のみを再生成する（人物の位置、背景の色調などの修正）。
- 使用場面: ユーザーから画像に関するフィードバックがあった時
- feedbackにユーザーの修正指示を含める
```
Action: regenerate_background
Action Input: {"feedback": "人物をもっと大きく表示して"}
```

### 7. update_text
テキスト要素を修正する（内容、色、サイズなど）。
- 使用場面: ユーザーからテキストに関するフィードバックがあった時
- element_idで対象を指定、changesに変更内容を指定
```
Action: update_text
Action Input: {"element_id": "headline-2", "changes": {"content": "AIドリブン", "color": "#3B82F6"}}
```

## 出力フォーマット

必ず以下の形式で出力してください：

```
Thought: [現状の分析と次のアクションの理由]
Action: [ツール名]
Action Input: [JSON形式のパラメータ]
```

または最終結果の場合：

```
Thought: [完了の確認]
Final Answer: [ユーザーへの最終回答]
```

## 重要なルール

1. **不要なツールは使わない**: シンプルな指示なら web_search は不要
2. **design → generate → ask_feedback の順序**: 必ずこの順で実行
3. **1回のレスポンスで1アクションのみ**: 複数アクションを同時に実行しない
4. **日本語で思考**: Thoughtは日本語で書く
5. **フィードバックループ**: ユーザーが「OK」「問題ない」等と言うまで ask_feedback を繰り返す
6. **修正の使い分け**: 画像の修正は regenerate_background、テキストの修正は update_text

## デザイン設計の指針

- 要素は **background（1枚の完成画像）** と **text（編集可能テキスト）** の2種類のみ
- 人物・イラスト・装飾は**すべてbackgroundに含める**
- 切り抜き感、貼り付け感は絶対NG
- テキスト色は配色パレットを活用（白一色は避ける）
- シンプルさが正義。余白を活かす。
"""

# デザイン生成用プロンプト（design アクション用）
DESIGN_PROMPT = """以下の情報に基づいて、スライド設計JSONを生成してください。

## ユーザーの指示
{user_prompt}

## これまでの分析
{reasoning}

## 参照画像の情報
{reference_info}

## JSON形式

```json
{{
  "meta": {{
    "theme": "テーマ名",
    "mood": "雰囲気",
    "color_scheme": {{
      "primary": "#主要色",
      "secondary": "#補助色",
      "accent": "#アクセント色",
      "background": "#背景色"
    }}
  }},
  "elements": [
    {{
      "type": "background",
      "prompt": "完成形の画像を叙述的に描写。人物や装飾もここに含める。",
      "style": {{
        "lighting": "照明",
        "color_tone": "色調",
        "texture": "質感"
      }}
    }},
    {{
      "type": "text",
      "id": "一意のID",
      "content": "表示するテキスト",
      "position": {{"x": 100, "y": 400, "width": 800, "height": 150}},
      "style": {{
        "fontSize": 72,
        "fontWeight": "bold",
        "color": "#色",
        "align": "left"
      }}
    }}
  ]
}}
```

## ルール
1. 要素はbackgroundとtextのみ
2. 人物・イラスト・装飾はbackgroundに含める（1枚絵として生成）
3. テキスト色は配色パレットを活用（白一色は避ける）
4. 切り抜き感、貼り付け感は絶対NG

JSONのみを出力してください。
"""


class ReActDesignerAgent:
    """ReAct方式で動作するデザイナーエージェント"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_tracing: bool = True
    ):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or ""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        self.client = genai.Client(api_key=self.api_key)
        self.session_id = session_id or self._generate_session_id()
        self.conversation_history: List[Dict[str, str]] = []
        self.tools_executed: List[Dict[str, Any]] = []

        # 参照画像（スタイル参考用）
        self.reference_image_base64: Optional[str] = None

        # トレーシング
        self.tracer = AgentTracer(
            session_id=self.session_id,
            enabled=enable_tracing
        )

    def _generate_session_id(self) -> str:
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=4)) + '-' + ''.join(random.choices(string.digits, k=4))

    def _get_output_dir(self) -> Path:
        output_dir = AGENT_OUTPUT_DIR / self.session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_image(self, image_base64: str, filename: str) -> str:
        output_dir = self._get_output_dir()
        output_path = output_dir / f"{filename}.png"
        image_data = base64.b64decode(image_base64)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        return str(output_path)

    def _parse_action(self, response_text: str) -> Dict[str, Any]:
        """レスポンスからAction/Action Inputをパース"""
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "final_answer": None
        }

        # Thoughtを抽出
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Final Answer:|$)', response_text, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Final Answerを抽出
        final_match = re.search(r'Final Answer:\s*(.+?)$', response_text, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Actionを抽出
        action_match = re.search(r'Action:\s*(\w+)', response_text)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # Action Inputを抽出
        input_match = re.search(r'Action Input:\s*(\{.+?\}|\{[\s\S]+?\n\})', response_text, re.DOTALL)
        if input_match:
            try:
                result["action_input"] = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                # JSONパースに失敗した場合、より緩い抽出を試みる
                input_text = input_match.group(1)
                # 改行を含むJSONの場合
                try:
                    result["action_input"] = json.loads(input_text.replace('\n', ''))
                except:
                    result["action_input"] = {"raw": input_text}

        return result

    def _execute_tool(self, action: str, action_input: Dict[str, Any]) -> str:
        """ツールを実行して結果を返す"""
        print(f"    [Tool] {action}")

        # スパン開始
        span_id = self.tracer.start_span(
            name=f"tool_{action}",
            span_type="tool",
            input_data={"action": action, "input": action_input}
        )

        result = ""
        try:
            if action == "web_search":
                result = self._tool_web_search(action_input)
            elif action == "reference_search":
                result = self._tool_reference_search(action_input)
            elif action == "design":
                result = self._tool_design(action_input)
            elif action == "generate":
                result = self._tool_generate(action_input)
            elif action == "ask_feedback":
                result = self._tool_ask_feedback(action_input)
            elif action == "regenerate_background":
                result = self._tool_regenerate_background(action_input)
            elif action == "update_text":
                result = self._tool_update_text(action_input)
            else:
                result = f"Error: Unknown tool '{action}'"
        except Exception as e:
            result = f"Error: {str(e)}"
        finally:
            # スパン終了
            self.tracer.end_span(span_id, output_data=result[:500])

        return result

    def _tool_web_search(self, params: Dict[str, Any]) -> str:
        """Web検索ツール"""
        query = params.get("query", "")
        if not query:
            return "Error: query is required"

        try:
            # Google Search を使用
            config = GenerateContentConfig(
                tools=[GeminiTool(google_search=GoogleSearch())]
            )

            prompt = f"以下について検索して、デザインに役立つ情報をまとめてください：\n{query}"

            response = self.client.models.generate_content(
                model=AGENT_MODEL,
                contents=[prompt],
                config=config
            )

            result_text = response.text or ""
            if not result_text:
                return "検索結果なし"

            # グラウンディング情報を抽出
            sources = []
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                if metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks[:3]:
                        if chunk.web:
                            sources.append(f"- {chunk.web.title}: {chunk.web.uri}")

            result = result_text[:1000]  # 長すぎる場合は切り詰め
            if sources:
                result += "\n\n参照ソース:\n" + "\n".join(sources)

            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def _tool_reference_search(self, params: Dict[str, Any]) -> str:
        """参照デザイン検索ツール"""
        category = params.get("category")
        taste = params.get("taste", [])
        palette = params.get("palette", [])

        result = search_references(
            category=category,
            taste=taste,
            palette=palette,
            limit=3
        )

        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"

        references = result.get("references", [])
        if not references:
            return "該当する参照デザインが見つかりませんでした。"

        # 結果をフォーマット
        lines = [f"見つかった参照デザイン: {len(references)}件\n"]
        for ref in references:
            lines.append(f"- **{ref.get('category')}** ({ref.get('id')})")
            lines.append(f"  テイスト: {', '.join(ref.get('taste', []))}")
            lines.append(f"  配色: {', '.join(ref.get('palette', []))}")
            lines.append(f"  コメント: {ref.get('comment', '')}")
            if ref.get('features'):
                lines.append(f"  特徴: {json.dumps(ref.get('features'), ensure_ascii=False)}")
            lines.append("")

        return "\n".join(lines)

    def _tool_design(self, params: Dict[str, Any]) -> str:
        """デザイン設計ツール"""
        user_prompt = params.get("user_prompt", "")
        reasoning = params.get("reasoning", "")

        # 参照画像情報
        reference_info = "なし"
        if self.reference_image_base64:
            reference_info = "参照画像あり（スタイル参考として使用）"

        # 設計プロンプトを構築
        design_prompt = DESIGN_PROMPT.format(
            user_prompt=user_prompt,
            reasoning=reasoning,
            reference_info=reference_info
        )

        contents = [design_prompt]

        # 参照画像がある場合は追加
        if self.reference_image_base64:
            try:
                image_bytes = base64.b64decode(self.reference_image_base64)
                pil_image = Image.open(io.BytesIO(image_bytes))
                contents.append(pil_image)
            except Exception as e:
                print(f"    Warning: Failed to load reference image: {e}")

        try:
            response = self.client.models.generate_content(
                model=AGENT_MODEL,
                contents=contents
            )

            text = response.text or ""

            # JSONを抽出
            json_match = re.search(r'\{[\s\S]*\}', text)
            if not json_match:
                return f"Error: Failed to parse design JSON: {text[:200]}"

            design_json = json.loads(json_match.group())

            # プリセット解決
            resolved_design = resolve_presets(design_json)

            # 設計を保存
            self._current_design = resolved_design

            # 設計を保存（ファイル）
            output_dir = self._get_output_dir()
            design_path = output_dir / "design.json"
            with open(design_path, 'w', encoding='utf-8') as f:
                json.dump(resolved_design, f, ensure_ascii=False, indent=2)

            return f"設計JSON生成完了。\n{json.dumps(resolved_design, ensure_ascii=False, indent=2)[:1500]}"

        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n{traceback.format_exc()}"

    def _tool_generate(self, params: Dict[str, Any]) -> str:
        """画像生成・PPTX作成ツール"""
        design = params.get("design") or getattr(self, '_current_design', None)

        if not design:
            return "Error: design is required. Run 'design' action first."

        elements = design.get("elements", [])
        meta = design.get("meta", {})
        color_scheme = meta.get("color_scheme", {})

        pptx_elements = []
        steps = []

        for i, elem in enumerate(elements):
            elem_type = elem.get("type")
            elem_id = elem.get("id", f"{elem_type}_{i}")

            if elem_type == "background":
                prompt = elem.get("prompt", "")
                style = elem.get("style", {})

                if prompt:
                    # スタイル説明を構築
                    style_parts = []
                    if style.get("lighting"):
                        style_parts.append(f"Lighting: {style['lighting']}")
                    if style.get("color_tone"):
                        style_parts.append(f"Color tone: {style['color_tone']}")
                    if style.get("texture"):
                        style_parts.append(f"Texture: {style['texture']}")
                    style_desc = ". ".join(style_parts)

                    # 参照画像をスタイル参照として使用
                    reference_images = None
                    if self.reference_image_base64:
                        reference_images = [self.reference_image_base64]

                    result = generate_image(
                        prompt=prompt,
                        reference_images=reference_images,
                        style_description=style_desc,
                        aspect_ratio="16:9",
                        image_size="2K",
                        no_text=True
                    )

                    if result.get("success"):
                        bg_path = self._save_image(result["image_base64"], "background")
                        pptx_elements.append({
                            "id": elem_id,
                            "type": "background",
                            "image_base64": result["image_base64"],
                            "file_path": bg_path
                        })
                        steps.append(f"背景画像生成: {bg_path}")
                    else:
                        steps.append(f"背景生成失敗: {result.get('error')}")

            elif elem_type == "text":
                content = elem.get("content", "")
                position = elem.get("position", {})
                style = elem.get("style", {})

                if content:
                    pptx_elements.append({
                        "id": elem_id,
                        "type": "text",
                        "content": content,
                        "bbox": {
                            "x": position.get("x", 960),
                            "y": position.get("y", 400),
                            "width": position.get("width", 1600),
                            "height": position.get("height", 100)
                        },
                        "style": {
                            "fontSize": style.get("fontSize", 48),
                            "fontWeight": style.get("fontWeight", "normal"),
                            "fontStyle": style.get("fontStyle", "normal"),
                            "color": style.get("color", "#FFFFFF"),
                            "align": style.get("align", "center")
                        }
                    })
                    steps.append(f"テキスト追加: {content[:30]}...")

        # PPTX生成
        pptx_result = image_to_pptx(
            elements=pptx_elements,
            session_id=self.session_id
        )

        if pptx_result.get("success"):
            pptx_path = pptx_result["file_path"]
            steps.append(f"PPTX生成完了: {pptx_path}")

            # 結果を保存
            self._result = {
                "success": True,
                "pptx_path": pptx_path,
                "background_path": pptx_elements[0].get("file_path") if pptx_elements else None,
                "steps": steps
            }

            # pptx_elementsも保存（update_text用）
            self._pptx_elements = pptx_elements

            return f"生成完了!\n- PPTX: {pptx_path}\n- ステップ: {len(steps)}件"
        else:
            return f"Error: PPTX生成失敗 - {pptx_result.get('error')}"

    def _tool_ask_feedback(self, params: Dict[str, Any]) -> str:
        """ユーザーにフィードバックを聞くツール"""
        question = params.get("question", "生成結果を確認してください。修正点はありますか？")

        print(f"\n{'='*50}")
        print(f"[Agent] {question}")
        print(f"{'='*50}")

        # 現在の結果を表示
        if self._result:
            if self._result.get("pptx_path"):
                print(f"PPTX: {self._result['pptx_path']}")
            if self._result.get("background_path"):
                print(f"背景画像: {self._result['background_path']}")

        print("\nフィードバックを入力してください（OKなら「OK」と入力）:")
        try:
            feedback = input("> ").strip()
        except EOFError:
            feedback = "OK"

        if not feedback:
            feedback = "OK"

        # フィードバックを保存
        self._last_feedback = feedback

        return f"ユーザーのフィードバック: {feedback}"

    def _tool_regenerate_background(self, params: Dict[str, Any]) -> str:
        """背景画像を再生成するツール"""
        feedback = params.get("feedback", "")

        if not self._current_design:
            return "Error: デザインがありません。先にdesignを実行してください。"

        # 現在の背景プロンプトを取得
        elements = self._current_design.get("elements", [])
        background_elem = None
        for elem in elements:
            if elem.get("type") == "background":
                background_elem = elem
                break

        if not background_elem:
            return "Error: 背景要素が見つかりません。"

        # フィードバックを反映した新しいプロンプトを生成
        original_prompt = background_elem.get("prompt", "")
        style = background_elem.get("style", {})

        # LLMにプロンプト修正を依頼
        modify_prompt = f"""以下の背景画像生成プロンプトを、ユーザーのフィードバックに基づいて修正してください。

## 元のプロンプト
{original_prompt}

## ユーザーのフィードバック
{feedback}

## 指示
- フィードバックを反映した新しいプロンプトを出力してください
- プロンプトのみを出力（説明不要）
- 英語で出力
"""

        try:
            response = self.client.models.generate_content(
                model=AGENT_MODEL,
                contents=[modify_prompt]
            )
            new_prompt = response.text.strip()
        except Exception as e:
            return f"Error: プロンプト修正に失敗 - {str(e)}"

        # スタイル説明を構築
        style_parts = []
        if style.get("lighting"):
            style_parts.append(f"Lighting: {style['lighting']}")
        if style.get("color_tone"):
            style_parts.append(f"Color tone: {style['color_tone']}")
        if style.get("texture"):
            style_parts.append(f"Texture: {style['texture']}")
        style_desc = ". ".join(style_parts)

        # 参照画像
        reference_images = None
        if self.reference_image_base64:
            reference_images = [self.reference_image_base64]

        # 再生成
        print(f"    背景を再生成中...")
        result = generate_image(
            prompt=new_prompt,
            reference_images=reference_images,
            style_description=style_desc,
            aspect_ratio="16:9",
            image_size="2K",
            no_text=True
        )

        if not result.get("success"):
            return f"Error: 背景再生成に失敗 - {result.get('error')}"

        # 新しい背景を保存
        bg_path = self._save_image(result["image_base64"], "background_v2")

        # デザインを更新
        background_elem["prompt"] = new_prompt

        # pptx_elementsを更新
        if hasattr(self, '_pptx_elements'):
            for elem in self._pptx_elements:
                if elem.get("type") == "background":
                    elem["image_base64"] = result["image_base64"]
                    elem["file_path"] = bg_path
                    break

        # PPTXを再生成
        pptx_result = image_to_pptx(
            elements=self._pptx_elements,
            session_id=self.session_id
        )

        if pptx_result.get("success"):
            pptx_path = pptx_result["file_path"]
            self._result = {
                "success": True,
                "pptx_path": pptx_path,
                "background_path": bg_path,
                "steps": ["背景再生成", "PPTX再生成"]
            }
            return f"背景を再生成しました!\n- 新しい背景: {bg_path}\n- PPTX: {pptx_path}"
        else:
            return f"Error: PPTX再生成に失敗 - {pptx_result.get('error')}"

    def _tool_update_text(self, params: Dict[str, Any]) -> str:
        """テキスト要素を更新するツール"""
        element_id = params.get("element_id")
        changes = params.get("changes", {})

        if not element_id:
            return "Error: element_id is required"

        if not hasattr(self, '_pptx_elements') or not self._pptx_elements:
            return "Error: 要素がありません。先にgenerateを実行してください。"

        # 対象要素を探す
        target_elem = None
        for elem in self._pptx_elements:
            if elem.get("id") == element_id and elem.get("type") == "text":
                target_elem = elem
                break

        if not target_elem:
            # 利用可能なテキスト要素をリスト
            text_ids = [e.get("id") for e in self._pptx_elements if e.get("type") == "text"]
            return f"Error: テキスト要素 '{element_id}' が見つかりません。\n利用可能なID: {text_ids}"

        # 変更を適用
        if "content" in changes:
            target_elem["content"] = changes["content"]
        if "color" in changes:
            target_elem["style"]["color"] = changes["color"]
        if "fontSize" in changes:
            target_elem["style"]["fontSize"] = changes["fontSize"]
        if "fontWeight" in changes:
            target_elem["style"]["fontWeight"] = changes["fontWeight"]
        if "align" in changes:
            target_elem["style"]["align"] = changes["align"]

        # デザインJSONも更新
        if self._current_design:
            for elem in self._current_design.get("elements", []):
                if elem.get("id") == element_id and elem.get("type") == "text":
                    if "content" in changes:
                        elem["content"] = changes["content"]
                    if "style" not in elem:
                        elem["style"] = {}
                    for key in ["color", "fontSize", "fontWeight", "align"]:
                        if key in changes:
                            elem["style"][key] = changes[key]
                    break

        # PPTXを再生成
        pptx_result = image_to_pptx(
            elements=self._pptx_elements,
            session_id=self.session_id
        )

        if pptx_result.get("success"):
            pptx_path = pptx_result["file_path"]
            self._result["pptx_path"] = pptx_path
            return f"テキストを更新しました!\n- 対象: {element_id}\n- 変更: {changes}\n- PPTX: {pptx_path}"
        else:
            return f"Error: PPTX再生成に失敗 - {pptx_result.get('error')}"

    def run(
        self,
        user_prompt: str,
        reference_image_base64: Optional[str] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        ReActループを実行

        Args:
            user_prompt: ユーザーの指示
            reference_image_base64: 参照画像（スタイル参考用）
            max_iterations: 最大イテレーション数

        Returns:
            dict: 実行結果
        """
        self.reference_image_base64 = reference_image_base64
        self.conversation_history = []
        self.tools_executed = []
        self._current_design = None
        self._result = None

        # トレース開始
        self.tracer.start_trace(
            name="ReActDesignerAgent",
            input_data={"user_prompt": user_prompt, "has_reference": reference_image_base64 is not None}
        )

        # 初期プロンプト
        initial_prompt = f"{REACT_SYSTEM_PROMPT}\n\n## ユーザーの指示\n{user_prompt}"
        if reference_image_base64:
            initial_prompt += "\n\n（参照画像が提供されています。スタイルの参考にしてください）"

        self.conversation_history.append({
            "role": "user",
            "content": initial_prompt
        })

        print(f"\n[ReAct Agent] Session: {self.session_id}")
        print(f"[User] {user_prompt[:100]}...")

        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")

            # LLMスパン開始
            llm_span_id = self.tracer.start_span(
                name=f"llm_iteration_{iteration + 1}",
                span_type="llm",
                input_data={"iteration": iteration + 1, "history_length": len(self.conversation_history)}
            )

            # 入力トークン数を推定
            input_text = "\n".join([msg["content"] for msg in self.conversation_history])
            input_tokens = estimate_tokens(input_text)

            # モデルに問い合わせ
            try:
                response = self.client.models.generate_content(
                    model=AGENT_MODEL,
                    contents=[msg["content"] for msg in self.conversation_history]
                )
                response_text = response.text or ""

                # 出力トークン数を推定
                output_tokens = estimate_tokens(response_text)

                # LLMスパン終了
                self.tracer.end_span(
                    llm_span_id,
                    output_data=response_text[:500],
                    model=AGENT_MODEL,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )

            except Exception as e:
                self.tracer.end_span(llm_span_id, output_data=f"Error: {str(e)}")
                print(f"  [Error] Model call failed: {e}")

                # トレース終了
                summary = self.tracer.end_trace({"success": False, "error": str(e)})
                self.tracer.print_summary()

                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id,
                    "tracing_summary": summary
                }

            # レスポンスをパース
            parsed = self._parse_action(response_text)

            print(f"  [Thought] {parsed['thought'][:200]}..." if parsed['thought'] else "  [Thought] (none)")

            # Final Answerの場合は終了
            if parsed["final_answer"]:
                print(f"  [Final Answer] {parsed['final_answer'][:200]}...")

                # トレース終了
                summary = self.tracer.end_trace({
                    "success": True,
                    "final_answer": parsed["final_answer"][:500],
                    "iterations": iteration + 1
                })
                self.tracer.print_summary()

                return {
                    "success": True,
                    "session_id": self.session_id,
                    "final_answer": parsed["final_answer"],
                    "tools_executed": self.tools_executed,
                    "result": self._result,
                    "iterations": iteration + 1,
                    "tracing_summary": summary
                }

            # アクションがない場合
            if not parsed["action"]:
                print("  [Warning] No action found, prompting for action...")
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })
                self.conversation_history.append({
                    "role": "user",
                    "content": "アクションを実行してください。Action: と Action Input: を指定してください。"
                })
                continue

            # ツールを実行
            action = parsed["action"]
            action_input = parsed["action_input"] or {}

            print(f"  [Action] {action}")
            print(f"  [Input] {json.dumps(action_input, ensure_ascii=False)[:200]}...")

            observation = self._execute_tool(action, action_input)

            print(f"  [Observation] {observation[:200]}...")

            # 履歴に追加
            self.tools_executed.append({
                "action": action,
                "input": action_input,
                "observation": observation[:500]
            })

            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            self.conversation_history.append({
                "role": "user",
                "content": f"Observation: {observation}"
            })

        # 最大イテレーション到達
        summary = self.tracer.end_trace({
            "success": False,
            "error": "Max iterations reached",
            "iterations": max_iterations
        })
        self.tracer.print_summary()

        return {
            "success": False,
            "error": "Max iterations reached",
            "session_id": self.session_id,
            "tools_executed": self.tools_executed,
            "tracing_summary": summary
        }


def main():
    """テスト用エントリーポイント"""
    import sys

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY が設定されていません")
        sys.exit(1)

    agent = ReActDesignerAgent()
    print(f"Session ID: {agent.session_id}")

    # 参照画像入力
    print("\n参照画像のパスを入力 (空でスキップ):")
    image_input = input("> ").strip().strip("'\"")

    reference_image = None
    if image_input and os.path.exists(image_input):
        with open(image_input, 'rb') as f:
            reference_image = base64.b64encode(f.read()).decode('utf-8')
        print(f"参照画像を読み込みました: {image_input}")

    # プロンプト入力
    print("\n" + "=" * 50)
    print("プロンプトを入力してください (空行で実行)")
    print("=" * 50 + "\n")

    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break

    user_prompt = "\n".join(lines)
    if not user_prompt.strip():
        print("プロンプトが空です。終了します。")
        sys.exit(0)

    # 実行
    result = agent.run(
        user_prompt=user_prompt,
        reference_image_base64=reference_image
    )

    print("\n" + "=" * 50)
    print("結果")
    print("=" * 50)

    if result.get("success"):
        print(f"成功! (イテレーション: {result.get('iterations')}回)")
        print(f"\nFinal Answer:\n{result.get('final_answer', '')}")

        if result.get("result"):
            r = result["result"]
            if r.get("pptx_path"):
                print(f"\nPPTX: {r['pptx_path']}")
            if r.get("background_path"):
                print(f"背景: {r['background_path']}")
    else:
        print(f"失敗: {result.get('error')}")

    print(f"\n実行したツール: {len(result.get('tools_executed', []))}件")
    for t in result.get("tools_executed", []):
        print(f"  - {t['action']}")


if __name__ == "__main__":
    main()
