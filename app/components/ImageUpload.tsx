'use client'

interface ImageUploadProps {
  preview: string
  onRemove: () => void
}

export function ImageUpload({ preview, onRemove }: ImageUploadProps) {
  return (
    <div className="inline-flex items-center gap-2 bg-[#1a1a1a] border border-[var(--border)] rounded-lg p-2">
      <img
        src={preview}
        alt="Upload preview"
        className="h-16 w-auto rounded"
      />
      <button
        type="button"
        onClick={onRemove}
        className="p-1 hover:bg-[#333] rounded transition-colors"
        title="画像を削除"
      >
        <svg
          className="w-4 h-4 text-[var(--muted)]"
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
      </button>
    </div>
  )
}
