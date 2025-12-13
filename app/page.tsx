'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChatInput } from './components/ChatInput'
import { ImageUpload } from './components/ImageUpload'

export default function Home() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)

  const handleSendMessage = (content: string) => {
    setIsLoading(true)
    // Generate a simple unique ID (timestamp + random string)
    const sessionId = Date.now().toString(36) + Math.random().toString(36).substring(2, 5)
    
    // Construct query parameters
    const params = new URLSearchParams()
    params.set('q', content)
    
    // We can't easily pass the full base64 image via URL due to length limits.
    // For now, if there is an image, we might need a different strategy (e.g., store in local storage or send immediately).
    // Given the constraints, let's just redirect for text now.
    // If we really need image support from landing page, we'd need to POST to create a session first.
    // But for a simple UI change request, let's keep it simple. 
    // *Self-correction*: If user uploads image on landing page, it will be lost on redirect.
    // Better UX: Don't support image on landing page OR use localStorage.
    // Let's use localStorage for the "pending" image transfer.
    
    if (uploadedImage) {
      sessionStorage.setItem(`pending_image_${sessionId}`, uploadedImage)
    }

    router.push(`/agents/${sessionId}?${params.toString()}`)
  }

  const handleImageUpload = (base64: string) => {
    setUploadedImage(base64)
  }

  const handleImageRemove = () => {
    setUploadedImage(null)
  }

  // Background images
  const baseImages = [
    '/1725068678_90f61b32.jpg',
    '/1752910135_aae98341.jpg',
    '/1764379829_df0d1cbe.jpg',
  ]
  // Create enough duplicates to fill vertical space for a 4x4 feel
  const bgImages = [...baseImages, ...baseImages, ...baseImages, ...baseImages]

  return (
    <div className="relative flex h-screen items-center justify-center overflow-hidden bg-white">
      {/* Background Grid - Force inline styles to ensure grid renders if CSS fails */}
      <div 
        className="absolute inset-0 -z-10 gap-4 p-4 opacity-20 pointer-events-none"
        style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr 1fr',
          height: '120vh', // Ensure it covers vertical scrolling if any
          alignItems: 'start'
        }}
      >
        {[0, 1, 2, 3].map((colIndex) => (
          <div 
            key={colIndex} 
            className="flex flex-col gap-4"
            style={{ 
              transform: colIndex % 2 === 1 ? 'translateY(-6rem)' : 'none' // Inline transform for reliability
            }}
          >
            {bgImages.map((src, imgIndex) => (
              <div key={`${colIndex}-${imgIndex}`} className="relative w-full aspect-[3/4] rounded-2xl overflow-hidden shadow-sm">
                 <img 
                   src={src} 
                   alt="" 
                   className="w-full h-full object-cover grayscale opacity-60"
                 />
              </div>
            ))}
          </div>
        ))}
      </div>
      
      {/* Gradient Overlay to ensure text readability */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-white/60 via-white/80 to-white"></div>

      <div className="w-full max-w-3xl px-4 animate-in fade-in zoom-in duration-500 flex flex-col items-center z-10">
        

        

        
        {/* Central Search Bar */}
        <div className="w-full max-w-2xl">
          <ChatInput
            onSend={handleSendMessage}
            onImageUpload={handleImageUpload}
            disabled={isLoading}
          />
        </div>

        {uploadedImage && (
          <div className="mt-6 w-full max-w-2xl p-4 bg-white rounded-xl shadow-sm border border-[var(--border)] animate-in slide-in-from-bottom-2">
            <ImageUpload
              preview={uploadedImage}
              onRemove={handleImageRemove}
            />
          </div>
        )}

      </div>
    </div>
  )
}