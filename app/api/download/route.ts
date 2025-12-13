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

  // PPTXファイルを探す
  const pptxPath = path.join(outputDir, `${sessionId}.pptx`)

  if (!fs.existsSync(pptxPath)) {
    return NextResponse.json({ error: 'PPTX file not found' }, { status: 404 })
  }

  const fileBuffer = fs.readFileSync(pptxPath)

  return new NextResponse(fileBuffer, {
    headers: {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'Content-Disposition': `attachment; filename="${sessionId}.pptx"`,
    },
  })
}
