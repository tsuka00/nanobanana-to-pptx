import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

interface RegenerateRequest {
  sessionId: string
  feedback: string
}

export async function POST(request: NextRequest) {
  const body: RegenerateRequest = await request.json()
  const { sessionId, feedback } = body

  if (!sessionId || !feedback) {
    return NextResponse.json(
      { error: 'sessionId and feedback are required' },
      { status: 400 }
    )
  }

  const projectRoot = process.cwd()

  const pythonScript = `
import sys
import os
import json
import base64

sys.path.insert(0, '${projectRoot}')
os.chdir('${projectRoot}')

from dotenv import load_dotenv
load_dotenv('${projectRoot}/.env.local')

from google import genai
from agents.tools.text_to_image import generate_image
from agents.tools.image_to_pptx import image_to_pptx
from pathlib import Path

session_id = '${sessionId}'
feedback = '''${feedback.replace(/'/g, "\\'")}'''

output_dir = Path('${projectRoot}/agent_output') / session_id
design_path = output_dir / 'design.json'

if not design_path.exists():
    print(json.dumps({'success': False, 'error': 'Design not found'}))
    sys.exit(0)

# design.jsonを読み込み
with open(design_path, 'r', encoding='utf-8') as f:
    design = json.load(f)

# 背景要素を探す
background_elem = None
for elem in design.get('elements', []):
    if elem.get('type') == 'background':
        background_elem = elem
        break

if not background_elem:
    print(json.dumps({'success': False, 'error': 'Background element not found'}))
    sys.exit(0)

original_prompt = background_elem.get('prompt', '')
style = background_elem.get('style', {})

# LLMにプロンプト修正を依頼
api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print(json.dumps({'success': False, 'error': 'API key not found'}))
    sys.exit(0)

client = genai.Client(api_key=api_key)

modify_prompt = f"""以下の背景画像生成プロンプトを、ユーザーのフィードバックに基づいて修正してください。

## 元のプロンプト
{original_prompt}

## ユーザーのフィードバック
{feedback}

## 指示
- フィードバックを反映した新しいプロンプトを出力してください
- プロンプトのみを出力（説明不要）
- 英語で出力
"""

try:
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[modify_prompt]
    )
    new_prompt = response.text.strip()
except Exception as e:
    print(json.dumps({'success': False, 'error': f'Prompt modification failed: {str(e)}'}))
    sys.exit(0)

# スタイル説明を構築
style_parts = []
if style.get('lighting'):
    style_parts.append(f"Lighting: {style['lighting']}")
if style.get('color_tone'):
    style_parts.append(f"Color tone: {style['color_tone']}")
if style.get('texture'):
    style_parts.append(f"Texture: {style['texture']}")
style_desc = ". ".join(style_parts)

# 画像を再生成
result = generate_image(
    prompt=new_prompt,
    reference_images=None,
    style_description=style_desc,
    aspect_ratio="16:9",
    image_size="2K",
    no_text=True
)

if not result.get('success'):
    print(json.dumps({'success': False, 'error': f"Image generation failed: {result.get('error')}"}))
    sys.exit(0)

# 新しい背景を保存
bg_path = output_dir / 'background_v2.png'
image_data = base64.b64decode(result['image_base64'])
with open(bg_path, 'wb') as f:
    f.write(image_data)

# デザインを更新
background_elem['prompt'] = new_prompt

# design.jsonを保存
with open(design_path, 'w', encoding='utf-8') as f:
    json.dump(design, f, ensure_ascii=False, indent=2)

# PPTX要素を構築
pptx_elements = []
for elem in design.get('elements', []):
    if elem.get('type') == 'background':
        pptx_elements.append({
            'id': elem.get('id', 'background'),
            'type': 'background',
            'image_base64': result['image_base64']
        })
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
pptx_result = image_to_pptx(elements=pptx_elements, session_id=session_id)

if pptx_result.get('success'):
    print(json.dumps({
        'success': True,
        'pptxPath': pptx_result['file_path'],
        'backgroundPath': str(bg_path)
    }))
else:
    print(json.dumps({'success': False, 'error': pptx_result.get('error', 'Unknown error')}))
`

  try {
    const result = await new Promise<{
      success: boolean
      error?: string
      pptxPath?: string
      backgroundPath?: string
    }>((resolve, reject) => {
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
    })

    if (result.success) {
      return NextResponse.json({
        success: true,
        pptxPath: result.pptxPath,
        backgroundPath: result.backgroundPath,
      })
    } else {
      return NextResponse.json({ success: false, error: result.error }, { status: 500 })
    }
  } catch (error) {
    console.error('Regenerate error:', error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
