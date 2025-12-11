"""
Langfuse トレーシングモジュール
ReActエージェントの実行をトレースし、コスト・トークン数を記録
"""

import os
import time
from typing import Optional, Dict, Any, List
from functools import wraps
from dotenv import load_dotenv

# .env.local を読み込み
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    # フォールバック: カレントディレクトリから探す
    load_dotenv(dotenv_path='.env.local', override=True)

# Langfuseのインポート
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    print("[Warning] Langfuse not installed. Tracing disabled.")


# Geminiモデルの料金（1M tokens あたりのUSD）
# https://ai.google.dev/pricing
GEMINI_PRICING = {
    "gemini-3-pro-preview": {
        "input": 1.25,   # $1.25 per 1M input tokens
        "output": 10.00  # $10.00 per 1M output tokens
    },
    "gemini-3-pro-image-preview": {
        "input": 1.25,
        "output": 10.00
    },
    "gemini-2.0-flash": {
        "input": 0.10,
        "output": 0.40
    }
}


class AgentTracer:
    """ReActエージェント用のトレーサー"""

    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        enabled: bool = True
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.enabled = enabled and LANGFUSE_AVAILABLE

        # 共通の初期化（enabled に関わらず必要）
        self._trace = None
        self._current_span = None
        self._spans = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0
        self.langfuse = None

        # Langfuseクライアント初期化
        if self.enabled:
            public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
            secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
            base_url = os.environ.get("LANGFUSE_URL", "https://cloud.langfuse.com")

            if not public_key or not secret_key:
                print(f"[Warning] Langfuse keys not found. PUBLIC_KEY: {'set' if public_key else 'missing'}, SECRET_KEY: {'set' if secret_key else 'missing'}")
                self.enabled = False
            else:
                try:
                    self.langfuse = Langfuse(
                        public_key=public_key,
                        secret_key=secret_key,
                        base_url=base_url
                    )
                    print(f"[Tracing] Langfuse initialized: {base_url}")
                except Exception as e:
                    print(f"[Warning] Langfuse initialization failed: {e}")
                    self.enabled = False

        # ローカル記録用
        self.events: List[Dict[str, Any]] = []

    def start_trace(self, name: str, input_data: Dict[str, Any]) -> None:
        """トレースを開始"""
        self.events.append({
            "type": "trace_start",
            "name": name,
            "input": input_data,
            "timestamp": time.time()
        })

        if not self.enabled:
            return

        try:
            self._trace = self.langfuse.trace(
                name=name,
                session_id=self.session_id,
                user_id=self.user_id,
                input=input_data,
                metadata={
                    "agent_type": "ReActDesignerAgent"
                }
            )
        except Exception as e:
            print(f"[Tracing] Error starting trace: {e}")

    def end_trace(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """トレースを終了し、サマリーを返す"""
        summary = {
            "session_id": self.session_id,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": round(self._total_cost, 6),
            "events_count": len(self.events)
        }

        self.events.append({
            "type": "trace_end",
            "output": output_data,
            "summary": summary,
            "timestamp": time.time()
        })

        if self.enabled and self._trace and self.langfuse:
            try:
                self._trace.update(
                    output=output_data,
                    metadata={
                        "total_tokens": summary["total_tokens"],
                        "total_input_tokens": summary["total_input_tokens"],
                        "total_output_tokens": summary["total_output_tokens"],
                        "total_cost_usd": summary["total_cost_usd"],
                        "events_count": summary["events_count"]
                    }
                )
                # フラッシュして送信
                self.langfuse.flush()
            except Exception as e:
                print(f"[Tracing] Error ending trace: {e}")

        return summary

    def start_span(
        self,
        name: str,
        span_type: str = "tool",
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """スパンを開始"""
        span_id = f"{name}_{len(self._spans)}"

        self.events.append({
            "type": "span_start",
            "span_id": span_id,
            "name": name,
            "span_type": span_type,
            "input": input_data,
            "timestamp": time.time()
        })

        if self.enabled and self._trace:
            try:
                if span_type == "llm":
                    self._current_span = self._trace.generation(
                        name=name,
                        input=input_data
                    )
                else:
                    self._current_span = self._trace.span(
                        name=name,
                        input=input_data
                    )
                self._spans.append({
                    "id": span_id,
                    "span": self._current_span,
                    "type": span_type
                })
            except Exception as e:
                print(f"[Tracing] Error starting span: {e}")

        return span_id

    def end_span(
        self,
        span_id: str,
        output_data: Optional[Any] = None,
        model: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> None:
        """スパンを終了"""
        # トークン数を加算
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        # コストを計算
        if model and model in GEMINI_PRICING:
            pricing = GEMINI_PRICING[model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            cost = input_cost + output_cost
            self._total_cost += cost
        else:
            cost = 0.0

        self.events.append({
            "type": "span_end",
            "span_id": span_id,
            "output": str(output_data)[:500] if output_data else None,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "timestamp": time.time()
        })

        if self.enabled:
            try:
                # 対応するスパンを探す
                for span_info in self._spans:
                    if span_info["id"] == span_id:
                        span = span_info["span"]
                        if span_info["type"] == "llm":
                            span.end(
                                output=output_data,
                                model=model,
                                usage={
                                    "input": input_tokens,
                                    "output": output_tokens,
                                    "total": input_tokens + output_tokens
                                }
                            )
                        else:
                            span.end(output=output_data)
                        break
            except Exception as e:
                print(f"[Tracing] Error ending span: {e}")

    def log_event(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """イベントをログ"""
        self.events.append({
            "type": "event",
            "name": name,
            "data": data,
            "timestamp": time.time()
        })

        if self.enabled and self._trace:
            try:
                self._trace.event(
                    name=name,
                    input=data
                )
            except Exception as e:
                print(f"[Tracing] Error logging event: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """現在のサマリーを取得"""
        return {
            "session_id": self.session_id,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": round(self._total_cost, 6),
            "events_count": len(self.events)
        }

    def print_summary(self) -> None:
        """サマリーを表示"""
        summary = self.get_summary()
        print("\n" + "=" * 50)
        print("📊 Tracing Summary")
        print("=" * 50)
        print(f"Session ID: {summary['session_id']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"  - Input:  {summary['total_input_tokens']:,}")
        print(f"  - Output: {summary['total_output_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost_usd']:.6f}")
        print(f"Events: {summary['events_count']}")
        if self.enabled:
            print(f"Langfuse: ✅ Enabled")
        else:
            print(f"Langfuse: ❌ Disabled")
        print("=" * 50)


def estimate_tokens(text: str) -> int:
    """テキストからトークン数を推定（簡易版）"""
    # 日本語は1文字≒1-2トークン、英語は1単語≒1トークン
    # 簡易的に文字数/3で推定
    if not text:
        return 0
    return max(1, len(text) // 3)


# シングルトンインスタンス（グローバルトレーサー）
_global_tracer: Optional[AgentTracer] = None


def get_tracer() -> Optional[AgentTracer]:
    """グローバルトレーサーを取得"""
    return _global_tracer


def set_tracer(tracer: AgentTracer) -> None:
    """グローバルトレーサーを設定"""
    global _global_tracer
    _global_tracer = tracer
