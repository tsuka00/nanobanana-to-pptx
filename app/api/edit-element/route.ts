import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

interface EditRequest {
  sessionId: string
  elementId: string
  content: string
}

export async function POST(request: NextRequest) {
  const body: EditRequest = await request.json()
  const { sessionId, elementId, content } = body

  if (!sessionId || !elementId || content === undefined) {
    return NextResponse.json(
      { error: 'sessionId, elementId, and content are required' },
      { status: 400 }
    )
  }

  const projectRoot = process.cwd()

  const pythonScript = `
import sys
import os
import json

sys.path.insert(0, '${projectRoot}')
os.chdir('${projectRoot}')

from dotenv import load_dotenv
load_dotenv('${projectRoot}/.env.local')

from agents.tools.image_to_pptx import image_to_pptx
from pathlib import Path

session_id = '${sessionId}'
element_id = '${elementId}'
new_content = '''${content.replace(/'/g, "\\'")}'''

output_dir = Path('${projectRoot}/agent_output') / session_id
design_path = output_dir / 'design.json'

if not design_path.exists():
    print(json.dumps({'success': False, 'error': 'Design not found'}))
    sys.exit(0)

# design.jsonを読み込み
with open(design_path, 'r', encoding='utf-8') as f:
    design = json.load(f)

# 要素を更新
updated = False
for elem in design.get('elements', []):
    if elem.get('id') == element_id and elem.get('type') == 'text':
        elem['content'] = new_content
        updated = True
        break

if not updated:
    print(json.dumps({'success': False, 'error': f'Element {element_id} not found'}))
    sys.exit(0)

# design.jsonを保存
with open(design_path, 'w', encoding='utf-8') as f:
    json.dump(design, f, ensure_ascii=False, indent=2)

# PPTX要素を構築
pptx_elements = []
for elem in design.get('elements', []):
    if elem.get('type') == 'background':
        # 背景画像を読み込む
        bg_paths = ['background_v2.png', 'background.png']
        for bg_name in bg_paths:
            bg_path = output_dir / bg_name
            if bg_path.exists():
                import base64
                with open(bg_path, 'rb') as f:
                    image_base64 = base64.b64encode(f.read()).decode('utf-8')
                pptx_elements.append({
                    'id': elem.get('id', 'background'),
                    'type': 'background',
                    'image_base64': image_base64
                })
                break
    elif elem.get('type') == 'text':
        position = elem.get('position', {})
        style = elem.get('style', {})
        pptx_elements.append({
            'id': elem.get('id', 'text'),
            'type': 'text',
            'content': elem.get('content', ''),
            'bbox': {
                'x': position.get('x', 960),
                'y': position.get('y', 400),
                'width': position.get('width', 1600),
                'height': position.get('height', 100)
            },
            'style': {
                'fontSize': style.get('fontSize', 48),
                'fontWeight': style.get('fontWeight', 'normal'),
                'color': style.get('color', '#FFFFFF'),
                'align': style.get('align', 'center')
            }
        })

# PPTXを再生成
result = image_to_pptx(elements=pptx_elements, session_id=session_id)

if result.get('success'):
    print(json.dumps({'success': True, 'pptxPath': result['file_path']}))
else:
    print(json.dumps({'success': False, 'error': result.get('error', 'Unknown error')}))
`

  try {
    const result = await new Promise<{ success: boolean; error?: string; pptxPath?: string }>(
      (resolve, reject) => {
        const pythonProcess = spawn('python3', ['-c', pythonScript], {
          cwd: projectRoot,
          env: { ...process.env },
        })

        let stdout = ''
        let stderr = ''

        pythonProcess.stdout.on('data', (data: Buffer) => {
          stdout += data.toString()
        })

        pythonProcess.stderr.on('data', (data: Buffer) => {
          stderr += data.toString()
        })

        pythonProcess.on('close', (code) => {
          if (code !== 0) {
            console.error('Python stderr:', stderr)
            reject(new Error(`Process exited with code ${code}`))
            return
          }

          try {
            const lines = stdout.trim().split('\n')
            const lastLine = lines[lines.length - 1]
            resolve(JSON.parse(lastLine))
          } catch {
            reject(new Error('Failed to parse Python output'))
          }
        })

        pythonProcess.on('error', reject)
      }
    )

    if (result.success) {
      return NextResponse.json({ success: true, pptxPath: result.pptxPath })
    } else {
      return NextResponse.json({ success: false, error: result.error }, { status: 500 })
    }
  } catch (error) {
    console.error('Edit error:', error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
