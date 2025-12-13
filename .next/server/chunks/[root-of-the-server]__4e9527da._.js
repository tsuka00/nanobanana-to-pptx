module.exports=[32319,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-unit-async-storage.external.js",()=>require("next/dist/server/app-render/work-unit-async-storage.external.js"))},24725,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/after-task-async-storage.external.js",()=>require("next/dist/server/app-render/after-task-async-storage.external.js"))},18622,(e,t,r)=>{t.exports=e.x("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js",()=>require("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js"))},56704,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-async-storage.external.js",()=>require("next/dist/server/app-render/work-async-storage.external.js"))},70406,(e,t,r)=>{t.exports=e.x("next/dist/compiled/@opentelemetry/api",()=>require("next/dist/compiled/@opentelemetry/api"))},93695,(e,t,r)=>{t.exports=e.x("next/dist/shared/lib/no-fallback-error.external.js",()=>require("next/dist/shared/lib/no-fallback-error.external.js"))},33405,(e,t,r)=>{t.exports=e.x("child_process",()=>require("child_process"))},66533,e=>{"use strict";var t=e.i(47909),r=e.i(74017),n=e.i(96250),s=e.i(59756),o=e.i(61916),a=e.i(14444),i=e.i(37092),l=e.i(69741),d=e.i(16795),p=e.i(87718),u=e.i(95169),c=e.i(47587),g=e.i(66012),h=e.i(70101),m=e.i(26937),x=e.i(10372),f=e.i(93695);e.i(52474);var _=e.i(220),v=e.i(89171),R=e.i(33405);async function y(e){let{sessionId:t,elementId:r,content:n}=await e.json();if(!t||!r||void 0===n)return v.NextResponse.json({error:"sessionId, elementId, and content are required"},{status:400});let s=process.cwd(),o=`
import sys
import os
import json

sys.path.insert(0, '${s}')
os.chdir('${s}')

from dotenv import load_dotenv
load_dotenv('${s}/.env.local')

from agents.tools.image_to_pptx import image_to_pptx
from pathlib import Path

session_id = '${t}'
element_id = '${r}'
new_content = '''${n.replace(/'/g,"\\'")}'''

