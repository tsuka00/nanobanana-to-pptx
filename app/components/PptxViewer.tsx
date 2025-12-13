'use client'

import { useState, useEffect } from 'react'

interface SlideElement {
  id: string
  type: 'text' | 'background' | 'image'
  content?: string
  position?: { x: number; y: number; width: number; height: number }
  style?: {
    fontSize?: number
    fontWeight?: string
    color?: string
    align?: string
  }
}

interface PptxViewerProps {
  pptxPath: string | null
  sessionId: string | null
}

export function PptxViewer({ pptxPath, sessionId }: PptxViewerProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [elements, setElements] = useState<SlideElement[]>([])
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [editingElement, setEditingElement] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // pptxPathが設定された時のみプレビューを読み込む
    if (sessionId && pptxPath) {
      loadPreview()
    }
  }, [sessionId, pptxPath])

  const loadPreview = async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      const response = await fetch(`/api/preview?sessionId=${sessionId}`)
      if (response.ok) {
        const data = await response.json()
        setPreviewUrl(data.previewUrl)
        setElements(data.elements || [])
      }
    } catch (error) {
      console.error('Failed to load preview:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleElementClick = (elementId: string) => {
    setSelectedElement(elementId)
  }

  const handleElementDoubleClick = (element: SlideElement) => {
    if (element.type === 'text') {
      setEditingElement(element.id)
      setEditValue(element.content || '')
    }
  }

  const handleEditSave = async () => {
    if (!editingElement || !sessionId) return

    try {
      const response = await fetch('/api/edit-element', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          elementId: editingElement,
          content: editValue,
        }),
      })

      if (response.ok) {
        setElements((prev) =>
          prev.map((el) =>
            el.id === editingElement ? { ...el, content: editValue } : el
          )
        )
        await loadPreview()
      }
    } catch (error) {
      console.error('Failed to save edit:', error)
    } finally {
      setEditingElement(null)
      setEditValue('')
    }
  }

  const handleEditCancel = () => {
    setEditingElement(null)
    setEditValue('')
  }

  const handleRegenerateBackground = async () => {
    if (!sessionId) return

    const feedback = prompt('背景の変更内容を入力してください:')
    if (!feedback) return

    setIsLoading(true)
    try {
      const response = await fetch('/api/regenerate-background', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, feedback }),
      })

      if (response.ok) {
        await loadPreview()
      }
    } catch (error) {
      console.error('Failed to regenerate background:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!sessionId) return
    window.open(`/api/download?sessionId=${sessionId}`, '_blank')
  }

  // PPTXが生成されていない場合はプレースホルダを表示
  if (!pptxPath) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--muted)]">
        <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
          />
        </svg>
        <p>スライドがここに表示されます</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={loadPreview}
          disabled={isLoading || !pptxPath}
          className="px-3 py-1.5 text-sm bg-white border border-[var(--border)] rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 text-[var(--foreground)]"
        >
          更新
        </button>
        <button
          onClick={handleRegenerateBackground}
          disabled={isLoading || !pptxPath}
          className="px-3 py-1.5 text-sm bg-white border border-[var(--border)] rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 text-[var(--foreground)]"
        >
          背景を再生成
        </button>
        <div className="flex-1" />
        <button
          onClick={handleDownload}
          disabled={!pptxPath}
          className="px-3 py-1.5 text-sm bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50"
        >
          ダウンロード
        </button>
      </div>

      {/* Preview */}
      <div className="flex-1 relative bg-gray-200 rounded-xl overflow-hidden shadow-inner">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-10">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
              <span className="text-[var(--foreground)]">読み込み中...</span>
            </div>
          </div>
        )}

        {previewUrl ? (
          <div className="relative w-full aspect-video">
            <img
              src={previewUrl}
              alt="Slide preview"
              className="w-full h-full object-contain"
            />

            {/* Element overlays for editing */}
            {elements.filter((el) => el.type === 'text').map((element) => (
              <div
                key={element.id}
                className={`absolute cursor-pointer transition-all ${
                  selectedElement === element.id
                    ? 'ring-2 ring-[var(--primary)]'
                    : 'hover:ring-2 hover:ring-[var(--primary)]/50'
                }`}
                style={{
                  left: `${((element.position?.x || 0) / 1920) * 100}%`,
                  top: `${((element.position?.y || 0) / 1080) * 100}%`,
                  width: `${((element.position?.width || 100) / 1920) * 100}%`,
                  height: `${((element.position?.height || 50) / 1080) * 100}%`,
                }}
                onClick={() => handleElementClick(element.id)}
                onDoubleClick={() => handleElementDoubleClick(element)}
              >
                {editingElement === element.id && (
                  <div className="absolute inset-0 bg-white/90 p-2 z-20 shadow-lg rounded">
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="w-full h-full bg-transparent border border-[var(--primary)] rounded p-1 text-sm resize-none focus:outline-none text-black"
                      autoFocus
                    />
                    <div className="absolute -bottom-8 right-0 flex gap-1">
                      <button
                        onClick={handleEditSave}
                        className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        保存
                      </button>
                      <button
                        onClick={handleEditCancel}
                        className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
                      >
                        キャンセル
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-[var(--muted)]">
            プレビューを読み込み中...
          </div>
        )}
      </div>

      {/* Element List */}
      {elements.length > 0 && (
        <div className="mt-4 p-3 bg-white border border-[var(--border)] rounded-xl shadow-sm">
          <div className="text-sm text-[var(--muted)] mb-2">要素一覧</div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {elements.map((element) => (
              <div
                key={element.id}
                className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                  selectedElement === element.id
                    ? 'bg-[var(--primary)]/10 text-[var(--primary)]'
                    : 'hover:bg-gray-50 text-[var(--foreground)]'
                }`}
                onClick={() => handleElementClick(element.id)}
                onDoubleClick={() => handleElementDoubleClick(element)}
              >
                <span className="text-xs text-[var(--muted)]">
                  {element.type === 'text' && '📝'}
                  {element.type === 'background' && '🖼️'}
                  {element.type === 'image' && '🎨'}
                </span>
                <span className="text-sm truncate flex-1">
                  {element.content || element.id}
                </span>
                {element.type === 'text' && (
                  <span className="text-xs text-[var(--muted)]">ダブルクリックで編集</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
