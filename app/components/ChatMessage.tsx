'use client'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  image?: string
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`message-enter flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-[var(--primary)] text-white shadow-md'
            : 'bg-white border border-[var(--border)] shadow-sm text-[var(--foreground)]'
        }`}
      >
        {message.image && (
          <div className="mb-3">
            <img
              src={message.image}
              alt="Uploaded"
              className="max-w-full max-h-48 rounded-lg"
            />
          </div>
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
        <div
          className={`text-xs mt-2 ${
            isUser ? 'text-emerald-100' : 'text-[var(--muted)]'
          }`}
        >
          {message.timestamp.toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  )
}
