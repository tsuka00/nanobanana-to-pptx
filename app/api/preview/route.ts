import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  const sessionId = request.nextUrl.searchParams.get('sessionId')

  if (!sessionId) {
    return NextResponse.json({ error: 'sessionId is required' }, { status: 400 })
  }

  const projectRoot = process.cwd()
  const outputDir = path.join(projectRoot, 'agent_output', sessionId)

  if (!fs.existsSync(outputDir)) {
    return NextResponse.json({ error: 'Session not found' }, { status: 404 })
  }

  // プレビュー画像を探す
  let previewUrl: string | null = null
  const possibleBackgrounds = ['background_v2.png', 'background.png', 'Slide1.jpg']

  for (const filename of possibleBackgrounds) {
    const filePath = path.join(outputDir, filename)
    if (fs.existsSync(filePath)) {
      const imageData = fs.readFileSync(filePath)
      const base64 = imageData.toString('base64')
      const ext = path.extname(filename).slice(1)
      const mimeType = ext === 'jpg' ? 'jpeg' : ext
      previewUrl = `data:image/${mimeType};base64,${base64}`
      break
    }
  }

  // design.jsonから要素を取得
  interface DesignElement {
    type: string
    id?: string
    content?: string
    position?: { x: number; y: number; width: number; height: number }
    style?: {
      fontSize?: number
      fontWeight?: string
      color?: string
      align?: string
    }
  }

  interface DesignJson {
    elements?: DesignElement[]
  }

  let elements: DesignElement[] = []
  const designPath = path.join(outputDir, 'design.json')
  if (fs.existsSync(designPath)) {
    try {
      const designJson = JSON.parse(fs.readFileSync(designPath, 'utf-8')) as DesignJson
      elements = (designJson.elements || []).map((elem: DesignElement, index: number) => ({
        id: elem.id || `${elem.type}_${index}`,
        type: elem.type,
        content: elem.content,
        position: elem.position,
        style: elem.style,
      }))
    } catch {
      // JSONパースに失敗した場合は空の配列
    }
  }

  return NextResponse.json({
    previewUrl,
    elements,
    sessionId,
  })
}
