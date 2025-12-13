import { NextRequest } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

interface AgentRequest {
  prompt: string
  imageBase64?: string
  sessionId?: string
  feedback?: string  // フィードバック継続用
}

export async function POST(request: NextRequest) {
  const body: AgentRequest = await request.json()
  const { prompt, imageBase64, sessionId: existingSessionId, feedback } = body

  if (!prompt && !feedback) {
    return new Response(JSON.stringify({ error: 'Prompt or feedback is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  const projectRoot = path.resolve(process.cwd())

  // ストリーミングレスポンスを設定
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Python agentをサブプロセスとして実行
        const pythonScript = `
import sys
import os
import json
import base64

# プロジェクトルートをパスに追加
sys.path.insert(0, '${projectRoot}')
os.chdir('${projectRoot}')

# .env.localを読み込み
from dotenv import load_dotenv
load_dotenv('${projectRoot}/.env.local')

from agents.react_agent import ReActDesignerAgent

# 入力を受け取る
input_data = json.loads(sys.stdin.read())

user_prompt = input_data.get('prompt', '')
image_base64 = input_data.get('image_base64')
session_id = input_data.get('session_id')

# エージェントを初期化
agent = ReActDesignerAgent(
    session_id=session_id,
    enable_tracing=True
)

# セッション開始イベント
print(json.dumps({'type': 'session_start', 'sessionId': agent.session_id}), flush=True)

# ツール実行をフックするためのモンキーパッチ
original_execute_tool = agent._execute_tool

def hooked_execute_tool(action, action_input):
    # ツール開始イベント
    print(json.dumps({
        'type': 'tool_start',
        'tool': action,
        'input': str(action_input)[:200]
    }), flush=True)

    result = original_execute_tool(action, action_input)

    # ツール終了イベント
    status = 'error' if result.startswith('Error:') else 'completed'
    print(json.dumps({
        'type': 'tool_end',
        'tool': action,
        'status': status,
        'result': result[:300]
    }), flush=True)

    return result

agent._execute_tool = hooked_execute_tool

# Thoughtをキャプチャするためのフック
original_parse = agent._parse_action

def hooked_parse(response_text):
    parsed = original_parse(response_text)
    if parsed.get('thought'):
        print(json.dumps({
            'type': 'thought',
            'content': parsed['thought'][:500]
        }), flush=True)
    return parsed

agent._parse_action = hooked_parse

# フィードバックツールをオーバーライド（Web UIではフィードバック待ちイベントを送信）
def web_ask_feedback(params):
    question = params.get('question', '生成結果を確認してください。修正点はありますか？')

    # フィードバック待ちイベントを送信
    print(json.dumps({
        'type': 'waiting_feedback',
        'question': question,
        'pptxPath': agent._result.get('pptx_path') if agent._result else None,
        'backgroundPath': agent._result.get('background_path') if agent._result else None
    }), flush=True)

    # Web UIでは自動的にOKで継続（後でフィードバック機能を追加可能）
    return "ユーザーのフィードバック: OK"

agent._tool_ask_feedback = web_ask_feedback

# 実行
result = agent.run(
    user_prompt=user_prompt,
    reference_image_base64=image_base64,
    max_iterations=10
)

# イテレーション情報
print(json.dumps({
    'type': 'iterations',
    'count': result.get('iterations', 0),
    'tools': [t['action'] for t in result.get('tools_executed', [])]
}), flush=True)

# 結果を出力
if result.get('success'):
    print(json.dumps({
        'type': 'message',
        'content': result.get('final_answer', 'スライドの生成が完了しました。')
    }), flush=True)

    if result.get('result') and result['result'].get('pptx_path'):
        print(json.dumps({
            'type': 'pptx_generated',
            'pptxPath': result['result']['pptx_path'],
            'previewPath': result['result'].get('background_path'),
            'sessionId': agent.session_id
        }), flush=True)
else:
    print(json.dumps({
        'type': 'error',
        'content': f"エラーが発生しました: {result.get('error', 'Unknown error')}"
    }), flush=True)

# トレーシングサマリー
if result.get('tracing_summary'):
    summary = result['tracing_summary']
    print(json.dumps({
        'type': 'tracing_summary',
        'totalTokens': summary.get('total_tokens', 0),
        'inputTokens': summary.get('input_tokens', 0),
        'outputTokens': summary.get('output_tokens', 0),
        'totalCost': summary.get('total_cost', 0)
    }), flush=True)

print(json.dumps({'type': 'done', 'sessionId': agent.session_id, 'success': result.get('success', False)}), flush=True)
`

        const inputData = {
          prompt,
          image_base64: imageBase64?.replace(/^data:image\/[^;]+;base64,/, ''),
          session_id: existingSessionId,
          feedback,
        }

        const pythonProcess = spawn('python3', ['-c', pythonScript], {
          cwd: projectRoot,
          env: { ...process.env },
        })

        // 入力データを送信
        pythonProcess.stdin.write(JSON.stringify(inputData))
        pythonProcess.stdin.end()

        // 出力を処理
        let buffer = ''

        pythonProcess.stdout.on('data', (data: Buffer) => {
          buffer += data.toString()
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.trim()) continue

            // JSONイベントのみを送信
            if (line.startsWith('{')) {
              try {
                JSON.parse(line) // 有効なJSONかチェック
                controller.enqueue(encoder.encode(line + '\n'))
              } catch {
                // JSONでない場合はスキップ
              }
            }
          }
        })

        pythonProcess.stderr.on('data', (data: Buffer) => {
          const stderr = data.toString()
          // Warningは無視、Errorのみログ
          if (stderr.includes('Error') && !stderr.includes('Warning')) {
            console.error('Python stderr:', stderr)
          }
        })

        await new Promise<void>((resolve, reject) => {
          pythonProcess.on('close', (code) => {
            // 残りのバッファを処理
            if (buffer.trim() && buffer.startsWith('{')) {
              try {
                JSON.parse(buffer)
                controller.enqueue(encoder.encode(buffer + '\n'))
              } catch {
                // ignore
              }
            }

            if (code !== 0 && code !== null) {
              controller.enqueue(
                encoder.encode(
                  JSON.stringify({
                    type: 'error',
                    content: `プロセスがエラーコード ${code} で終了しました。`,
                  }) + '\n'
                )
              )
            }
            resolve()
          })

          pythonProcess.on('error', (err) => {
            reject(err)
          })
        })

      } catch (error) {
        controller.enqueue(
          encoder.encode(
            JSON.stringify({
              type: 'error',
              content: `エラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`,
            }) + '\n'
          )
        )
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'Cache-Control': 'no-cache',
    },
  })
}
