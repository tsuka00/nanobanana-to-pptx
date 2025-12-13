'use client'

export interface ToolExecutionItem {
  id: string
  name: string
  status: 'running' | 'completed' | 'error'
  startTime: Date
  endTime?: Date
  input?: string
  result?: string
}

export interface ThoughtItem {
  id: string
  content: string
  timestamp: Date
}

interface ToolExecutionProps {
  executions: ToolExecutionItem[]
  thoughts?: ThoughtItem[]
  waitingFeedback?: {
    question: string
    pptxPath?: string
    backgroundPath?: string
  } | null
  tracingSummary?: {
    totalTokens: number
    inputTokens: number
    outputTokens: number
    totalCost: number
  } | null
}

const toolDisplayNames: Record<string, { name: string; icon: string; description: string }> = {
  web_search: { name: 'Web検索', icon: '🔍', description: 'デザイントレンドを調査中' },
  reference_search: { name: 'リファレンス検索', icon: '📚', description: '参照デザインを検索中' },
  design: { name: 'デザイン設計', icon: '🎨', description: '設計JSONを生成中' },
  generate: { name: '画像・PPTX生成', icon: '📊', description: '画像とPPTXを生成中' },
  ask_feedback: { name: 'フィードバック', icon: '💬', description: 'ユーザーの確認を待機中' },
  regenerate_background: { name: '背景再生成', icon: '🖼️', description: '背景画像を再生成中' },
  update_text: { name: 'テキスト更新', icon: '✏️', description: 'テキストを更新中' },
}

function getToolInfo(toolName: string) {
  return toolDisplayNames[toolName] || { name: toolName, icon: '⚙️', description: '処理中' }
}

function formatDuration(start: Date, end?: Date) {
  const endTime = end || new Date()
  const ms = endTime.getTime() - start.getTime()
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function ToolExecution({ executions, thoughts, waitingFeedback, tracingSummary }: ToolExecutionProps) {
  return (
    <div className="space-y-3">
      {/* Thoughts (Agent's reasoning) */}
      {thoughts && thoughts.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
          <div className="flex items-center gap-2 text-sm text-indigo-600 mb-3">
            <span>🧠</span>
            <span>エージェントの思考</span>
          </div>
          <div className="space-y-2">
            {thoughts.slice(-3).map((thought) => (
              <div
                key={thought.id}
                className="text-sm text-indigo-900 bg-white/50 border border-indigo-100 rounded-lg p-3"
              >
                {thought.content}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tool Executions */}
      <div className="bg-white border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-[var(--muted)] mb-3">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span>ツール実行状況</span>
          <span className="text-xs">({executions.length}件)</span>
        </div>

        <div className="space-y-2">
          {executions.map((execution) => {
            const toolInfo = getToolInfo(execution.name)
            return (
              <div
                key={execution.id}
                className={`p-3 rounded-lg bg-gray-50 border border-gray-100 ${
                  execution.status === 'running' ? 'tool-executing' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Icon */}
                  <span className="text-lg">{toolInfo.icon}</span>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-[var(--foreground)]">{toolInfo.name}</div>
                    <div className="text-xs text-[var(--muted)]">
                      {execution.status === 'running' ? toolInfo.description : formatDuration(execution.startTime, execution.endTime)}
                    </div>
                  </div>

                  {/* Status */}
                  <div className="flex items-center gap-2 shrink-0">
                    {execution.status === 'running' && (
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                        <span className="text-xs text-yellow-600">実行中</span>
                      </div>
                    )}
                    {execution.status === 'completed' && (
                      <div className="flex items-center gap-1">
                        <svg
                          className="w-4 h-4 text-emerald-500"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <span className="text-xs text-emerald-600">完了</span>
                      </div>
                    )}
                    {execution.status === 'error' && (
                      <div className="flex items-center gap-1">
                        <svg
                          className="w-4 h-4 text-red-500"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                        <span className="text-xs text-red-600">エラー</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Result preview (collapsed) */}
                {execution.status === 'completed' && execution.result && (
                  <div className="mt-2 text-xs text-[var(--muted)] bg-white border border-gray-100 rounded p-2 max-h-16 overflow-hidden">
                    {execution.result.slice(0, 150)}...
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Waiting for Feedback */}
      {waitingFeedback && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
          <div className="flex items-center gap-2 text-sm text-emerald-600 mb-2">
            <span>💬</span>
            <span>フィードバック待ち</span>
          </div>
          <p className="text-sm text-emerald-900">{waitingFeedback.question}</p>
        </div>
      )}

      {/* Tracing Summary */}
      {tracingSummary && (
        <div className="bg-white border border-[var(--border)] rounded-xl p-3 shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--muted)]">
            <span>📊 トークン: {tracingSummary.totalTokens.toLocaleString()}</span>
            <span>💰 コスト: ${tracingSummary.totalCost.toFixed(4)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
