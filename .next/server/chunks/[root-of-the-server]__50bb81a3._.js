module.exports=[93695,(e,t,r)=>{t.exports=e.x("next/dist/shared/lib/no-fallback-error.external.js",()=>require("next/dist/shared/lib/no-fallback-error.external.js"))},32319,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-unit-async-storage.external.js",()=>require("next/dist/server/app-render/work-unit-async-storage.external.js"))},18622,(e,t,r)=>{t.exports=e.x("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js",()=>require("next/dist/compiled/next-server/app-page-turbo.runtime.prod.js"))},56704,(e,t,r)=>{t.exports=e.x("next/dist/server/app-render/work-async-storage.external.js",()=>require("next/dist/server/app-render/work-async-storage.external.js"))},70406,(e,t,r)=>{t.exports=e.x("next/dist/compiled/@opentelemetry/api",()=>require("next/dist/compiled/@opentelemetry/api"))},14747,(e,t,r)=>{t.exports=e.x("path",()=>require("path"))},33405,(e,t,r)=>{t.exports=e.x("child_process",()=>require("child_process"))},57522,e=>{"use strict";var t=e.i(47909),r=e.i(74017),n=e.i(96250),s=e.i(59756),a=e.i(61916),o=e.i(14444),i=e.i(37092),u=e.i(69741),l=e.i(16795),p=e.i(87718),d=e.i(95169),c=e.i(47587),g=e.i(66012),h=e.i(70101),_=e.i(26937),m=e.i(10372),f=e.i(93695);e.i(52474);var x=e.i(220),y=e.i(33405),R=e.i(14747);async function v(e){let{prompt:t,imageBase64:r,sessionId:n,feedback:s}=await e.json();if(!t&&!s)return new Response(JSON.stringify({error:"Prompt or feedback is required"}),{status:400,headers:{"Content-Type":"application/json"}});let a=R.default.resolve(process.cwd()),o=new TextEncoder,i=new ReadableStream({async start(e){try{let i=`
import sys
import os
import json
import base64

# プロジェクトルートをパスに追加
sys.path.insert(0, '${a}')
os.chdir('${a}')

# .env.localを読み込み
from dotenv import load_dotenv
load_dotenv('${a}/.env.local')

from agents.react_agent import ReActDesignerAgent

# 入力を受け取る
input_data = json.loads(sys.stdin.read())

user_prompt = input_data.get('prompt', '')
image_base64 = input_data.get('image_base64')
session_id = input_data.get('session_id')

# エージェントを初期化
agent = ReActDesignerAgent(
    session_id=session_id,
    enable_tracing=True
)

# セッション開始イベント
print(json.dumps({'type': 'session_start', 'sessionId': agent.session_id}), flush=True)

# ツール実行をフックするためのモンキーパッチ
original_execute_tool = agent._execute_tool

def hooked_execute_tool(action, action_input):
    # ツール開始イベント
    print(json.dumps({
        'type': 'tool_start',
        'tool': action,
        'input': str(action_input)[:200]
    }), flush=True)

    result = original_execute_tool(action, action_input)

    # ツール終了イベント
    status = 'error' if result.startswith('Error:') else 'completed'
    print(json.dumps({
        'type': 'tool_end',
        'tool': action,
        'status': status,
        'result': result[:300]
    }), flush=True)

    return result

agent._execute_tool = hooked_execute_tool

# Thoughtをキャプチャするためのフック
original_parse = agent._parse_action

def hooked_parse(response_text):
    parsed = original_parse(response_text)
    if parsed.get('thought'):
        print(json.dumps({
            'type': 'thought',
            'content': parsed['thought'][:500]
        }), flush=True)
    return parsed

agent._parse_action = hooked_parse

# フィードバックツールをオーバーライド（Web UIではフィードバック待ちイベントを送信）
def web_ask_feedback(params):
    question = params.get('question', '生成結果を確認してください。修正点はありますか？')

    # フィードバック待ちイベントを送信
    print(json.dumps({
        'type': 'waiting_feedback',
        'question': question,
        'pptxPath': agent._result.get('pptx_path') if agent._result else None,
        'backgroundPath': agent._result.get('background_path') if agent._result else None
    }), flush=True)

    # Web UIでは自動的にOKで継続（後でフィードバック機能を追加可能）
    return "ユーザーのフィードバック: OK"

agent._tool_ask_feedback = web_ask_feedback

# 実行
result = agent.run(
    user_prompt=user_prompt,
    reference_image_base64=image_base64,
    max_iterations=10
)

# イテレーション情報
print(json.dumps({
    'type': 'iterations',
    'count': result.get('iterations', 0),
    'tools': [t['action'] for t in result.get('tools_executed', [])]
}), flush=True)

# 結果を出力
if result.get('success'):
    print(json.dumps({
        'type': 'message',
        'content': result.get('final_answer', 'スライドの生成が完了しました。')
    }), flush=True)

    if result.get('result') and result['result'].get('pptx_path'):
        print(json.dumps({
            'type': 'pptx_generated',
            'pptxPath': result['result']['pptx_path'],
            'previewPath': result['result'].get('background_path'),
            'sessionId': agent.session_id
        }), flush=True)
else:
    print(json.dumps({
        'type': 'error',
        'content': f"エラーが発生しました: {result.get('error', 'Unknown error')}"
    }), flush=True)

# トレーシングサマリー
if result.get('tracing_summary'):
    summary = result['tracing_summary']
    print(json.dumps({
        'type': 'tracing_summary',
        'totalTokens': summary.get('total_tokens', 0),
        'inputTokens': summary.get('input_tokens', 0),
        'outputTokens': summary.get('output_tokens', 0),
        'totalCost': summary.get('total_cost', 0)
    }), flush=True)

print(json.dumps({'type': 'done', 'sessionId': agent.session_id, 'success': result.get('success', False)}), flush=True)
`,u={prompt:t,image_base64:r?.replace(/^data:image\/[^;]+;base64,/,""),session_id:n,feedback:s},l=(0,y.spawn)("python3",["-c",i],{cwd:a,env:{...process.env}});l.stdin.write(JSON.stringify(u)),l.stdin.end();let p="";l.stdout.on("data",t=>{let r=(p+=t.toString()).split("\n");for(let t of(p=r.pop()||"",r))if(t.trim()&&t.startsWith("{"))try{JSON.parse(t),e.enqueue(o.encode(t+"\n"))}catch{}}),l.stderr.on("data",e=>{let t=e.toString();t.includes("Error")&&!t.includes("Warning")&&console.error("Python stderr:",t)}),await new Promise((t,r)=>{l.on("close",r=>{if(p.trim()&&p.startsWith("{"))try{JSON.parse(p),e.enqueue(o.encode(p+"\n"))}catch{}0!==r&&null!==r&&e.enqueue(o.encode(JSON.stringify({type:"error",content:`プロセスがエラーコード ${r} で終了しました。`})+"\n")),t()}),l.on("error",e=>{r(e)})})}catch(t){e.enqueue(o.encode(JSON.stringify({type:"error",content:`エラーが発生しました: ${t instanceof Error?t.message:"Unknown error"}`})+"\n"))}finally{e.close()}}});return new Response(i,{headers:{"Content-Type":"text/plain; charset=utf-8","Transfer-Encoding":"chunked","Cache-Control":"no-cache"}})}e.s(["POST",()=>v],44242);var w=e.i(44242);let b=new t.AppRouteRouteModule({definition:{kind:r.RouteKind.APP_ROUTE,page:"/api/agent/route",pathname:"/api/agent",filename:"route",bundlePath:""},distDir:".next",relativeProjectDir:"",resolvedPagePath:"[project]/app/api/agent/route.ts",nextConfigOutput:"",userland:w}),{workAsyncStorage:E,workUnitAsyncStorage:T,serverHooks:k}=b;function C(){return(0,n.patchFetch)({workAsyncStorage:E,workUnitAsyncStorage:T})}async function A(e,t,n){b.isDev&&(0,s.addRequestMeta)(e,"devRequestTimingInternalsEnd",process.hrtime.bigint());let y="/api/agent/route";y=y.replace(/\/index$/,"")||"/";let R=await b.prepare(e,t,{srcPage:y,multiZoneDraftMode:!1});if(!R)return t.statusCode=400,t.end("Bad Request"),null==n.waitUntil||n.waitUntil.call(n,Promise.resolve()),null;let{buildId:v,params:w,nextConfig:E,parsedUrl:T,isDraftMode:k,prerenderManifest:C,routerServerContext:A,isOnDemandRevalidate:N,revalidateOnlyGenerated:P,resolvedPathname:j,clientReferenceManifest:q,serverActionsManifest:O}=R,S=(0,u.normalizeAppPath)(y),I=!!(C.dynamicRoutes[S]||C.routes[j]),U=async()=>((null==A?void 0:A.render404)?await A.render404(e,t,T,!1):t.end("This page could not be found"),null);if(I&&!k){let e=!!C.routes[j],t=C.dynamicRoutes[S];if(t&&!1===t.fallback&&!e){if(E.experimental.adapterPath)return await U();throw new f.NoFallbackError}}let H=null;!I||b.isDev||k||(H="/index"===(H=j)?"/":H);let M=!0===b.isDev||!I,D=I&&!M;O&&q&&(0,o.setReferenceManifestsSingleton)({page:y,clientReferenceManifest:q,serverActionsManifest:O,serverModuleMap:(0,i.createServerModuleMap)({serverActionsManifest:O})});let $=e.method||"GET",K=(0,a.getTracer)(),F=K.getActiveScopeSpan(),W={params:w,prerenderManifest:C,renderOpts:{experimental:{authInterrupts:!!E.experimental.authInterrupts},cacheComponents:!!E.cacheComponents,supportsDynamicResponse:M,incrementalCache:(0,s.getRequestMeta)(e,"incrementalCache"),cacheLifeProfiles:E.cacheLife,waitUntil:n.waitUntil,onClose:e=>{t.on("close",e)},onAfterTaskError:void 0,onInstrumentationRequestError:(t,r,n)=>b.onRequestError(e,t,n,A)},sharedContext:{buildId:v}},J=new l.NodeNextRequest(e),B=new l.NodeNextResponse(t),L=p.NextRequestAdapter.fromNodeNextRequest(J,(0,p.signalFromNodeResponse)(t));try{let o=async e=>b.handle(L,W).finally(()=>{if(!e)return;e.setAttributes({"http.status_code":t.statusCode,"next.rsc":!1});let r=K.getRootSpanAttributes();if(!r)return;if(r.get("next.span_type")!==d.BaseServerSpan.handleRequest)return void console.warn(`Unexpected root span type '${r.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let n=r.get("next.route");if(n){let t=`${$} ${n}`;e.setAttributes({"next.route":n,"http.route":n,"next.span_name":t}),e.updateName(t)}else e.updateName(`${$} ${y}`)}),i=!!(0,s.getRequestMeta)(e,"minimalMode"),u=async s=>{var a,u;let l=async({previousCacheEntry:r})=>{try{if(!i&&N&&P&&!r)return t.statusCode=404,t.setHeader("x-nextjs-cache","REVALIDATED"),t.end("This page could not be found"),null;let a=await o(s);e.fetchMetrics=W.renderOpts.fetchMetrics;let u=W.renderOpts.pendingWaitUntil;u&&n.waitUntil&&(n.waitUntil(u),u=void 0);let l=W.renderOpts.collectedTags;if(!I)return await (0,g.sendResponse)(J,B,a,W.renderOpts.pendingWaitUntil),null;{let e=await a.blob(),t=(0,h.toNodeOutgoingHttpHeaders)(a.headers);l&&(t[m.NEXT_CACHE_TAGS_HEADER]=l),!t["content-type"]&&e.type&&(t["content-type"]=e.type);let r=void 0!==W.renderOpts.collectedRevalidate&&!(W.renderOpts.collectedRevalidate>=m.INFINITE_CACHE)&&W.renderOpts.collectedRevalidate,n=void 0===W.renderOpts.collectedExpire||W.renderOpts.collectedExpire>=m.INFINITE_CACHE?void 0:W.renderOpts.collectedExpire;return{value:{kind:x.CachedRouteKind.APP_ROUTE,status:a.status,body:Buffer.from(await e.arrayBuffer()),headers:t},cacheControl:{revalidate:r,expire:n}}}}catch(t){throw(null==r?void 0:r.isStale)&&await b.onRequestError(e,t,{routerKind:"App Router",routePath:y,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:D,isOnDemandRevalidate:N})},A),t}},p=await b.handleResponse({req:e,nextConfig:E,cacheKey:H,routeKind:r.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:C,isRoutePPREnabled:!1,isOnDemandRevalidate:N,revalidateOnlyGenerated:P,responseGenerator:l,waitUntil:n.waitUntil,isMinimalMode:i});if(!I)return null;if((null==p||null==(a=p.value)?void 0:a.kind)!==x.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==p||null==(u=p.value)?void 0:u.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});i||t.setHeader("x-nextjs-cache",N?"REVALIDATED":p.isMiss?"MISS":p.isStale?"STALE":"HIT"),k&&t.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let d=(0,h.fromNodeOutgoingHttpHeaders)(p.value.headers);return i&&I||d.delete(m.NEXT_CACHE_TAGS_HEADER),!p.cacheControl||t.getHeader("Cache-Control")||d.get("Cache-Control")||d.set("Cache-Control",(0,_.getCacheControlHeader)(p.cacheControl)),await (0,g.sendResponse)(J,B,new Response(p.value.body,{headers:d,status:p.value.status||200})),null};F?await u(F):await K.withPropagatedContext(e.headers,()=>K.trace(d.BaseServerSpan.handleRequest,{spanName:`${$} ${y}`,kind:a.SpanKind.SERVER,attributes:{"http.method":$,"http.target":e.url}},u))}catch(t){if(t instanceof f.NoFallbackError||await b.onRequestError(e,t,{routerKind:"App Router",routePath:S,routeType:"route",revalidateReason:(0,c.getRevalidateReason)({isStaticGeneration:D,isOnDemandRevalidate:N})}),I)throw t;return await (0,g.sendResponse)(J,B,new Response(null,{status:500})),null}}e.s(["handler",()=>A,"patchFetch",()=>C,"routeModule",()=>b,"serverHooks",()=>k,"workAsyncStorage",()=>E,"workUnitAsyncStorage",()=>T],57522)}];

//# sourceMappingURL=%5Broot-of-the-server%5D__50bb81a3._.js.map