output_dir = Path('${s}/agent_output') / session_id
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
`;try{let e=await new Promise((e,t)=>{let r=(0,R.spawn)("python3",["-c",o],{cwd:s,env:{...process.env}}),n="",a="";r.stdout.on("data",e=>{n+=e.toString()}),r.stderr.on("data",e=>{a+=e.toString()}),r.on("close",r=>{if(0!==r){console.error("Python stderr:",a),t(Error(`Process exited with code ${r}`));return}try{let t=n.trim().split("\n"),r=t[t.length-1];e(JSON.parse(r))}catch{t(Error("Failed to parse Python output"))}}),r.on("error",t)});if(e.success)return v.NextResponse.json({success:!0,pptxPath:e.pptxPath});return v.NextResponse.json({success:!1,error:e.error},{status:500})}catch(e){return console.error("Edit error:",e),v.NextResponse.json({success:!1,error:e instanceof Error?e.message:"Unknown error"},{status:500})}}e.s(["POST",()=>y],78414);var w=e.i(78414);let b=new t.AppRouteRouteModule({definition:{kind:r.RouteKind.APP_ROUTE,page:"/api/edit-element/route",pathname:"/api/edit-element",filename:"route",bundlePath:""},distDir:".next",relativeProjectDir:"",resolvedPagePath:"[project]/app/api/edit-element/route.ts",nextConfigOutput:"",userland:w}),{workAsyncStorage:E,workUnitAsyncStorage:P,serverHooks:C}=b;function j(){return(0,n.patchFetch)({workAsyncStorage:E,workUnitAsyncStorage:P})}async function k(e,t,n){b.isDev&&(0,s.addRequestMeta)(e,"devRequestTimingInternalsEnd",process.hrtime.bigint());let v="/api/edit-element/route";v=v.replace(/\/index$/,"")||"/";let R=await b.prepare(e,t,{srcPage:v,multiZoneDraftMode:!1});if(!R)return t.statusCode=400,t.end("Bad Request"),null==n.waitUntil||n.waitUntil.call(n,Promise.resolve()),null;let{buildId:y,params:w,nextConfig:E,parsedUrl:P,isDraftMode:C,prerenderManifest:j,routerServerContext:k,isOnDemandRevalidate:A,revalidateOnlyGenerated:T,resolvedPathname:N,clientReferenceManifest:S,serverActionsManifest:O}=R,q=(0,l.normalizeAppPath)(v),F=!!(j.dynamicRoutes[q]||j.routes[N]),U=async()=>((null==k?void 0:k.render404)?await k.render404(e,t,P,!1):t.end("This page could not be found"),null);if(F&&!C){let e=!!j.routes[N],t=j.dynamicRoutes[q];if(t&&!1===t.fallback&&!e){if(E.experimental.adapterPath)return await U();throw new f.NoFallbackError}}let H=null;!F||b.isDev||C||(H="/index"===(H=N)?"/":H);let I=!0===b.isDev||!F,$=F&&!I;O&&S&&(0,a.setReferenceManifestsSingleton)({page:v,clientReferenceManifest:S,serverActionsManifest:O,serverModuleMap:(0,i.createServerModuleMap)({serverActionsManifest:O})});let M=e.method||"GET",D=(0,o.getTracer)(),K=D.getActiveScopeSpan(),B={params:w,prerenderManifest:j,renderOpts:{experimental:{authInterrupts:!!E.experimental.authInterrupts},cacheComponents:!!E.cacheComponents,supportsDynamicResponse:I,incrementalCache:(0,s.getRequestMeta)(e,"incrementalCache"),cacheLifeProfiles:E.cacheLife,waitUntil:n.waitUntil,onClose:e=>{t.on("close",e)},onAfterTaskError:void 0,onInstrumentationRequestError:(t,r,n)=>b.onRequestError(e,t,n,k)},sharedContext:{buildId:y}},L=new d.NodeNextRequest(e),X=new d.NodeNextResponse(t),W=p.NextRequestAdapter.fromNodeNextRequest(L,(0,p.signalFromNodeResponse)(t));try{let a=async e=>b.handle(W,B).finally(()=>{if(!e)return;e.setAttributes({"http.status_code":t.statusCode,"next.rsc":!1});let r=D.getRootSpanAttributes();if(!r)return;if(r.get("next.span_type")!==u.BaseServerSpan.handleRequest)return void console.warn(`Unexpected root span type '${r.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let n=r.get("next.route");if(n){let t=`${M} ${n}`;e.setAttributes({"next.route":n,"http.route":n,"next.span_name":t}),e.updateName(t)}else e.updateName(`${M} ${v}`)}),i=!!(0,s.getRequestMeta)(e,"minimalMode"),l=async s=>{var o,l;let d=async({previousCacheEntry:r})=>{try{if(!i&&A&&T&&!r)return t.statusCode=404,t.setHeader("x-nextjs-cache","REVALIDATED"),t.end("This page could not be found"),null;let o=await a(s);e.fetchMetrics=B.renderOpts.fetchMetrics;let l=B.renderOpts.pendingWaitUntil;l&&n.waitUntil&&(n.waitUntil(l),l=void 0);let d=B.renderOpts.collectedTags;if(!F)return await (0,g.sendResponse)(L,X,o,B.renderOpts.pendingWaitUntil),null;{let e=await o.blob(),t=(0,h.toNodeOutgoingHttpHeaders)(o.headers);d&&(t[x.NEXT_CACHE_TAGS_HEADER]=d),!t["content-type"]&&e.type&&(t["content-type"]=e.type);let r=void 0!==B.renderOpts.collectedRevalidate&&!(B.renderOpts.collectedRevalidate>=x.INFINITE_CACHE)&&B.renderOpts.collectedRevalidate,n=void 0===B.renderOpts.collectedExpire||B.renderOpts.collectedExpire>=x.INFINITE_CACHE?void 0:B.renderOpts.collectedExpire;return{value:{kind:_.CachedRouteKind.APP_ROUTE,status:o.status,body:Buffer.from(await e.arrayBuffer()),headers:t},cacheControl:{revalidate:r,expire:n}}}}catch(t){throw(null==r?void 0:r.isStale)&&await b.onRequestError(e,t,{routerKind:"App Router",routePath:v,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:$,isOnDemandRevalidate:A})},k),t}},p=await b.handleResponse({req:e,nextConfig:E,cacheKey:H,routeKind:r.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:j,isRoutePPREnabled:!1,isOnDemandRevalidate:A,revalidateOnlyGenerated:T,responseGenerator:d,waitUntil:n.waitUntil,isMinimalMode:i});if(!F)return null;if((null==p||null==(o=p.value)?void 0:o.kind)!==_.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==p||null==(l=p.value)?void 0:l.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});i||t.setHeader("x-nextjs-cache",A?"REVALIDATED":p.isMiss?"MISS":p.isStale?"STALE":"HIT"),C&&t.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let u=(0,h.fromNodeOutgoingHttpHeaders)(p.value.headers);return i&&F||u.delete(x.NEXT_CACHE_TAGS_HEADER),!p.cacheControl||t.getHeader("Cache-Control")||u.get("Cache-Control")||u.set("Cache-Control",(0,m.getCacheControlHeader)(p.cacheControl)),await (0,g.sendResponse)(L,X,new Response(p.value.body,{headers:u,status:p.value.status||200})),null};K?await l(K):await D.withPropagatedContext(e.headers,()=>D.trace(u.BaseServerSpan.handleRequest,{spanName:`${M} ${v}`,kind:o.SpanKind.SERVER,attributes:{"http.method":M,"http.target":e.url}},l))}catch(t){if(t instanceof f.NoFallbackError||await b.onRequestError(e,t,{routerKind:"App Router",routePath:q,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:$,isOnDemandRevalidate:A})}),F)throw t;return await (0,g.sendResponse)(L,X,new Response(null,{status:500})),null}}e.s(["handler",()=>k,"patchFetch",()=>j,"routeModule",()=>b,"serverHooks",()=>C,"workAsyncStorage",()=>E,"workUnitAsyncStorage",()=>P],66533)}];

//# sourceMappingURL=%5Broot-of-the-server%5D__4e9527da._.js.map