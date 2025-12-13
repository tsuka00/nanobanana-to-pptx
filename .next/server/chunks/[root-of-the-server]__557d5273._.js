module.exports=[32319,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-unit-async-storage.external.js",()=>require("next/dist/server/app-render/work-unit-async-storage.external.js"))},24725,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/after-task-async-storage.external.js",()=>require("next/dist/server/app-render/after-task-async-storage.external.js"))},18622,(e,t,r)=>{t.exports=e.x("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js",()=>require("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js"))},56704,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-async-storage.external.js",()=>require("next/dist/server/app-render/work-async-storage.external.js"))},70406,(e,t,r)=>{t.exports=e.x("next/dist/compiled/@opentelemetry/api",()=>require("next/dist/compiled/@opentelemetry/api"))},93695,(e,t,r)=>{t.exports=e.x("next/dist/shared/lib/no-fallback-error.external.js",()=>require("next/dist/shared/lib/no-fallback-error.external.js"))},33405,(e,t,r)=>{t.exports=e.x("child_process",()=>require("child_process"))},45094,e=>{"use strict";var t=e.i(47909),r=e.i(74017),n=e.i(96250),s=e.i(59756),o=e.i(61916),a=e.i(14444),i=e.i(37092),l=e.i(69741),p=e.i(16795),d=e.i(87718),u=e.i(95169),c=e.i(47587),g=e.i(66012),m=e.i(70101),h=e.i(26937),x=e.i(10372),f=e.i(93695);e.i(52474);var _=e.i(220),y=e.i(89171),v=e.i(33405);async function R(e){let{sessionId:t,feedback:r}=await e.json();if(!t||!r)return y.NextResponse.json({error:"sessionId and feedback are required"},{status:400});let n=process.cwd(),s=`
import sys
import os
import json
import base64

sys.path.insert(0, '${n}')
os.chdir('${n}')

from dotenv import load_dotenv
load_dotenv('${n}/.env.local')

from google import genai
from agents.tools.text_to_image import generate_image
from agents.tools.image_to_pptx import image_to_pptx
from pathlib import Path

session_id = '${t}'
feedback = '''${r.replace(/'/g,"\\'")}'''

