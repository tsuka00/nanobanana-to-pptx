'use client'

import React, { useState, useRef, KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  onImageUpload: (base64: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, onImageUpload, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('画像ファイルを選択してください')
      return
    }

    const reader = new FileReader()
    reader.onload = (event) => {
      const base64 = event.target?.result as string
      onImageUpload(base64)
    }
    reader.readAsDataURL(file)

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="group relative flex items-end gap-2 p-2 bg-white border border-gray-200 rounded-[26px] shadow-sm transition-all duration-200 hover:shadow-md hover:border-gray-300 focus-within:shadow-md focus-within:border-gray-400">
      {/* Image Upload Button */}
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        className="flex items-center justify-center w-9 h-9 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0 outline-none"
        title="画像をアップロード"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
          />
        </svg>
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Text Input */}
      <div className="flex-1 relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="ReDesignへようこそ！編集可能なクリエイティブに"
          disabled={disabled}
          rows={1}
          className="w-full py-2 bg-transparent border-none resize-none focus:outline-none focus:ring-0 text-gray-800 placeholder-gray-400 text-sm leading-5 disabled:opacity-50 disabled:cursor-not-allowed no-scrollbar"
          style={{
            minHeight: '36px',
            maxHeight: '200px',
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement
            target.style.height = 'auto'
            target.style.height = `${Math.min(target.scrollHeight, 200)}px`
          }}
        />
      </div>

      {/* Send Button */}
      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className={`flex items-center justify-center w-9 h-9 rounded-full transition-all duration-200 shrink-0 ${
          !input.trim()
            ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
            : 'bg-gray-900 text-white hover:bg-black hover:scale-105 shadow-sm'
        }`}
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 12h14M12 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>
  )
}
