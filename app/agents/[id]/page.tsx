'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import { ChatMessage, Message } from '../../components/ChatMessage'
import { ChatInput } from '../../components/ChatInput'
import { ToolExecution, ToolExecutionItem, ThoughtItem } from '../../components/ToolExecution'
import { PptxViewer } from '../../components/PptxViewer'
import { ImageUpload } from '../../components/ImageUpload'

interface TracingSummary {
  totalTokens: number
  inputTokens: number
  outputTokens: number
  totalCost: number
}

interface WaitingFeedback {
  question: string
  pptxPath?: string
  backgroundPath?: string
}

export default function AgentPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const sessionId = params.id as string

  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [toolExecutions, setToolExecutions] = useState<ToolExecutionItem[]>([])
  const [thoughts, setThoughts] = useState<ThoughtItem[]>([])
  const [currentPptx, setCurrentPptx] = useState<string | null>(null)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [waitingFeedback, setWaitingFeedback] = useState<WaitingFeedback | null>(null)
  const [tracingSummary, setTracingSummary] = useState<TracingSummary | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  
  // 初期ロード時の自動実行フラグ
  const hasInitializedRef = useRef(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, toolExecutions, thoughts])

  // 初期プロンプトの処理
  useEffect(() => {
    if (!hasInitializedRef.current && searchParams) {
      const initialPrompt = searchParams.get('q')
      
      // Check for pending image transfer from landing page
      let pendingImage: string | null = null
      if (typeof window !== 'undefined') {
        const key = `pending_image_${sessionId}`
        pendingImage = sessionStorage.getItem(key)
        if (pendingImage) {
          setUploadedImage(pendingImage)
          sessionStorage.removeItem(key)
        }
      }

      if (initialPrompt) {
        hasInitializedRef.current = true
        handleSendMessage(initialPrompt, pendingImage)
      }
    }
  }, [searchParams, sessionId])

  const handleSendMessage = async (content: string, imageOverride?: string | null) => {
    // Use override if provided, otherwise current state
    const currentImage = imageOverride !== undefined ? imageOverride : uploadedImage

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      image: currentImage || undefined,
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setToolExecutions([])
    setThoughts([])
    setWaitingFeedback(null)
    setTracingSummary(null)
    setUploadedImage(null)

    try {
      const response = await fetch('/api/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: content,
          imageBase64: currentImage,
          sessionId,
        }),
      })

      if (!response.ok) throw new Error('Agent request failed')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No response body')

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          try {
            const event = JSON.parse(line)
            handleStreamEvent(event)
          } catch {
            // Skip non-JSON lines
          }
        }
      }
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleStreamEvent = (event: {
    type: string
    sessionId?: string
    tool?: string
    status?: 'running' | 'completed' | 'error'
    result?: string
    input?: string
    content?: string
    pptxPath?: string
    previewPath?: string
    backgroundPath?: string
    question?: string
    totalTokens?: number
    inputTokens?: number
    outputTokens?: number
    totalCost?: number
  }) => {
    switch (event.type) {
      // session_startはここでは無視（URLで固定のため）
      case 'thought':
        if (event.content) {
          setThoughts((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              content: event.content!,
              timestamp: new Date(),
            },
          ])
        }
        break

      case 'tool_start':
        setToolExecutions((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            name: event.tool || 'unknown',
            status: 'running',
            startTime: new Date(),
            input: event.input,
          },
        ])
        break

      case 'tool_end':
        setToolExecutions((prev) =>
          prev.map((t) =>
            t.name === event.tool && t.status === 'running'
              ? {
                  ...t,
                  status: event.status || 'completed',
                  result: event.result,
                  endTime: new Date(),
                }
              : t
          )
        )
        break

      case 'waiting_feedback':
        setWaitingFeedback({
          question: event.question || '',
          pptxPath: event.pptxPath,
          backgroundPath: event.backgroundPath,
        })
        if (event.pptxPath) {
          setCurrentPptx(event.pptxPath)
          setShowPreview(true)
        }
        break

      case 'message':
        const assistantMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: event.content || '',
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
        break

      case 'error':
        const errorMsg: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: event.content || 'エラーが発生しました。',
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMsg])
        break

      case 'pptx_generated':
        if (event.pptxPath) {
          setCurrentPptx(event.pptxPath)
          setShowPreview(true)
        }
        setWaitingFeedback(null)
        break

      case 'tracing_summary':
        setTracingSummary({
          totalTokens: event.totalTokens || 0,
          inputTokens: event.inputTokens || 0,
          outputTokens: event.outputTokens || 0,
          totalCost: event.totalCost || 0,
        })
        break

      case 'done':
        setWaitingFeedback(null)
        break
    }
  }

  const handleImageUpload = (base64: string) => {
    setUploadedImage(base64)
  }

  const handleImageRemove = () => {
    setUploadedImage(null)
  }

  const handleClosePreview = () => {
    setShowPreview(false)
  }

  return (
    <div className="flex h-screen">
      {/* Chat Section */}
      <div className="flex flex-col flex-1 relative transition-all duration-500 ease-in-out">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-transparent bg-transparent absolute top-0 w-full z-10">
          <div className="transition-opacity duration-300">
             <h1 className="text-xl font-bold text-[var(--foreground)]">NanoBanana</h1>
          </div>
          <div className="flex items-center gap-4">
            {currentPptx && (
              <button
                onClick={() => setShowPreview(!showPreview)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors border border-[var(--border)] ${showPreview ? 'bg-[var(--primary)] text-white border-transparent' : 'bg-white hover:bg-gray-50 text-[var(--foreground)]'}`}
              >
                {showPreview ? 'プレビューを閉じる' : 'プレビューを表示'}
              </button>
            )}
            {sessionId && (
              <span className="text-sm text-[var(--muted)]">Session: {sessionId}</span>
            )}
          </div>
        </header>

        {/* Chat State (Messages List) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 no-scrollbar pt-20">
          {messages.length === 0 && !isLoading && (
             <div className="flex flex-col items-center justify-center h-full text-center text-[var(--muted)] animate-in fade-in zoom-in duration-300">
               <div className="mb-4 text-4xl">🍌</div>
               <p className="text-lg">何をお手伝いしましょうか？</p>
             </div>
          )}
          
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {/* Tool Executions & Thoughts */}
          {(toolExecutions.length > 0 || thoughts.length > 0) && (
            <ToolExecution
              executions={toolExecutions}
              thoughts={thoughts}
              waitingFeedback={waitingFeedback}
              tracingSummary={tracingSummary}
            />
          )}

          {isLoading && toolExecutions.length === 0 && (
            <div className="flex items-center gap-2 text-[var(--muted)]">
              <div className="w-2 h-2 bg-[var(--primary)] rounded-full animate-pulse" />
              <span>エージェントを起動中...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Image Upload Preview (Bottom) */}
        {uploadedImage && (
          <div className="px-6 py-2 border-t border-[var(--border)] bg-white/50">
            <ImageUpload
              preview={uploadedImage}
              onRemove={handleImageRemove}
            />
          </div>
        )}

        {/* Input (Bottom) */}
        <div className="p-6 border-t border-[var(--border)] bg-white/50 backdrop-blur-md">
          <ChatInput
            onSend={handleSendMessage}
            onImageUpload={handleImageUpload}
            disabled={isLoading}
          />
        </div>
      </div>

      {/* PPTX Viewer Section - Only show when preview is enabled */}
      {showPreview && currentPptx && (
        <div className="w-[600px] flex flex-col bg-gray-50 border-l border-[var(--border)] shadow-xl">
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)] bg-white">
            <h2 className="text-lg font-semibold text-[var(--foreground)]">プレビュー</h2>
            <button
              onClick={handleClosePreview}
              className="p-1 hover:bg-gray-100 rounded transition-colors text-[var(--muted)] hover:text-[var(--foreground)]"
              title="閉じる"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            <PptxViewer
              pptxPath={currentPptx}
              sessionId={sessionId}
            />
          </div>
        </div>
      )}
    </div>
  )
}