output_dir = Path('${n}/agent_output') / session_id
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
`;try{let e=await new Promise((e,t)=>{let r=(0,v.spawn)("python3",["-c",s],{cwd:n,env:{...process.env}}),o="",a="";r.stdout.on("data",e=>{o+=e.toString()}),r.stderr.on("data",e=>{a+=e.toString()}),r.on("close",r=>{if(0!==r){console.error("Python stderr:",a),t(Error(`Process exited with code ${r}`));return}try{let t=o.trim().split("\n"),r=t[t.length-1];e(JSON.parse(r))}catch{t(Error("Failed to parse Python output"))}}),r.on("error",t)});if(e.success)return y.NextResponse.json({success:!0,pptxPath:e.pptxPath,backgroundPath:e.backgroundPath});return y.NextResponse.json({success:!1,error:e.error},{status:500})}catch(e){return console.error("Regenerate error:",e),y.NextResponse.json({success:!1,error:e instanceof Error?e.message:"Unknown error"},{status:500})}}e.s(["POST",()=>R],59456);var b=e.i(59456);let w=new t.AppRouteRouteModule({definition:{kind:r.RouteKind.APP_ROUTE,page:"/api/regenerate-background/route",pathname:"/api/regenerate-background",filename:"route",bundlePath:""},distDir:".next",relativeProjectDir:"",resolvedPagePath:"[project]/app/api/regenerate-background/route.ts",nextConfigOutput:"",userland:b}),{workAsyncStorage:k,workUnitAsyncStorage:E,serverHooks:P}=w;function C(){return(0,n.patchFetch)({workAsyncStorage:k,workUnitAsyncStorage:E})}async function j(e,t,n){w.isDev&&(0,s.addRequestMeta)(e,"devRequestTimingInternalsEnd",process.hrtime.bigint());let y="/api/regenerate-background/route";y=y.replace(/\/index$/,"")||"/";let v=await w.prepare(e,t,{srcPage:y,multiZoneDraftMode:!1});if(!v)return t.statusCode=400,t.end("Bad Request"),null==n.waitUntil||n.waitUntil.call(n,Promise.resolve()),null;let{buildId:R,params:b,nextConfig:k,parsedUrl:E,isDraftMode:P,prerenderManifest:C,routerServerContext:j,isOnDemandRevalidate:A,revalidateOnlyGenerated:N,resolvedPathname:T,clientReferenceManifest:S,serverActionsManifest:O}=v,q=(0,l.normalizeAppPath)(y),F=!!(C.dynamicRoutes[q]||C.routes[T]),I=async()=>((null==j?void 0:j.render404)?await j.render404(e,t,E,!1):t.end("This page could not be found"),null);if(F&&!P){let e=!!C.routes[T],t=C.dynamicRoutes[q];if(t&&!1===t.fallback&&!e){if(k.experimental.adapterPath)return await I();throw new f.NoFallbackError}}let U=null;!F||w.isDev||P||(U="/index"===(U=T)?"/":U);let H=!0===w.isDev||!F,M=F&&!H;O&&S&&(0,a.setReferenceManifestsSingleton)({page:y,clientReferenceManifest:S,serverActionsManifest:O,serverModuleMap:(0,i.createServerModuleMap)({serverActionsManifest:O})});let $=e.method||"GET",D=(0,o.getTracer)(),K=D.getActiveScopeSpan(),L={params:b,prerenderManifest:C,renderOpts:{experimental:{authInterrupts:!!k.experimental.authInterrupts},cacheComponents:!!k.cacheComponents,supportsDynamicResponse:H,incrementalCache:(0,s.getRequestMeta)(e,"incrementalCache"),cacheLifeProfiles:k.cacheLife,waitUntil:n.waitUntil,onClose:e=>{t.on("close",e)},onAfterTaskError:void 0,onInstrumentationRequestError:(t,r,n)=>w.onRequestError(e,t,n,j)},sharedContext:{buildId:R}},B=new p.NodeNextRequest(e),G=new p.NodeNextResponse(t),X=d.NextRequestAdapter.fromNodeNextRequest(B,(0,d.signalFromNodeResponse)(t));try{let a=async e=>w.handle(X,L).finally(()=>{if(!e)return;e.setAttributes({"http.status_code":t.statusCode,"next.rsc":!1});let r=D.getRootSpanAttributes();if(!r)return;if(r.get("next.span_type")!==u.BaseServerSpan.handleRequest)return void console.warn(`Unexpected root span type '${r.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let n=r.get("next.route");if(n){let t=`${$} ${n}`;e.setAttributes({"next.route":n,"http.route":n,"next.span_name":t}),e.updateName(t)}else e.updateName(`${$} ${y}`)}),i=!!(0,s.getRequestMeta)(e,"minimalMode"),l=async s=>{var o,l;let p=async({previousCacheEntry:r})=>{try{if(!i&&A&&N&&!r)return t.statusCode=404,t.setHeader("x-nextjs-cache","REVALIDATED"),t.end("This page could not be found"),null;let o=await a(s);e.fetchMetrics=L.renderOpts.fetchMetrics;let l=L.renderOpts.pendingWaitUntil;l&&n.waitUntil&&(n.waitUntil(l),l=void 0);let p=L.renderOpts.collectedTags;if(!F)return await (0,g.sendResponse)(B,G,o,L.renderOpts.pendingWaitUntil),null;{let e=await o.blob(),t=(0,m.toNodeOutgoingHttpHeaders)(o.headers);p&&(t[x.NEXT_CACHE_TAGS_HEADER]=p),!t["content-type"]&&e.type&&(t["content-type"]=e.type);let r=void 0!==L.renderOpts.collectedRevalidate&&!(L.renderOpts.collectedRevalidate>=x.INFINITE_CACHE)&&L.renderOpts.collectedRevalidate,n=void 0===L.renderOpts.collectedExpire||L.renderOpts.collectedExpire>=x.INFINITE_CACHE?void 0:L.renderOpts.collectedExpire;return{value:{kind:_.CachedRouteKind.APP_ROUTE,status:o.status,body:Buffer.from(await e.arrayBuffer()),headers:t},cacheControl:{revalidate:r,expire:n}}}}catch(t){throw(null==r?void 0:r.isStale)&&await w.onRequestError(e,t,{routerKind:"App Router",routePath:y,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:M,isOnDemandRevalidate:A})},j),t}},d=await w.handleResponse({req:e,nextConfig:k,cacheKey:U,routeKind:r.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:C,isRoutePPREnabled:!1,isOnDemandRevalidate:A,revalidateOnlyGenerated:N,responseGenerator:p,waitUntil:n.waitUntil,isMinimalMode:i});if(!F)return null;if((null==d||null==(o=d.value)?void 0:o.kind)!==_.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==d||null==(l=d.value)?void 0:l.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});i||t.setHeader("x-nextjs-cache",A?"REVALIDATED":d.isMiss?"MISS":d.isStale?"STALE":"HIT"),P&&t.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let u=(0,m.fromNodeOutgoingHttpHeaders)(d.value.headers);return i&&F||u.delete(x.NEXT_CACHE_TAGS_HEADER),!d.cacheControl||t.getHeader("Cache-Control")||u.get("Cache-Control")||u.set("Cache-Control",(0,h.getCacheControlHeader)(d.cacheControl)),await (0,g.sendResponse)(B,G,new Response(d.value.body,{headers:u,status:d.value.status||200})),null};K?await l(K):await D.withPropagatedContext(e.headers,()=>D.trace(u.BaseServerSpan.handleRequest,{spanName:`${$} ${y}`,kind:o.SpanKind.SERVER,attributes:{"http.method":$,"http.target":e.url}},l))}catch(t){if(t instanceof f.NoFallbackError||await w.onRequestError(e,t,{routerKind:"App Router",routePath:q,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:M,isOnDemandRevalidate:A})}),F)throw t;return await (0,g.sendResponse)(B,G,new Response(null,{status:500})),null}}e.s(["handler",()=>j,"patchFetch",()=>C,"routeModule",()=>w,"serverHooks",()=>P,"workAsyncStorage",()=>k,"workUnitAsyncStorage",()=>E],45094)}];

//# sourceMappingURL=%5Broot-of-the-server%5D__557d5273._.js.map