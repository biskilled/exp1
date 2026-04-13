(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))o(n);new MutationObserver(n=>{for(const i of n)if(i.type==="childList")for(const a of i.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&o(a)}).observe(document,{childList:!0,subtree:!0});function r(n){const i={};return n.integrity&&(i.integrity=n.integrity),n.referrerPolicy&&(i.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?i.credentials="include":n.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function o(n){if(n.ep)return;n.ep=!0;const i=r(n);fetch(n.href,i)}})();const Ro="modulepreload",Ao=function(e){return"/"+e},kr={},Or=function(t,r,o){let n=Promise.resolve();if(r&&r.length>0){document.getElementsByTagName("link");const a=document.querySelector("meta[property=csp-nonce]"),s=a?.nonce||a?.getAttribute("nonce");n=Promise.allSettled(r.map(d=>{if(d=Ao(d),d in kr)return;kr[d]=!0;const l=d.endsWith(".css"),c=l?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${d}"]${c}`))return;const g=document.createElement("link");if(g.rel=l?"stylesheet":Ro,l||(g.as="script"),g.crossOrigin="",g.href=d,s&&g.setAttribute("nonce",s),document.head.appendChild(g),l)return new Promise((f,u)=>{g.addEventListener("load",f),g.addEventListener("error",()=>u(new Error(`Unable to preload CSS for ${d}`)))})}))}function i(a){const s=new Event("vite:preloadError",{cancelable:!0});if(s.payload=a,window.dispatchEvent(s),!s.defaultPrevented)throw a}return n.then(a=>{for(const s of a||[])s.status==="rejected"&&i(s.reason);return t().catch(i)})},kt={MOBILE:767,TABLET:1100},Y={get isMobile(){return window.innerWidth<=kt.MOBILE},get isTablet(){return window.innerWidth>kt.MOBILE&&window.innerWidth<=kt.TABLET},get isDesktop(){return window.innerWidth>kt.TABLET},get isTouch(){return window.matchMedia("(hover: none) and (pointer: coarse)").matches},get isPWA(){return window.matchMedia("(display-mode: standalone)").matches||window.navigator.standalone===!0},get isIOS(){return/iPad|iPhone|iPod/.test(navigator.userAgent)},get isAndroid(){return/Android/.test(navigator.userAgent)},get orientation(){return window.innerWidth>window.innerHeight?"landscape":"portrait"}},Mo=new Set;let Er;window.addEventListener("resize",()=>{clearTimeout(Er),Er=setTimeout(()=>{Ut(),Mo.forEach(e=>e(Y))},100)});function Ut(){const e=document.documentElement;e.classList.toggle("is-mobile",Y.isMobile),e.classList.toggle("is-tablet",Y.isTablet),e.classList.toggle("is-desktop",Y.isDesktop),e.classList.toggle("is-touch",Y.isTouch),e.classList.toggle("is-pwa",Y.isPWA),e.classList.toggle("is-ios",Y.isIOS),e.classList.toggle("is-android",Y.isAndroid),e.classList.toggle("is-landscape",Y.orientation==="landscape"),e.classList.toggle("is-portrait",Y.orientation==="portrait")}function Do(){return Y.isMobile||Y.isTablet?"steps":"visual"}let Ho=window.innerHeight;function No(){Y.isTouch&&window.visualViewport?.addEventListener("resize",()=>{const e=window.visualViewport.height,t=Ho-e;t>100?(document.body.style.paddingBottom=t+"px",document.getElementById("app")?.style.setProperty("height",e+"px"),setTimeout(()=>{const r=document.activeElement;r&&(r.tagName==="INPUT"||r.tagName==="TEXTAREA")&&r.scrollIntoView({behavior:"smooth",block:"center"})},50)):(document.body.style.paddingBottom="",document.getElementById("app")?.style.removeProperty("height"))})}function Oo(e,t){if(!Y.isTouch)return;let r=0,o=!1;e.addEventListener("touchstart",n=>{e.scrollTop===0&&(r=n.touches[0].clientY,o=!0)},{passive:!0}),e.addEventListener("touchmove",n=>{if(!o)return;const i=n.touches[0].clientY-r;i>0&&i<80&&(e.style.transform=`translateY(${i*.4}px)`)},{passive:!0}),e.addEventListener("touchend",async()=>{if(!o)return;o=!1;const n=parseFloat(e.style.transform.replace("translateY(","")||"0");e.style.transform="",n>25&&await t()})}function Ft({title:e,content:t,actions:r=[]}){const o=document.getElementById("bottom-sheet-overlay");o&&o.remove();const n=document.createElement("div");n.id="bottom-sheet-overlay",n.style.cssText=`
    position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:500;
    display:flex;align-items:flex-end;
    backdrop-filter:blur(4px);
    animation:fadeIn 0.15s ease-out;
  `;const i=document.createElement("div");i.style.cssText=`
    width:100%;
    background:var(--surface);
    border-radius:16px 16px 0 0;
    border-top:1px solid var(--border2);
    padding:0.75rem 1.25rem calc(1.25rem + var(--safe-bottom));
    max-height:85vh;
    overflow-y:auto;
    animation:slideUp 0.25s cubic-bezier(0.32,0.72,0,1);
    -webkit-overflow-scrolling:touch;
  `,i.innerHTML=`
    <div style="width:40px;height:4px;background:var(--border2);border-radius:2px;margin:0 auto 1rem"></div>
    <div style="font-family:var(--font-ui);font-weight:700;font-size:1rem;margin-bottom:0.5rem">${e}</div>
    <div id="bottom-sheet-content">${t}</div>
    ${r.length?`
      <div style="display:flex;flex-direction:column;gap:0.5rem;margin-top:1rem">
        ${r.map(s=>`
          <button class="btn ${s.style||"btn-ghost"}" onclick="${s.onclick}" style="width:100%;min-height:48px;font-size:0.85rem">
            ${s.label}
          </button>
        `).join("")}
        <button class="btn btn-ghost" onclick="document.getElementById('bottom-sheet-overlay').remove()"
          style="width:100%;min-height:48px;color:var(--muted)">Cancel</button>
      </div>
    `:""}
  `,n.appendChild(i),document.body.appendChild(n);let a=0;if(i.addEventListener("touchstart",s=>{a=s.touches[0].clientY},{passive:!0}),i.addEventListener("touchmove",s=>{const d=s.touches[0].clientY-a;d>0&&(i.style.transform=`translateY(${Math.min(d,200)}px)`)},{passive:!0}),i.addEventListener("touchend",s=>{const d=s.changedTouches[0].clientY-a;i.style.transform="",d>80&&n.remove()}),n.addEventListener("click",s=>{s.target===n&&n.remove()}),!document.getElementById("sheet-anim")){const s=document.createElement("style");s.id="sheet-anim",s.textContent=`
      @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
      @keyframes slideUp { from{transform:translateY(100%)} to{transform:translateY(0)} }
    `,document.head.appendChild(s)}return n}function Ge(e="light"){if(Y.isTouch)try{const t={light:[10],medium:[30],heavy:[50],success:[10,50,10]};navigator.vibrate?.(t[e]||[10])}catch{}}function Ur(e,{onLeft:t,onRight:r,threshold:o=60}={}){if(!Y.isTouch)return()=>{};let n=0;const i=s=>{n=s.touches[0].clientX},a=s=>{const d=s.changedTouches[0].clientX-n;Math.abs(d)<o||(d<0&&t&&(Ge("light"),t()),d>0&&r&&(Ge("light"),r()))};return e.addEventListener("touchstart",i,{passive:!0}),e.addEventListener("touchend",a,{passive:!0}),()=>{e.removeEventListener("touchstart",i),e.removeEventListener("touchend",a)}}function Uo(){Ut(),No(),typeof window<"u"&&window.__PLATFORM__&&document.documentElement.classList.add(`platform-${window.__PLATFORM__}`),window.addEventListener("orientationchange",()=>{setTimeout(Ut,200)}),console.log(`[Layout] ${Y.isDesktop?"Desktop":Y.isTablet?"Tablet":"Mobile"} · Touch:${Y.isTouch} · PWA:${Y.isPWA}`)}const or=typeof import.meta<"u"&&"http://localhost:8000"||typeof window<"u"&&window.__BACKEND_URL__||"http://localhost:8000",x={user:null,balanceInfo:null,platformStats:null,requireAuth:!1,activeView:"home",activeSettingsSection:"apikeys",projects:[],currentProject:null,currentProjectTab:"chat",workflows:[],workflowMode:"yaml",settings:{backend_url:or,default_models:{claude:"claude-sonnet-4-6",openai:"gpt-4.1",deepseek:"deepseek-chat",gemini:"gemini-2.0-flash",grok:"grok-3"},ui:{theme:"dark",font_size:13}},backendOnline:!1},Wt=new Set;function Fo(e){return Wt.add(e),()=>Wt.delete(e)}function U(e){Object.assign(x,e),Wt.forEach(t=>t(x))}const Wo=Object.freeze(Object.defineProperty({__proto__:null,setState:U,state:x,subscribe:Fo},Symbol.toStringTag,{value:"Module"}));function N(){return(x.settings?.backend_url||"http://localhost:8000").replace(/\/$/,"")}function O(e={}){const t={"Content-Type":"application/json",...e},r=localStorage.getItem("aicli_token");return r&&(t.Authorization=`Bearer ${r}`),t}function At(e,t){return!e||!e.detail?t:Array.isArray(e.detail)?e.detail.map(r=>r.msg||JSON.stringify(r)).join("; "):String(e.detail)}async function k(e){const t=new AbortController,r=setTimeout(()=>t.abort(),3e4);try{const o=await fetch(N()+e,{headers:O(),signal:t.signal});if(!o.ok){const n=await o.json().catch(()=>({detail:o.statusText}));throw new Error(At(n,o.statusText))}return o.json()}finally{clearTimeout(r)}}async function I(e,t={}){const r=new AbortController,o=setTimeout(()=>r.abort(),3e4);try{const n=await fetch(N()+e,{method:"POST",headers:O(),body:JSON.stringify(t),signal:r.signal});if(!n.ok){const i=await n.json().catch(()=>({detail:n.statusText}));throw new Error(At(i,n.statusText))}return n.json()}finally{clearTimeout(o)}}async function Be(e,t={}){const r=new AbortController,o=setTimeout(()=>r.abort(),3e4);try{const n=await fetch(N()+e,{method:"PUT",headers:O(),body:JSON.stringify(t),signal:r.signal});if(!n.ok){const i=await n.json().catch(()=>({detail:n.statusText}));throw new Error(At(i,n.statusText))}return n.json()}finally{clearTimeout(o)}}async function Z(e){const t=new AbortController,r=setTimeout(()=>t.abort(),3e4);try{const o=await fetch(N()+e,{method:"DELETE",headers:O(),signal:t.signal});if(!o.ok){const n=await o.json().catch(()=>({detail:o.statusText}));throw new Error(At(n,o.statusText))}return o.json()}finally{clearTimeout(r)}}const m={health:()=>k("/health"),login:(e,t)=>I("/auth/login",{email:e,password:t}),register:(e,t)=>I("/auth/register",{email:e,password:t}),me:()=>k("/auth/me"),usage:()=>k("/usage/me"),listProjects:()=>k("/projects/"),getProject:e=>k(`/projects/${encodeURIComponent(e)}`),createProject:e=>I("/projects/",e),switchProject:e=>I(`/projects/switch/${encodeURIComponent(e)}`),getProjectConfig:e=>k(`/projects/${encodeURIComponent(e)}/config`),updateProjectConfig:(e,t)=>Be(`/projects/${encodeURIComponent(e)}/config`,t),getProjectSummary:e=>k(`/projects/${encodeURIComponent(e)}/summary`),updateProjectSummary:(e,t)=>Be(`/projects/${encodeURIComponent(e)}/summary`,{content:t}),getProjectContext:(e,t=!1)=>k(`/projects/${encodeURIComponent(e)}/context?save=${t}`),generateMemory:e=>I(`/projects/${encodeURIComponent(e)}/memory`,{}),getMemoryStatus:e=>k(`/projects/${encodeURIComponent(e)}/memory-status`),runCommand:(e,t)=>I(`/projects/${encodeURIComponent(e)}/run-command`,{command:t}),listPrompts:e=>k(`/prompts/?project=${encodeURIComponent(e)}`),readPrompt:(e,t)=>k(`/prompts/read?path=${encodeURIComponent(e)}&project=${encodeURIComponent(t)}`),writePrompt:(e,t,r)=>Be(`/prompts/?project=${encodeURIComponent(r)}`,{path:e,content:t}),deletePrompt:(e,t)=>Z(`/prompts/?path=${encodeURIComponent(e)}&project=${encodeURIComponent(t)}`),listWorkflows:e=>k(`/workflows/?project=${encodeURIComponent(e)}`),readWorkflow:(e,t)=>k(`/workflows/${encodeURIComponent(t)}?project=${encodeURIComponent(e)}`),writeWorkflow:(e,t,r)=>Be(`/workflows/${encodeURIComponent(t)}?project=${encodeURIComponent(e)}`,{yaml_content:r}),getFiles:(e=3)=>k(`/files/code?max_depth=${e}`),readFile:e=>k(`/files/read?path=${encodeURIComponent(e)}&root=code`),async chatStream(e,t,r,o="",n={}){const i=await fetch(N()+"/chat/stream",{method:"POST",headers:O(),body:JSON.stringify({message:e,provider:t,session_id:r,system:o,stream:!0,tags:n})});if(!i.ok)throw new Error(`Chat error: ${i.statusText}`);return i},chatSessions:()=>k("/chat/sessions"),chatSession:e=>k(`/chat/sessions/${encodeURIComponent(e)}`),patchSessionTags:(e,t,r)=>fetch(N()+`/chat/sessions/${encodeURIComponent(e)}/tags`+(r?`?project=${encodeURIComponent(r)}`:""),{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),historyChat:(e,t=200)=>k(`/history/chat?project=${encodeURIComponent(e||"")}&limit=${t}`),historyCommits:(e,t=100)=>k(`/history/commits?project=${encodeURIComponent(e||"")}&limit=${t}`),patchCommit:(e,t)=>fetch(N()+`/history/commits/${encodeURIComponent(e)}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),getSessionCommits:(e,t)=>k(`/history/session-commits?session_id=${encodeURIComponent(e)}&project=${encodeURIComponent(t||"")}`),syncCommits:e=>fetch(N()+`/history/commits/sync?project=${encodeURIComponent(e||"")}`,{method:"POST",headers:O()}).then(t=>t.ok?t.json():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText)))),getSessionTags:e=>k(`/history/session-tags?project=${encodeURIComponent(e||"")}`),getSessionPhases:e=>k(`/history/session-phases?project=${encodeURIComponent(e||"")}`),putSessionTags:(e,t)=>fetch(N()+`/history/session-tags?project=${encodeURIComponent(e||"")}`,{method:"PUT",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),gitStatus:e=>k(`/git/${encodeURIComponent(e)}/status`),gitBranches:e=>k(`/git/${encodeURIComponent(e)}/branches`),gitOauthDeviceStart:e=>I("/git/oauth/device/start",e),gitOauthDevicePoll:e=>I("/git/oauth/device/poll",e),gitOauthCreateRepo:e=>I("/git/oauth/create-repo",e),gitTestConnection:e=>k(`/git/${encodeURIComponent(e)}/test`),gitPull:e=>I(`/git/${encodeURIComponent(e)}/pull`,{}),gitPushAll:e=>I(`/git/${encodeURIComponent(e)}/push-all`,{}),gitSetup:(e,t)=>I(`/git/${encodeURIComponent(e)}/setup`,t),gitCommitPush:(e,t)=>I(`/git/${encodeURIComponent(e)}/commit-push`,t),adminGetStats:()=>k("/admin/stats"),adminListUsers:()=>k("/admin/users"),adminPatchUser:(e,t)=>fetch(N()+`/admin/users/${encodeURIComponent(e)}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail)))),adminDeleteUser:e=>Z(`/admin/users/${encodeURIComponent(e)}`),adminGetPricing:()=>k("/admin/pricing"),adminSavePricing:e=>Be("/admin/pricing",e),adminGetCoupons:()=>k("/admin/coupons"),adminCreateCoupon:e=>I("/admin/coupons",e),adminDeleteCoupon:e=>Z(`/admin/coupons/${encodeURIComponent(e)}`),adminGetApiKeys:()=>k("/admin/api-keys"),adminSaveApiKeys:e=>Be("/admin/api-keys",e),adminGetApiBalances:()=>k("/admin/api-balances"),adminGetUsageTable:()=>k("/admin/usage-table"),adminGetProviderCosts:()=>k("/admin/provider-costs"),adminSaveProviderCosts:e=>Be("/admin/provider-costs",e),adminFetchProviderUsage:e=>I("/admin/fetch-provider-usage",e),adminGetProviderUsageHistory:e=>k(`/admin/provider-usage-history${e?`?provider=${encodeURIComponent(e)}`:""}`),adminDeleteProviderUsageRecord:(e,t)=>fetch(N()+`/admin/provider-usage-history?provider=${encodeURIComponent(e)}&fetched_at=${encodeURIComponent(t)}`,{method:"DELETE",headers:O()}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),adminClearProviderUsageHistory:e=>fetch(N()+`/admin/provider-usage-history?provider=${encodeURIComponent(e)}`,{method:"DELETE",headers:O()}).then(t=>t.ok?t.json():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText)))),adminGetProviderBalances:()=>k("/admin/provider-balances"),adminSaveProviderBalances:e=>Be("/admin/provider-balances",e),billingBalance:()=>k("/billing/balance"),billingApplyCoupon:e=>I("/billing/apply-coupon",{code:e}),billingHistory:()=>k("/billing/history"),billingAddPayment:()=>I("/billing/add-payment",{})};m.workflowRuns={start:(e,t,r)=>I(`/workflows/${encodeURIComponent(t)}/runs?project=${encodeURIComponent(e||"")}`,{user_input:r}),get:(e,t)=>k(`/workflows/runs/${encodeURIComponent(t)}?project=${encodeURIComponent(e||"")}`),list:e=>k(`/workflows/runs?project=${encodeURIComponent(e||"")}`),decide:(e,t,r,o=null)=>I(`/workflows/runs/${encodeURIComponent(t)}/decision?project=${encodeURIComponent(e||"")}`,{action:r,next_step:o})};m.search={semantic:e=>I("/search/semantic",e),ingest:e=>k(`/search/ingest?project=${encodeURIComponent(e||"")}`)};function je(e){return`project=${encodeURIComponent(e||"")}`}m.entities={listCategories:e=>k(`/entities/categories?${je(e)}`),createCategory:e=>I("/entities/categories",e),patchCategory:(e,t)=>fetch(N()+`/entities/categories/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail)))),deleteCategory:e=>Z(`/entities/categories/${e}`),listValues:(e,t,r={})=>{const o=new URLSearchParams({project:e||""});return t&&o.set("category_id",t),r.category_name&&o.set("category_name",r.category_name),r.status&&o.set("status",r.status),k(`/entities/values?${o}`)},createValue:e=>I("/entities/values",e),patchValue:(e,t)=>fetch(N()+`/entities/values/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail)))),deleteValue:e=>Z(`/entities/values/${e}`),listEvents:(e,t={})=>{const r=new URLSearchParams({project:e||""});return t.event_type&&r.set("event_type",t.event_type),t.value_id&&r.set("value_id",t.value_id),t.limit&&r.set("limit",t.limit),k(`/entities/events?${r}`)},syncEvents:e=>I(`/entities/events/sync?${je(e)}`,{}),addTag:(e,t)=>I(`/entities/events/${e}/tag`,{entity_value_id:t}),removeTag:(e,t)=>Z(`/entities/events/${e}/tag/${t}`),valueEvents:(e,t)=>k(`/entities/values/${e}/events?${je(t)}`),addLink:(e,t)=>I(`/entities/events/${e}/link`,t),removeLink:(e,t,r)=>Z(`/entities/events/${e}/link/${t}/${r}`),getLinks:e=>k(`/entities/events/${e}/links`),sessionTag:e=>I("/entities/session-tag",e),getEntitySessionTags:(e,t)=>k(`/entities/session-tags?session_id=${encodeURIComponent(e)}&${je(t)}`),tagBySourceId:e=>I("/entities/events/tag-by-source-id",e),untagBySourceId:(e,t,r)=>Z(`/entities/events/tag-by-source-id?source_id=${encodeURIComponent(e)}&tag=${encodeURIComponent(t)}&${je(r)}`),untagSession:(e,t,r)=>Z(`/entities/session-tag?session_id=${encodeURIComponent(e)}&tag=${encodeURIComponent(t)}&${je(r)}`),getSourceTags:e=>k(`/entities/events/source-tags?${je(e)}`),getSuggestions:(e,t)=>k(`/entities/suggestions?${je(e)}${t?`&source_id=${encodeURIComponent(t)}`:""}`),dismissSuggestions:e=>I(`/entities/suggestions/${e}/dismiss`,{}),getValueLinks:e=>k(`/entities/values/${e}/links`),createValueLink:(e,t)=>I(`/entities/values/${e}/links`,t),deleteValueLink:(e,t,r="blocks")=>Z(`/entities/values/${e}/links/${t}?link_type=${encodeURIComponent(r)}`),githubSync:(e,t,r,o="",n="open")=>{const i=new URLSearchParams({project:e||"",owner:t,repo:r,state:n});return o&&i.set("token",o),I(`/entities/github-sync?${i}`,{})}};function T(e){return encodeURIComponent(e||"")}m.tags={list:e=>k(`/tags?project=${T(e)}`),create:e=>I("/tags",e),update:(e,t)=>fetch(N()+`/tags/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail)))),delete:(e,t,r=!1)=>Z(`/tags/${T(e)}?project=${T(t)}${r?"&force=true":""}`),merge:e=>I("/tags/merge",e),migrateToAiSuggestions:e=>I(`/tags/migrate-to-ai-suggestions?project=${T(e)}`),plan:(e,t)=>I(`/tags/${T(e)}/plan?project=${T(t)}`),getSnapshot:(e,t,r="ai")=>k(`/tags/${T(e)}/snapshot?project=${T(t)}&version=${T(r)}`),getSources:(e,t)=>k(`/tags/${T(e)}/sources?project=${T(t)}`),addSource:e=>I("/tags/source",e),removeSource:e=>Z(`/tags/source/${T(e)}`),sessionContext:e=>k(`/tags/session-context?project=${T(e)}`),saveContext:(e,t)=>I(`/tags/session-context?project=${T(e)}`,t),categories:{list:()=>k("/tags/categories"),create:e=>I("/tags/categories",e),update:(e,t)=>fetch(N()+`/tags/categories/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail)))),delete:e=>Z(`/tags/categories/${e}`)},suggestions:{generate:e=>I(`/tags/suggestions/generate?project=${T(e)}`),apply:(e,t)=>I(`/tags/suggestions/apply?project=${T(e)}`,t),ignore:(e,t)=>I(`/tags/suggestions/ignore?project=${T(e)}`,t)},relations:{list:e=>k(`/tags/relations?project=${T(e)}`),create:e=>I("/tags/relations",e),delete:e=>Z(`/tags/relations/${T(e)}`),listForWorkItem:(e,t)=>k(`/tags/relations?project=${encodeURIComponent(e)}&work_item_id=${encodeURIComponent(t)}`),listForTag:(e,t)=>k(`/tags/relations?project=${encodeURIComponent(e)}&tag_id=${encodeURIComponent(t)}`),approve:e=>fetch(N()+`/tags/relations/${encodeURIComponent(e)}`,{method:"PATCH",headers:O(),body:JSON.stringify({related_approved:"approved"})}).then(t=>t.ok?t.json():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText)))),reject:e=>fetch(N()+`/tags/relations/${encodeURIComponent(e)}`,{method:"PATCH",headers:O(),body:JSON.stringify({related_approved:"rejected"})}).then(t=>t.ok?t.json():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText))))}};m.workItems={list:(e,t,r)=>{const o=e&&typeof e=="object"?e:{project:e,category:t,status:r},n=new URLSearchParams({project:o.project||""});return o.category&&n.set("category",o.category),o.status&&n.set("status",o.status),o.name&&n.set("name",o.name),k(`/work-items?${n}`)},get:(e,t)=>k(`/work-items/${T(e)}?project=${T(t||"")}`),unlinked:e=>k(`/work-items/unlinked?project=${T(e||"")}`),rematchAll:e=>I(`/work-items/rematch-all?project=${T(e||"")}`,{}),create:(e,t)=>I(`/work-items?project=${T(e)}`,t),patch:(e,t,r)=>fetch(N()+`/work-items/${T(e)}?project=${T(t)}`,{method:"PATCH",headers:O(),body:JSON.stringify(r)}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),delete:(e,t)=>fetch(N()+`/work-items/${T(e)}?project=${T(t)}`,{method:"DELETE",headers:O()}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),interactions:(e,t,r=20)=>k(`/work-items/${T(e)}/interactions?project=${T(t)}&limit=${r}`),commits:(e,t,r=20)=>k(`/work-items/${T(e)}/commits?project=${T(t)}&limit=${r}`),merge:(e,t,r)=>fetch(N()+`/work-items/${T(e)}/merge?project=${T(r)}`,{method:"POST",headers:O(),body:JSON.stringify({merge_with:t})}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),dismerge:(e,t)=>fetch(N()+`/work-items/${T(e)}/dismerge?project=${T(t)}`,{method:"POST",headers:O()}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),facts:e=>k(`/work-items/facts?project=${T(e)}`),memoryItems:(e,t)=>{const r=new URLSearchParams({project:e||""});return t&&r.set("scope",t),k(`/work-items/memory-items?${r}`)},extract:(e,t)=>I(`/work-items/${T(e)}/extract?project=${T(t)}`)};m.agentRoles={list:(e="_global")=>k(`/agent-roles/?project=${T(e)}`),create:e=>I("/agent-roles/",e),patch:(e,t)=>fetch(N()+`/agent-roles/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),delete:e=>Z(`/agent-roles/${e}`),versions:e=>k(`/agent-roles/${e}/versions`),restore:(e,t)=>I(`/agent-roles/${e}/restore/${t}`,{}),availableTools:()=>k("/agent-roles/available-tools"),validateYaml:e=>I("/agent-roles/validate-yaml",e),syncYaml:e=>I("/agent-roles/sync-yaml",e),exportYaml:e=>fetch(N()+`/agent-roles/${e}/export-yaml`,{headers:O()}).then(t=>t.ok?t.text():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText))))};m.systemRoles={list:()=>k("/system-roles/"),create:e=>I("/system-roles/",e),patch:(e,t)=>fetch(N()+`/system-roles/${e}`,{method:"PATCH",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),delete:e=>Z(`/system-roles/${e}`),listLinks:e=>k(`/system-roles/agent-roles/${e}/links`),attach:(e,t)=>I(`/system-roles/agent-roles/${e}/links`,t),detach:(e,t)=>Z(`/system-roles/agent-roles/${e}/links/${t}`)};m.agents={listRoles:()=>k("/agents/roles"),listPipelines:()=>k("/agents/pipelines"),runAgent:e=>I("/agents/run",e),runPipeline:e=>I("/agents/run-pipeline",e),getRun:e=>k(`/agents/runs/${T(e)}`)};m.graphWorkflows={list:e=>k(`/graph/?project=${T(e)}`),create:e=>I("/graph/",e),get:e=>k(`/graph/${e}`),update:(e,t)=>fetch(N()+`/graph/${e}`,{method:"PUT",headers:O(),body:JSON.stringify(t)}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText)))),delete:e=>Z(`/graph/${e}`),createNode:(e,t)=>I(`/graph/${e}/nodes`,t),updateNode:(e,t,r)=>fetch(N()+`/graph/${e}/nodes/${t}`,{method:"PATCH",headers:O(),body:JSON.stringify(r)}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),deleteNode:(e,t)=>Z(`/graph/${e}/nodes/${t}`),createEdge:(e,t)=>I(`/graph/${e}/edges`,t),updateEdge:(e,t,r)=>fetch(N()+`/graph/${e}/edges/${t}`,{method:"PATCH",headers:O(),body:JSON.stringify(r)}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),deleteEdge:(e,t)=>Z(`/graph/${e}/edges/${t}`),startRun:(e,t)=>I(`/graph/${e}/runs`,t),getRun:e=>k(`/graph/runs/${e}`),listRuns:e=>k(`/graph/${e}/runs`),cancelRun:e=>Z(`/graph/runs/${e}`),decide:(e,t)=>I(`/graph/runs/${e}/decision`,t),approvalChat:(e,t)=>I(`/graph/runs/${e}/chat`,t),exportYAML:e=>fetch(N()+`/graph/${T(e)}/export-yaml`,{headers:O()}).then(t=>t.ok?t.text():t.json().then(r=>Promise.reject(new Error(r.detail||t.statusText)))),importYAML:(e,t)=>I(`/graph/import-yaml?project=${T(e)}`,{yaml_text:t}),recentRuns:(e,t=20)=>k(`/graph/runs/recent?project=${T(e)}&limit=${t}`),deliverables:e=>k(`/graph/runs/${T(e)}/deliverables`)};m.documents={list:e=>k(`/documents/?project=${T(e)}`),read:(e,t)=>k(`/documents/read?path=${T(e)}&project=${T(t)}`),save:(e,t,r)=>fetch(N()+`/documents/?project=${T(r)}`,{method:"PUT",headers:O(),body:JSON.stringify({path:e,content:t})}).then(o=>o.ok?o.json():o.json().then(n=>Promise.reject(new Error(n.detail||o.statusText)))),delete:(e,t)=>fetch(N()+`/documents/?path=${T(e)}&project=${T(t)}`,{method:"DELETE",headers:O()}).then(r=>r.ok?r.json():r.json().then(o=>Promise.reject(new Error(o.detail||r.statusText))))};m.pipeline={status:e=>k(`/memory/${T(e)}/pipeline-status`),templates:e=>k(`/memory/${T(e)}/workflow-templates`),runFromSnapshot:(e,t,r,o)=>I(`/tags/${T(e)}/snapshot/${t}/run-workflow?project=${T(r)}&workflow_id=${T(o)}`,{})};const Fr="aicli_recent_projects";function qo(e){let t=nr();t=[e,...t.filter(r=>r!==e)].slice(0,10),localStorage.setItem(Fr,JSON.stringify(t))}function nr(){try{return JSON.parse(localStorage.getItem(Fr)||"[]")}catch{return[]}}function p(e,t="info",r=3e3){let o=document.querySelector(".toast-container");o||(o=document.createElement("div"),o.className="toast-container",document.body.appendChild(o));const n=document.createElement("div");n.className=`toast ${t}`;const i={success:"✓",error:"✕",info:"ℹ"};n.innerHTML=`<span>${i[t]||"ℹ"}</span><span>${e}</span>`,o.appendChild(n),setTimeout(()=>{n.style.opacity="0",n.style.transition="opacity 0.3s",setTimeout(()=>n.remove(),300)},r)}async function Go(e){e.className="view active",e.style.cssText="display:flex;flex-direction:column;overflow:hidden;height:100%",e.innerHTML=`
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Admin Panel</span>
        <div style="flex:1"></div>
      </div>

      <!-- Tab bar -->
      <div style="display:flex;border-bottom:1px solid var(--border);flex-shrink:0;padding:0 1.25rem">
        ${["users","pricing","coupons","apikeys","usage","billing"].map((r,o)=>`
          <button id="admin-tab-${r}" onclick="window._adminTab('${r}')"
            style="padding:0.55rem 1rem;border:none;border-bottom:2px solid ${o===0?"var(--accent)":"transparent"};
                   background:none;cursor:pointer;font-size:0.75rem;
                   color:${o===0?"var(--text)":"var(--text2)"};
                   font-weight:${o===0?"600":"normal"};transition:all 0.15s">
            ${{users:"👥 Users",pricing:"💲 Pricing",coupons:"🎟 Coupons",apikeys:"🔑 API Keys",usage:"📊 Usage",billing:"🔬 Billing"}[r]}
          </button>
        `).join("")}
      </div>

      <div id="admin-body" style="flex:1;overflow-y:auto;padding:1rem 1.25rem"></div>
    </div>
  `,window._adminTab=r=>{["users","pricing","coupons","apikeys","usage","billing"].forEach(o=>{const n=document.getElementById(`admin-tab-${o}`);n&&(n.style.borderBottomColor=o===r?"var(--accent)":"transparent",n.style.color=o===r?"var(--text)":"var(--text2)",n.style.fontWeight=o===r?"600":"normal")}),t(r)};async function t(r){const o=document.getElementById("admin-body");if(o){o.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Loading…</div>';try{r==="users"&&await qt(o),r==="pricing"&&await Ko(o),r==="coupons"&&await Gt(o),r==="apikeys"&&await Wr(o),r==="usage"&&await qr(o),r==="billing"&&await Xo(o)}catch(n){o.innerHTML=`<div style="color:var(--red);font-size:0.75rem">Error: ${n.message}</div>`}}}await t("users"),window._adminRefreshUsers=async()=>{const r=document.getElementById("admin-stats-refresh"),o=document.getElementById("admin-body");r&&(r.style.opacity="0.3"),o&&await qt(o).catch(()=>{}),r&&(r.style.opacity="1"),window._updateBalance&&window._updateBalance().catch(()=>{})}}async function qt(e){const[t,r,o]=await Promise.all([m.adminListUsers(),m.adminGetStats(),m.adminGetProviderBalances().catch(()=>({}))]),n=t.users||[],i=r.by_provider||{};let a=null;Object.entries(o).forEach(([g,f])=>{if(f?.balance_usd!=null){const u=i[g]?.real_cost_usd||0;a===null&&(a=0),a+=Math.max(0,f.balance_usd-u)}});const s=a===null?"var(--muted)":a>=5?"var(--green)":a>=1?"var(--accent)":"var(--red)",d=g=>`$${(g||0).toFixed(2)}`,l=(g,f,u="var(--text)")=>`<div style="display:flex;flex-direction:column;gap:0.2rem">
       <div style="font-size:0.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em">${g}</div>
       <div style="font-size:0.95rem;font-weight:700;color:${u}">${f}</div>
     </div>`,c=`
    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;align-items:flex-start;background:var(--surface2);
                border:1px solid var(--border);border-radius:var(--radius);
                padding:0.85rem 1.2rem;margin-bottom:1.1rem;position:relative">
      ${l("Users",`${r.active_users??n.length} / ${r.user_count??n.length}`)}
      ${l("Total Balance",d(r.total_balance_usd),r.total_balance_usd>=0?"var(--green)":"var(--red)")}
      ${l("Total Added",d(r.total_added_usd))}
      ${l("Total Charged",d(r.total_charged_usd),"var(--accent)")}
      ${l("Real Cost",d(r.total_real_cost_usd),"var(--text2)")}
      ${l("Margin",d(r.total_margin_usd),r.total_margin_usd>=0?"var(--green)":"var(--red)")}
      ${l("API Budget",a!==null?d(a):"—",s)}
      <button onclick="window._adminRefreshUsers()" title="Refresh"
        style="position:absolute;top:0.5rem;right:0.5rem;background:none;border:none;
               color:var(--muted);cursor:pointer;font-size:0.8rem;padding:2px 5px;
               border-radius:4px;transition:opacity 0.2s" id="admin-stats-refresh">↺</button>
    </div>`;if(!n.length){e.innerHTML=c+'<div class="empty-state"><p>No users yet.</p></div>';return}e.innerHTML=c+`
    <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
      <thead>
        <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
          <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Email</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Role</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Balance</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Used</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Calls</th>
          <th style="text-align:center;padding:0.4rem 0.5rem;font-weight:500">Actions</th>
        </tr>
      </thead>
      <tbody id="admin-users-tbody">
        ${n.map(g=>Vo(g)).join("")}
      </tbody>
    </table>
  `,n.forEach(g=>Yo())}function Vo(e){const t=e.balance_usd??(e.balance_added_usd||0)-(e.balance_used_usd||0),r=e.role||(e.is_admin?"admin":"free");return`
    <tr id="urow-${e.id}" style="border-bottom:1px solid var(--border)">
      <td style="padding:0.5rem;color:var(--text)">${K(e.email)}</td>
      <td style="padding:0.5rem">
        <select id="role-${e.id}" style="background:var(--surface2);border:1px solid var(--border);
                border-radius:4px;color:var(--text);font-size:0.72rem;padding:2px 4px">
          ${["admin","paid","free"].map(o=>`<option value="${o}" ${r===o?"selected":""}>${o}</option>`).join("")}
        </select>
      </td>
      <td style="padding:0.5rem;text-align:right;color:${t>=.1?"var(--green)":t>=0?"var(--text2)":"var(--red)"}">
        $${t.toFixed(2)}
      </td>
      <td style="padding:0.5rem;text-align:right;color:var(--muted)">
        $${(e.balance_used_usd||0).toFixed(4)}
      </td>
      <td style="padding:0.5rem;text-align:right;color:var(--muted)">
        ${e.usage?.total_calls||0}
      </td>
      <td style="padding:0.5rem;text-align:center">
        <div style="display:flex;gap:4px;justify-content:center;align-items:center">
          <input id="credit-${e.id}" type="number" min="0" step="0.01" placeholder="$"
            style="width:55px;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;color:var(--text);font-size:0.72rem;padding:2px 5px" />
          <button id="credit-btn-${e.id}" onclick="window._adminCredit('${e.id}')"
            style="padding:2px 8px;background:var(--accent);border:none;border-radius:4px;
                   color:#fff;font-size:0.7rem;cursor:pointer">+$</button>
          <button onclick="window._adminSaveRole('${e.id}')"
            style="padding:2px 8px;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;color:var(--text2);font-size:0.7rem;cursor:pointer">✓</button>
          <button onclick="window._adminDelUser('${e.id}', '${K(e.email)}')"
            style="padding:2px 8px;background:none;border:1px solid var(--border);
                   border-radius:4px;color:var(--red);font-size:0.7rem;cursor:pointer">✕</button>
        </div>
      </td>
    </tr>
  `}function Yo(e){window._adminSaveRole=async t=>{const r=document.getElementById(`role-${t}`);if(r)try{await m.adminPatchUser(t,{role:r.value}),p("Role updated","success")}catch(o){p(`Error: ${o.message}`,"error")}},window._adminCredit=async t=>{const r=document.getElementById(`credit-${t}`);if(!r)return;const o=parseFloat(r.value);if(!o||o<=0){p("Enter a positive amount","error");return}try{await m.adminPatchUser(t,{credit_usd:o}),p(`$${o.toFixed(2)} credited`,"success"),r.value="";const n=document.getElementById("admin-body");n&&(n.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Refreshing…</div>',await qt(n))}catch(n){p(`Error: ${n.message}`,"error")}},window._adminDelUser=async(t,r)=>{if(confirm(`Deactivate user: ${r}?`))try{await m.adminDeleteUser(t),p(`User deactivated: ${r}`,"success");const o=document.getElementById(`urow-${t}`);o&&(o.style.opacity="0.3")}catch(o){p(`Error: ${o.message}`,"error")}}}function K(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ko(e){const t=await m.adminGetPricing(),r=["claude","openai","deepseek","gemini","grok"],o=["claude-sonnet-4-6","claude-haiku-4-5-20251001","gpt-4.1","deepseek-chat","gemini-2.0-flash","grok-3"];e.innerHTML=`
    <div style="max-width:600px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:1rem">Pricing Configuration</div>

      <div style="margin-bottom:1.25rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.4rem">Free Tier Limit (USD)</div>
        <input id="price-free-limit" type="number" min="0" step="0.5"
          value="${t.free_tier_limit_usd??5}"
          style="width:120px;background:var(--surface2);border:1px solid var(--border);
                 border-radius:6px;color:var(--text);font-size:0.82rem;padding:0.4rem 0.6rem" />
        <span style="font-size:0.65rem;color:var(--muted);margin-left:0.5rem">Maximum spend for free-tier users</span>
      </div>

      <div style="margin-bottom:1.25rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">Free Tier Models</div>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem">
          ${o.map(n=>`
            <label style="display:flex;align-items:center;gap:0.35rem;font-size:0.72rem;cursor:pointer;
                           background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:0.25rem 0.5rem">
              <input type="checkbox" id="ftm-${n.replace(/[^a-z0-9]/gi,"-")}"
                ${(t.free_tier_models||[]).includes(n)?"checked":""}
                style="accent-color:var(--accent)" />
              ${n}
            </label>
          `).join("")}
        </div>
      </div>

      <div style="margin-bottom:1.5rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">Markup % per Provider</div>
        <div style="display:flex;flex-direction:column;gap:0.5rem">
          ${r.map(n=>`
            <div style="display:flex;align-items:center;gap:0.75rem">
              <div style="width:80px;font-size:0.75rem">${n}</div>
              <input id="markup-${n}" type="number" min="0" max="500" step="5"
                value="${t.providers?.[n]?.markup_percent??0}"
                style="width:80px;background:var(--surface2);border:1px solid var(--border);
                       border-radius:6px;color:var(--text);font-size:0.8rem;padding:0.3rem 0.5rem" />
              <span style="font-size:0.68rem;color:var(--muted)">%</span>
            </div>
          `).join("")}
        </div>
      </div>

      <button onclick="window._savePricing()"
        style="padding:0.5rem 1.25rem;background:var(--accent);border:none;border-radius:6px;
               color:#fff;font-size:0.82rem;font-weight:600;cursor:pointer">
        Save Pricing
      </button>
      <span id="pricing-status" style="font-size:0.68rem;color:var(--muted);margin-left:0.75rem"></span>
    </div>
  `,window._savePricing=async()=>{const n=parseFloat(document.getElementById("price-free-limit").value)||5,i=o.filter(d=>document.getElementById(`ftm-${d.replace(/[^a-z0-9]/gi,"-")}`)?.checked),a={};r.forEach(d=>{const l=document.getElementById(`markup-${d}`);a[d]={markup_percent:parseFloat(l?.value||"0")}});const s=document.getElementById("pricing-status");try{await m.adminSavePricing({free_tier_limit_usd:n,free_tier_models:i,providers:a}),s&&(s.textContent="✓ Saved",s.style.color="var(--green)"),p("Pricing saved","success")}catch(d){s&&(s.textContent=`✕ ${d.message}`,s.style.color="var(--red)"),p(`Save failed: ${d.message}`,"error")}}}async function Gt(e){const r=(await m.adminGetCoupons()).coupons||[];e.innerHTML=`
    <div style="max-width:700px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:1rem">Coupon Codes</div>

      <!-- Create form -->
      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                  padding:0.75rem 1rem;margin-bottom:1.25rem">
        <div style="font-size:0.72rem;font-weight:600;margin-bottom:0.6rem">Create New Coupon</div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end">
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Code</div>
            <input id="new-coupon-code" placeholder="MYCODE" style="width:110px;${st()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Amount ($)</div>
            <input id="new-coupon-amount" type="number" min="0" step="0.5" value="10" style="width:80px;${st()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Max Uses</div>
            <input id="new-coupon-uses" type="number" min="1" value="999" style="width:80px;${st()}"/>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.2rem">Description</div>
            <input id="new-coupon-desc" placeholder="Optional" style="width:160px;${st()}"/>
          </div>
          <button onclick="window._createCoupon()"
            style="padding:0.4rem 1rem;background:var(--accent);border:none;border-radius:6px;
                   color:#fff;font-size:0.78rem;cursor:pointer;white-space:nowrap">
            + Create
          </button>
        </div>
        <div id="coupon-create-status" style="font-size:0.65rem;color:var(--muted);margin-top:0.4rem"></div>
      </div>

      <!-- Coupon table -->
      <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
        <thead>
          <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
            <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Code</th>
            <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Amount</th>
            <th style="text-align:right;padding:0.4rem 0.5rem;font-weight:500">Uses</th>
            <th style="text-align:left;padding:0.4rem 0.5rem;font-weight:500">Description</th>
            <th style="text-align:center;padding:0.4rem 0.5rem;font-weight:500">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${r.map(o=>`
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:0.5rem;font-family:monospace;color:var(--accent)">${K(o.code)}</td>
              <td style="padding:0.5rem;text-align:right">$${(o.amount_usd||0).toFixed(2)}</td>
              <td style="padding:0.5rem;text-align:right;color:var(--muted)">${o.used_count||0} / ${o.max_uses||"∞"}</td>
              <td style="padding:0.5rem;color:var(--text2)">${K(o.description||"")}</td>
              <td style="padding:0.5rem;text-align:center">
                <button onclick="window._deleteCoupon('${K(o.code)}')"
                  style="padding:2px 8px;background:none;border:1px solid var(--border);
                         border-radius:4px;color:var(--red);font-size:0.7rem;cursor:pointer">✕</button>
              </td>
            </tr>
          `).join("")}
          ${r.length?"":'<tr><td colspan="5" style="padding:1rem;text-align:center;color:var(--muted)">No coupons yet</td></tr>'}
        </tbody>
      </table>
    </div>
  `,window._createCoupon=async()=>{const o=document.getElementById("new-coupon-code")?.value.trim().toUpperCase(),n=parseFloat(document.getElementById("new-coupon-amount")?.value||"0"),i=parseInt(document.getElementById("new-coupon-uses")?.value||"1",10),a=document.getElementById("new-coupon-desc")?.value.trim(),s=document.getElementById("coupon-create-status");if(!o){s&&(s.textContent="Enter a code",s.style.color="var(--red)");return}if(!n||n<=0){s&&(s.textContent="Enter a positive amount",s.style.color="var(--red)");return}try{await m.adminCreateCoupon({code:o,amount_usd:n,max_uses:i,description:a}),s&&(s.textContent=`✓ Coupon ${o} created`,s.style.color="var(--green)"),p(`Coupon ${o} created`,"success");const d=document.getElementById("admin-body");d&&await Gt(d)}catch(d){s&&(s.textContent=`✕ ${d.message}`,s.style.color="var(--red)"),p(`Error: ${d.message}`,"error")}},window._deleteCoupon=async o=>{if(confirm(`Delete coupon ${o}?`))try{await m.adminDeleteCoupon(o),p(`Coupon ${o} deleted`,"success");const n=document.getElementById("admin-body");n&&await Gt(n)}catch(n){p(`Error: ${n.message}`,"error")}}}function st(){return"background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text);font-size:0.78rem;padding:0.3rem 0.5rem;"}async function Wr(e){const[t,r,o]=await Promise.all([m.adminGetApiKeys(),m.adminGetStats(),m.adminGetApiBalances().catch(()=>({}))]),n=r.by_provider||{},i=[{id:"claude",label:"Claude (Anthropic)"},{id:"openai",label:"OpenAI"},{id:"deepseek",label:"DeepSeek"},{id:"gemini",label:"Gemini"},{id:"grok",label:"Grok (xAI)"}],a=d=>{const l={saved:{label:"saved",color:"var(--green)",bg:"rgba(34,197,94,0.1)"},env:{label:"from .env",color:"var(--accent)",bg:"rgba(255,107,53,0.1)"},unset:{label:"not set",color:"var(--muted)",bg:"var(--surface2)"}}[d]||{label:d,color:"var(--muted)",bg:"var(--surface2)"};return`<span style="font-size:0.6rem;padding:1px 6px;border-radius:10px;
                         background:${l.bg};color:${l.color};font-weight:500">${l.label}</span>`},s=d=>d?.available?`<span style="font-size:0.65rem;font-weight:600;color:${d.balance_usd>=5?"var(--green)":d.balance_usd>=1?"var(--accent)":"var(--red)"}">
                live: $${d.balance_usd.toFixed(2)}
              </span>`:"";e.innerHTML=`
    <div style="max-width:680px">
      <div style="font-weight:700;font-size:0.8rem;margin-bottom:0.25rem">Server API Keys</div>
      <div style="font-size:0.65rem;color:var(--muted);margin-bottom:1.25rem">
        Keys are stored in <code>api_keys.json</code> — your <code>.env</code> file is never modified.
        Leave a key field blank to keep the current value.
        Provider balances are managed in the <strong>📊 Usage</strong> tab.
      </div>

      <div style="display:flex;flex-direction:column;gap:1.1rem">
        ${i.map(d=>{const l=t[d.id]||{masked:"",source:"unset"},c=n[d.id]||null,g=o[d.id]||null,f=c?`<span style="color:var(--accent)">$${c.charged_usd.toFixed(4)} charged</span>
               <span style="color:var(--muted)">·</span>
               <span style="color:var(--text2)">$${c.real_cost_usd.toFixed(4)} real</span>
               <span style="color:var(--muted)">·</span>
               <span>${c.calls} call${c.calls!==1?"s":""}</span>`:'<span style="color:var(--muted)">No usage recorded yet</span>';return`
          <div style="background:var(--surface2);border:1px solid var(--border);
                      border-radius:var(--radius);padding:0.65rem 0.85rem">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;flex-wrap:wrap">
              <div style="font-size:0.75rem;font-weight:600;color:var(--text)">${d.label}</div>
              ${a(l.source)}
              ${s(g)}
            </div>
            <div style="font-size:0.6rem;color:var(--muted);margin-bottom:0.55rem;
                        display:flex;gap:0.4rem;align-items:center;flex-wrap:wrap">
              <span style="color:var(--text2);font-weight:500">Tracked spend:</span>
              ${f}
            </div>
            <!-- API Key row -->
            <div style="display:flex;gap:0.5rem;align-items:center">
              <label style="font-size:0.6rem;color:var(--muted);white-space:nowrap;min-width:55px">API Key</label>
              <input id="apikey-${d.id}" type="password"
                placeholder="${l.masked?l.masked:"Not configured"}"
                style="flex:1;${st()}" />
              <button onclick="window._toggleKeyVis('${d.id}')"
                style="background:none;border:1px solid var(--border);border-radius:4px;
                       color:var(--text2);font-size:0.72rem;padding:4px 8px;cursor:pointer">👁</button>
            </div>
          </div>`}).join("")}
      </div>

      <div style="margin-top:1.25rem;display:flex;gap:0.75rem;align-items:center">
        <button onclick="window._saveApiKeys()"
          style="padding:0.5rem 1.25rem;background:var(--accent);border:none;border-radius:6px;
                 color:#fff;font-size:0.82rem;font-weight:600;cursor:pointer">
          Save Keys
        </button>
        <span id="apikeys-status" style="font-size:0.68rem;color:var(--muted)"></span>
      </div>
      <div style="margin-top:0.75rem;font-size:0.65rem;color:var(--muted)">
        <strong>Tracked spend</strong>: what this server has billed through these keys.<br>
        To set and track provider balances, open the <strong>📊 Usage</strong> tab.
      </div>
    </div>
  `,window._toggleKeyVis=d=>{const l=document.getElementById(`apikey-${d}`);l&&(l.type=l.type==="password"?"text":"password")},window._saveApiKeys=async()=>{const d=document.getElementById("apikeys-status");d&&(d.textContent="Saving…",d.style.color="var(--muted)");try{const l={};i.forEach(g=>{const f=document.getElementById(`apikey-${g.id}`)?.value.trim();f&&(l[g.id]=f)}),Object.keys(l).length&&await m.adminSaveApiKeys(l),d&&(d.textContent="✓ Saved",d.style.color="var(--green)"),p("Keys saved","success"),window._updateBalance&&window._updateBalance().catch(()=>{});const c=document.getElementById("admin-body");c&&await Wr(c)}catch(l){d&&(d.textContent=`✕ ${l.message}`,d.style.color="var(--red)"),p(`Error: ${l.message}`,"error")}}}async function qr(e){e.innerHTML='<div style="color:var(--muted);font-size:0.72rem;padding:1rem">Loading usage data…</div>';let t,r,o;try{[t,r,o]=await Promise.all([m.adminGetUsageTable(),m.adminGetProviderBalances().catch(()=>({})),m.adminGetStats().catch(()=>({}))])}catch(b){e.innerHTML=`
      <div style="color:var(--red);font-size:0.75rem;margin-bottom:0.5rem">Error loading usage: ${b.message}</div>
      <button onclick="window._adminTab('usage')" style="margin-top:0.75rem;padding:0.35rem 0.85rem;
        background:var(--surface2);border:1px solid var(--border);border-radius:4px;
        color:var(--text2);font-size:0.72rem;cursor:pointer">↺ Retry</button>`;return}const n=t.rows||[],i=t.system_rows||[],a=o.by_provider||{},s=[{id:"claude",label:"Claude (Anthropic)"},{id:"openai",label:"OpenAI"},{id:"deepseek",label:"DeepSeek"},{id:"gemini",label:"Gemini"},{id:"grok",label:"Grok (xAI)"}],d={};for(const b of i)b.api_balance?.available&&(d[b.provider]=b.api_balance);const l={};s.forEach(b=>{l[b.id]=r[b.id]?.balance_usd??""});const c=(b,z=4)=>b!=null?`$${Number(b).toFixed(z)}`:"—",g=b=>b!=null?Number(b).toLocaleString():"—",f=b=>b>0?"var(--green)":b<0?"var(--red)":"var(--text2)",u=(b,z="right")=>`<th style="text-align:${z};padding:0.4rem 0.6rem;font-weight:500;font-size:0.65rem;
               color:var(--muted);white-space:nowrap">${b}</th>`,h=s.map(b=>{const z=a[b.id]||null,y=r[b.id]||null,$=d[b.id]||null,E=z?.real_cost_usd??null,R=y?.balance_usd!=null?y.balance_usd:"",A=y?.updated_at?new Date(y.updated_at).toLocaleDateString():null;let F=null;R!==""&&E!=null&&(F=Number(R)-E);const M=E!=null?`$${Number(E).toFixed(4)}`:"—";let Q="—",te="var(--muted)";return F!=null?(Q=`$${F.toFixed(2)}`,te=F>=5?"var(--green)":F>=1?"var(--accent)":"var(--red)"):$?.available&&(Q=`$${$.balance_usd.toFixed(2)} (live)`,te=$.balance_usd>=5?"var(--green)":$.balance_usd>=1?"var(--accent)":"var(--red)"),`
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:0.45rem 0.6rem;font-size:0.75rem;font-weight:600;color:var(--text)">${K(b.label)}</td>
        <td style="padding:0.45rem 0.6rem;font-size:0.72rem;text-align:right;color:var(--accent)">${M}</td>
        <td style="padding:0.45rem 0.6rem;text-align:right">
          <input id="mbal-${b.id}" type="number" step="0.01" min="0"
            placeholder="0.00" value="${R}"
            style="width:90px;background:var(--surface);border:1px solid var(--border);
                   border-radius:4px;padding:0.2rem 0.45rem;font-size:0.72rem;
                   color:var(--text);text-align:right" />
        </td>
        <td style="padding:0.45rem 0.6rem;font-size:0.72rem;text-align:right;font-weight:600;color:${te}">${Q}</td>
        <td style="padding:0.45rem 0.6rem;font-size:0.65rem;color:var(--muted)">${A?`Updated ${A}`:"—"}</td>
      </tr>`}).join("");let _="";const C=n.map(b=>{const z=b.date!==_?`<tr><td colspan="10" style="padding:0.3rem 0.5rem;font-size:0.65rem;font-weight:600;
              color:var(--muted);background:var(--surface);border-top:1px solid var(--border);
              border-bottom:1px solid var(--border)">${b.date}</td></tr>`:"";return _=b.date,z+`
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:0.4rem 0.5rem;font-size:0.7rem;color:var(--muted)">${b.date}</td>
        <td style="padding:0.4rem 0.5rem;font-size:0.72rem;overflow:hidden;max-width:120px;
                   text-overflow:ellipsis;white-space:nowrap" title="${K(b.email)}">${K(b.email)}</td>
        <td style="padding:0.4rem 0.5rem;font-size:0.72rem;color:var(--text2)">${K(b.llm)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem">${g(b.tokens)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--text2)">${c(b.cost)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--accent)">${c(b.revenue)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:${f(b.margin)}">${c(b.margin)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem">${c(b.balance,2)}</td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--green)">
          ${b.topup_cash>0?`${c(b.topup_cash,2)} (${b.topup_cash_cnt}×)`:"—"}
        </td>
        <td style="padding:0.4rem 0.5rem;text-align:right;font-size:0.72rem;color:var(--accent)">
          ${b.topup_coupon>0?`${c(b.topup_coupon,2)} (${b.topup_coupon_cnt}×)`:"—"}
        </td>
      </tr>`}).join("");e.innerHTML=`
    <!-- Provider Balances section -->
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.4rem">
      <div style="font-weight:700;font-size:0.8rem">Provider Balances</div>
      <span id="bal-status" style="font-size:0.65rem;color:var(--muted)"></span>
      <button id="save-bal-btn" onclick="window._saveUsageBalances()" disabled
        style="margin-left:auto;padding:0.3rem 0.85rem;background:var(--accent);border:none;
               border-radius:5px;color:#fff;font-size:0.72rem;font-weight:600;cursor:pointer;opacity:0.4">
        Save Balances
      </button>
    </div>
    <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.6rem">
      Enter the current balance from your provider's billing dashboard.
      <em>Remaining</em> = manual balance − tracked spend on this server.
      Only <strong>DeepSeek</strong> shows a live balance via API.
    </div>
    <div style="border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-bottom:1.75rem">
      <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
        <thead>
          <tr style="background:var(--surface2);border-bottom:2px solid var(--border)">
            ${u("Provider","left")}
            ${u("Tracked Spend")}
            ${u("Manual Balance")}
            ${u("Remaining (est.)")}
            ${u("Last Updated","left")}
          </tr>
        </thead>
        <tbody>${h}</tbody>
      </table>
    </div>

    <!-- Usage table -->
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.25rem">
      <div style="font-weight:700;font-size:0.8rem">Usage & Revenue</div>
      <button onclick="window._adminTab('usage')"
        style="background:none;border:1px solid var(--border);border-radius:4px;
               color:var(--text2);font-size:0.7rem;padding:2px 7px;cursor:pointer"
        title="Refresh">↺ Refresh</button>
    </div>
    <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.6rem">
      Daily aggregated by user × LLM.
    </div>
    <div style="overflow-x:auto;border:1px solid var(--border);border-radius:6px">
      <table style="width:100%;border-collapse:collapse;font-size:0.75rem;min-width:720px">
        <thead>
          <tr style="background:var(--surface2);border-bottom:2px solid var(--border)">
            ${u("Date","left")}
            ${u("User","left")}
            ${u("LLM","left")}
            ${u("Tokens")}
            ${u("Cost")}
            ${u("Revenue")}
            ${u("Margin")}
            ${u("Balance")}
            ${u("Cash Topup")}
            ${u("Coupon Topup")}
          </tr>
        </thead>
        <tbody>
          ${C||`<tr><td colspan="10" style="padding:1.5rem;text-align:center;color:var(--muted);font-size:0.75rem">
            No usage data yet. Usage will appear here after the first chat message.
          </td></tr>`}
        </tbody>
      </table>
    </div>
  `;const S=document.getElementById("save-bal-btn"),v=()=>{const b=s.some(z=>{const y=document.getElementById(`mbal-${z.id}`)?.value.trim()??"",$=l[z.id]!==""?String(l[z.id]):"";return y!==$});S&&(S.disabled=!b,S.style.opacity=b?"1":"0.4")};s.forEach(b=>{document.getElementById(`mbal-${b.id}`)?.addEventListener("input",v)}),window._saveUsageBalances=async()=>{const b=document.getElementById("bal-status");S&&(S.disabled=!0,S.style.opacity="0.4"),b&&(b.textContent="Saving…",b.style.color="var(--muted)");try{const z={};s.forEach($=>{const E=document.getElementById(`mbal-${$.id}`)?.value.trim();E!==""&&(z[$.id]=parseFloat(E)||0)}),await m.adminSaveProviderBalances(z),p("Balances saved","success");const y=document.getElementById("admin-body");y&&await qr(y).catch(()=>{}),window._updateBalance&&window._updateBalance().catch(()=>{})}catch(z){b&&(b.textContent=`✕ ${z.message}`,b.style.color="var(--red)"),p(`Error: ${z.message}`,"error"),S&&(S.disabled=!1,S.style.opacity="1")}}}async function Xo(e){e.innerHTML='<div style="color:var(--muted);font-size:0.72rem;padding:1rem">Loading…</div>';let t,r;try{[t,r]=await Promise.all([m.adminGetProviderCosts(),m.adminGetProviderUsageHistory()])}catch(y){e.innerHTML=`<div style="color:var(--red);font-size:0.75rem">Error: ${y.message}</div>`;return}const o=t.model_list||[],n=r.records||[],i=t.updated_at?new Date(t.updated_at).toLocaleString():"never",a=t.updated_by||"",s=y=>String(y).replace(/[^a-zA-Z0-9]/g,"-"),d={};for(const y of o)d[y.provider]||(d[y.provider]=[]),d[y.provider].push(y);const l=Object.entries(d).map(([y,$])=>`
    <div style="margin-bottom:1.25rem">
      <div style="font-size:0.72rem;font-weight:700;color:var(--text);margin-bottom:0.4rem;
                  text-transform:capitalize">${K(y)}</div>
      <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
        <thead>
          <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
            <th style="text-align:left;padding:0.3rem 0.5rem;font-weight:500">Model</th>
            <th style="text-align:right;padding:0.3rem 0.5rem;font-weight:500">Input ($/token)</th>
            <th style="text-align:right;padding:0.3rem 0.5rem;font-weight:500">Output ($/token)</th>
          </tr>
        </thead>
        <tbody>
          ${$.map(E=>`
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:0.3rem 0.5rem;font-family:monospace;font-size:0.68rem;color:var(--text2)">${K(E.model)}</td>
              <td style="padding:0.3rem 0.5rem;text-align:right">
                <input type="number" step="0.000000001" min="0"
                  id="cost-${s(y)}-${s(E.model)}-in"
                  value="${E.input}"
                  style="width:110px;background:var(--surface);border:1px solid var(--border);
                         border-radius:4px;padding:0.2rem 0.4rem;font-size:0.68rem;
                         color:var(--text);text-align:right">
              </td>
              <td style="padding:0.3rem 0.5rem;text-align:right">
                <input type="number" step="0.000000001" min="0"
                  id="cost-${s(y)}-${s(E.model)}-out"
                  value="${E.output}"
                  style="width:110px;background:var(--surface);border:1px solid var(--border);
                         border-radius:4px;padding:0.2rem 0.4rem;font-size:0.68rem;
                         color:var(--text);text-align:right">
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `).join(""),c=y=>{const $=y.ok?"✓":"✕",E=y.ok?"var(--green)":"var(--red)",R=y.fetched_at?new Date(y.fetched_at).toLocaleString():"—",A=y.errors||[],F=y.notes||[],M=[...A,...F],Q=M.join(`
`)||"",te=A.length?"var(--red)":"var(--muted)";let j="—";y.mode==="local_recalculate"?j=`${y.records_processed||0} recs · $${(y.total_estimated_usd||0).toFixed(4)}`:y.total_prompt_tokens!=null?j=`↑${y.total_prompt_tokens.toLocaleString()} ↓${(y.total_completion_tokens||0).toLocaleString()}`:y.total_input_tokens!=null&&(j=`↑${y.total_input_tokens.toLocaleString()} ↓${(y.total_output_tokens||0).toLocaleString()}`);const W=y.mode==="local_recalculate"?"local":y.provider||"—",ae=y.provider||y.mode||"local_recalculate",Ie=M.length?M[0].slice(0,60)+(M[0].length>60||M.length>1?"…":""):"",Ke=Q?`<button onclick="navigator.clipboard.writeText(${JSON.stringify(Q)}).then(()=>window._cpToast())"
           style="margin-left:4px;background:none;border:1px solid var(--border);border-radius:3px;
                  font-size:0.58rem;padding:1px 4px;cursor:pointer;color:var(--muted)" title="Copy errors">📋</button>`:"";return`
      <tr style="border-bottom:1px solid var(--border)">
        <td style="padding:0.35rem 0.5rem;font-size:0.65rem;color:var(--muted);white-space:nowrap">${R}</td>
        <td style="padding:0.35rem 0.5rem;font-size:0.72rem;text-transform:capitalize">${K(W)}</td>
        <td style="padding:0.35rem 0.5rem;font-size:0.68rem;color:var(--muted);white-space:nowrap">${K(y.start_date||"—")} → ${K(y.end_date||"—")}</td>
        <td style="padding:0.35rem 0.5rem;font-size:0.72rem;font-weight:700;color:${E};text-align:center">${$}</td>
        <td style="padding:0.35rem 0.5rem;font-size:0.68rem;text-align:right;white-space:nowrap">${j}</td>
        <td style="padding:0.35rem 0.5rem;font-size:0.62rem;color:${te};max-width:240px">
          <span title="${K(Q)}">${K(Ie)}</span>${Ke}
        </td>
        <td style="padding:0.35rem 0.5rem;text-align:center">
          <button data-prov="${K(ae)}" data-ts="${K(y.fetched_at||"")}"
            onclick="window._deleteHistRow(this.dataset.prov, this.dataset.ts)"
            style="background:none;border:1px solid var(--border);border-radius:3px;
                   font-size:0.65rem;padding:1px 5px;color:var(--red);cursor:pointer"
            title="Delete this record">✕</button>
        </td>
      </tr>`},g=`<tr><td colspan="7" style="padding:1rem;text-align:center;color:var(--muted);font-size:0.72rem">
    No usage fetches yet. Use "⚡ Local Recalculate" above to estimate costs from local data.
  </td></tr>`,f=n.length?n.map(c).join(""):g,u=new Date().toISOString().slice(0,10),h=new Date(Date.now()-7*864e5).toISOString().slice(0,10);e.innerHTML=`
    <!-- Cost Config Section -->
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem">
      <div style="font-weight:700;font-size:0.8rem">Provider Cost Config</div>
      <span style="font-size:0.65rem;color:var(--muted)">
        Last updated: <strong>${K(i)}</strong>${a?` by ${K(a)}`:""}
      </span>
      <button id="save-costs-btn" onclick="window._saveCosts()" disabled
        style="margin-left:auto;padding:0.35rem 0.9rem;background:var(--accent);border:none;
               border-radius:5px;color:#fff;font-size:0.72rem;font-weight:600;cursor:pointer;opacity:0.4">
        Save Costs
      </button>
      <span id="costs-status" style="font-size:0.65rem;color:var(--muted)"></span>
    </div>
    <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.75rem">
      Per-token pricing used for real-time cost estimation. Values are in USD per token
      (e.g. 0.000003 = $3 per 1M tokens). Updated at: <em>${K(i)}</em>.
    </div>

    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;
                padding:1rem;margin-bottom:1.5rem;max-height:400px;overflow-y:auto">
      ${l}
    </div>

    <!-- Fetch Provider Usage Section -->
    <div style="font-weight:700;font-size:0.8rem;margin-bottom:0.5rem">Fetch / Estimate Usage</div>

    <div style="font-size:0.65rem;background:rgba(255,107,53,0.07);border:1px solid rgba(255,107,53,0.2);
                border-radius:4px;padding:0.5rem 0.75rem;margin-bottom:0.75rem;color:var(--text2);line-height:1.55">
      <strong>OpenAI</strong>: First tries the Admin API (<code>/v1/organization/usage/completions</code>) — requires
      an <strong>Admin API key</strong> from <em>platform.openai.com → Organization → Admin keys</em>.
      Falls back to legacy per-day API (<code>/v1/usage?date=</code>) which works with regular API keys.
      The billing dashboard (<code>/v1/dashboard/billing/*</code>) cannot be called with API keys (browser-only).<br>
      <strong>Anthropic</strong>: Requires an <strong>Admin API key</strong> (<code>sk-ant-admin-…</code>) and
      your <strong>Org ID</strong> from <em>console.anthropic.com → Settings</em>. Regular workspace keys
      return 403. Beta feature — may not be available for all accounts.<br>
      <strong>Local Recalculate</strong>: Re-estimates cost from our own usage_logs using the current cost config above.
      No provider API key needed — recommended as the primary method.
    </div>

    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;
                padding:1rem;margin-bottom:1rem">
      <div style="display:flex;flex-wrap:wrap;gap:0.75rem;align-items:flex-end">
        <div style="display:flex;flex-direction:column;gap:0.25rem">
          <label style="font-size:0.65rem;color:var(--muted)">Source</label>
          <select id="fetch-provider"
            style="background:var(--surface);border:1px solid var(--border);border-radius:4px;
                   padding:0.3rem 0.5rem;font-size:0.72rem;color:var(--text)">
            <option value="local">⚡ Local Recalculate (no API key needed)</option>
            <option value="openai">OpenAI API (Admin or regular key)</option>
            <option value="anthropic">Anthropic API (Admin key + Org ID)</option>
          </select>
        </div>
        <div style="display:flex;flex-direction:column;gap:0.25rem">
          <label style="font-size:0.65rem;color:var(--muted)">Start Date</label>
          <input type="date" id="fetch-start" value="${h}"
            style="background:var(--surface);border:1px solid var(--border);border-radius:4px;
                   padding:0.3rem 0.5rem;font-size:0.72rem;color:var(--text)">
        </div>
        <div style="display:flex;flex-direction:column;gap:0.25rem">
          <label style="font-size:0.65rem;color:var(--muted)">End Date</label>
          <input type="date" id="fetch-end" value="${u}"
            style="background:var(--surface);border:1px solid var(--border);border-radius:4px;
                   padding:0.3rem 0.5rem;font-size:0.72rem;color:var(--text)">
        </div>
        <div id="org-id-wrap" style="display:none;flex-direction:column;gap:0.25rem">
          <label style="font-size:0.65rem;color:var(--muted)">Org ID (Anthropic)</label>
          <input type="text" id="fetch-org-id" placeholder="org-XXXXXXXXXXXX"
            style="background:var(--surface);border:1px solid var(--border);border-radius:4px;
                   padding:0.3rem 0.5rem;font-size:0.72rem;color:var(--text);width:180px">
        </div>
        <button id="fetch-usage-btn" onclick="window._fetchProviderUsage()"
          style="padding:0.35rem 0.9rem;background:var(--accent);border:none;border-radius:5px;
                 color:#fff;font-size:0.72rem;font-weight:600;cursor:pointer">
          ↓ Run
        </button>
        <span id="fetch-status" style="font-size:0.65rem;color:var(--muted);max-width:320px;word-break:break-word"></span>
      </div>
      <!-- Notes/warnings from last fetch -->
      <div id="fetch-notes" style="margin-top:0.6rem;font-size:0.65rem;color:var(--text2);display:none;
                                    background:var(--surface);border-left:3px solid var(--accent);
                                    border-radius:2px;padding:0.4rem 0.6rem;line-height:1.55;
                                    position:relative">
        <button onclick="window._copyNotes()" title="Copy to clipboard"
          style="position:absolute;top:4px;right:4px;background:var(--surface2);border:1px solid var(--border);
                 border-radius:4px;padding:2px 7px;font-size:0.6rem;color:var(--text2);cursor:pointer">📋 Copy</button>
      </div>
    </div>

    <!-- Fetch History -->
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.4rem">
      <div style="font-weight:700;font-size:0.8rem">Fetch History</div>
      <button onclick="window._refreshBillingHistory()" title="Refresh"
        style="background:none;border:1px solid var(--border);border-radius:4px;
               color:var(--text2);font-size:0.7rem;padding:2px 7px;cursor:pointer">↺</button>
      <button onclick="window._clearBillingHistory()" title="Clear all"
        style="background:none;border:1px solid var(--border);border-radius:4px;
               color:var(--red);font-size:0.7rem;padding:2px 7px;cursor:pointer">🗑 Clear all</button>
    </div>
    <div id="billing-history-wrap"
         style="overflow:auto;max-height:320px;border:1px solid var(--border);border-radius:6px">
      <table style="width:100%;border-collapse:collapse;font-size:0.72rem;min-width:640px">
        <thead style="position:sticky;top:0;background:var(--surface2);z-index:1">
          <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
            <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:500">Fetched At</th>
            <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:500">Source</th>
            <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:500">Date Range</th>
            <th style="text-align:center;padding:0.35rem 0.5rem;font-weight:500">OK</th>
            <th style="text-align:right;padding:0.35rem 0.5rem;font-weight:500">Result</th>
            <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:500">Errors / Notes</th>
            <th style="text-align:center;padding:0.35rem 0.5rem;font-weight:500"></th>
          </tr>
        </thead>
        <tbody id="billing-hist-tbody">${f}</tbody>
      </table>
    </div>
  `;const _=()=>{const y={};for(const[$,E]of Object.entries(d))for(const R of E)y[`${$}|${R.model}|in`]=document.getElementById(`cost-${s($)}-${s(R.model)}-in`)?.value??"",y[`${$}|${R.model}|out`]=document.getElementById(`cost-${s($)}-${s(R.model)}-out`)?.value??"";return y};let C=_();const S=document.getElementById("save-costs-btn"),v=()=>{const y=_(),$=Object.keys(y).some(E=>y[E]!==C[E]);S&&(S.disabled=!$,S.style.opacity=$?"1":"0.4")};for(const[y,$]of Object.entries(d))for(const E of $)document.getElementById(`cost-${s(y)}-${s(E.model)}-in`)?.addEventListener("input",v),document.getElementById(`cost-${s(y)}-${s(E.model)}-out`)?.addEventListener("input",v);const b=document.getElementById("fetch-provider"),z=document.getElementById("org-id-wrap");if(b&&z){const y=()=>{z.style.display=b.value==="anthropic"?"flex":"none"};b.addEventListener("change",y),y()}window._copyNotes=()=>{const y=document.getElementById("fetch-notes"),$=y?y.innerText.replace("📋 Copy","").trim():"";$&&navigator.clipboard.writeText($).then(()=>window._cpToast())},window._cpToast=()=>p("Copied to clipboard","success"),window._deleteHistRow=async(y,$)=>{try{await m.adminDeleteProviderUsageRecord(y,$);const E=await m.adminGetProviderUsageHistory(),R=document.getElementById("billing-hist-tbody");R&&(R.innerHTML=(E.records||[]).length?(E.records||[]).map(c).join(""):g)}catch(E){p(`Delete failed: ${E.message}`,"error")}},window._refreshBillingHistory=async()=>{try{const y=await m.adminGetProviderUsageHistory(),$=document.getElementById("billing-hist-tbody");$&&($.innerHTML=(y.records||[]).length?(y.records||[]).map(c).join(""):g)}catch(y){p(`Error: ${y.message}`,"error")}},window._clearBillingHistory=async()=>{if(confirm("Clear all fetch history records?"))try{for(const $ of["openai","anthropic","local_recalculate"])await m.adminClearProviderUsageHistory($).catch(()=>{});const y=document.getElementById("billing-hist-tbody");y&&(y.innerHTML=g),p("History cleared","success")}catch(y){p(`Error: ${y.message}`,"error")}},window._saveCosts=async()=>{const y=document.getElementById("costs-status");S&&(S.disabled=!0,S.style.opacity="0.4"),y&&(y.textContent="Saving…",y.style.color="var(--muted)");try{const $={};for(const[E,R]of Object.entries(d)){$[E]={};for(const A of R){const F=document.getElementById(`cost-${s(E)}-${s(A.model)}-in`),M=document.getElementById(`cost-${s(E)}-${s(A.model)}-out`);$[E][A.model]={input:parseFloat(F?.value||A.input),output:parseFloat(M?.value||A.output)}}}await m.adminSaveProviderCosts({providers:$}),y&&(y.textContent="✓ Saved",y.style.color="var(--green)"),p("Provider costs saved","success"),C=_(),v()}catch($){y&&(y.textContent=`✕ ${$.message}`,y.style.color="var(--red)"),p(`Error: ${$.message}`,"error"),S&&(S.disabled=!1,S.style.opacity="1")}},window._fetchProviderUsage=async()=>{const y=document.getElementById("fetch-provider")?.value,$=document.getElementById("fetch-start")?.value,E=document.getElementById("fetch-end")?.value,R=document.getElementById("fetch-org-id")?.value?.trim()||null,A=document.getElementById("fetch-status"),F=document.getElementById("fetch-usage-btn");if(!$||!E){p("Please select a date range","error");return}F&&(F.disabled=!0),A&&(A.textContent="Fetching…",A.style.color="var(--muted)");try{const M=await m.adminFetchProviderUsage({provider:y,start_date:$,end_date:E,org_id:R}),Q=document.getElementById("fetch-notes"),te=[...M.notes||[],...M.errors||[]];if(Q&&te.length?(Q.innerHTML=te.map(j=>`<div>⚠ ${K(j)}</div>`).join(""),Q.style.display="block"):Q&&(Q.style.display="none"),M.ok){let j="";M.mode==="local_recalculate"?j=`${M.records_processed} records · est. $${(M.total_estimated_usd||0).toFixed(4)}`:M.total_prompt_tokens!=null?j=`${(M.total_prompt_tokens||0).toLocaleString()} prompt / ${(M.total_completion_tokens||0).toLocaleString()} completion tokens`:M.total_input_tokens!=null?j=`${(M.total_input_tokens||0).toLocaleString()} in / ${(M.total_output_tokens||0).toLocaleString()} out tokens`:j="done",A&&(A.textContent=`✓ ${j}`,A.style.color="var(--green)"),p(`Done: ${j}`,"success")}else{const j=M.error||(M.errors||[]).slice(0,1).join("")||"Unknown error";A&&(A.textContent=`✕ ${j}`,A.style.color="var(--red)"),p(`Failed: ${j.slice(0,80)}`,"error")}try{const j=await m.adminGetProviderUsageHistory(),W=document.getElementById("billing-hist-tbody");W&&(W.innerHTML=j.records?.length?j.records.map(c).join(""):g)}catch{}}catch(M){A&&(A.textContent=`✕ ${M.message}`,A.style.color="var(--red)"),p(`Error: ${M.message}`,"error")}finally{F&&(F.disabled=!1)}}}function Gr(e,t,r,o=null){let n="login";function i(){const d=n==="register";e.innerHTML=`
      <div class="login-overlay">
        <div class="login-card">
          ${o?`
          <button id="login-close-btn" title="Close" style="
            position:absolute;top:0.75rem;right:0.75rem;
            background:none;border:none;color:var(--text2,#888);
            font-size:1rem;cursor:pointer;width:28px;height:28px;
            display:flex;align-items:center;justify-content:center;
            border-radius:50%;transition:background 0.15s;line-height:1
          ">✕</button>`:""}
          <div class="login-logo">aicli</div>
          <div class="login-subtitle">AI-powered dev CLI</div>

          <div class="login-tabs">
            <button class="login-tab ${d?"":"active"}" id="tab-login">Sign in</button>
            <button class="login-tab ${d?"active":""}" id="tab-register">Create account</button>
          </div>

          <form id="login-form">
            <div class="login-field">
              <label>Email</label>
              <input type="email" id="login-email" placeholder="you@example.com" autocomplete="email" required />
            </div>
            <div class="login-field">
              <label>Password</label>
              <input type="password" id="login-password" placeholder="••••••••" autocomplete="${d?"new-password":"current-password"}" required />
            </div>
            ${d?`
            <div class="login-field">
              <label>Confirm password</label>
              <input type="password" id="login-confirm" placeholder="••••••••" autocomplete="new-password" required />
            </div>
            <div class="login-field">
              <label>Coupon code <span style="color:var(--text2,#777);font-weight:400">(optional)</span></label>
              <input type="text" id="login-coupon" placeholder="e.g. AICLI" autocomplete="off" />
            </div>`:""}
            <div id="login-error" class="login-error" style="display:none"></div>
            <button type="submit" class="login-btn" id="login-submit">
              ${d?"Create account":"Sign in"}
            </button>
          </form>

          <div class="login-note">
            API keys are managed by the server admin.
            The server tracks token usage for billing purposes.
          </div>
        </div>
      </div>
    `,Jo();const l=document.getElementById("login-close-btn");l&&o&&(l.onclick=o,l.onmouseenter=()=>{l.style.background="rgba(128,128,128,0.15)"},l.onmouseleave=()=>{l.style.background="none"}),document.getElementById("tab-login").onclick=()=>{n="login",i()},document.getElementById("tab-register").onclick=()=>{n="register",i()},document.getElementById("login-form").onsubmit=c=>a(c)}async function a(d){d.preventDefault();const l=document.getElementById("login-email").value.trim(),c=document.getElementById("login-password").value,g=document.getElementById("login-error"),f=document.getElementById("login-submit");if(n==="register"){const h=document.getElementById("login-confirm").value;if(c!==h){s("Passwords do not match");return}}f.disabled=!0,f.textContent="Working…",g.style.display="none";const u=n==="register"?"/auth/register":"/auth/login";try{const h=await fetch(`${t}${u}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:l,password:c})}),_=await h.json();if(!h.ok){const C=_.detail,S=Array.isArray(C)?C.map(v=>v.msg||JSON.stringify(v)).join("; "):typeof C=="string"?C:"Authentication failed";s(S);return}if(localStorage.setItem("aicli_token",_.token),localStorage.setItem("aicli_user",JSON.stringify(_.user)),n==="register"){const S=document.getElementById("login-coupon")?.value.trim();if(S)try{await fetch(`${t}/billing/apply-coupon`,{method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${_.token}`},body:JSON.stringify({code:S})})}catch{}}e.innerHTML="",r(_.token,_.user)}catch(h){s(`Connection error: ${h.message}`)}finally{f.disabled=!1,f.textContent=n==="register"?"Create account":"Sign in"}}function s(d){const l=document.getElementById("login-error");l&&(l.textContent=d,l.style.display="block")}i()}async function Vr(e){const t=localStorage.getItem("aicli_token");if(!t)return{valid:!1,token:null,user:null};try{const r=await fetch(`${e}/auth/me`,{headers:{Authorization:`Bearer ${t}`}});if(r.ok){const o=await r.json();return{valid:!0,token:t,user:o}}}catch{}return{valid:!1,token:null,user:null}}function Yr(){localStorage.removeItem("aicli_token"),localStorage.removeItem("aicli_user")}function Jo(){if(document.getElementById("login-styles"))return;const e=document.createElement("style");e.id="login-styles",e.textContent=`
    .login-overlay {
      position: fixed; inset: 0;
      background: var(--bg, #0d0d0d);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999;
    }
    .login-card {
      background: var(--surface, #1a1a1a);
      border: 1px solid var(--border, #333);
      border-radius: 12px;
      padding: 2rem 2.5rem;
      width: 100%; max-width: 400px;
      box-shadow: 0 24px 64px rgba(0,0,0,.6);
      position: relative;
    }
    .login-logo {
      font-family: var(--font-ui, monospace);
      font-size: 1.8rem; font-weight: 900;
      letter-spacing: -2px; color: var(--accent, #7c5cbf);
      margin-bottom: 0.2rem;
    }
    .login-subtitle {
      font-size: 0.72rem; color: var(--text2, #777);
      margin-bottom: 1.5rem;
    }
    .login-tabs {
      display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
    }
    .login-tab {
      flex: 1; padding: 0.45rem;
      background: transparent;
      border: 1px solid var(--border, #333);
      border-radius: 6px;
      color: var(--text2, #888);
      cursor: pointer; font-size: 0.8rem;
      transition: all 0.15s;
    }
    .login-tab.active {
      background: var(--accent, #7c5cbf);
      border-color: var(--accent, #7c5cbf);
      color: #fff;
    }
    .login-field { margin-bottom: 1rem; }
    .login-field label {
      display: block; font-size: 0.72rem;
      color: var(--text2, #777); margin-bottom: 0.35rem;
    }
    .login-field input {
      width: 100%; box-sizing: border-box;
      padding: 0.55rem 0.75rem;
      background: var(--bg, #111);
      border: 1px solid var(--border, #333);
      border-radius: 6px;
      color: var(--text, #eee);
      font-size: 0.88rem;
      outline: none;
    }
    .login-field input:focus { border-color: var(--accent, #7c5cbf); }
    .login-error {
      background: #3d1515; border: 1px solid #7a2a2a;
      border-radius: 6px; padding: 0.5rem 0.75rem;
      color: #ff8080; font-size: 0.78rem;
      margin-bottom: 0.75rem;
    }
    .login-btn {
      width: 100%; padding: 0.65rem;
      background: var(--accent, #7c5cbf);
      border: none; border-radius: 6px;
      color: #fff; font-size: 0.9rem; font-weight: 600;
      cursor: pointer; transition: opacity 0.15s;
    }
    .login-btn:hover { opacity: 0.88; }
    .login-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .login-note {
      margin-top: 1.25rem;
      font-size: 0.67rem; color: var(--text2, #555);
      text-align: center; line-height: 1.5;
    }
  `,document.head.appendChild(e)}const Qo=Object.freeze(Object.defineProperty({__proto__:null,checkStoredAuth:Vr,logout:Yr,renderLogin:Gr},Symbol.toStringTag,{value:"Module"}));function Vt(e){e.className="view active",e.style.cssText="overflow-y:auto;padding:2rem;";const t=nr(),r=x.projects||[],o=[...r].sort((n,i)=>{const a=t.indexOf(n.name),s=t.indexOf(i.name);return a===-1&&s===-1?n.name.localeCompare(i.name):a===-1?1:s===-1?-1:a-s});e.innerHTML=`
    <div style="max-width:800px;margin:0 auto">

      <!-- Header -->
      <div style="margin-bottom:2rem">
        <div style="font-family:var(--font-ui);font-size:1.8rem;font-weight:900;letter-spacing:-2px;color:var(--text)">
          ai<span style="color:var(--accent)">cli</span>
        </div>
        <div style="font-size:0.7rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:0.25rem">
          Multi-LLM developer command centre
        </div>
      </div>

      <!-- Recent projects -->
      ${t.length>0?`
        <div style="margin-bottom:2rem">
          <div style="font-family:var(--font-ui);font-size:0.75rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text2);margin-bottom:0.75rem">
            Recent
          </div>
          <div style="display:flex;flex-direction:column;gap:0.35rem">
            ${t.slice(0,5).map(n=>{const i=r.find(a=>a.name===n);return`
                <div onclick="window._openProject('${n}')"
                  data-project-name="${n}"
                  style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.85rem;
                    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                    cursor:pointer;transition:border-color 0.15s"
                  onmouseenter="this.style.borderColor='var(--accent)'"
                  onmouseleave="this.style.borderColor='var(--border)'">
                  <span style="color:var(--accent)">◫</span>
                  <span style="flex:1;font-size:0.82rem">${n}</span>
                  ${i?.description?`<span style="font-size:0.65rem;color:var(--muted)">${i.description}</span>`:""}
                  ${i?.default_provider?`<span style="font-size:0.6rem;color:var(--text2);letter-spacing:1px;text-transform:uppercase">${i.default_provider}</span>`:""}
                  <span style="color:var(--muted);font-size:0.7rem">→</span>
                </div>
              `}).join("")}
          </div>
        </div>
      `:""}

      <!-- All projects -->
      <div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
          <div style="font-family:var(--font-ui);font-size:0.75rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text2)">
            ${r.length>0?"All Projects":"Get Started"}
          </div>
          <button class="btn btn-primary btn-sm" onclick="window._showNewProject()">+ New Project</button>
        </div>

        ${r.length===0?`
          <div class="empty-state" style="padding:3rem">
            <div class="empty-state-icon">◫</div>
            <p>No projects yet</p>
            <p style="font-size:0.7rem;color:var(--muted);margin-top:0.5rem">Create a project to organise your prompts, chats, and workflows.</p>
            <button class="btn btn-primary btn-sm" style="margin-top:1rem" onclick="window._showNewProject()">Create first project</button>
          </div>
        `:`
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem">
            ${o.map(n=>`
              <div onclick="window._openProject('${n.name}')"
                data-project-name="${n.name}"
                style="padding:1rem 1.1rem;background:var(--surface);border:1px solid var(--border);
                  border-radius:var(--radius-lg);cursor:pointer;transition:border-color 0.15s"
                onmouseenter="this.style.borderColor='var(--accent)'"
                onmouseleave="this.style.borderColor='var(--border)'">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">
                  <span style="color:var(--accent)">◫</span>
                  <span style="font-size:0.85rem;font-weight:600">${n.name}</span>
                </div>
                <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.4rem">${n.description||"No description"}</div>
                <div style="font-size:0.58rem;color:var(--text2);letter-spacing:1px;text-transform:uppercase">
                  ${n.default_provider||"claude"}${n.active?' · <span style="color:var(--green)">active</span>':""}
                </div>
              </div>
            `).join("")}
          </div>
        `}
      </div>

    </div>
  `,Zo()}function Zo(){window._showNewProject=()=>{const e={step:1,name:"",description:"",code_dir:"",template:"blank",provider:"claude",git:null,claude_cli:!1,cursor:!1},t=document.createElement("div");t.className="modal-overlay open",document.body.appendChild(t),t.addEventListener("click",o=>{o.target===t&&t.remove()});function r(){const n=["Basics","Git","IDE Support","Review"].map((s,d)=>{const l=d+1===e.step,c=d+1<e.step;return`<span style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.7rem;
          color:${l?"var(--accent)":c?"var(--green)":"var(--muted)"}">
          <span style="width:8px;height:8px;border-radius:50%;background:${l?"var(--accent)":c?"var(--green)":"var(--border)"}"></span>
          ${s}
        </span>`}).join('<span style="color:var(--border);margin:0 0.3rem">–</span>'),i=`<button class="btn btn-ghost btn-sm" style="position:absolute;top:1rem;right:1rem"
        onclick="window._wizardSkip()">Skip for now →</button>`;let a="";e.step===1&&(a=en(e)),e.step===2&&(a=tn(e)),e.step===3&&(a=rn(e)),e.step===4&&(a=on(e)),t.innerHTML=`
        <div class="modal" style="min-width:480px;max-width:580px;position:relative">
          <div style="margin-bottom:1.2rem">
            <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.5rem">
              Step ${e.step} of 4
            </div>
            <div style="display:flex;align-items:center;gap:0.2rem;flex-wrap:wrap">${n}</div>
          </div>
          ${e.step>1&&e.step<4?i:""}
          ${a}
        </div>
      `,window._wizardNext=()=>nn(e,t,r),window._wizardBack=()=>{e.step--,r()},window._wizardSkip=()=>{e.step++,r()},window._wizardCreate=()=>sn(e,t),window._pickCodeDir=async()=>{const s=await window.electronAPI?.openDirectory();if(s){const d=document.getElementById("np-code");d&&(d.value=s,e.code_dir=s),an(e.code_dir)}},window._wizardGitTabSwitch=s=>{document.getElementById("git-oauth-tab").style.display=s==="oauth"?"":"none",document.getElementById("git-pat-tab").style.display=s==="pat"?"":"none",document.querySelectorAll("[data-git-tab]").forEach(d=>{d.style.borderBottom=d.dataset.gitTab===s?"2px solid var(--accent)":"2px solid transparent"})}}r()}}function en(e){return`
    <div class="modal-title">New Project</div>
    <div class="modal-subtitle">A project contains prompts, chat history, and workflows.</div>

    <div class="field-group">
      <div class="field-label">Project name <span style="color:var(--red)">*</span></div>
      <input class="field-input" id="np-name" placeholder="my-project" autofocus
        value="${e.name}" oninput="window._wizard.name=this.value.replace(/\\s+/g,'-')" />
    </div>
    <div class="field-group">
      <div class="field-label">Description</div>
      <input class="field-input" id="np-desc" placeholder="What is this project for?"
        value="${e.description}" oninput="window._wizard.description=this.value" />
    </div>
    <div class="field-group">
      <div class="field-label">Code folder <span style="font-weight:400;color:var(--muted)">(optional)</span></div>
      <div style="display:flex;gap:0.5rem">
        <input class="field-input" id="np-code" placeholder="/path/to/your/code" style="flex:1"
          value="${e.code_dir}" oninput="window._wizard.code_dir=this.value" />
        <button class="btn btn-ghost btn-sm" onclick="window._pickCodeDir()">Browse…</button>
      </div>
    </div>
    <div class="field-group">
      <div class="field-label">Template</div>
      <select class="field-input" id="np-template" onchange="window._wizard.template=this.value">
        ${["blank","python_api","quant_notebook","ui_app"].map(t=>`<option value="${t}"${e.template===t?" selected":""}>${t}</option>`).join("")}
      </select>
    </div>
    <div class="field-group">
      <div class="field-label">Default provider</div>
      <select class="field-input" id="np-provider" onchange="window._wizard.provider=this.value">
        ${["claude","openai","deepseek","gemini","grok"].map(t=>`<option value="${t}"${e.provider===t?" selected":""}>${t.charAt(0).toUpperCase()+t.slice(1)}</option>`).join("")}
      </select>
    </div>

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: Git →</button>
    </div>
  `}function tn(e){return`
    <div class="modal-title">Git Setup</div>
    <div class="modal-subtitle">Connect a GitHub repository for auto-commit and push.</div>

    <div style="display:flex;border-bottom:1px solid var(--border);margin-bottom:1rem;gap:0">
      <button data-git-tab="oauth" onclick="window._wizardGitTabSwitch('oauth')"
        style="padding:0.5rem 1rem;background:none;border:none;border-bottom:2px solid var(--accent);
          color:var(--text);cursor:pointer;font-size:0.8rem">GitHub OAuth</button>
      <button data-git-tab="pat" onclick="window._wizardGitTabSwitch('pat')"
        style="padding:0.5rem 1rem;background:none;border:none;border-bottom:2px solid transparent;
          color:var(--text);cursor:pointer;font-size:0.8rem">Personal Token</button>
    </div>

    <div id="git-oauth-tab">
      <div style="font-size:0.78rem;color:var(--muted);margin-bottom:0.75rem">
        Login with GitHub to automatically configure push credentials.
      </div>
      <button class="btn btn-ghost btn-sm" onclick="window._wizardGitOAuth()">Login with GitHub</button>
      <div id="git-oauth-code" style="display:none;margin-top:0.75rem;padding:0.75rem;background:var(--bg);border-radius:var(--radius);font-size:0.8rem"></div>
    </div>

    <div id="git-pat-tab" style="display:none">
      <div class="field-group">
        <div class="field-label">GitHub username</div>
        <input class="field-input" id="git-username" placeholder="octocat"
          value="${e.git?.username||""}" oninput="window._wizardSetGit('username',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Email</div>
        <input class="field-input" id="git-email" placeholder="you@example.com"
          value="${e.git?.email||""}" oninput="window._wizardSetGit('email',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Personal Access Token</div>
        <input class="field-input" id="git-token" type="password" placeholder="ghp_..."
          value="${e.git?.token||""}" oninput="window._wizardSetGit('token',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Repository URL</div>
        <input class="field-input" id="git-repo" placeholder="https://github.com/you/repo"
          value="${e.git?.repo||""}" oninput="window._wizardSetGit('repo',this.value)" />
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: IDE Support →</button>
    </div>
  `}function rn(e){const t=!!e.code_dir,r=t?"":"opacity:0.45;pointer-events:none",o=t?"":`<div style="font-size:0.68rem;color:var(--yellow);margin-top:0.5rem">
      ⚠ Set a Code folder in Step 1 to enable IDE integrations.
    </div>`,n=e.code_dir||"{code_dir}",i=(a,s,d,l)=>`
    <label style="display:flex;gap:0.75rem;align-items:flex-start;cursor:pointer;${r}">
      <input type="checkbox" id="np-${a}" style="margin-top:3px"
        ${e[s]?"checked":""}
        onchange="window._wizard.${s}=this.checked" />
      <div>
        <div style="font-size:0.82rem;font-weight:600">${d}</div>
        <div style="font-size:0.7rem;color:var(--muted);margin-top:0.2rem">${l}</div>
      </div>
    </label>`;return`
    <div class="modal-title">AI IDE &amp; Provider Support</div>
    <div class="modal-subtitle">Choose how aicli memory is delivered to each tool.</div>
    ${o}

    <div style="font-size:0.7rem;color:var(--muted);margin:0.75rem 0 0.4rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px">
      IDE / Desktop — MCP + file-based context
    </div>
    <div style="display:flex;flex-direction:column;gap:0.75rem">
      ${i("claude-cli","claude_cli","Claude CLI &amp; Claude Code",`Creates <code>${n}/.claude/settings.local.json</code> (hooks: session log + auto-commit)<br>
         Creates <code>${n}/.mcp.json</code> — MCP server gives Claude live memory tools:<br>
         &nbsp;get_project_state · get_recent_history · search_memory · get_commits`)}
      ${i("cursor","cursor","Cursor",`Creates <code>${n}/.cursor/rules/aicli.mdrules</code> (project context, refreshed on /memory)<br>
         Creates <code>${n}/.cursor/mcp.json</code> — same 8 MCP tools available in Cursor Composer`)}
    </div>

    <div style="font-size:0.7rem;color:var(--muted);margin:1rem 0 0.4rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px">
      API providers — context injected by aicli before every prompt
    </div>
    <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.5rem">
      When used via aicli CLI or UI, these providers automatically receive <code>context.md</code>
      (project state + recent history) prepended to their system prompt. Set API keys in Admin → API Keys.
    </div>
    <div style="display:flex;flex-direction:column;gap:0.6rem">
      ${i("openai","openai","OpenAI (GPT-4o, o1, …)","Injects context.md via system prompt. Uses OpenAI Chat API.")}
      ${i("deepseek","deepseek","DeepSeek","OpenAI-compatible API. Context injected the same way.")}
      ${i("gemini","gemini","Gemini","Injects context.md via Google Generative AI system instruction.")}
      ${i("grok","grok","Grok (xAI)","OpenAI-compatible API. Context injected the same way.")}
    </div>

    <div class="modal-footer" style="margin-top:1.25rem">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: Review →</button>
    </div>
  `}function on(e){const t=e.git?.token?e.git.method==="oauth"?"OAuth configured":"Token saved":"Skipped",r=[e.claude_cli?"Claude CLI/Code ✓":null,e.cursor?"Cursor ✓":null,e.openai?"OpenAI ✓":null,e.deepseek?"DeepSeek ✓":null,e.gemini?"Gemini ✓":null,e.grok?"Grok ✓":null].filter(Boolean).join(", ")||"None";return`
    <div class="modal-title">Review & Create</div>

    <div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-lg);
      padding:1rem;margin-bottom:1.25rem;display:flex;flex-direction:column;gap:0.5rem">
      ${it("Project",`<strong>${e.name||"(unnamed)"}</strong> <span style="color:var(--muted)">(template: ${e.template})</span>`)}
      ${it("Code folder",e.code_dir||'<span style="color:var(--muted)">not set</span>')}
      ${it("Provider",e.provider)}
      ${it("Git",t)}
      ${it("IDE support",r)}
    </div>

    ${e.name?"":`<div style="color:var(--red);font-size:0.75rem;margin-bottom:0.75rem">
      ⚠ Project name is required — go back to Step 1.
    </div>`}

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardCreate()" ${e.name?"":"disabled"}>
        Create Project →
      </button>
    </div>
  `}function it(e,t){return`<div style="display:flex;gap:0.75rem;font-size:0.78rem">
    <span style="color:var(--muted);width:90px;flex-shrink:0">${e}</span>
    <span>${t}</span>
  </div>`}function nn(e,t,r){if(e.step===1){const o=(document.getElementById("np-name")?.value||"").trim().replace(/\s+/g,"-");if(!o){p("Project name is required","error");return}e.name=o,e.description=(document.getElementById("np-desc")?.value||"").trim(),e.code_dir=(document.getElementById("np-code")?.value||"").trim(),e.template=document.getElementById("np-template")?.value||"blank",e.provider=document.getElementById("np-provider")?.value||"claude"}e.step===3&&(e.claude_cli=document.getElementById("np-claude-cli")?.checked||!1,e.cursor=document.getElementById("np-cursor")?.checked||!1),e.step++,window._wizard=e,r()}function an(e){const t=!!e;["np-claude-cli","np-cursor","np-openai","np-deepseek","np-gemini","np-grok"].forEach(r=>{const o=document.getElementById(r);o&&(o.closest("label").style.cssText+=t?"opacity:1;pointer-events:auto":"opacity:0.45;pointer-events:none")})}window._wizardSetGit=(e,t)=>{window._wizard.git||(window._wizard.git={method:"pat"}),window._wizard.git[e]=t};window._wizardGitOAuth=async()=>{const e=document.getElementById("git-oauth-code");if(e){e.style.display="",e.textContent="Starting OAuth flow…";try{const t=await m.gitOauthDeviceStart({client_id:""});e.innerHTML=`Open <strong>${t.verification_uri}</strong> and enter code: <strong>${t.user_code}</strong>`;const r=setInterval(async()=>{try{const o=await m.gitOauthDevicePoll({device_code:t.device_code,client_id:""});o.access_token&&(clearInterval(r),window._wizard.git||(window._wizard.git={}),window._wizard.git.token=o.access_token,window._wizard.git.method="oauth",e.textContent="✓ GitHub authenticated")}catch{}},5e3)}catch(t){e.textContent=`Error: ${t.message}`}}};async function sn(e,t){if(!e.name){p("Project name is required","error");return}const r=t.querySelector(".btn-primary");r&&(r.disabled=!0,r.textContent="Creating…");try{if(await m.createProject({name:e.name,template:e.template,code_dir:e.code_dir,description:e.description,default_provider:e.provider,claude_cli_support:!!e.claude_cli,cursor_support:!!e.cursor,openai_support:!!e.openai,deepseek_support:!!e.deepseek,gemini_support:!!e.gemini,grok_support:!!e.grok}),e.git?.token&&e.git?.repo)try{await m.gitSetup(e.name,{token:e.git.token,username:e.git.username||"",email:e.git.email||"",github_repo:e.git.repo,git_branch:"main"})}catch(i){p(`Git setup warning: ${i.message}`,"warning")}try{const i=await m.generateMemory(e.name);i.generated?.length&&p(`Memory files generated (${i.generated.length} files)`,"success")}catch{}p(`Project "${e.name}" created`,"success"),t.remove();const o=await m.listProjects(),{setState:n}=await Or(async()=>{const{setState:i}=await Promise.resolve().then(()=>Wo);return{setState:i}},void 0);n({projects:o.projects||[]}),window._openProject(e.name)}catch(o){p(`Error: ${o.message}`,"error"),r&&(r.disabled=!1,r.textContent="Create Project →")}}function xe(e){if(!e)return"";const t=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),r=[];e=e.replace(/```(\w*)\n?([\s\S]*?)```/g,(s,d,l)=>{const c=r.length;return r.push(`<pre><code${d?` class="lang-${d}"`:""}>${t(l.trim())}</code></pre>`),`\0CODEBLOCK${c}\0`});const o=[];e=e.replace(/`([^`\n]+)`/g,(s,d)=>{const l=o.length;return o.push(`<code>${t(d)}</code>`),`\0INLINE${l}\0`}),e=t(e),e=e.replace(/^#{6} (.+)$/gm,"<h6>$1</h6>").replace(/^#{5} (.+)$/gm,"<h5>$1</h5>").replace(/^#{4} (.+)$/gm,"<h4>$1</h4>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>"),e=e.replace(/^---+$/gm,"<hr>"),e=e.replace(/^&gt; (.+)$/gm,"<blockquote>$1</blockquote>"),e=e.replace(/\*\*\*(.+?)\*\*\*/g,"<strong><em>$1</em></strong>").replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>").replace(/__(.+?)__/g,"<strong>$1</strong>").replace(/_(.+?)_/g,"<em>$1</em>"),e=e.replace(/~~(.+?)~~/g,"<del>$1</del>"),e=e.replace(/^- \[x\] (.+)$/gim,'<li class="task-done">$1</li>').replace(/^- \[ \] (.+)$/gim,'<li class="task-todo">$1</li>'),e=e.replace(/^[-*] (.+)$/gm,"<li>$1</li>"),e=e.replace(/^\d+\. (.+)$/gm,'<li class="ol">$1</li>'),e=e.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>'),e=e.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img src="$2" alt="$1" style="max-width:100%;border-radius:var(--radius)">'),e=e.replace(/((<li class="ol">.*<\/li>\n?)+)/g,"<ol>$1</ol>"),e=e.replace(/((<li(?! class="ol")>.*<\/li>\n?)+)/g,"<ul>$1</ul>");const n=e.split(`
`),i=[];let a=!1;for(const s of n)/^<(h[1-6]|hr|ul|ol|li|blockquote|pre|div)/.test(s)||s===""?(a&&(i.push("</p>"),a=!1),i.push(s)):(a?i.push("<br>"):(i.push("<p>"),a=!0),i.push(s));return a&&i.push("</p>"),e=i.join(`
`),e=e.replace(/\x00CODEBLOCK(\d+)\x00/g,(s,d)=>r[d]),e=e.replace(/\x00INLINE(\d+)\x00/g,(s,d)=>o[d]),e}async function dn(e,t){if(e.className="view active summary-view",e.innerHTML=`
    <div class="summary-toolbar">
      <span style="font-size:0.65rem;color:var(--muted);flex:1">
        ${t?`PROJECT.md — ${t}`:"No project open"}
      </span>
      <button class="btn btn-ghost btn-sm" id="summary-ctx-btn" title="Rebuild CONTEXT.md from PROJECT.md + history"
              onclick="window._summaryRefreshContext()">↺ Context</button>
      <button class="btn btn-ghost btn-sm" id="summary-edit-btn" onclick="window._summaryToggleEdit()">Edit</button>
      <button class="btn btn-primary btn-sm" id="summary-save-btn" disabled style="opacity:0.4" onclick="window._summarySave()">Save</button>
    </div>
    <div id="summary-body" class="summary-content">
      <div class="empty-state"><div class="empty-state-icon">📄</div><p>Loading…</p></div>
    </div>
  `,!t){document.getElementById("summary-body").innerHTML='<div class="empty-state"><div class="empty-state-icon">◫</div><p>No project open</p><p style="font-size:0.68rem;margin-top:0.3rem;color:var(--muted)">Open a project from the Projects view.</p></div>';return}let r="",o=!1;const n=document.getElementById("summary-edit-btn"),i=document.getElementById("summary-save-btn"),a=document.getElementById("summary-body");function s(u){i.disabled=!0,i.style.opacity="0.4",u.addEventListener("input",()=>{const h=u.value!==r;i.disabled=!h,i.style.opacity=h?"1":"0.4"}),u.addEventListener("keydown",h=>{(h.metaKey||h.ctrlKey)&&h.key==="s"&&(h.preventDefault(),i.disabled||window._summarySave())})}window._summaryToggleEdit=()=>{if(o=!o,o){n.textContent="Preview",a.className="",a.style.cssText="flex:1;display:flex;flex-direction:column;overflow:hidden";const u=document.createElement("textarea");u.className="summary-textarea",u.id="summary-textarea",u.value=r,a.innerHTML="",a.appendChild(u),s(u),u.focus()}else{n.textContent="Edit";const u=document.getElementById("summary-textarea");u&&(r=u.value),a.className="summary-content",a.style.cssText="",a.innerHTML=`<div class="summary-md">${xe(r)}</div>`,i.disabled=!0,i.style.opacity="0.4"}},window._summaryRefreshContext=async()=>{const u=document.getElementById("summary-ctx-btn");u&&(u.disabled=!0,u.textContent="…");try{await m.getProjectContext(t,!0),p("CONTEXT.md rebuilt and saved","success")}catch(h){p(`Context refresh failed: ${h.message}`,"error")}finally{u&&(u.disabled=!1,u.textContent="↺ Context")}},window._summarySave=async()=>{const u=document.getElementById("summary-textarea");if(!u)return;const h=u.value;try{await m.updateProjectSummary(t,h),r=h,i.disabled=!0,i.style.opacity="0.4",p("PROJECT.md saved","success")}catch(_){p(`Save failed: ${_.message}`,"error")}};let d=null;async function l(){try{const h=(await m.workItems.facts(t)).facts||[];if(!h.length){d.innerHTML="";return}const _=h.map(S=>`<tr>
          <td style="padding:0.18rem 0.6rem 0.18rem 0;font-weight:500;white-space:nowrap;
                     font-size:0.67rem;color:var(--text)">${S.fact_key}</td>
          <td style="padding:0.18rem 0;font-size:0.67rem;color:var(--text2)">${S.fact_value}</td>
         </tr>`).join(""),C=h[0]?.valid_from?.slice(0,10)||"";d.innerHTML=`
        <div style="border:1px solid var(--border);border-radius:8px;background:var(--surface);
                    padding:0.65rem 1rem;font-size:0.72rem">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
            <span style="font-size:0.95rem">📌</span>
            <strong style="font-size:0.75rem">Project Facts</strong>
            ${C?`<span style="margin-left:auto;color:var(--muted);font-size:0.62rem">updated: ${C}</span>`:""}
          </div>
          <table style="border-collapse:collapse;width:100%">${_}</table>
        </div>
      `}catch{d.innerHTML=""}}let c=null;async function g(){try{const u=await m.getMemoryStatus(t),h=u.needs_memory,_=u.prompts_since_last_memory||0,C=u.total_prompts||0,S=u.days_since_last_memory,v=u.last_memory_run?u.last_memory_run.slice(0,10)+(S!=null?` (${S}d ago)`:""):"Never",b=h?"#ffc107":"#27ae60",z=h?"#fff8e1":"#f0faf4",y=h?"⚠️":"✅";c.innerHTML=`
        <div style="border:1px solid ${b};border-radius:8px;background:${z};
                    padding:0.75rem 1rem;font-size:0.72rem;color:var(--text)">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
            <span style="font-size:1rem">${y}</span>
            <strong style="font-size:0.78rem">Memory Health</strong>
            <span style="margin-left:auto;color:var(--muted);font-size:0.65rem">
              Last run: ${v}
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:1rem">
            <span>New prompts: <strong>${_}</strong>${h?` ⚠ (threshold: ${u.threshold})`:` / ${u.threshold}`}</span>
            <span style="color:var(--muted)">Total: ${C}</span>
            ${h?`<button id="summary-run-memory"
              style="margin-left:auto;background:#ffc107;border:none;color:#000;font-size:0.62rem;
                     padding:0.2rem 0.65rem;border-radius:4px;cursor:pointer;font-family:inherit;
                     font-weight:600">Run /memory Now</button>`:""}
          </div>
        </div>
      `,document.getElementById("summary-run-memory")?.addEventListener("click",async()=>{const $=document.getElementById("summary-run-memory");$&&($.disabled=!0,$.textContent="…");try{await m.generateMemory(t),p("/memory completed — memory files refreshed","success"),await g()}catch(E){p(`/memory failed: ${E.message}`,"error"),$&&($.disabled=!1,$.textContent="Run /memory Now")}})}catch{c.innerHTML=""}}d=document.createElement("div"),d.id="summary-facts-card",d.style.cssText="margin:0.75rem 0 0.4rem 0;",c=document.createElement("div"),c.id="summary-memory-card",c.style.cssText="margin:0.75rem 0;",c.innerHTML=`
    <div style="border:1px solid var(--border);border-radius:8px;background:var(--surface);
                padding:0.65rem 1rem;font-size:0.72rem;color:var(--muted);
                display:flex;align-items:center;gap:0.5rem">
      <span style="font-size:0.85rem">⏳</span> Checking memory health…
    </div>`;const f=document.createElement("div");try{r=(await m.getProjectSummary(t)).content||"",f.className="summary-md",f.innerHTML=xe(r)}catch{r=`# ${t}

Project description goes here.
`,f.innerHTML=`<div class="summary-md">${xe(r)}</div>
      <p style="font-size:0.68rem;color:var(--muted);margin-top:1rem">
        No PROJECT.md found. Click <strong>Edit</strong> to create one.
      </p>`}a.className="summary-content",a.innerHTML="",a.appendChild(d),a.appendChild(c),a.appendChild(f),l().catch(()=>{}),g().catch(()=>{})}let H={project:null,categories:[],values:{},loaded:!1};async function Fe(e,t=!1){if(!t&&H.project===e&&H.loaded)return H;H={project:e,categories:[],values:{},loaded:!1};try{const r=await m.entities.listCategories(e);if(H.categories=r.categories||[],r.fallback)return H;let o=!1;await Promise.all(H.categories.map(async n=>{try{const i=await m.entities.listValues(e,n.id);i.fallback?(o=!0,H.values[String(n.id)]=[],n.value_count=0):(H.values[String(n.id)]=i.values||[],n.value_count=H.values[String(n.id)].length)}catch{H.values[String(n.id)]=[],n.value_count=0}})),o||(H.loaded=!0)}catch(r){console.warn("[tagCache] load failed:",r.message)}return H}const se=()=>H.categories,Pe=e=>H.values[String(e)]||[],ln=()=>H.project,Cr=()=>H.loaded,cn=e=>Pe(e).filter(t=>!t.parent_id),Kr=e=>Object.values(H.values).flat().filter(t=>String(t.parent_id)===String(e));function Tt(e){return Kr(e).flatMap(r=>[r,...Tt(r.id)])}function ir(e,t){const r=String(e);H.values[r]||(H.values[r]=[]),H.values[r].push(t);const o=H.categories.find(n=>String(n.id)===r);o&&(o.value_count=H.values[r].length)}function ar(e,t){for(const r of Object.keys(H.values)){const o=H.values[r].findIndex(n=>n.id===e);if(o!==-1){H.values[r][o]={...H.values[r][o],...t};return}}}function zr(e){for(const t of Object.keys(H.values)){const r=H.values[t].findIndex(o=>o.id===e);if(r!==-1){H.values[t].splice(r,1);const o=H.categories.find(n=>String(n.id)===t);o&&(o.value_count=H.values[t].length);return}}}function mn(e){H.categories.push({...e,value_count:0}),H.values[String(e.id)]=[]}const Yt=[{id:"claude",label:"Claude"},{id:"openai",label:"OpenAI"},{id:"deepseek",label:"DeepSeek"},{id:"gemini",label:"Gemini"},{id:"grok",label:"Grok"}];let ne=null,Me="claude",Xr=!1,ce=[],Te=[],ut=[],ve={phase:""},ze=[],oe=[],_e=[],Kt=!1;const Jr=[{id:"feature",icon:"⬡",color:"#27ae60"},{id:"bug",icon:"⚠",color:"#e74c3c"},{id:"task",icon:"✓",color:"#4a90e2"}],Qr=[{value:"",label:"⚠ Phase (required)"},{value:"discovery",label:"Discovery"},{value:"development",label:"Development"},{value:"testing",label:"Testing"},{value:"review",label:"Review"},{value:"production",label:"Production"},{value:"maintenance",label:"Maintenance"},{value:"bugfix",label:"Bug Fix"}];function pn(e){Me=x.currentProject?.default_provider||"claude",e.className="view active",e.style.cssText="display:flex;flex-direction:column;overflow:hidden;height:100%";const t=parseInt(localStorage.getItem("aicli_chat_sessions_w")||"190",10);e.innerHTML=`
    <div style="display:flex;flex:1;overflow:hidden;min-height:0">

      <!-- Session sidebar -->
      <div id="chat-session-panel"
           style="width:${t}px;border-right:1px solid var(--border);background:var(--surface);
                  display:flex;flex-direction:column;flex-shrink:0;overflow:hidden">
        <div style="padding:0.6rem;border-bottom:1px solid var(--border)">
          <button class="btn btn-ghost btn-sm" style="width:100%;font-size:0.7rem"
            onclick="window._chatNew()">+ New Chat</button>
        </div>
        <div style="padding:0.35rem 0.6rem 0.15rem;font-size:0.55rem;color:var(--muted);
                    letter-spacing:2px;text-transform:uppercase">Sessions</div>
        <div id="chat-sessions" style="flex:1;overflow-y:auto;padding:0.15rem 0.4rem 0.5rem"></div>
      </div>

      <!-- Session panel resize handle -->
      <div id="chat-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize panel"></div>

      <!-- Main chat -->
      <div style="flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden">

        <!-- Provider / context bar -->
        <div style="display:flex;align-items:center;gap:0.75rem;padding:0.45rem 1rem;
                    border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
          <span style="font-size:0.62rem;color:var(--muted)">LLM:</span>
          <select id="chat-provider"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.5rem;
                   border-radius:var(--radius);cursor:pointer;outline:none">
            ${Yt.map(r=>`
              <option value="${r.id}" ${r.id===Me?"selected":""}>
                ${r.label}
              </option>`).join("")}
          </select>
          <span style="font-size:0.62rem;color:var(--muted)">Role:</span>
          <select id="chat-role"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.5rem;
                   border-radius:var(--radius);cursor:pointer;outline:none">
            <option value="">Default (CLAUDE.md)</option>
          </select>
          ${x.currentProject?.name?`
            <span style="margin-left:auto;font-size:0.62rem;color:var(--muted)">
              <span style="color:var(--accent)">${x.currentProject.name}</span>
            </span>`:""}
        </div>

        <!-- Session tag bar: phase (mandatory) + entity chips (optional) -->
        <div id="chat-tag-bar"
          style="display:flex;align-items:center;gap:0.45rem;padding:0.3rem 0.75rem;
                 border-bottom:1px solid var(--border);background:var(--surface2);flex-shrink:0;
                 flex-wrap:wrap;min-height:2rem">
          <span style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase;white-space:nowrap;flex-shrink:0">Phase:</span>

          <!-- Phase (mandatory) -->
          <select id="chat-phase-sel"
            style="background:var(--bg);border:1px solid var(--red,#e74c3c);color:var(--text);
                   font-family:var(--font);font-size:0.64rem;padding:0.15rem 0.35rem;
                   border-radius:var(--radius);cursor:pointer;outline:none;max-width:118px;flex-shrink:0"
            title="Mandatory: set a phase for this session">
            ${Qr.map(r=>`<option value="${P(r.value)}">${P(r.label)}</option>`).join("")}
          </select>

          <!-- Applied entity chips (feature/bug/task) -->
          <div id="chat-entity-chips"
               style="display:flex;gap:0.25rem;flex-wrap:wrap;align-items:center;flex:1;min-width:0;overflow:hidden"></div>

          <!-- Add tag button -->
          <button id="chat-add-tag-btn"
            onclick="window._toggleEntityPicker()"
            style="background:var(--surface);border:1px solid var(--border);color:var(--text2);
                   font-family:var(--font);font-size:0.58rem;padding:0.12rem 0.4rem;
                   border-radius:var(--radius);cursor:pointer;white-space:nowrap;flex-shrink:0;outline:none"
            title="Tag this session with a feature, bug, or task">+ Tag</button>

          <!-- Save tags button — always visible, disabled when nothing pending -->
          <button id="chat-save-tags-btn"
            onclick="window._saveEntitiesToSession()"
            disabled
            style="font-family:var(--font);font-size:0.58rem;padding:0.12rem 0.5rem;
                   border-radius:var(--radius);cursor:not-allowed;white-space:nowrap;flex-shrink:0;
                   outline:none;background:var(--surface);border:1px solid var(--border);
                   color:var(--muted);transition:all 0.15s"
            title="Save selected tags to this session">💾 Save</button>

          <span id="chat-tag-status"
                style="font-size:0.58rem;color:var(--red,#e74c3c);white-space:nowrap;flex-shrink:0">⚠ phase</span>
          <span style="font-size:0.58rem;color:var(--muted);cursor:pointer;white-space:nowrap;flex-shrink:0"
            onclick="window._chatNew()" title="Start new session">+ new</span>
        </div>

        <!-- AI Suggestions banner — only shown after /memory returns suggestions -->
        <div id="chat-ai-suggestions" style="display:none"></div>

        <!-- Entity picker panel (shown when + Tag is clicked) — grouped listbox -->
        <div id="chat-entity-picker"
          style="display:none;flex-direction:column;max-height:280px;
                 border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
          <!-- Filter row -->
          <div style="display:flex;align-items:center;gap:0.4rem;padding:0.35rem 0.75rem;
                      border-bottom:1px solid var(--border);flex-shrink:0">
            <input id="picker-filter-inp" type="text" placeholder="🔍 Filter tags…"
              autocomplete="off"
              oninput="window._pickerFilter(this.value)"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.4rem;
                     border-radius:var(--radius);outline:none" />
            <button onclick="window._closeEntityPicker()"
              style="background:none;border:none;color:var(--muted);cursor:pointer;
                     font-size:0.8rem;padding:0 0.25rem;flex-shrink:0;line-height:1">✕</button>
          </div>
          <!-- Grouped tag list -->
          <div id="picker-groups-list"
               style="flex:1;overflow-y:auto;padding:0.2rem 0;min-height:60px"></div>
          <!-- Add new section -->
          <div style="border-top:1px solid var(--border);padding:0.3rem 0.75rem;flex-shrink:0;
                      display:flex;align-items:center;gap:0.4rem">
            <span style="font-size:0.6rem;color:var(--muted);white-space:nowrap;flex-shrink:0">+ Add:</span>
            <select id="picker-add-cat"
              style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.62rem;padding:0.15rem 0.3rem;
                     border-radius:var(--radius);outline:none;max-width:115px;flex-shrink:0">
              <option value="">Category…</option>
            </select>
            <input id="picker-add-name" type="text" placeholder="Tag name"
              onkeydown="if(event.key==='Enter')window._pickerSaveNew()"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.62rem;padding:0.15rem 0.3rem;
                     border-radius:var(--radius);outline:none;min-width:0" />
            <button onclick="window._pickerSaveNew()"
              style="background:var(--accent);border:none;color:#fff;font-size:0.6rem;
                     padding:0.2rem 0.5rem;border-radius:var(--radius);cursor:pointer;
                     font-family:var(--font);outline:none;white-space:nowrap;flex-shrink:0">Save</button>
          </div>
        </div>

        <!-- Messages -->
        <div id="chat-messages"
          style="flex:1;overflow-y:auto;padding:1.25rem;display:flex;flex-direction:column;gap:1rem">
        </div>

        <!-- Input -->
        <div style="padding:0.75rem 1rem;border-top:1px solid var(--border);flex-shrink:0">
          <div style="position:relative">
            <div id="chat-cmd-popup-wrap"></div>
            <div id="chat-input-box"
              style="display:flex;align-items:flex-end;gap:0.75rem;background:var(--surface2);
                     border:1px solid var(--border);border-radius:var(--radius);
                     padding:0.6rem 0.75rem 0.6rem 1rem;transition:border-color 0.15s">
              <span style="color:var(--accent);font-size:0.85rem;margin-bottom:3px">❯</span>
              <textarea id="chat-input"
                style="flex:1;background:none;border:none;color:var(--text);font-family:var(--font);
                       font-size:0.8rem;line-height:1.6;resize:none;outline:none;max-height:140px;
                       user-select:text;-webkit-user-select:text"
                placeholder="Message… (/ for commands · Enter to send · Shift+Enter for newline)"
                rows="1"></textarea>
              <button id="chat-send-btn"
                style="background:var(--accent);border:none;color:#fff;width:28px;height:28px;
                       border-radius:6px;cursor:pointer;font-size:1rem;flex-shrink:0;
                       display:flex;align-items:center;justify-content:center;transition:opacity 0.15s"
                onclick="window._chatSend()">↑</button>
            </div>
          </div>
          <div style="margin-top:0.35rem;font-size:0.6rem;color:var(--muted)">
            / for commands · Enter to send · Shift+Enter for newline
          </div>
        </div>

      </div>
    </div>
  `,document.getElementById("chat-provider")?.addEventListener("change",r=>{Me=r.target.value}),document.getElementById("chat-role")?.addEventListener("change",async r=>{const o=r.target.value,n=x.currentProject;if(n)if(o)try{const i=await m.readPrompt(o,n.name);U({currentProject:{...x.currentProject,system_prompt:i.content||""}}),p(`Role: ${o}`,"info")}catch(i){p(`Could not load role: ${i.message}`,"error")}else{const i=await m.getProject(n.name).catch(()=>n);U({currentProject:{...x.currentProject,system_prompt:i.claude_md||i.project_md||""}})}}),un(),(async()=>{const r=x.currentProject?.name;if(r)try{const o=await m.getSessionTags(r);if(o?.phase&&!ve.phase){ve={phase:o.phase};const n=document.getElementById("chat-phase-sel");n&&(n.value=o.phase),window.__currentPhase=o.phase,Pt()}}catch{}})(),$n(),En(),Ze(),kn().then(()=>cr())}function un(){const e=document.getElementById("chat-phase-sel");e&&(e.value=ve.phase||"",Pt(),$e(),e.addEventListener("change",()=>{const t=e.value;ve={...ve,phase:t},window.__currentPhase=t,Pt(),Le();const r=x.currentProject?.name;r&&m.putSessionTags(r,{phase:t||null}).catch(()=>{}),ne?m.patchSessionTags(ne,{phase:t||null},r).then(()=>Ze()).catch(()=>Ze()):Ze()}),window._toggleEntityPicker=gn,window._closeEntityPicker=ht,window._pickerFilter=vn,window._pickerSaveNew=yn,window._applyTagDirect=hn,window._saveEntitiesToSession=sr,window._removePendingTag=bn,window._removeAppliedTag=wn)}function Le(){const e=document.getElementById("chat-save-tags-btn");if(!e)return;const t=oe.length>0;e.disabled=!t,t?(e.style.cursor="pointer",e.style.background="var(--accent)",e.style.color="#fff",e.style.border="1px solid var(--accent)",e.title=`Save ${oe.length} pending tag(s) to session`,e.textContent=`💾 Save (${oe.length})`):(e.style.cursor="not-allowed",e.style.background="var(--surface)",e.style.color="var(--muted)",e.style.border="1px solid var(--border)",e.title="No pending tags",e.textContent="💾 Save")}function Pt(){const e=document.getElementById("chat-phase-sel"),t=document.getElementById("chat-tag-status");if(!e||!t)return;const r=!!ve.phase;if(e.style.borderColor=r?"var(--border)":"var(--red,#e74c3c)",r){const o=Qr.find(n=>n.value===ve.phase)?.label||ve.phase;t.style.color="var(--green,#27ae60)",t.textContent=`✓ ${o}`}else t.style.color="var(--red,#e74c3c)",t.textContent="⚠ phase"}function Zr(e){ve={phase:e?.phase||""},ze=[],oe=[],_e=[];const t=document.getElementById("chat-phase-sel");t&&(t.value=ve.phase),Pt(),Le(),$e(),ot()}function gn(){if(Kt){ht();return}const e=document.getElementById("chat-entity-picker");e&&(Kt=!0,e.style.display="flex",fn())}function ht(){const e=document.getElementById("chat-entity-picker");e&&(e.style.display="none"),Kt=!1}function fn(){const e=se(),t=document.getElementById("picker-add-cat");t&&(t.innerHTML='<option value="">Category…</option>'+e.map(n=>`<option value="${n.id}">${P(n.icon)} ${P(n.name)}</option>`).join(""));const r=document.getElementById("picker-filter-inp");r&&(r.value="",setTimeout(()=>r.focus(),0));const o=document.getElementById("picker-add-name");o&&(o.value=""),eo("")}function eo(e){const t=document.getElementById("picker-groups-list");if(!t)return;const r=se(),o=(e||"").toLowerCase().trim();let n="";for(const i of r){const a=Pe(i.id).filter(d=>!d.status||d.status==="active"),s=o?a.filter(d=>d.name.toLowerCase().includes(o)):a;s.length&&(n+=`
      <div class="picker-group">
        <div style="padding:0.18rem 0.75rem;font-size:0.57rem;font-weight:600;
                    color:${i.color};text-transform:uppercase;letter-spacing:0.04em">
          ${P(i.icon)} ${P(i.name)}
        </div>
        ${s.map(d=>`
          <div onmousedown="event.preventDefault();window._applyTagDirect(${d.id},'${P(d.name)}',${i.id},'${P(i.name)}','${P(i.icon)}','${P(i.color)}')"
               style="padding:0.22rem 0.75rem 0.22rem 1.6rem;cursor:pointer;font-size:0.68rem;
                      display:flex;align-items:center;justify-content:space-between;gap:6px"
               onmouseenter="this.style.background='var(--surface2)'"
               onmouseleave="this.style.background='transparent'">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${P(d.name)}</span>
            ${d.event_count?`<span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${d.event_count}</span>`:""}
          </div>`).join("")}
      </div>`)}t.innerHTML=n||`
    <div style="padding:1rem;text-align:center;font-size:0.65rem;color:var(--muted)">
      ${o?"No matching tags":"No tags yet — add one below"}
    </div>`}function vn(e){eo(e)}function yn(){const e=document.getElementById("picker-add-cat"),t=document.getElementById("picker-add-name"),r=e?.value,o=(t?.value||"").trim();if(!r){p("Select a category","error");return}if(!o){p("Enter a tag name","error");return}const n=se().find(l=>String(l.id)===String(r))||{},i=n.name||"",a=n.icon||"⬡",s=n.color||"#4a90e2";oe.some(l=>l.name===o&&l.category_name===i)||ze.some(l=>l.name===o&&l.category_name===i)||(oe.push({value_id:null,category_name:i,name:o,color:s,icon:a,is_new:!0}),$e(),Le()),t&&(t.value=""),ht()}function hn(e,t,r,o,n,i){oe.some(s=>s.value_id===e)||ze.some(s=>s.value_id===e)||(oe.push({value_id:e,category_name:o,name:t,color:i,icon:n}),$e(),Le()),ht()}function bn(e){oe.splice(e,1),$e(),Le()}async function wn(e){const t=ze[e];if(!t)return;ze.splice(e,1),$e();const r=x.currentProject?.name||"";if(ne&&t.value_id)try{await m.entities.untagSession(ne,t.value_id,r)}catch(o){console.warn("Remove applied tag failed:",o.message),ze.splice(e,0,t),$e()}}async function sr(){if(!oe.length)return;const e=x.currentProject?.name;if(!e){p("No project open","error");return}if(!ne){p(`${oe.length} tag(s) queued — will be saved when you send your first message`,"info");return}const t=document.getElementById("chat-save-tags-btn");t&&(t.textContent="💾 Saving…");const r=[...oe];let o=0;for(const n of r)try{const i=n.value_id?{session_id:ne,project:e,value_id:n.value_id}:{session_id:ne,project:e,category_name:n.category_name,value_name:n.name},a=await m.entities.sessionTag(i),s=a.value_id||n.value_id;n.is_new&&s&&ir(se().find(d=>d.name===n.category_name)?.id,{id:s,name:n.name,status:"active",event_count:a.events_tagged||0}),ze.push({...n,value_id:s}),o++}catch(i){p(`Tag "${n.name}" error: ${i.message}`,"error")}oe=[],$e(),Le(),o&&p(`${o} tag(s) saved to session`,"success")}function $e(){const e=document.getElementById("chat-entity-chips");if(!e)return;const t=ze.map((o,n)=>`
    <span class="entity-chip user-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:${o.color}22;border:1px solid ${o.color}55;color:${o.color};
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap"
          title="Saved · ${P(o.category_name)}/${P(o.name)}">
      ${P(o.icon)} ${P(o.name)}
      <button onclick="window._removeAppliedTag(${n})"
        style="border:none;background:none;cursor:pointer;color:${o.color};font-size:0.6rem;padding:0 1px;line-height:1;opacity:.7"
        title="Remove tag">✕</button>
    </span>`).join(""),r=oe.map((o,n)=>`
    <span class="entity-chip pending-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:${o.color}11;border:1px dashed ${o.color}88;color:${o.color};
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap;
                 opacity:0.82"
          title="Pending · ${P(o.category_name)}/${P(o.name)} — click 💾 Save to apply">
      ${P(o.icon)} ${P(o.name)}
      <button onclick="window._removePendingTag(${n})"
        style="border:none;background:none;cursor:pointer;color:${o.color};font-size:0.6rem;padding:0 1px;line-height:1"
        title="Remove">✕</button>
    </span>`).join("");e.innerHTML=t+r}function ot(){const e=document.getElementById("chat-ai-suggestions");if(!e)return;if(!_e.length){e.style.display="none";return}const t=x.currentProject?.name||"",r=ne?ne.slice(0,8)+"…":"new session",o=_e.map((n,i)=>{const s=se().find(d=>d.name===n.category)||Jr.find(d=>d.id===n.category)||{color:"#9b7fcc",icon:"⬡"};return`
      <span style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:${s.color}18;border:1px solid ${s.color}55;
                   border-radius:6px;padding:0.2rem 0.5rem;font-size:0.62rem;white-space:nowrap">
        <span style="color:${s.color}">${P(s.icon)}</span>
        <span style="color:var(--muted);font-size:0.55rem">${P(n.category)}</span>
        <strong style="color:var(--text)">${P(n.name)}</strong>
        <button onclick="window._acceptSuggestedTag(${i})"
          style="border:1px solid #27ae60;background:#27ae6018;cursor:pointer;color:#27ae60;
                 font-size:0.58rem;padding:0.06rem 0.35rem;border-radius:4px;line-height:1.2;
                 font-family:var(--font);white-space:nowrap">✓ Accept</button>
        <button onclick="window._dismissSuggestedTag(${i})"
          style="border:none;background:none;cursor:pointer;color:var(--muted);
                 font-size:0.65rem;padding:0 2px;line-height:1"
          title="Dismiss">✕</button>
      </span>`}).join("");e.style.display="block",e.innerHTML=`
    <div style="display:flex;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;
                padding:0.5rem 0.75rem;border-bottom:2px solid #d4a017;
                background:linear-gradient(to right,#fffbe6,#fff9d6)">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;flex-wrap:wrap">
          <span style="font-size:0.62rem;font-weight:700;color:#8a6500">🤖 AI Tag Suggestions</span>
          <span style="font-size:0.55rem;color:#b08000;background:#d4a01722;border:1px solid #d4a01744;
                       border-radius:4px;padding:0.05rem 0.3rem">
            session: <code style="font-size:0.55rem">${P(r)}</code>
            ${t?` · ${P(t)}`:""}
          </span>
          <span style="font-size:0.55rem;color:#b08000;font-style:italic">
            Based on your recent history — click ✓ Accept to apply
          </span>
        </div>
        <div style="display:flex;gap:0.35rem;flex-wrap:wrap;align-items:center">${o}</div>
      </div>
      <button onclick="window._dismissAllSuggestions()"
        style="border:none;background:none;cursor:pointer;color:#b08000;font-size:0.6rem;
               padding:0;line-height:1;white-space:nowrap;flex-shrink:0;align-self:flex-start"
        title="Dismiss all suggestions">Dismiss all</button>
    </div>`}window._acceptSuggestedTag=async e=>{const t=_e[e];if(!t)return;const r=se().find(n=>n.name===t.category),o=r||Jr.find(n=>n.id===t.category)||{color:"#9b7fcc",icon:"⬡"};oe.push({value_id:null,category_name:t.category,name:t.name,color:o.color,icon:o.icon,is_new:!r}),_e=_e.filter((n,i)=>i!==e),ot(),$e(),ne?await sr():Le()};window._dismissSuggestedTag=e=>{_e=_e.filter((t,r)=>r!==e),ot()};window._dismissAllSuggestions=()=>{_e=[],ot()};const xn=[{cmd:"/help",args:"",desc:"Show all available commands"},{cmd:"/memory",args:"",desc:"Refresh CLAUDE.md + CONTEXT.md → copy to code dir"},{cmd:"/role",args:"[name]",desc:"Set system prompt role"},{cmd:"/workflow",args:"[name]",desc:"List or run a workflow"},{cmd:"/switch",args:"<provider>",desc:"Switch LLM (claude/openai/deepseek/gemini/grok)"},{cmd:"/compare",args:"<prompt.md>",desc:"Run prompt on multiple LLMs side-by-side"},{cmd:"/project",args:"new|list|switch",desc:"Manage projects"},{cmd:"/tag",args:"<name>",desc:"Tag this session"},{cmd:"/feature",args:"<name>",desc:"Set feature context"},{cmd:"/search-tag",args:"<tag>",desc:"Search history by tag"},{cmd:"/push",args:"[branch]",desc:"Commit and push to git (optional: branch name)"},{cmd:"/analytics",args:"",desc:"Show usage and cost stats"},{cmd:"/history",args:"",desc:"Show last 20 commits"},{cmd:"/reload",args:"",desc:"Reload system prompt"},{cmd:"/pipeline",args:"[status]",desc:"Show pipeline health dashboard"},{cmd:"/clear",args:"",desc:"Clear conversation history"}];let he=-1,dr=!1;function _n(e){const t=document.getElementById("chat-cmd-popup-wrap");if(!t)return;let r=xn.map(n=>n.cmd==="/role"&&ce.length?{...n,desc:`Roles: ${ce.map(i=>i.name.replace(".md","")).join(", ")}`}:n.cmd==="/workflow"&&Te.length?{...n,desc:`Workflows: ${Te.map(i=>typeof i=="string"?i:i.name).join(", ")}`}:n);(e.startsWith("/role")&&e!=="/role"||e==="/role"&&ce.length)&&ce.length&&(r=r.filter(n=>n.cmd!=="/role"),ce.forEach(n=>{r.push({cmd:`/role ${n.name.replace(".md","")}`,args:"",desc:n.path})})),(e.startsWith("/workflow")&&e!=="/workflow"||e==="/workflow"&&Te.length)&&Te.length&&(r=r.filter(n=>n.cmd!=="/workflow"),Te.forEach(n=>{const i=typeof n=="string"?n:n.name,a=n.description?n.description:`Run workflow: ${i}`;r.push({cmd:`/workflow ${i}`,args:"",desc:a})}));const o=e==="/"?r:r.filter(n=>n.cmd.startsWith(e));if(!o.length){mt();return}dr=!0,he=-1,t.innerHTML=`
    <div class="cmd-popup" id="cmd-popup">
      ${o.map((n,i)=>`
        <div class="cmd-popup-item" data-idx="${i}"
             onmousedown="window._cmdComplete('${P(n.cmd)}', ${!!n.args})"
             onmouseenter="window._cmdHover(${i})">
          <span class="cmd-popup-cmd">${P(n.cmd)}</span>
          ${n.args?`<span class="cmd-popup-args">${P(n.args)}</span>`:""}
          <span class="cmd-popup-desc">${P(n.desc)}</span>
        </div>
      `).join("")}
    </div>
  `,t._matches=o}function mt(){dr=!1,he=-1;const e=document.getElementById("chat-cmd-popup-wrap");e&&(e.innerHTML="")}window._cmdHover=e=>{he=e,Xt()};window._cmdComplete=(e,t=!1)=>{const r=document.getElementById("chat-input");if(r){if(t){const o=e.indexOf(" ");r.value=(o===-1?e:e.slice(0,o))+" "}else r.value=e;r.style.height="auto",mt(),r.focus()}};function Xt(){document.querySelectorAll("#cmd-popup .cmd-popup-item").forEach((e,t)=>{e.classList.toggle("selected",t===he)})}function $n(){const e=document.getElementById("chat-input"),t=document.getElementById("chat-input-box");e&&(e.addEventListener("input",()=>{e.style.height="auto",e.style.height=Math.min(e.scrollHeight,140)+"px";const r=e.value;r.startsWith("/")&&!r.includes(`
`)&&!r.includes(" ")?_n(r):mt()}),e.addEventListener("keydown",r=>{if(dr){const n=document.getElementById("chat-cmd-popup-wrap")?._matches||[];if(r.key==="ArrowDown"){r.preventDefault(),he=Math.min(he+1,n.length-1),Xt();return}if(r.key==="ArrowUp"){r.preventDefault(),he=Math.max(he-1,0),Xt();return}if(r.key==="Tab"||r.key==="Enter"&&he>=0){r.preventDefault();const i=he>=0?he:0,a=n[i];a&&window._cmdComplete(a.cmd,!!a.args);return}if(r.key==="Escape"){r.preventDefault(),mt();return}}r.key==="Enter"&&!r.shiftKey&&(r.preventDefault(),window._chatSend())}),e.addEventListener("focus",()=>{t&&(t.style.borderColor="rgba(255,107,53,0.4)")}),e.addEventListener("blur",()=>{t&&(t.style.borderColor="var(--border)"),setTimeout(mt,150)}))}async function Ze(){const e=document.getElementById("chat-sessions");if(!e)return;const t=x.currentProject?.name,r=[];try{const o=await m.chatSessions();(Array.isArray(o)?o:o.sessions||[]).forEach(i=>r.push({id:i.id,title:i.title||i.id.slice(0,14),source:"ui",ts:i.created_at||i.id,message_count:i.message_count||0,phase:i.phase||null,feature:i.feature||null,bug_ref:i.bug_ref||null,tags:i.tags||{},entries:null}))}catch{}if(t)try{const o=await m.historyChat(t,300),n=new Map;for(const i of o.entries||[]){const a=i.source||"ui";if(a==="ui")continue;const s=i.session_id||"hist_"+i.ts;n.has(s)||n.set(s,{id:s,title:(i.user_input||"").slice(0,60)||s.slice(0,14),source:a,ts:i.ts||"",message_count:0,entries:[]});const d=n.get(s);d.message_count++,d.entries.push(i),i.phase&&!d.phase&&(d.phase=i.phase,d.tags={phase:i.phase})}r.push(...n.values())}catch{}if(t)try{const o=await m.getSessionPhases(t);for(const n of r){const i=o[n.id];i?.phase&&(n.phase=i.phase,n.tags={...n.tags||{},phase:i.phase})}}catch{}if(r.sort((o,n)=>(n.ts||"").localeCompare(o.ts||"")),ut=r,!r.length){e.innerHTML='<div style="font-size:0.65rem;color:var(--muted);padding:0.5rem 0.25rem">No sessions yet</div>';return}e.innerHTML=r.slice(0,60).map((o,n)=>{const i=o.id===ne,a=o.source==="ui"?"var(--accent)":o.source==="claude_cli"?"var(--blue)":"var(--green)",s=o.source==="ui"?"UI":o.source==="claude_cli"?"CLI":"WF",d=!!o.phase,l=o.phase||null,c=d?`<span style="font-size:0.5rem;background:var(--accent)22;color:var(--accent);padding:0 0.22rem;border-radius:2px;flex-shrink:0">${P(l)}</span>`:'<span style="font-size:0.5rem;color:#e74c3c;flex-shrink:0" title="Missing phase — load session and set it">⚠</span>',g=o.feature?`<span style="font-size:0.5rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60px">#${P(o.feature)}</span>`:"",f=d?i?"2px solid var(--accent)":"2px solid transparent":"2px solid #e74c3c";return`
      <div onclick="window._chatLoadAny('${P(o.id)}')"
        style="padding:0.32rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               border-left:${f};
               font-size:0.63rem;color:${i?"var(--text)":"var(--text2)"};
               background:${i?"var(--surface2)":""};
               transition:background 0.1s;margin-bottom:1px"
        title="${P(o.title)}"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background='${i?"var(--surface2)":""}'">
        <div style="display:flex;align-items:center;gap:0.3rem;margin-bottom:2px">
          <span style="font-size:0.52rem;color:var(--muted);flex-shrink:0">${n+1}.</span>
          <span style="font-size:0.5rem;color:${a};background:${a}1a;
                       padding:0 0.22rem;border-radius:2px;flex-shrink:0;letter-spacing:0.5px">${s}</span>
          ${c}
          ${g}
        </div>
        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${P(o.title)}</div>
      </div>`}).join("")}window._chatLoadAny=async e=>{const t=ut.find(i=>i.id===e);if(!t)return;if(t.source==="ui"){await window._chatLoad(e);return}ne=e,Zr(t.tags||{});const r=document.getElementById("chat-messages");if(!r)return;if(r.innerHTML="",!t.entries?.length){V("No messages in this session.");return}const o=["<task-notification>","<tool-use-id>","<task-id>","<parameter>"],n=[...t.entries].sort((i,a)=>(i.ts||"").localeCompare(a.ts||""));for(const i of n){const a=i.user_input||"";o.some(s=>a.startsWith(s))||(a&&lr(a),i.output&&to(i.output))}document.querySelectorAll("#chat-sessions > div").forEach((i,a)=>{const s=ut[a]?.id===e;i.style.background=s?"var(--surface2)":"",i.style.color=s?"var(--text)":"var(--text2)"})};async function kn(){const e=x.currentProject?.name;if(e){try{ce=((await m.listPrompts(e)).prompts||[]).filter(o=>o.path.startsWith("roles/"));const r=document.getElementById("chat-role");r&&ce.length&&ce.forEach(o=>{const n=document.createElement("option");n.value=o.path,n.textContent=o.name.replace(".md",""),r.appendChild(n)})}catch{}try{Te=(await m.listWorkflows(e)).workflows||[]}catch{}}}window._chatNew=()=>{ne=null,ze=[],oe=[],_e=[],ht();const e=document.getElementById("chat-messages");e&&(e.innerHTML=""),cr(),$e(),ot(),Le(),Ze()};function En(){const e=document.getElementById("chat-resize-handle"),t=document.getElementById("chat-session-panel");if(!e||!t)return;let r=!1,o=0,n=0;e.addEventListener("mousedown",i=>{r=!0,o=i.clientX,n=t.offsetWidth,document.body.style.cursor="col-resize",document.body.style.userSelect="none",i.preventDefault()}),e.addEventListener("mouseover",()=>{e.style.background="var(--accent)"}),e.addEventListener("mouseout",()=>{r||(e.style.background="var(--border)")}),document.addEventListener("mousemove",i=>{r&&(t.style.width=`${Math.max(120,Math.min(400,n+(i.clientX-o)))}px`)}),document.addEventListener("mouseup",()=>{r&&(r=!1,document.body.style.cursor=document.body.style.userSelect="",e.style.background="var(--border)",localStorage.setItem("aicli_chat_sessions_w",String(t.offsetWidth)))})}async function Cn(e,t,r){const o=document.getElementById("session-commits-footer");if(o&&o.remove(),!!t)try{const n=await m.getSessionCommits(t,r),i=n.commits||[];if(!i.length)return;const a=(n.github_repo||"").replace(/\/$/,""),s=i.map(l=>{const c=(l.commit_hash||"").slice(0,8),g=(l.committed_at||"").slice(0,16).replace("T"," "),f=(l.commit_msg||"").slice(0,80);return`<div style="display:flex;gap:0.6rem;align-items:baseline;padding:0.18rem 0;
                          border-bottom:1px solid var(--border);font-size:0.62rem">
        ${a?`<a href="${a}/commit/${P(l.commit_hash)}" target="_blank"
              style="font-family:monospace;color:var(--accent);text-decoration:none"
              title="Open in GitHub">${c} ↗</a>`:`<span style="font-family:monospace;color:var(--accent)">${c}</span>`}
        <span style="color:var(--muted);white-space:nowrap">${P(g)}</span>
        <span style="color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${P(f)}</span>
        ${l.feature?`<span style="color:#27ae60;white-space:nowrap;font-size:0.55rem">#${P(l.feature)}</span>`:""}
      </div>`}).join(""),d=document.createElement("div");d.id="session-commits-footer",d.style.cssText="margin:1rem 0.75rem 0.5rem;border:1px solid var(--border);border-radius:6px;overflow:hidden",d.innerHTML=`
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.6rem;
                  background:var(--surface2);border-bottom:1px solid var(--border)">
        <span style="font-size:0.6rem;font-weight:700;color:var(--muted);letter-spacing:1px;text-transform:uppercase">
          ⑂ ${i.length} Commit${i.length!==1?"s":""} in this session
        </span>
        ${a?`<a href="${a}/commits" target="_blank"
            style="font-size:0.55rem;color:var(--accent);text-decoration:none;margin-left:auto">
            View on GitHub ↗</a>`:""}
      </div>
      <div style="padding:0.3rem 0.6rem 0.2rem">${s}</div>`,e.appendChild(d)}catch{}}window._chatLoad=async e=>{ne=e;try{const t=await m.chatSession(e),r=document.getElementById("chat-messages");if(!r)return;r.innerHTML="";const o=t.metadata?.tags||{},n=ut.find(s=>s.id===e)?.tags||{},i=Object.keys(o).length?o:n;Zr(i);for(const s of t.messages||[])s.role==="user"&&lr(s.content),s.role==="assistant"&&to(s.content);const a=x.currentProject?.name;try{ze=((await m.entities.getEntitySessionTags(e,a)).tags||[]).map(d=>({value_id:d.id,category_name:d.category_name,name:d.name,color:d.color,icon:d.icon})),$e(),Le()}catch{}Cn(r,e,a),document.querySelectorAll("#chat-sessions > div").forEach((s,d)=>{const l=ut[d]?.id===e;s.style.background=l?"var(--surface2)":""})}catch{p("Could not load session","error")}};window._chatSend=async()=>{if(Xr)return;const e=document.getElementById("chat-input"),t=e?.value?.trim();if(!t)return;if(t==="/help"){e.value="",e.style.height="auto";const i=ce.map(s=>s.name.replace(".md","")).join(", ")||"(none loaded)",a=Te.map(s=>typeof s=="string"?s:s.name).join(", ")||"(none loaded)";V(`## Available Commands

| Command | Description |
|---|---|
| \`/help\` | Show this help |
| \`/memory\` | Refresh CLAUDE.md + CONTEXT.md → copy to code dir |
| \`/role <name>\` | Set system prompt role · available: ${i} |
| \`/workflow <name>\` | Run a workflow · available: ${a} |
| \`/switch <provider>\` | Switch LLM: claude, openai, deepseek, gemini, grok |
| \`/compare <prompt.md>\` | Run prompt on multiple LLMs side-by-side |
| \`/project new\\|list\\|switch\` | Manage projects |
| \`/tag <name>\` | Tag this session |
| \`/feature <name>\` | Set feature context |
| \`/search-tag <tag>\` | Search history by tag |
| \`/push [branch]\` | Commit and push to git · e.g. \`/push master\` |
| \`/analytics\` | Show usage and cost stats |
| \`/history\` | Show last 20 commits |
| \`/reload\` | Reload system prompt |
| \`/clear\` | Clear conversation history |
| \`/pipeline [status]\` | Show pipeline health dashboard |`);return}if(t.startsWith("/role ")){const i=t.slice(6).trim();e.value="",e.style.height="auto";const a=x.currentProject?.name;if(!a){p("No project open","error");return}const s=ce.find(d=>d.name.replace(".md","")===i||d.path===i);if(s)try{const d=await m.readPrompt(s.path,a);U({currentProject:{...x.currentProject,system_prompt:d.content||""}});const l=document.getElementById("chat-role");l&&(l.value=s.path),V(`Role set: **${s.name.replace(".md","")}**`)}catch(d){p(`Could not load role: ${d.message}`,"error")}else V(`Role not found: ${i}. Available: ${ce.map(d=>d.name.replace(".md","")).join(", ")}`);return}if(t==="/memory"){e.value="",e.style.height="auto";const i=x.currentProject?.name;if(!i){p("No project open","error");return}V("Generating memory files…");try{const a=await m.generateMemory(i);a.suggested_tags?.length&&(_e=a.suggested_tags,ot());try{const l=await m.getProjectContext(i,!1),c=l.context||l.claude_md||"";c&&U({currentProject:{...x.currentProject,system_prompt:c}})}catch{}const s=(a.generated||[]).slice(0,4).join(", "),d=a.synthesized?" *(LLM-synthesized)*":"";V(`✓ **Memory files refreshed**${d} → \`${s}\``),a.suggested_tags?.length?V(`📎 **${a.suggested_tags.length}** AI tag suggestion${a.suggested_tags.length>1?"s":""} appeared above the chat — review and accept or dismiss.`):a.suggestions_note&&V(`ℹ️ No tag suggestions: *${a.suggestions_note}* — check backend logs for detail.`)}catch(a){V(`Error: ${a.message}`)}return}if(t==="/push"||t.startsWith("/push ")){const i=t.slice(5).trim();e.value="",e.style.height="auto";const a=x.currentProject?.name;if(!a){p("No project open","error");return}V(`Committing and pushing${i?` to **${i}**`:""}…`);try{const s=await m.gitCommitPush(a,{message_hint:"manual /push from chat",provider:Me,branch:i});if(s.committed===!1)V("✓ **No changes** to commit — working tree is clean.");else if(s.pushed){const d=s.pull_message?`

**Sync:** ${s.pull_message}`:"";V(`✓ **Pushed** \`${s.commit_hash}\` → \`${i||"default branch"}\`

**Message:** ${s.commit_message}

**Files:** ${(s.files||[]).join(", ")}`+d)}else V(`✓ Committed \`${s.commit_hash}\` but **push failed:**

\`${s.push_error||"Check credentials in Settings → Project → Git"}\``)}catch(s){V(`**Push failed:** ${s.message}`)}return}if(t==="/pipeline"||t==="/pipeline status"){e.value="",e.style.height="auto";const i=x.currentProject?.name;if(!i){p("No project open","error");return}V("Fetching pipeline status…");try{const a=await m.pipeline.status(i),s=a?.last_24h||{},d=a?.pending||{},l=["commit_embed","commit_store","commit_code_extract","session_summary","tag_match","work_item_embed"],c={commit_embed:"commit_embed",commit_store:"commit_store",commit_code_extract:"commit_code",session_summary:"session_summary",tag_match:"tag_match",work_item_embed:"wi_embed"};let g=`## Pipeline Health — last 24h

`;g+=`| Pipeline | OK | Errors | Skipped | Last Run |
`,g+=`|---|---|---|---|---|
`;for(const u of l){const h=s[u]||{ok:0,error:0,skipped:0,last_run:null},_=h.last_run?new Date(h.last_run).toLocaleTimeString():"—";g+=`| \`${c[u]}\` | ${h.ok} | ${h.error} | ${h.skipped} | ${_} |
`}const f=[];d.commits_not_embedded>0&&f.push(`- ${d.commits_not_embedded} commit(s) not embedded`),d.work_items_unmatched>0&&f.push(`- ${d.work_items_unmatched} work item(s) unmatched`),f.length&&(g+=`
**Pending:**
${f.join(`
`)}`),V(g),window._nav("pipeline")}catch(a){V(`**Pipeline status error:** ${a.message}`)}return}if(t==="/clear"){e.value="",e.style.height="auto",ne=null;const i=document.getElementById("chat-messages");i&&(i.innerHTML=""),cr();return}if(t.startsWith("/switch ")||t==="/switch"){const i=t.slice(8).trim();e.value="",e.style.height="auto";const a=document.getElementById("chat-provider");Yt.find(s=>s.id===i)?(Me=i,a&&(a.value=i),V(`Switched to **${i}**`)):V(`Unknown provider: ${i}. Options: ${Yt.map(s=>s.id).join(", ")}`);return}e.value="",e.style.height="auto",document.querySelector(".chat-welcome")?.remove(),lr(t);const{bubble:r,scrollInto:o}=Tn(Me);Ir(!0);const n=x.currentProject?.system_prompt||"";ve.phase||V("⚠ **No phase tag set.** Select a phase above to categorize this session.");try{const i=await m.chatStream(t,Me,ne,n,ve),a=i.headers.get("X-Session-Id");a&&(ne=a,oe.length&&sr());const s=i.body.getReader(),d=new TextDecoder;let l="",c="",g=null;e:for(;;){const{done:u,value:h}=await s.read();if(u)break;l+=d.decode(h,{stream:!0});const _=l.split(`

`);l=_.pop();for(const C of _){if(!C.startsWith("data: "))continue;const S=C.slice(6);if(S==="[DONE]")break e;if(S.startsWith("[ERROR]"))throw new Error(S.slice(8).trim()||"Stream error");if(S.startsWith("[EVENT:")){g=S.slice(7);continue}c+=S,r.innerHTML=Lt(c)+'<span style="opacity:0.3;animation:cursorBlink 1s infinite">▌</span>',o()}}if(r.innerHTML=Lt(c),o(),Ze(),g){const u=g;setTimeout(()=>In(u),2500)}const f=x.currentProject;f?.auto_commit_push&&f?.name&&zn(f.name,t,c)}catch(i){r.innerHTML=`<span style="color:var(--red)">Error: ${P(i.message)}</span>`,p(i.message,"error")}finally{Ir(!1),e?.focus()}};async function zn(e,t){try{const r=await m.gitCommitPush(e,{message_hint:t.slice(0,200),provider:Me});if(r.committed===!1)return;if(r.pushed)V(`↑ **Auto-pushed** \`${r.commit_hash}\` — ${r.commit_message}`);else{const o=r.push_error||"Check Git credentials in Settings → Project → Git";V(`↑ Committed \`${r.commit_hash}\` but **push failed:** ${o}`)}}catch(r){V(`⚠ Auto-commit failed: ${r.message}

Check **Settings → Project** — make sure *Code directory* and *Git credentials* are configured.`)}}async function In(e){try{const t=x.currentProject?.name||"",o=(await m.entities.getSuggestions(t,e))?.events?.[0];o?.metadata?.tag_suggestions?.length&&Sn(o)}catch{}}function Sn(e){const t=document.getElementById("chat-messages");if(!t)return;const r=e.metadata?.tag_suggestions||[];if(!r.length)return;const o=document.createElement("div");o.dataset.suggestionEventId=e.id,o.style.cssText=["display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap","padding:0.35rem 0.75rem;margin:0.15rem 0","animation:msgIn 0.2s ease-out"].join(";");const n=document.createElement("span");n.style.cssText="font-size:0.6rem;color:var(--muted);white-space:nowrap",n.textContent="📎 Tag:",o.appendChild(n),r.forEach(s=>{const d=document.createElement("span"),l=s.from_session===!0;d.style.cssText=[`background:${l?"var(--accent)":"var(--surface2)"}`,`color:${l?"#fff":"var(--text)"}`,"border:1px solid var(--border)","border-radius:12px","padding:0.15rem 0.55rem","font-size:0.62rem","cursor:pointer","transition:background 0.15s,opacity 0.15s","user-select:none"].join(";"),d.title=l?"Applied from session tags":"Click to apply tag",d.dataset.valueId=s.value_id,d.dataset.applied=l?"true":"false",d.innerHTML=`${P(s.category)}/<strong>${P(s.name)}</strong>${l?" ✓":" +"}`,l||d.addEventListener("click",async()=>{if(d.dataset.applied!=="true")try{await m.entities.addTag(e.id,{entity_value_id:s.value_id,auto_tagged:!1}),d.dataset.applied="true",d.style.background="var(--accent)",d.style.color="#fff",d.innerHTML=`${P(s.category)}/<strong>${P(s.name)}</strong> ✓`}catch(c){p(c.message,"error")}}),o.appendChild(d)});const i=r.filter(s=>!s.from_session);if(i.length>1){const s=document.createElement("span");s.style.cssText="font-size:0.6rem;color:var(--accent);cursor:pointer;white-space:nowrap;text-decoration:underline",s.textContent="apply all",s.addEventListener("click",async()=>{for(const d of i)try{await m.entities.addTag(e.id,{entity_value_id:d.value_id,auto_tagged:!1})}catch{}o.querySelectorAll("span[data-value-id]").forEach(d=>{d.dataset.applied="true",d.style.background="var(--accent)",d.style.color="#fff"}),s.remove()}),o.appendChild(s)}const a=document.createElement("span");a.style.cssText="font-size:0.7rem;color:var(--muted);cursor:pointer;margin-left:auto;padding:0 0.25rem",a.title="Dismiss suggestions",a.textContent="✕",a.addEventListener("click",async()=>{o.remove();try{await m.entities.dismissSuggestions(e.id)}catch{}}),o.appendChild(a),t.appendChild(o),t.scrollTop=t.scrollHeight}function Ir(e){Xr=e;const t=document.getElementById("chat-send-btn");t&&(t.disabled=e,t.style.opacity=e?"0.35":"1",t.textContent=e?"■":"↑")}function V(e){const t=document.getElementById("chat-messages");if(!t)return;const r=document.createElement("div");r.style.cssText="display:flex;justify-content:center;animation:msgIn 0.2s ease-out",r.innerHTML=`<div style="font-size:0.68rem;color:var(--muted);background:var(--surface2);
    border:1px solid var(--border);border-radius:20px;padding:0.25rem 0.85rem">
    ${Lt(e)}</div>`,t.appendChild(r),t.scrollTop=t.scrollHeight}function lr(e){const t=document.getElementById("chat-messages");if(!t)return;const r=document.createElement("div");r.style.cssText="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end;animation:msgIn 0.2s ease-out",r.innerHTML=`
    <div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">you</div>
    <div style="max-width:78%;background:var(--surface2);border:1px solid var(--border);
                border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;
                word-break:break-word;user-select:text;-webkit-user-select:text;
                white-space:pre-wrap">${P(e)}</div>`,t.appendChild(r),t.scrollTop=t.scrollHeight}function to(e){const t=document.getElementById("chat-messages");if(!t)return;const r=document.createElement("div");r.style.cssText="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-start;animation:msgIn 0.2s ease-out";const o=document.createElement("div");o.style.cssText="max-width:78%;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;word-break:break-word;user-select:text;-webkit-user-select:text",o.innerHTML=Lt(e),r.innerHTML='<div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">assistant</div>',r.appendChild(o),t.appendChild(r),t.scrollTop=t.scrollHeight}function Tn(e){const t=document.getElementById("chat-messages"),r=document.createElement("div");r.style.cssText="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-start;animation:msgIn 0.2s ease-out",r.innerHTML=`<div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">${P(e)}</div>`;const o=document.createElement("div");return o.style.cssText="max-width:78%;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;word-break:break-word;user-select:text;-webkit-user-select:text",o.innerHTML='<span style="opacity:0.3;animation:cursorBlink 1s infinite">▌</span>',r.appendChild(o),t.appendChild(r),t.scrollTop=t.scrollHeight,{bubble:o,scrollInto:()=>{t.scrollTop=t.scrollHeight}}}function cr(){const e=document.getElementById("chat-messages");if(!e)return;const t=document.createElement("div");t.className="chat-welcome",t.style.cssText="padding:1.5rem 2rem;max-width:720px;width:100%";const r=x.currentProject;if(!r){t.innerHTML=`
      <div style="font-size:1.4rem;font-weight:800;color:var(--accent);margin-bottom:0.35rem">aicli Chat</div>
      <div style="font-size:0.68rem;color:var(--muted)">Open a project from the sidebar to start chatting with context.</div>`,e.appendChild(t);return}const o=ce.length?`
    <div style="margin-bottom:1.2rem">
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Roles</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem">
        <button onclick="window._quickRole('')"
          style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                 border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
          onmouseenter="this.style.borderColor='var(--accent)'"
          onmouseleave="this.style.borderColor='var(--border)'">Default</button>
        ${ce.map(a=>`
          <button onclick="window._quickRole('${P(a.path)}')"
            style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                   border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">${P(a.name.replace(".md",""))}</button>`).join("")}
      </div>
    </div>`:"",n=Te.length?`
    <div style="margin-bottom:1.2rem">
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Workflows</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem">
        ${Te.slice(0,8).map(a=>{const s=typeof a=="string"?a:a.name;return`<button onclick="document.getElementById('chat-input').value='/workflow ${P(s)}';document.getElementById('chat-input').focus()"
            style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                   border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">⟳ ${P(s)}</button>`}).join("")}
      </div>
    </div>`:"";window._chatWelcomePrompts=["Explain the purpose, architecture and current state of this project.","Based on the project context and recent history, what should I focus on next?","Summarize the most recent changes and commits to this project."];const i=["Explain this project","What should I work on?","Summarise recent changes"];t.innerHTML=`
    <div style="display:flex;align-items:baseline;gap:0.6rem;margin-bottom:0.2rem">
      <div style="font-size:0.9rem;font-weight:700;color:var(--text)">${P(r.name)}</div>
      ${r.system_prompt?'<span style="font-size:0.58rem;color:var(--green)">✓ context loaded</span>':""}
    </div>
    <div style="font-size:0.62rem;color:var(--muted);margin-bottom:1.2rem">${P(r.description||"AI-assisted development workspace")}</div>
    ${o}
    ${n}
    <div>
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Quick start</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:0.4rem">
        ${i.map((a,s)=>`
          <div onclick="window._chatQuickPrompt(${s})"
            style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                   padding:0.5rem 0.7rem;cursor:pointer;font-size:0.68rem;line-height:1.4;transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">${P(a)}</div>`).join("")}
      </div>
    </div>
  `,e.appendChild(t)}window._chatQuickPrompt=e=>{const t=(window._chatWelcomePrompts||[])[e];if(!t)return;const r=document.getElementById("chat-input");r&&(r.value=t,r.focus())};window._quickRole=async e=>{const t=x.currentProject;if(!t)return;const r=document.getElementById("chat-role");if(e)try{const o=await m.readPrompt(e,t.name);U({currentProject:{...x.currentProject,system_prompt:o.content||""}}),r&&(r.value=e),p(`Role: ${e.split("/").pop().replace(".md","")}`,"info")}catch(o){p(`Could not load role: ${o.message}`,"error")}else{const o=await m.getProject(t.name).catch(()=>t);U({currentProject:{...x.currentProject,system_prompt:o.claude_md||o.project_md||""}}),r&&(r.value=""),p("Role reset to default","info")}};function Lt(e){return e?e.replace(/```(\w*)\n?([\s\S]*?)```/g,(t,r,o)=>`<pre style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:0.75rem;overflow-x:auto;margin:0.5rem 0"><code style="color:var(--green);font-size:0.72rem;white-space:pre">${P(o.trim())}</code></pre>`).replace(/`([^`\n]+)`/g,'<code style="background:var(--bg);border:1px solid var(--border);padding:0.1rem 0.3rem;border-radius:3px;font-size:0.75rem;color:var(--blue)">$1</code>').replace(/^### (.+)$/gm,'<h3 style="font-size:0.82rem;color:var(--accent);margin:0.6rem 0 0.2rem;font-family:var(--font-ui)">$1</h3>').replace(/^## (.+)$/gm,'<h2 style="font-size:0.9rem;margin:0.75rem 0 0.3rem;font-family:var(--font-ui)">$1</h2>').replace(/^# (.+)$/gm,'<h1 style="font-size:1rem;margin:0.75rem 0 0.3rem;font-family:var(--font-ui)">$1</h1>').replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>").replace(/^[-*] (.+)$/gm,'<li style="margin-left:1.2rem;margin-bottom:0.15rem">$1</li>').replace(/^(\d+)\. (.+)$/gm,'<li style="margin-left:1.2rem;margin-bottom:0.15rem">$2</li>').replace(/\n\n+/g,'</p><p style="margin:0.5rem 0">').replace(/\n/g,"<br>"):""}function P(e){return e?String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"):""}const ro=document.createElement("style");ro.textContent=`
  @keyframes msgIn        { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
  @keyframes cursorBlink  { 0%,49%{opacity:0.3} 50%,100%{opacity:0} }
`;document.head.appendChild(ro);let Ve=null,ue=[],oo=null,gt=!1,me=[],Ne={},Ce=null;function no(e,t,r=""){return new Promise(o=>{const n=document.createElement("div");n.style.cssText="position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);display:flex;align-items:center;justify-content:center";const i=document.createElement("div");i.style.cssText="background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;padding:1.5rem;min-width:320px;box-shadow:0 24px 64px rgba(0,0,0,0.7)",i.innerHTML=`
      <div style="font-size:0.95rem;font-weight:700;margin-bottom:0.75rem;color:#fff">${e}</div>
      <label style="display:block;font-size:0.7rem;color:rgba(255,255,255,0.5);margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.05em">${t}</label>
      <input id="_pm-input" type="text" value="" placeholder="${r}"
        style="width:100%;box-sizing:border-box;padding:0.5rem 0.6rem;border:1px solid rgba(255,255,255,0.18);border-radius:6px;background:rgba(255,255,255,0.07);color:#fff;font-size:0.84rem;outline:none">
      <div style="display:flex;justify-content:flex-end;gap:0.5rem;margin-top:1rem;padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08)">
        <button id="_pm-cancel" class="btn btn-ghost btn-sm">Cancel</button>
        <button id="_pm-ok" class="btn btn-primary btn-sm">Create</button>
      </div>`,n.appendChild(i),document.body.appendChild(n);const a=i.querySelector("#_pm-input");setTimeout(()=>{a.focus(),a.select()},0);const s=d=>{n.remove(),o(d)};i.querySelector("#_pm-cancel").onclick=()=>s(null),i.querySelector("#_pm-ok").onclick=()=>s(a.value),i.addEventListener("keydown",d=>{d.key==="Enter"&&s(a.value),d.key==="Escape"&&s(null)}),n.onclick=d=>{d.target===n&&s(null)}})}const Pn=["anthropic","openai","deepseek","gemini","xai","ollama"],Jt={anthropic:["claude-sonnet-4-6","claude-haiku-4-5-20251001","claude-opus-4-6"],openai:["gpt-4o","gpt-4o-mini","gpt-4-turbo"],deepseek:["deepseek-chat","deepseek-coder"],gemini:["gemini-1.5-pro","gemini-1.5-flash"],xai:["grok-2-latest","grok-vision-beta"],ollama:["llama3","mistral","codellama"]};async function Ln(e,t){Ve=null,Ce=null,oo=t,gt=!1,me=[],Ne={};const r=parseInt(localStorage.getItem("aicli_prompts_tree_w")||"220",10);if(e.className="view active",e.style.cssText="display:flex;flex-direction:column;overflow:hidden;height:100%",e.innerHTML=`
    <div class="prompts-view" style="flex:1;overflow:hidden">
      <!-- Left panel -->
      <div class="prompts-tree" id="prompts-tree-panel" style="width:${r}px;display:flex;flex-direction:column">

        <!-- Agent Roles section (top, takes most space) -->
        <div class="prompts-tree-header" style="flex-shrink:0">
          <span class="prompts-tree-label">Agent Roles</span>
          <button class="btn btn-ghost btn-sm" style="padding:0.15rem 0.4rem;font-size:0.65rem"
            onclick="window._rolesNew()" title="New agent role">+</button>
        </div>
        <div id="roles-list-body" style="overflow-y:auto;flex:1;min-height:120px;border-bottom:1px solid var(--border)">
          <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- System Roles section (bottom) -->
        <div id="sys-roles-section" style="display:flex;flex-shrink:0;flex-direction:column;max-height:35%">
          <div class="prompts-tree-header" style="flex-shrink:0">
            <span class="prompts-tree-label" style="font-size:0.62rem">System Roles</span>
            <button id="sys-roles-new-btn" class="btn btn-ghost btn-sm"
              style="padding:0.12rem 0.35rem;font-size:0.6rem;display:none"
              onclick="window._sysRolesNew()" title="New system role">+</button>
          </div>
          <div id="sys-roles-list-body" style="overflow-y:auto;flex:1">
            <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
          </div>
        </div>

      </div>

      <!-- Resize handle -->
      <div id="prompts-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize"></div>

      <!-- Right panel -->
      <div class="prompts-editor-area">
        <div class="prompts-editor-toolbar" id="prompts-toolbar">
          <span class="prompts-editor-path" id="prompts-path">Select a role or file</span>
        </div>
        <div id="prompts-editor-body"
          style="flex:1;display:flex;align-items:center;justify-content:center;
                 color:var(--muted);font-size:0.72rem">
          <span>Select a role or file from the left panel</span>
        </div>
      </div>
    </div>
  `,window._rolesNew=jn,window._rolesSelect=io,window._rolesDelete=On,window._rolesSave=Nn,window._rolesExportYaml=Hn,window._rolesProviderChange=Un,window._sysRolesNew=Wn,window._sysRolesSelect=ao,window._sysRolesSave=qn,window._sysRolesDelete=Gn,window._sysRolesAttach=Vn,window._sysRolesDetach=Yn,Kn(),!t){document.getElementById("roles-list-body").innerHTML='<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">No project open</div>';return}await Bn(t)}async function Bn(e){const t=document.getElementById("roles-list-body");if(t)try{const[r,o]=await Promise.all([m.agentRoles.list(e||"_global"),m.systemRoles.list().catch(()=>({system_roles:[],is_admin:!1}))]);ue=r.roles||r||[],gt=r.is_admin||o.is_admin||!1,me=o.system_roles||[];const n=document.getElementById("sys-roles-section"),i=document.getElementById("sys-roles-new-btn");n&&(n.style.display="flex"),i&&(i.style.display=gt?"":"none"),bt(),wt()}catch(r){t.innerHTML=`<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--red)">${G(r.message)}</div>`}}function Sr(e){const t=Ve?.id===e.id,o=e.role_type==="internal"?`<span style="font-size:0.55rem;padding:0.05rem 0.3rem;border-radius:3px;
                   background:rgba(155,126,248,0.18);color:#9b7ef8;flex-shrink:0">INT</span>`:"";return`
    <div onclick="window._rolesSelect(${e.id})"
         style="padding:0.4rem 0.75rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.5rem;
                background:${t?"rgba(100,108,255,0.1)":"transparent"};
                border-left:2px solid ${t?"var(--accent)":"transparent"}"
         onmouseenter="this.style.background='${t?"rgba(100,108,255,0.1)":"var(--surface2)"}'"
         onmouseleave="this.style.background='${t?"rgba(100,108,255,0.1)":"transparent"}'">
      <div style="flex:1;min-width:0">
        <div style="font-size:0.7rem;font-weight:500;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${G(e.name)}</div>
        <div style="font-size:0.55rem;color:var(--muted)">${G(e.provider||"")} ${e.model?"· "+G(e.model):""}</div>
      </div>
      ${o}
    </div>`}function bt(){const e=document.getElementById("roles-list-body");if(!e)return;if(!ue.length){e.innerHTML=`<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">
      No roles yet — click <strong>+</strong> to create one</div>`;return}const t=ue.filter(n=>n.role_type!=="internal"),r=ue.filter(n=>n.role_type==="internal");let o=t.map(Sr).join("");r.length&&(o+=`<div style="padding:0.3rem 0.75rem;font-size:0.58rem;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.06em;color:#9b7ef8;
                          background:rgba(155,126,248,0.06);border-top:1px solid var(--border);
                          border-bottom:1px solid var(--border);margin-top:0.25rem">
               Internal Prompts
             </div>`,o+=r.map(Sr).join("")),e.innerHTML=o}async function jn(){const e=await no("New Agent Role",'Role name (e.g. "Senior Developer"):',"My Role");if(e?.trim())try{const t=await m.agentRoles.create({name:e.trim(),provider:"anthropic",model:"claude-haiku-4-5-20251001",description:"",system_prompt:"",project:oo||"_global"});ue.push(t),bt(),io(t.id),p(`Role "${e}" created`,"success")}catch(t){p("Create failed: "+t.message,"error")}}async function io(e){Ce=null;const t=ue.find(o=>o.id===e);if(!t)return;Ve=t,bt(),Mn(t);const r=document.getElementById("prompts-path");r&&(r.textContent=`Role: ${t.name}`),Rn(t);try{const o=await m.systemRoles.listLinks(e);Ne[e]=o.links||[]}catch{Ne[e]=[]}mr(e)}async function Rn(e){const t=document.getElementById("role-tools-grid");if(!t)return;let r=[];try{r=(await m.agentRoles.availableTools()).tools||[]}catch{t.innerHTML='<div style="font-size:0.65rem;color:var(--muted)">Tools unavailable</div>';return}const o=new Set(e.tools||[]),n={};for(const s of r)n[s.category]||(n[s.category]=[]),n[s.category].push(s);const i={git:"#e8834e",file:"#5b8af5",memory:"#9b7ef8",work_items:"#4ec9a6",other:"#888"};let a="";for(const[s,d]of Object.entries(n)){const l=i[s]||"#888";a+=d.map(c=>`
      <label style="display:flex;align-items:center;gap:0.35rem;cursor:pointer;
                    padding:0.2rem 0.4rem;border-radius:4px;border:1px solid var(--border);
                    background:var(--surface2);font-size:0.65rem;color:var(--text)">
        <input type="checkbox" value="${c.name}" ${o.has(c.name)?"checked":""}
          style="width:12px;height:12px;accent-color:${l};cursor:pointer">
        <span style="color:${l};font-size:0.55rem;font-weight:600;text-transform:uppercase">${s}</span>
        <span>${c.name}</span>
      </label>`).join("")}t.innerHTML=a||'<div style="font-size:0.65rem;color:var(--muted)">No tools registered</div>'}function mr(e){const t=document.getElementById("role-sys-roles-list");if(!t)return;const r=Ne[e]||[];if(!gt){if(!r.length){t.innerHTML='<div style="font-size:0.65rem;color:var(--muted)">No system roles attached</div>';return}t.innerHTML=r.map(a=>`
      <span style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:var(--surface2);border:1px solid var(--border);
                   border-radius:var(--radius);padding:0.2rem 0.5rem;
                   font-size:0.65rem;color:var(--text)">
        ${G(a.name)}
        <span style="font-size:0.55rem;opacity:0.6">[${G(a.category)}]</span>
      </span>
    `).join("");return}const o=new Set(r.map(a=>a.id)),n=me.filter(a=>!o.has(a.id));let i="";r.length?i+=r.map(a=>`
      <div style="display:flex;align-items:center;gap:0.5rem;
                  background:var(--surface2);border:1px solid var(--border);
                  border-radius:var(--radius);padding:0.3rem 0.6rem;
                  font-size:0.68rem">
        <span style="color:var(--muted);cursor:default" title="Drag to reorder">⠿</span>
        <span style="flex:1;color:var(--text)">${G(a.name)}</span>
        <span style="font-size:0.55rem;padding:0.1rem 0.35rem;background:var(--surface3);
                     border-radius:3px;color:var(--muted)">${G(a.category)}</span>
        <button onclick="window._sysRolesDetach(${e},${a.id})"
          style="background:none;border:none;cursor:pointer;color:var(--muted);
                 font-size:0.8rem;padding:0 0.2rem;line-height:1" title="Remove">×</button>
      </div>
    `).join(""):i+='<div style="font-size:0.65rem;color:var(--muted)">No system roles attached</div>',n.length&&(i+=`
      <div style="display:flex;gap:0.4rem;margin-top:0.3rem">
        <select id="sys-role-add-select"
          style="flex:1;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.25rem 0.4rem;border-radius:var(--radius);outline:none">
          <option value="">─ add a system role ─</option>
          ${n.map(a=>`<option value="${a.id}">${G(a.name)} [${G(a.category)}]</option>`).join("")}
        </select>
        <button class="btn btn-ghost btn-sm" onclick="window._sysRolesAttach(${e})"
          style="font-size:0.62rem;white-space:nowrap">Add</button>
      </div>
    `),t.innerHTML=i}const An=["prompt","md","code","github","tests","report","feedback","score","json"];function Qt(e,t,r){const o=r?.name||"",n=r?.type||"prompt";return`<div style="display:flex;gap:0.3rem;align-items:center" data-io-idx="${t}">
    <input value="${G(o)}" placeholder="name" data-io-name="${e}"
      style="flex:1;min-width:0;background:var(--bg);border:1px solid var(--border);
             color:var(--text);font-family:var(--font);font-size:0.68rem;padding:0.25rem 0.4rem;
             border-radius:var(--radius);outline:none">
    <select data-io-type="${e}"
      style="background:var(--bg);border:1px solid var(--border);color:var(--text);
             font-family:var(--font);font-size:0.68rem;padding:0.25rem 0.3rem;
             border-radius:var(--radius);outline:none">
      ${An.map(i=>`<option value="${i}" ${n===i?"selected":""}>${i}</option>`).join("")}
    </select>
    <button onclick="window._rolesRemoveIO('${e}',${t})"
      style="background:none;border:none;color:var(--muted);cursor:pointer;padding:0 0.2rem;font-size:0.8rem">✕</button>
  </div>`}window._rolesAddIO=function(e){const t=document.getElementById(`role-${e}s-list`);if(!t)return;const r=t.children.length,o=document.createElement("div");o.innerHTML=Qt(e,r,{name:"",type:"prompt"}),t.appendChild(o.firstElementChild)};window._rolesRemoveIO=function(e,t){const r=document.getElementById(`role-${e}s-list`);if(!r)return;r.querySelectorAll("[data-io-idx]").forEach(n=>{parseInt(n.dataset.ioIdx)===t&&n.remove()}),r.querySelectorAll("[data-io-idx]").forEach((n,i)=>{n.dataset.ioIdx=i,n.querySelectorAll("button").forEach(a=>{a.setAttribute("onclick",`window._rolesRemoveIO('${e}',${i})`)})})};function Tr(e){const t=document.getElementById(`role-${e}s-list`);if(!t)return[];const r=[];return t.querySelectorAll("[data-io-idx]").forEach(o=>{const n=o.querySelector(`[data-io-name="${e}"]`)?.value?.trim()||"",i=o.querySelector(`[data-io-type="${e}"]`)?.value||"prompt";n&&r.push({name:n,type:i})}),r}function Mn(e){const t=document.getElementById("prompts-editor-body"),r=document.getElementById("prompts-toolbar");if(!t)return;const o=e.role_type==="internal";r&&(r.innerHTML=`
    <span class="prompts-editor-path" id="prompts-path">Role: ${G(e.name)}</span>
    ${o?`<span style="font-size:0.6rem;padding:0.15rem 0.5rem;border-radius:10px;
                      background:rgba(155,126,248,0.18);color:#9b7ef8">INT — system managed</span>`:`<button class="btn btn-ghost btn-sm" style="color:var(--red);border-color:var(--red);font-size:0.62rem"
           onclick="window._rolesDelete(${e.id})">Delete</button>`}
    <button class="btn btn-ghost btn-sm" style="font-size:0.62rem"
      onclick="window._rolesExportYaml(${e.id}, ${JSON.stringify(e.name)})">↓ YAML</button>
    <button class="btn btn-primary btn-sm" id="roles-save-btn"
      onclick="window._rolesSave(${e.id})">Save</button>
  `);const n=(Jt[e.provider]||[]).concat(e.model&&!(Jt[e.provider]||[]).includes(e.model)?[e.model]:[]);t.style.cssText="flex:1;overflow-y:auto;padding:1.5rem",t.innerHTML=`
    <div style="max-width:700px;display:flex;flex-direction:column;gap:1rem">

      <!-- Name + Provider + Model row -->
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem">
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Name</label>
          <input id="role-name" value="${G(e.name)}"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Provider</label>
          <select id="role-provider" onchange="window._rolesProviderChange(this.value)"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
            ${Pn.map(i=>`<option value="${i}" ${e.provider===i?"selected":""}>${i}</option>`).join("")}
          </select>
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Model</label>
          <input id="role-model" value="${G(e.model||"")}" list="role-model-list"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
          <datalist id="role-model-list">
            ${n.map(i=>`<option value="${G(i)}">`).join("")}
          </datalist>
        </div>
      </div>

      <!-- Description + Role Type row -->
      <div style="display:grid;grid-template-columns:1fr auto;gap:0.75rem;align-items:start">
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Description</label>
          <input id="role-description" value="${G(e.description||"")}" placeholder="Short description of this role's purpose…"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Role Type</label>
          <select id="role-type"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none;white-space:nowrap">
            <option value="agent" ${(e.role_type||"agent")==="agent"?"selected":""}>Agent</option>
            <option value="system_designer" ${e.role_type==="system_designer"?"selected":""}>System Designer</option>
            <option value="reviewer" ${e.role_type==="reviewer"?"selected":""}>Reviewer</option>
            <option value="internal" ${e.role_type==="internal"?"selected":""}>Internal</option>
          </select>
        </div>
      </div>

      <!-- IO Types -->
      <div>
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          Inputs / Outputs <span style="text-transform:none;font-weight:400;opacity:0.7">(IO contract for pipeline)</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem">
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.3rem">Inputs</div>
            <div id="role-inputs-list" style="display:flex;flex-direction:column;gap:0.25rem">
              ${(e.inputs||[]).map((i,a)=>Qt("input",a,i)).join("")}
            </div>
            <button onclick="window._rolesAddIO('input')"
              style="margin-top:0.3rem;font-size:0.62rem;background:none;border:1px dashed var(--border);
                     color:var(--muted);border-radius:var(--radius);padding:0.2rem 0.5rem;cursor:pointer">+ Input</button>
          </div>
          <div>
            <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.3rem">Outputs</div>
            <div id="role-outputs-list" style="display:flex;flex-direction:column;gap:0.25rem">
              ${(e.outputs||[]).map((i,a)=>Qt("output",a,i)).join("")}
            </div>
            <button onclick="window._rolesAddIO('output')"
              style="margin-top:0.3rem;font-size:0.62rem;background:none;border:1px dashed var(--border);
                     color:var(--muted);border-radius:var(--radius);padding:0.2rem 0.5rem;cursor:pointer">+ Output</button>
          </div>
        </div>
      </div>

      <!-- ReAct + Max Iterations -->
      <div style="display:grid;grid-template-columns:auto auto 1fr;gap:1rem;align-items:center">
        <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer;font-size:0.72rem;color:var(--text)">
          <input type="checkbox" id="role-react" ${e.react!==!1?"checked":""}
            onchange="document.getElementById('role-max-iter-wrap').style.display=this.checked?'flex':'none'"
            style="width:14px;height:14px;cursor:pointer">
          Use ReAct reasoning (Thought / Action / Observation)
        </label>
        <div id="role-max-iter-wrap" style="display:${e.react!==!1?"flex":"none"};align-items:center;gap:0.4rem">
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;white-space:nowrap">Max iterations</label>
          <input type="number" id="role-max-iterations" value="${e.max_iterations||10}" min="1" max="50"
            style="width:60px;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;
                   padding:0.3rem 0.4rem;border-radius:var(--radius);outline:none;text-align:center">
        </div>
        <div></div>
      </div>

      <!-- Tools -->
      <div>
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          Tools <span style="text-transform:none;font-weight:400;opacity:0.7">(allowed in agentic loop)</span>
        </div>
        <div id="role-tools-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.25rem">
          <div style="font-size:0.65rem;color:var(--muted)">Loading tools…</div>
        </div>
      </div>

      <!-- System Roles (prepended fragments) -->
      <div id="role-sys-roles-section">
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          System Roles <span style="text-transform:none;font-weight:400;opacity:0.7">(prepended to prompt)</span>
        </div>
        <div id="role-sys-roles-list" style="display:flex;flex-direction:column;gap:0.3rem">
          <div style="font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>
      </div>

      <!-- System Prompt -->
      <div style="flex:1">
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">System Prompt</label>
        <textarea id="role-system-prompt"
          style="width:100%;box-sizing:border-box;min-height:320px;resize:vertical;
                 background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.5rem;border-radius:var(--radius);outline:none;
                 line-height:1.55"
          placeholder="You are a senior software architect…">${G(e.system_prompt||"")}</textarea>
      </div>

      <!-- Tags / extra info -->
      <div style="font-size:0.6rem;color:var(--muted)">
        ID: ${e.id} · created: ${e.created_at?new Date(e.created_at).toLocaleDateString():"—"}
      </div>
    </div>
  `}function Dn(){const e=document.querySelectorAll("#role-tools-grid input[type=checkbox]");return Array.from(e).filter(t=>t.checked).map(t=>t.value)}async function Hn(e,t){try{const r=await m.agentRoles.exportYaml(e),o=new Blob([r],{type:"text/yaml"}),n=URL.createObjectURL(o),i=document.createElement("a");i.href=n,i.download=`${(t||"role").toLowerCase().replace(/\s+/g,"_")}.yaml`,i.click(),URL.revokeObjectURL(n)}catch(r){p("Export failed: "+r.message,"error")}}async function Nn(e){const t=document.getElementById("role-name")?.value?.trim(),r=document.getElementById("role-provider")?.value,o=document.getElementById("role-model")?.value?.trim(),n=document.getElementById("role-description")?.value?.trim(),i=document.getElementById("role-system-prompt")?.value,a=document.getElementById("role-type")?.value||"agent",s=document.getElementById("role-react")?.checked??!0,d=parseInt(document.getElementById("role-max-iterations")?.value||"10",10),l=Dn(),c=Tr("input"),g=Tr("output");if(!t){p("Name required","error");return}Pr([]);try{const f=await m.agentRoles.patch(e,{name:t,provider:r,model:o,description:n,system_prompt:i,role_type:a,inputs:c,outputs:g,tools:l,react:s,max_iterations:d}),u=ue.findIndex(h=>h.id===e);u!==-1&&(ue[u]={...ue[u],...f,name:t,provider:r,model:o,description:n,system_prompt:i,role_type:a,inputs:c,outputs:g,tools:l,react:s,max_iterations:d}),Ve=ue[u]||Ve,bt(),p("Role saved","success")}catch(f){let u=[];try{const h=JSON.parse(f.message.match(/\{.*\}/s)?.[0]||"{}");u=h.errors||h.detail?.errors||[]}catch{}u.length?Pr(u):p("Save failed: "+f.message,"error")}}function Pr(e){let t=document.getElementById("role-validation-errors");if(!e.length){t&&t.remove();return}if(!t){t=document.createElement("div"),t.id="role-validation-errors",t.style.cssText=["background:rgba(220,53,69,0.12)","border:1px solid rgba(220,53,69,0.4)","border-radius:6px","padding:0.6rem 0.8rem","margin-bottom:0.75rem","font-size:0.7rem","color:#f08080"].join(";");const r=document.querySelector("#prompts-editor-body > div");r&&r.prepend(t)}t.innerHTML='<div style="font-weight:600;margin-bottom:0.3rem">Validation errors — role not saved:</div>'+e.map(r=>`<div>• ${r}</div>`).join("")}async function On(e){if(confirm("Delete this role? Pipeline steps using it will fall back to inline prompts."))try{await m.agentRoles.delete(e),ue=ue.filter(o=>o.id!==e),Ve=null,bt();const t=document.getElementById("prompts-editor-body");t&&(t.innerHTML=`<div style="display:flex;align-items:center;justify-content:center;
      height:100%;color:var(--muted);font-size:0.72rem">Role deleted</div>`);const r=document.getElementById("prompts-toolbar");r&&(r.innerHTML='<span class="prompts-editor-path" id="prompts-path">Select a role or file</span>'),p("Role deleted","success")}catch(t){p("Delete failed: "+t.message,"error")}}function Un(e){const t=document.getElementById("role-model-list");t&&(t.innerHTML=(Jt[e]||[]).map(r=>`<option value="${G(r)}">`).join(""))}function wt(){const e=document.getElementById("sys-roles-list-body");if(!e)return;if(!me.length){e.innerHTML=`<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">
      ${gt?"No system roles yet — click <strong>+</strong> to create one":"No system roles configured"}</div>`;return}const t={quality:"#4a90e2",security:"#e25c4a",output:"#4ae29b",review:"#e2b44a",general:"#999"};e.innerHTML=me.map(r=>`
    <div onclick="window._sysRolesSelect(${r.id})"
         style="padding:0.35rem 0.75rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.45rem;
                background:${Ce?.id===r.id?"var(--accent)18":"transparent"};
                border-left:2px solid ${Ce?.id===r.id?"var(--accent)":"transparent"}"
         onmouseenter="if(${Ce?.id!==r.id})this.style.background='var(--surface2)'"
         onmouseleave="if(${Ce?.id!==r.id})this.style.background='transparent'">
      <span style="width:6px;height:6px;border-radius:50%;flex-shrink:0;
                   background:${t[r.category]||"#999"}"></span>
      <div style="flex:1;min-width:0">
        <div style="font-size:0.68rem;font-weight:500;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${G(r.name)}</div>
        <div style="font-size:0.55rem;color:var(--muted)">${G(r.category)}</div>
      </div>
    </div>
  `).join("")}function ao(e){Ve=null;const t=me.find(o=>o.id===e);if(!t)return;Ce=t,wt(),Fn(t);const r=document.getElementById("prompts-path");r&&(r.textContent=`System Role: ${t.name}`)}function Fn(e){const t=document.getElementById("prompts-editor-body"),r=document.getElementById("prompts-toolbar");if(!t)return;r&&(r.innerHTML=`
    <span class="prompts-editor-path" id="prompts-path">System Role: ${G(e.name)}</span>
    <button class="btn btn-ghost btn-sm" style="color:var(--red);border-color:var(--red);font-size:0.62rem"
      onclick="window._sysRolesDelete(${e.id})">Delete</button>
    <button class="btn btn-primary btn-sm" onclick="window._sysRolesSave(${e.id})">Save</button>
  `);const o=["quality","security","output","review","general"];t.style.cssText="flex:1;overflow-y:auto;padding:1.5rem",t.innerHTML=`
    <div style="max-width:700px;display:flex;flex-direction:column;gap:1rem">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem">
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Name</label>
          <input id="sysrole-name" value="${G(e.name)}"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Category</label>
          <select id="sysrole-category"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
            ${o.map(n=>`<option value="${n}" ${e.category===n?"selected":""}>${n}</option>`).join("")}
          </select>
        </div>
      </div>
      <div>
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Description</label>
        <input id="sysrole-description" value="${G(e.description||"")}" placeholder="Short description…"
          style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                 border-radius:var(--radius);outline:none">
      </div>
      <div style="flex:1">
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Content (prepended as Markdown)</label>
        <textarea id="sysrole-content"
          style="width:100%;box-sizing:border-box;min-height:300px;resize:vertical;
                 background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.5rem;border-radius:var(--radius);outline:none;line-height:1.55"
          placeholder="## Coding Standards
- …">${G(e.content||"")}</textarea>
      </div>
      <div style="font-size:0.6rem;color:var(--muted)">
        ID: ${e.id} · category: ${G(e.category)} · created: ${e.created_at?new Date(e.created_at).toLocaleDateString():"—"}
      </div>
    </div>
  `}async function Wn(){const e=await no("New System Role",'System role name (e.g. "coding_standards"):',"my_standards");if(e?.trim())try{const t=await m.systemRoles.create({name:e.trim(),category:"general",description:"",content:""});me.push(t),wt(),ao(t.id),p(`System role "${e}" created`,"success")}catch(t){p("Create failed: "+t.message,"error")}}async function qn(e){const t=document.getElementById("sysrole-name")?.value?.trim(),r=document.getElementById("sysrole-category")?.value,o=document.getElementById("sysrole-description")?.value?.trim(),n=document.getElementById("sysrole-content")?.value;if(!t){p("Name required","error");return}try{const i=await m.systemRoles.patch(e,{name:t,category:r,description:o,content:n}),a=me.findIndex(s=>s.id===e);a!==-1&&(me[a]={...me[a],...i}),Ce=me[a]||Ce,wt(),p("System role saved","success")}catch(i){p("Save failed: "+i.message,"error")}}async function Gn(e){if(confirm("Delete this system role? Roles using it will no longer have it prepended."))try{await m.systemRoles.delete(e),me=me.filter(o=>o.id!==e),Ce=null,wt();const t=document.getElementById("prompts-editor-body"),r=document.getElementById("prompts-toolbar");t&&(t.innerHTML=`<div style="display:flex;align-items:center;justify-content:center;
      height:100%;color:var(--muted);font-size:0.72rem">System role deleted</div>`),r&&(r.innerHTML='<span class="prompts-editor-path" id="prompts-path">Select a role or file</span>'),p("System role deleted","success")}catch(t){p("Delete failed: "+t.message,"error")}}async function Vn(e){const t=document.getElementById("sys-role-add-select"),r=parseInt(t?.value||"0");if(!r){p("Select a system role to add","error");return}const o=(Ne[e]||[]).length;try{await m.systemRoles.attach(e,{system_role_id:r,order_index:o});const n=await m.systemRoles.listLinks(e);Ne[e]=n.links||[],mr(e),p("System role attached","success")}catch(n){p("Attach failed: "+n.message,"error")}}async function Yn(e,t){try{await m.systemRoles.detach(e,t),Ne[e]=(Ne[e]||[]).filter(r=>r.id!==t),mr(e),p("System role removed","success")}catch(r){p("Remove failed: "+r.message,"error")}}function Kn(){const e=document.getElementById("prompts-resize-handle"),t=document.getElementById("prompts-tree-panel");if(!e||!t)return;let r=!1,o=0,n=0;e.addEventListener("mousedown",i=>{r=!0,o=i.clientX,n=t.offsetWidth,document.body.style.cursor="col-resize",document.body.style.userSelect="none",i.preventDefault()}),e.addEventListener("mouseover",()=>{e.style.background="var(--accent)"}),e.addEventListener("mouseout",()=>{r||(e.style.background="var(--border)")}),document.addEventListener("mousemove",i=>{r&&(t.style.width=`${Math.max(150,Math.min(500,n+(i.clientX-o)))}px`)}),document.addEventListener("mouseup",()=>{r&&(r=!1,document.body.style.cursor=document.body.style.userSelect="",e.style.background="var(--border)",localStorage.setItem("aicli_prompts_tree_w",String(t.offsetWidth)))})}function G(e){return e?String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"):""}async function Xn(e,t,r){e.className="view active",e.style.cssText="display:flex;flex-direction:column;overflow:hidden;height:100%";const o=r?.code_dir||"",n=parseInt(localStorage.getItem("aicli_code_tree_w")||"200");e.innerHTML=`
    <div style="display:flex;flex-direction:column;overflow:hidden;height:100%">
      <div class="code-view-header">
        <span style="color:var(--muted)">Code folder:</span>
        <span id="code-dir-path"
              style="color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
          ${o||'<span style="color:var(--muted)">Not configured</span>'}
        </span>
        <button class="btn btn-ghost btn-sm" onclick="window._changeCodeDir()">Change…</button>
      </div>

      <div style="flex:1;display:flex;overflow:hidden">
        <!-- Resizable file tree -->
        <div class="code-file-tree" id="code-file-tree"
             style="width:${n}px;flex:none;overflow-y:auto">
          <div style="padding:0.5rem 0.75rem;font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- Drag handle -->
        <div id="code-resize-handle"
             style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
             title="Drag to resize panel"></div>

        <!-- File viewer -->
        <div class="code-viewer" id="code-viewer"
             style="flex:1;overflow:hidden;display:flex;flex-direction:column">
          <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
            Select a file from the tree
          </div>
        </div>
      </div>
    </div>
  `,Jn(),window._changeCodeDir=async()=>{let i=null;if(window.electronAPI?.openDirectory?i=await window.electronAPI.openDirectory():i=prompt("Code folder path:",o||""),!(!i||!t))try{await m.updateProjectConfig(t,{code_dir:i}),p("Code folder updated — restart backend to apply","success"),document.getElementById("code-dir-path").textContent=i}catch(a){p(`Error: ${a.message}`,"error")}},await Qn()}function Jn(){const e=document.getElementById("code-resize-handle"),t=document.getElementById("code-file-tree");if(!e||!t)return;let r=!1,o=0,n=0;e.addEventListener("mousedown",i=>{r=!0,o=i.clientX,n=t.offsetWidth,document.body.style.cursor="col-resize",document.body.style.userSelect="none",i.preventDefault()}),e.addEventListener("mouseover",()=>{e.style.background="var(--accent)"}),e.addEventListener("mouseout",()=>{r||(e.style.background="var(--border)")}),document.addEventListener("mousemove",i=>{r&&(t.style.width=`${Math.max(120,Math.min(600,n+(i.clientX-o)))}px`)}),document.addEventListener("mouseup",()=>{r&&(r=!1,document.body.style.cursor=document.body.style.userSelect="",e.style.background="var(--border)",localStorage.setItem("aicli_code_tree_w",String(t.offsetWidth)))})}async function Qn(){const e=document.getElementById("code-file-tree");if(e)try{const t=await m.getFiles(4);if(!t||t.name==="(no code_dir)"){e.innerHTML=`<div class="empty-state" style="padding:1.25rem">
        <p style="font-size:0.68rem">No code folder configured.</p>
        <p style="font-size:0.62rem;color:var(--muted);margin-top:0.3rem">
          Click <strong>Change…</strong> to set the code directory.</p></div>`;return}const r=t.type==="dir"?t.children||[]:[t];let o=0;e.innerHTML=r.map(n=>so(n,0,()=>o++)).join("")}catch(t){e.innerHTML=`<div style="padding:0.75rem;font-size:0.68rem;color:var(--red)">${De(t.message)}</div>`}}function so(e,t,r){if(!e)return"";const o=t*12;if(e.type==="dir"){const n=`cd${r()}`,i=(e.children||[]).map(a=>so(a,t+1,r)).join("");return`
      <div class="code-dir-row" style="padding-left:${o}px"
           onclick="window._toggleCodeDir('${n}')">
        <span id="${n}-icon" style="display:inline-block;width:10px;font-size:0.58rem;
               color:var(--accent);transition:transform 0.15s">▸</span>
        <span>${De(e.name)}/</span>
      </div>
      <div id="${n}-ch" style="display:none">${i}</div>`}return`
    <div class="code-file-item" data-path="${De(e.path)}"
         style="padding-left:${o+14}px"
         onclick="window._viewCodeFile('${De(e.path)}')">
      <span style="font-size:0.55rem;color:var(--muted)">·</span>
      <span>${De(e.name)}</span>
    </div>`}window._toggleCodeDir=e=>{const t=document.getElementById(`${e}-ch`),r=document.getElementById(`${e}-icon`);if(!t)return;const o=t.style.display!=="none";t.style.display=o?"none":"block",r.style.transform=o?"":"rotate(90deg)"};window._viewCodeFile=async e=>{const t=document.getElementById("code-viewer");if(t){document.querySelectorAll(".code-file-item").forEach(r=>r.classList.toggle("active",r.dataset.path===e)),t.innerHTML='<div style="color:var(--muted);font-size:0.68rem;padding:1.5rem;margin:auto">Loading…</div>';try{const o=(await m.readFile(e)).content||"",n=o.split(`
`).length,i=`cp${Date.now()}`;t.innerHTML=`
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0.75rem;
                  border-bottom:1px solid var(--border);flex-shrink:0;background:var(--surface)">
        <span style="font-size:0.65rem;color:var(--text2);flex:1;overflow:hidden;
                     text-overflow:ellipsis;white-space:nowrap">${De(e)}</span>
        <span style="font-size:0.6rem;color:var(--muted)">${n} lines</span>
        <button class="btn btn-ghost btn-sm" id="${i}">Copy</button>
      </div>
      <div style="flex:1;overflow:auto">
        <pre style="padding:1rem;margin:0;font-family:var(--font);font-size:0.74rem;
                    line-height:1.7;white-space:pre;tab-size:2;color:var(--text)">${De(o)}</pre>
      </div>`,document.getElementById(i)?.addEventListener("click",function(){navigator.clipboard.writeText(o),this.textContent="Copied!",setTimeout(()=>{this.textContent="Copy"},1500)})}catch(r){t.innerHTML=`<div style="padding:1rem;font-size:0.68rem;color:var(--red)">${De(r.message)}</div>`}}};function De(e){return e?String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"):""}async function Zt(e,t,r,o){return new Promise(async n=>{document.getElementById("workflow-picker-overlay")?.remove();let i={},a=[];try{const c=await m.pipeline.templates(o);i=c.templates||{},a=c.workflows||[]}catch(c){console.warn("workflowPicker: failed to load templates",c)}if(!a.length){p("No workflows configured for this project","warning"),n(null);return}const s=document.createElement("div");s.id="workflow-picker-overlay",s.style.cssText="position:fixed;inset:0;z-index:9500;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px)";const d=(r||"").slice(0,200);s.innerHTML=`
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                  width:440px;max-width:95vw;padding:1.5rem;box-shadow:0 8px 32px rgba(0,0,0,0.4)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
          <h3 style="margin:0;font-size:1rem">Run Workflow &mdash; Use Case ${t}</h3>
          <button id="wfp-cancel-btn" style="background:none;border:none;color:var(--muted);font-size:1.2rem;
                  cursor:pointer;padding:0.2rem 0.4rem;line-height:1">&#10005;</button>
        </div>
        ${d?`
        <div style="font-size:0.78rem;color:var(--muted);background:var(--surface2);border-radius:var(--radius);
                    padding:0.6rem 0.75rem;margin-bottom:1rem;line-height:1.5;max-height:80px;overflow:hidden">
          ${d}${r&&r.length>200?"&hellip;":""}
        </div>`:""}
        <div style="margin-bottom:1rem">
          <label style="font-size:0.78rem;font-weight:600;color:var(--text);display:block;margin-bottom:0.5rem">
            Select workflow:
          </label>
          <div id="wfp-workflow-list" style="display:flex;flex-direction:column;gap:0.4rem;max-height:200px;overflow-y:auto">
            ${a.map((c,g)=>`
              <label style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.65rem;
                            border-radius:var(--radius);border:1px solid var(--border);cursor:pointer;
                            font-size:0.8rem;background:var(--surface2)">
                <input type="radio" name="wfp-wf" value="${c.id}" ${g===0?"checked":""}
                       style="accent-color:var(--accent)">
                <span>${c.name}</span>
                <span style="color:var(--muted);margin-left:auto;font-size:0.7rem">${c.node_count} node${c.node_count!==1?"s":""}</span>
              </label>
            `).join("")}
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:0.5rem">
          <button id="wfp-cancel2-btn" class="btn btn-ghost btn-sm">Cancel</button>
          <button id="wfp-run-btn" class="btn btn-primary btn-sm">&#9654; Run</button>
        </div>
      </div>
    `,document.body.appendChild(s);const l=(c=null)=>{s.remove(),n(c)};s.querySelector("#wfp-cancel-btn").onclick=()=>l(null),s.querySelector("#wfp-cancel2-btn").onclick=()=>l(null),s.addEventListener("click",c=>{c.target===s&&l(null)}),s.querySelector("#wfp-run-btn").onclick=async()=>{const c=s.querySelector('input[name="wfp-wf"]:checked');if(!c)return;const g=c.value,f=s.querySelector("#wfp-run-btn");f.disabled=!0,f.textContent="Starting…";try{const u=await m.pipeline.runFromSnapshot(e,t,o,g);p(`Workflow started: ${u.workflow_name||g}`,"success"),l(u.run_id),setTimeout(()=>window._nav?.("workflow"),1500)}catch(u){p(`Failed to start workflow: ${u.message}`,"error"),f.disabled=!1,f.textContent="▶ Run"}}})}const lo="aicli_docs_tree_w";let pe="",rt="";async function Zn(e,t){pe=t||"",rt="",e.className="view active",e.style.cssText="display:flex;flex-direction:column;overflow:hidden;height:100%";const r=parseInt(localStorage.getItem(lo)||"220");e.innerHTML=`
    <div style="display:flex;overflow:hidden;height:100%">
      <!-- Left: file tree -->
      <div id="doc-tree"
           style="width:${r}px;flex:none;overflow-y:auto;border-right:1px solid var(--border);
                  display:flex;flex-direction:column">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:0.5rem 0.75rem;border-bottom:1px solid var(--border)">
          <span style="font-size:0.68rem;color:var(--muted);font-weight:600">documents/</span>
          <button class="btn btn-ghost btn-sm" id="doc-new-btn"
                  style="font-size:0.65rem;padding:0.15rem 0.4rem">+ New</button>
        </div>
        <div id="doc-tree-body" style="flex:1;overflow-y:auto;padding:0.25rem 0">
          <div style="padding:0.75rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>
      </div>

      <!-- Resize handle -->
      <div id="doc-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize"></div>

      <!-- Right: viewer -->
      <div id="doc-viewer"
           style="flex:1;overflow:hidden;display:flex;flex-direction:column">
        <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
          Select a file from the tree
        </div>
      </div>
    </div>
  `,ei(),document.getElementById("doc-new-btn").addEventListener("click",si),await Mt()}function ei(){const e=document.getElementById("doc-resize-handle"),t=document.getElementById("doc-tree");if(!e||!t)return;let r=!1,o=0,n=0;e.addEventListener("mousedown",i=>{r=!0,o=i.clientX,n=t.offsetWidth,document.body.style.cursor="col-resize",document.body.style.userSelect="none",i.preventDefault()}),e.addEventListener("mouseover",()=>{e.style.background="var(--accent)"}),e.addEventListener("mouseout",()=>{r||(e.style.background="var(--border)")}),document.addEventListener("mousemove",i=>{r&&(t.style.width=`${Math.max(160,Math.min(500,n+(i.clientX-o)))}px`)}),document.addEventListener("mouseup",()=>{r&&(r=!1,document.body.style.cursor=document.body.style.userSelect="",e.style.background="var(--border)",localStorage.setItem(lo,String(t.offsetWidth)))})}async function Mt(){const e=document.getElementById("doc-tree-body");if(e)try{const r=(await m.documents.list(pe)).documents||[];if(r.length===0){e.innerHTML='<div style="padding:0.75rem;font-size:0.68rem;color:var(--muted)">No documents yet.</div>';return}const o=ti(r);e.innerHTML=co(o,0),ri(e)}catch(t){e.innerHTML=`<div style="padding:0.75rem;font-size:0.68rem;color:var(--red)">${be(t.message)}</div>`}}function ti(e){const t={name:"",path:"",children:{},isDir:!0};for(const r of e){const o=r.path.split("/");let n=t;for(let i=0;i<o.length;i++){const a=o[i];if(!n.children[a]){const s=i<o.length-1,d=o.slice(0,i+1).join("/");n.children[a]={name:a,path:d,isDir:s,children:{},size:r.size}}n=n.children[a]}}return t}function co(e,t){const r=t*14;let o="";const n=Object.values(e.children).sort((i,a)=>i.isDir!==a.isDir?i.isDir?-1:1:i.name.localeCompare(a.name));for(const i of n)if(i.isDir){const a=`ddir-${i.path.replace(/[^a-z0-9]/gi,"_")}`;o+=`
        <div class="doc-dir-row" data-dir-id="${a}"
             style="padding:0.3rem 0.5rem 0.3rem ${r+8}px;cursor:pointer;
                    font-size:0.7rem;color:var(--muted);display:flex;align-items:center;gap:0.35rem;
                    user-select:none"
             onclick="window._docToggleDir('${a}')">
          <span id="${a}-arrow" style="font-size:0.6rem">▶</span>
          <span>${be(i.name)}/</span>
        </div>
        <div id="${a}-children" style="display:none">
          ${co(i,t+1)}
        </div>`}else{const a=i.path===rt;o+=`
        <div class="doc-file-row" data-path="${be(i.path)}"
             style="padding:0.2rem 0.4rem 0.2rem ${r+8}px;cursor:pointer;
                    font-size:0.7rem;border-radius:3px;display:flex;align-items:center;gap:0.25rem;
                    ${a?"background:var(--accent-dim,rgba(99,102,241,.15));color:var(--accent)":"color:var(--text)"}">
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${be(i.name)}</span>
          <span class="doc-tree-del" data-del-path="${be(i.path)}"
                style="opacity:0;transition:opacity 0.1s;flex-shrink:0;font-size:0.75rem;
                       line-height:1;padding:0 0.2rem;border-radius:2px;color:var(--red)"
                title="Delete ${be(i.name)}">×</span>
        </div>`}return o}function ri(e){e.querySelectorAll(".doc-file-row").forEach(t=>{t.addEventListener("click",r=>{r.target.classList.contains("doc-tree-del")||mo(t.dataset.path)}),t.addEventListener("mouseenter",()=>{const r=t.querySelector(".doc-tree-del");r&&(r.style.opacity="1")}),t.addEventListener("mouseleave",()=>{const r=t.querySelector(".doc-tree-del");r&&(r.style.opacity="0")})}),e.querySelectorAll(".doc-tree-del").forEach(t=>{t.addEventListener("click",async r=>{r.stopPropagation();const o=t.dataset.delPath;if(!(!o||!confirm(`Delete "${o}"?`)))try{if(await m.documents.delete(o,pe),p("Deleted","success"),rt===o){rt="";const n=document.getElementById("doc-viewer");n&&(n.innerHTML='<div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">Select a file from the tree</div>')}await Mt()}catch(n){p(`Delete failed: ${n.message}`,"error")}})})}window._docToggleDir=e=>{const t=document.getElementById(`${e}-children`),r=document.getElementById(`${e}-arrow`);if(!t)return;const o=t.style.display==="none";t.style.display=o?"":"none",r&&(r.textContent=o?"▼":"▶")};async function mo(e){rt=e,document.querySelectorAll(".doc-file-row").forEach(r=>{const o=r.dataset.path===e;r.style.background=o?"var(--accent-dim,rgba(99,102,241,.15))":"",r.style.color=o?"var(--accent)":"var(--text)"});const t=document.getElementById("doc-viewer");if(t){t.innerHTML='<div style="padding:1rem;font-size:0.7rem;color:var(--muted)">Loading…</div>';try{const r=await m.documents.read(e,pe);pr(e,r.content||"")}catch(r){t.innerHTML=`<div style="padding:1rem;font-size:0.7rem;color:var(--red)">${be(r.message)}</div>`}}}function pr(e,t){const r=document.getElementById("doc-viewer");if(!r)return;const o=e.endsWith(".md")||e.endsWith(".markdown"),n=e.match(/^features\/([^/]+)\/(feature_ai|feature_final)\.md$/);if(r.innerHTML=`
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.68rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
        ${be(e)}
      </span>
      <div style="display:flex;gap:0.4rem;flex-shrink:0">
        ${n?`<button class="btn btn-ghost btn-sm" id="doc-workflow-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem;color:var(--accent)">▶ Workflow</button>`:""}
        <button class="btn btn-ghost btn-sm" id="doc-edit-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Edit</button>
        <button class="btn btn-ghost btn-sm" id="doc-delete-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem;color:var(--red)">Delete</button>
      </div>
    </div>
    ${o?`<div id="doc-content-pre" class="md-body"
              style="flex:1;overflow:auto;padding:1.25rem 1.5rem;line-height:1.7;font-size:0.82rem">${xe(t)}</div>`:`<pre id="doc-content-pre"
              style="flex:1;overflow:auto;margin:0;padding:1rem;font-size:0.72rem;
                     line-height:1.55;white-space:pre-wrap;word-break:break-word">${be(t)}</pre>`}
  `,document.getElementById("doc-edit-btn").addEventListener("click",()=>ni(e,t)),document.getElementById("doc-delete-btn").addEventListener("click",()=>ai(e)),n){const i=n[1];document.getElementById("doc-workflow-btn").addEventListener("click",async()=>{try{const a=await m.tags.list(pe),s=[],d=f=>f.forEach(u=>{s.push(u),u.children&&d(u.children)});d(a);const l=f=>f.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,""),c=s.find(f=>l(f.name)===i);if(!c){p("Feature tag not found","warning");return}const g=await m.tags.getSnapshot(c.id,pe,"user").catch(()=>m.tags.getSnapshot(c.id,pe,"ai").catch(()=>null));if(!g?.use_cases?.length){p("No use cases found in snapshot","warning");return}if(g.use_cases.length===1){const f=g.use_cases[0];await Zt(c.id,f.use_case_num,f.use_case_summary,pe)}else{const f=await oi(g.use_cases);f&&await Zt(c.id,f.use_case_num,f.use_case_summary,pe)}}catch(a){p(`Workflow error: ${a.message}`,"error")}})}}async function oi(e){return new Promise(t=>{const r=document.createElement("div");r.style.cssText="position:fixed;inset:0;z-index:9400;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.55)",r.innerHTML=`
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                  padding:1.2rem;width:340px;max-width:95vw">
        <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.75rem">Select Use Case</div>
        ${e.map(o=>`
          <div data-uc="${o.use_case_num}" style="padding:0.5rem 0.65rem;border-radius:var(--radius);
               border:1px solid var(--border);margin-bottom:0.35rem;cursor:pointer;font-size:0.78rem;
               background:var(--surface2)" onmouseenter="this.style.borderColor='var(--accent)'"
               onmouseleave="this.style.borderColor='var(--border)'">
            UC${o.use_case_num}: ${o.use_case_type||"feature"} — ${(o.use_case_summary||"").slice(0,60)}
          </div>
        `).join("")}
        <button style="margin-top:0.5rem;width:100%;background:none;border:1px solid var(--border);
                border-radius:var(--radius);padding:0.35rem;cursor:pointer;font-size:0.75rem;color:var(--muted)"
                id="uc-cancel-btn">Cancel</button>
      </div>
    `,document.body.appendChild(r),r.querySelectorAll("[data-uc]").forEach(o=>{o.addEventListener("click",()=>{const n=parseInt(o.dataset.uc,10),i=e.find(a=>a.use_case_num===n);r.remove(),t(i||null)})}),r.querySelector("#uc-cancel-btn").onclick=()=>{r.remove(),t(null)},r.addEventListener("click",o=>{o.target===r&&(r.remove(),t(null))})})}function ni(e,t){const r=document.getElementById("doc-viewer");r&&(r.innerHTML=`
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.68rem;color:var(--muted)">${be(e)}</span>
      <div style="display:flex;gap:0.4rem">
        <button class="btn btn-sm btn-primary" id="doc-save-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Save</button>
        <button class="btn btn-ghost btn-sm" id="doc-cancel-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Cancel</button>
      </div>
    </div>
    <textarea id="doc-edit-area"
              style="flex:1;resize:none;border:none;outline:none;padding:1rem;
                     font-size:0.72rem;line-height:1.55;background:var(--bg);color:var(--text);
                     font-family:var(--font-mono,monospace)">${be(t)}</textarea>
  `,document.getElementById("doc-save-btn").addEventListener("click",async()=>{const o=document.getElementById("doc-edit-area")?.value??"";await ii(e,o)}),document.getElementById("doc-cancel-btn").addEventListener("click",()=>pr(e,t)))}async function ii(e,t){try{await m.documents.save(e,t,pe),p("Saved","success"),pr(e,t)}catch(r){p(`Save failed: ${r.message}`,"error")}}async function ai(e){if(confirm(`Delete "${e}"?`))try{await m.documents.delete(e,pe),p("Deleted","success"),rt="",document.getElementById("doc-viewer").innerHTML=`
      <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
        Select a file from the tree
      </div>`,await Mt()}catch(t){p(`Delete failed: ${t.message}`,"error")}}async function si(){const e=prompt("New document path (e.g. notes/design.md):");if(!e?.trim())return;const t=e.trim().replace(/^\/+/,"");try{await m.documents.save(t,"",pe),p("Created","success"),await Mt(),await mo(t)}catch(r){p(`Could not create: ${r.message}`,"error")}}function be(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}let ie="",L=null,He=null,re=null,ge=null,Ye=[],et=null,J=null,Ee=[],we=null,Bt=[],dt={},Qe="",zt=!1,po=null;function di(e){e.className="view active gw-view";const t=ie;if(ie=x.currentProject?.name||"",t!==ie&&(we=null),re&&(clearInterval(re),re=null),L=null,He=null,!ie){e.innerHTML=`
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                  height:100%;gap:1rem;color:var(--muted);text-align:center;padding:2rem">
        <div style="font-size:2.5rem">◈</div>
        <div style="font-size:1rem;font-weight:600;color:var(--fg)">No project open</div>
        <div style="font-size:0.82rem">Open a project first, then come back to Pipelines to create and run workflows.</div>
      </div>`;return}e.innerHTML=`
    <style>
      .gw-view { display:flex; flex-direction:column; height:100%; overflow:hidden; }

      /* Layout */
      .gw-body2 { display:flex; flex:1; overflow:hidden; }
      .gw-sidebar2 { width:220px; min-width:180px; border-right:1px solid var(--border);
        overflow-y:auto; display:flex; flex-direction:column; gap:0; }
      .gw-main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
      .gw-detail { width:320px; border-left:1px solid var(--border); overflow-y:auto;
        display:none; flex-direction:column; }
      .gw-detail.open { display:flex; }

      /* Sidebar */
      .gw-sb-section { border-bottom:1px solid var(--border); padding:0.5rem 0; }
      .gw-sb-label { font-size:0.65rem; font-weight:600; text-transform:uppercase;
        letter-spacing:0.05em; color:var(--muted); padding:0.25rem 0.75rem 0.1rem; }
      .gw-wf-item { padding:0.35rem 0.75rem; cursor:pointer; font-size:0.8rem;
        border-left:3px solid transparent; transition:background 0.1s; }
      .gw-wf-item:hover { background:var(--hover); }
      .gw-wf-item.active { border-left-color:var(--accent); background:var(--hover); font-weight:500; }
      .gw-role-card { display:flex; align-items:center; gap:0.4rem; padding:0.3rem 0.75rem;
        cursor:pointer; font-size:0.78rem; border-radius:0; transition:background 0.1s; }
      .gw-role-card:hover { background:var(--hover); }
      .gw-role-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
      .gw-role-badge { font-size:0.6rem; background:var(--border); border-radius:3px;
        padding:0.05rem 0.25rem; color:var(--muted); }
      .gw-io-legend { display:flex; flex-wrap:wrap; gap:0.25rem; padding:0.35rem 0.5rem; }
      .gw-io-pill { font-size:0.62rem; border-radius:8px; padding:0.1rem 0.4rem;
        font-weight:500; cursor:default; }

      /* Toolbar */
      .gw-toolbar2 { display:flex; align-items:center; gap:0.5rem; padding:0.5rem 0.75rem;
        border-bottom:1px solid var(--border); flex-shrink:0; }
      .gw-wf-name { font-size:0.85rem; font-weight:600; padding:0.25rem 0.5rem;
        border:1px solid transparent; border-radius:4px; background:transparent;
        color:var(--fg); min-width:120px; max-width:240px; }
      .gw-wf-name:focus { border-color:var(--accent); outline:none; background:var(--bg2); }

      /* Canvas area */
      .gw-canvas-area { flex:1; overflow:hidden; display:flex; flex-direction:column; }
      .gw-pipeline-scroll { flex-shrink:0; overflow-x:auto; overflow-y:hidden;
        padding:1.5rem 2rem; max-height:260px; min-height:120px; }
      .gw-pipeline { display:flex; align-items:flex-start; gap:0; min-height:160px; }

      /* Node cards */
      .gw-node-card { width:210px; flex-shrink:0; border:2px solid var(--border);
        border-radius:8px; background:var(--bg1); cursor:pointer; transition:all 0.15s; }
      .gw-node-card:hover { border-color:var(--accent); box-shadow:0 2px 12px rgba(0,0,0,0.18); }
      .gw-node-card.selected { border-color:var(--accent); box-shadow:0 0 0 3px rgba(100,108,255,0.25); }
      .gw-node-header { display:flex; align-items:center; gap:0.35rem; padding:0.45rem 0.6rem;
        border-bottom:1px solid var(--border); }
      .gw-node-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
      .gw-node-name { flex:1; font-size:0.78rem; font-weight:600; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis; }
      .gw-node-badge { font-size:0.57rem; padding:0.1rem 0.28rem; border-radius:3px;
        background:var(--border); color:var(--muted); flex-shrink:0; }
      .gw-node-del { background:rgba(232,93,117,0.12); border:1px solid rgba(232,93,117,0.3);
        border-radius:4px; color:#e85d75; cursor:pointer; font-size:0.68rem; font-weight:700;
        padding:1px 5px; line-height:1.4; flex-shrink:0; opacity:0; transition:opacity 0.15s; }
      .gw-node-card:hover .gw-node-del { opacity:1; }
      .gw-node-del:hover { background:rgba(232,93,117,0.25) !important; }
      .gw-node-body { padding:0.45rem 0.6rem; display:flex; flex-direction:column; gap:0.3rem; }
      .gw-node-row { display:flex; align-items:baseline; gap:0.3rem; }
      .gw-node-row-lbl { font-size:0.58rem; text-transform:uppercase; letter-spacing:0.04em;
        color:var(--muted); flex-shrink:0; width:28px; }
      .gw-node-row-val { font-size:0.7rem; color:var(--fg); overflow:hidden;
        text-overflow:ellipsis; white-space:nowrap; }
      .gw-node-row-val.muted { color:var(--muted); font-style:italic; }
      .gw-node-cfg-badges { display:flex; flex-wrap:wrap; gap:0.2rem; padding-top:0.1rem; }
      .gw-cfg-badge { font-size:0.58rem; padding:0.1rem 0.35rem; border-radius:10px;
        background:var(--border); color:var(--muted); }
      .gw-cfg-stateless { background:rgba(45,212,191,0.18); color:#2dd4bf; }
      .gw-cfg-warn      { background:rgba(245,166,35,0.18);  color:#f5a623; }
      .gw-cfg-approval  { background:rgba(155,126,248,0.18); color:#9b7ef8; }
      .gw-node-footer { padding:0.3rem 0.6rem 0.4rem; border-top:1px solid var(--border);
        font-size:0.63rem; color:var(--muted); display:flex; align-items:center; gap:0.4rem; }
      .gw-node-status { width:7px; height:7px; border-radius:50%; flex-shrink:0; display:none; }
      .gw-node-status.running  { background:#f5a623; animation:pulse 1s infinite; display:inline-block; }
      .gw-node-status.done     { background:#3ecf8e; display:inline-block; }
      .gw-node-status.error    { background:#e85d75; display:inline-block; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

      /* Inline modal */
      .gw-modal-overlay { position:fixed;inset:0;z-index:9000;
        background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);
        display:flex;align-items:center;justify-content:center; }
      .gw-modal-box { background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;
        padding:1.5rem;min-width:340px;max-width:500px;width:92%;
        box-shadow:0 24px 64px rgba(0,0,0,0.7); }
      .gw-modal-title { font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#fff; }
      .gw-modal-desc { font-size:0.8rem;color:rgba(255,255,255,0.5);margin:-0.5rem 0 0.9rem; }
      .gw-modal-field { margin-bottom:0.75rem; }
      .gw-modal-field label { display:block;font-size:0.7rem;color:rgba(255,255,255,0.5);
        margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.05em;font-weight:600; }
      .gw-modal-field input, .gw-modal-field textarea {
        width:100%;box-sizing:border-box;padding:0.5rem 0.6rem;
        border:1px solid rgba(255,255,255,0.18);border-radius:6px;
        background:rgba(255,255,255,0.07);color:#fff;font-size:0.84rem; }
      .gw-modal-field input:focus, .gw-modal-field textarea:focus {
        outline:none;border-color:var(--accent);background:rgba(255,255,255,0.1); }
      .gw-modal-field textarea { resize:vertical; font-family:inherit; }
      .gw-modal-footer { display:flex;justify-content:flex-end;gap:0.5rem;margin-top:1rem;
        padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08); }

      /* Connectors */
      .gw-connector { display:flex; align-items:center; padding:0 0.2rem; flex-shrink:0;
        position:relative; }
      .gw-conn-line { width:32px; height:2px; background:var(--border); position:relative; }
      .gw-conn-line::after { content:'▶'; position:absolute; right:-6px; top:-7px;
        font-size:0.75rem; color:var(--border); }
      .gw-conn-label { position:absolute; top:-14px; left:50%; transform:translateX(-50%);
        font-size:0.6rem; color:var(--muted); white-space:nowrap; background:var(--bg1);
        padding:0 2px; }
      .gw-add-btn { width:36px; height:36px; border-radius:50%; border:2px dashed var(--border);
        background:none; color:var(--muted); cursor:pointer; font-size:1.1rem; display:flex;
        align-items:center; justify-content:center; margin:auto 0.5rem; transition:all 0.15s; }
      .gw-add-btn:hover { border-color:var(--accent); color:var(--accent); }

      /* Run log */
      .gw-log { border-top:1px solid var(--border); flex-shrink:0; max-height:220px;
        display:none; flex-direction:column; }
      .gw-log.open { display:flex; }
      .gw-log-hdr { display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0.75rem;
        cursor:pointer; background:var(--bg2); font-size:0.78rem; font-weight:600; }
      .gw-log-body { overflow-y:auto; flex:1; font-size:0.75rem; padding:0.5rem 0.75rem; }
      .gw-log-entry { padding:0.2rem 0; border-bottom:1px solid var(--border); }
      .gw-log-entry:last-child { border:none; }

      /* Approval panel */
      .gw-approval { background:rgba(245,166,35,0.08); border:1px solid rgba(245,166,35,0.4);
        border-radius:6px; padding:0.75rem; margin-bottom:0.5rem; }
      .gw-approval h4 { margin:0 0 0.4rem; font-size:0.8rem; }
      .gw-approval pre { max-height:100px; overflow:auto; font-size:0.7rem;
        background:var(--bg2); border-radius:4px; padding:0.4rem; margin:0.4rem 0; }
      .gw-approval-btns { display:flex; gap:0.5rem; margin-top:0.5rem; }

      /* Detail panel */
      .gw-detail-hdr { display:flex; align-items:center; justify-content:space-between;
        padding:0.6rem 0.75rem; border-bottom:1px solid var(--border); font-weight:600;
        font-size:0.82rem; }
      .gw-detail-body { padding:0.75rem; overflow-y:auto; flex:1; }
      .gw-field { margin-bottom:0.75rem; }
      .gw-field label { display:block; font-size:0.72rem; font-weight:600; margin-bottom:0.25rem;
        color:var(--muted); text-transform:uppercase; letter-spacing:0.03em; }
      .gw-field input, .gw-field select, .gw-field textarea {
        width:100%; box-sizing:border-box; padding:0.3rem 0.5rem; border:1px solid var(--border);
        border-radius:4px; background:var(--bg1); color:var(--fg); font-size:0.8rem; }
      .gw-field textarea { resize:vertical; min-height:60px; }
      .gw-io-editor { display:flex; flex-direction:column; gap:0.3rem; }
      .gw-io-row { display:flex; align-items:center; gap:0.3rem; }
      .gw-io-row input { flex:1; }
      .gw-io-row select { width:90px; flex-shrink:0; }
      .gw-io-row button { padding:0.2rem 0.4rem; border:none; background:none;
        color:var(--muted); cursor:pointer; font-size:0.75rem; }
      .gw-add-io-btn { font-size:0.72rem; color:var(--accent); background:none; border:none;
        cursor:pointer; padding:0.15rem 0; }
      .gw-toggle-row { display:flex; align-items:center; justify-content:space-between; }
      .gw-detail-footer { padding:0.6rem 0.75rem; border-top:1px solid var(--border); }

      /* Empty state */
      .gw-empty { flex:1; display:flex; align-items:center; justify-content:center;
        flex-direction:column; gap:0.5rem; color:var(--muted); font-size:0.85rem; }

      /* Run progress panel (directly below nodes, fills remaining canvas space) */
      .gw-run-panel { border-top:1px solid var(--border); display:none;
        flex-direction:column; overflow:hidden; flex:1; min-height:0; }
      .gw-run-panel.open { display:flex; }
      .gw-rp-hdr { padding:0.45rem 0.75rem; border-bottom:1px solid var(--border); flex-shrink:0;
        display:flex; align-items:center; gap:0.75rem; }
      .gw-rp-wf-name { font-size:0.78rem; font-weight:700; white-space:nowrap; overflow:hidden;
        text-overflow:ellipsis; max-width:180px; }
      .gw-rp-meta { display:flex; align-items:center; gap:0.5rem;
        font-size:0.72rem; color:var(--muted); }
      .gw-rp-status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
      .gw-rp-status-dot.running { background:#f5a623; animation:pulse 1s infinite; }
      .gw-rp-status-dot.done    { background:#3ecf8e; }
      .gw-rp-status-dot.error   { background:#e85d75; }
      .gw-rp-status-dot.stopped, .gw-rp-status-dot.cancelled { background:var(--muted); }
      .gw-rp-actions { display:flex; gap:0.4rem; align-items:center; }
      /* Timeline: horizontal cards in bottom panel */
      .gw-rp-timeline { padding:0.5rem 0.75rem; display:flex; flex-direction:row;
        gap:0.5rem; align-items:flex-start; flex-wrap:nowrap; overflow-x:auto; }
      .gw-rp-step { min-width:160px; max-width:220px; flex-shrink:0; border-radius:6px;
        border:2px solid var(--border); padding:0.45rem 0.55rem; transition:background 0.1s; }
      .gw-rp-step.pending  { border-color:var(--border); opacity:0.5; }
      .gw-rp-step.running  { border-color:#f5a623; background:rgba(245,166,35,0.06); }
      .gw-rp-step.done     { border-color:#3ecf8e; }
      .gw-rp-step.error    { border-color:#e85d75; background:rgba(232,93,117,0.06); }
      .gw-rp-step.skipped  { border-color:var(--muted); opacity:0.5; }
      .gw-rp-step-hdr { display:flex; align-items:center; gap:0.35rem; }
      .gw-rp-step-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0;
        background:var(--border); }
      .gw-rp-step.pending .gw-rp-step-dot  { background:var(--border); }
      .gw-rp-step.running .gw-rp-step-dot  { background:#f5a623; animation:pulse 1s infinite; }
      .gw-rp-step.done    .gw-rp-step-dot  { background:#3ecf8e; }
      .gw-rp-step.error   .gw-rp-step-dot  { background:#e85d75; }
      .gw-rp-step-name { font-size:0.75rem; font-weight:600; flex:1;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .gw-rp-step-meta { font-size:0.63rem; color:var(--muted); margin-top:0.2rem; }
      .gw-rp-step-out { font-size:0.65rem; color:var(--muted); margin-top:0.3rem;
        line-height:1.4; max-height:52px; overflow:hidden;
        background:var(--bg2); border-radius:4px; padding:0.2rem 0.35rem;
        white-space:pre-wrap; word-break:break-word; }
      .gw-rp-deliverables { flex-shrink:0; overflow-y:auto; padding:0.5rem 0.6rem; }
      .gw-rp-del-title { font-size:0.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.05em; color:var(--muted); margin-bottom:0.4rem; }
      .gw-rp-del-file { font-size:0.72rem; padding:0.2rem 0; display:flex;
        align-items:center; gap:0.35rem; color:var(--fg); cursor:default; }
      .gw-rp-del-file span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .gw-rp-history { border-top:1px solid var(--border); }
      .gw-rp-hist-item { display:flex; align-items:center; gap:0.4rem;
        padding:0.3rem 0.75rem; font-size:0.75rem; cursor:pointer; }
      .gw-rp-hist-item:hover { background:var(--hover); }

      /* Recent runs sidebar section */
      .gw-run-row { display:flex; align-items:center; gap:0.4rem; padding:0.3rem 0.75rem;
        cursor:pointer; font-size:0.75rem; }
      .gw-run-row:hover { background:var(--hover); }
      .gw-run-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
    </style>

    <div class="gw-toolbar2">
      <button class="btn btn-primary btn-sm" id="gw-new-btn" onclick="window._gwNew()">+ New Pipeline</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate(event)" title="Create from template">From Template ▾</button>
      <button class="btn btn-ghost btn-sm" id="gw-react-btn" onclick="window._gwOpenReActRunner()" title="Run a YAML-defined ReAct pipeline (PM → Architect → Developer → Reviewer)">▶ ReAct Run</button>
      <div id="gw-wf-name-wrap" style="display:none">
        <input class="gw-wf-name" id="gw-wf-name" placeholder="Flow name" onblur="window._gwSaveName(this.value)" />
      </div>
      <div style="flex:1"></div>
      <div id="gw-run-controls" style="display:none;gap:0.4rem;align-items:center" class="flex">
        <button class="btn btn-ghost btn-sm" onclick="window._gwExportYAML()">Export YAML</button>
        <label class="btn btn-ghost btn-sm" style="cursor:pointer">
          Import YAML <input type="file" accept=".yaml,.yml" style="display:none" onchange="window._gwImportYAML(this)">
        </label>
        <button class="btn btn-primary btn-sm" onclick="window._gwStartRun()">▶ Run</button>
      </div>
    </div>

    <div class="gw-body2">
      <div class="gw-sidebar2">
        <div class="gw-sb-section">
          <div class="gw-sb-label">Saved Pipelines</div>
          <div id="gw-wf-list"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
        <div class="gw-sb-section">
          <div class="gw-sb-label">Role Library</div>
          <div id="gw-role-library"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
        <div class="gw-sb-section">
          <div class="gw-sb-label">Recent Runs</div>
          <div id="gw-recent-runs"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
      </div>

      <div class="gw-main">
        <div class="gw-canvas-area">
          <div class="gw-pipeline-scroll" id="gw-pipeline-scroll">
            <div class="gw-empty" id="gw-empty-state">
              <div style="font-size:2rem">◈</div>
              <div style="font-weight:600">Select a pipeline or create a new one</div>
              <div style="font-size:0.78rem">Use <b>From Template</b> to instantly create a PM→Dev→Reviewer pipeline</div>
              <div style="font-size:0.78rem">or click a role in the sidebar to add it to the pipeline</div>
              <div style="margin-top:0.5rem;display:flex;gap:0.5rem">
                <button class="btn btn-primary btn-sm" onclick="window._gwNew()">+ New Pipeline</button>
                <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate(event)">From Template ▾</button>
              </div>
            </div>
            <div class="gw-pipeline" id="gw-pipeline" style="display:none"></div>
          </div>
          <!-- Run progress panel (directly below nodes, fills remaining canvas space) -->
          <div class="gw-run-panel" id="gw-run-panel">
            <div class="gw-rp-hdr">
              <div style="display:flex;align-items:center;gap:0.75rem;flex:1;min-width:0">
                <div class="gw-rp-wf-name" id="gw-rp-wf-name">Pipeline</div>
                <div class="gw-rp-meta" style="flex-wrap:nowrap">
                  <div class="gw-rp-status-dot running" id="gw-rp-dot"></div>
                  <span id="gw-rp-status">running</span>
                  <span id="gw-rp-timer" style="font-variant-numeric:tabular-nums">0s</span>
                  <span id="gw-rp-nodes">0/0</span>
                  <span id="gw-rp-cost">$0.0000</span>
                </div>
              </div>
              <div class="gw-rp-actions" style="margin-top:0;flex-shrink:0">
                <button class="btn btn-ghost btn-sm" id="gw-rp-stop"
                  style="color:var(--red);font-size:0.72rem" onclick="window._gwCancelRun()">■ Stop</button>
                <button class="btn btn-ghost btn-sm" style="font-size:0.72rem"
                  onclick="window._gwCloseRunPanel()">✕ Close</button>
              </div>
            </div>
            <!-- Approval panel shown here when waiting -->
            <div id="gw-approval-wrap" style="display:none;padding:0.5rem 0.75rem 0;flex-shrink:0"></div>
            <div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;">
              <!-- Status cards row -->
              <div class="gw-rp-timeline" id="gw-rp-timeline"></div>
              <!-- Full-width text log -->
              <div id="gw-run-log" style="flex:1;overflow-y:auto;padding:0.5rem 0.75rem;
                   font-family:var(--font-mono,monospace);font-size:0.72rem;line-height:1.6;
                   border-top:1px solid var(--border);min-height:80px"></div>
              <!-- Deliverables (shown on completion) -->
              <div class="gw-rp-deliverables" id="gw-rp-deliverables" style="display:none;border-top:1px solid var(--border)"></div>
            </div>
            <!-- Legacy log body (hidden, kept for backward compat) -->
            <div id="gw-log" style="display:none">
              <div class="gw-log-body" id="gw-log-body"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="gw-detail" id="gw-detail">
        <div class="gw-detail-hdr">
          <span id="gw-detail-title">Node Config</span>
          <button class="btn btn-ghost btn-sm" onclick="window._gwCloseDetail()">✕</button>
        </div>
        <div class="gw-detail-body" id="gw-detail-body"></div>
        <div class="gw-detail-footer">
          <button class="btn btn-primary btn-sm" style="width:100%" onclick="window._gwSaveNode()">Save Changes</button>
        </div>
      </div>
    </div>
  `,window._gwNew=()=>ui(),window._gwSaveName=r=>yi(r),window._gwAddPreset=r=>_i(),window._gwFromTemplate=r=>fi(r),window._gwStartRun=()=>ki(),window._gwCancelRun=()=>Ti(),window._gwToggleLog=Ei,window._gwCloseDetail=fo,window._gwSaveNode=wi,window._gwExportYAML=Pi,window._gwImportYAML=Li,window._gwCloseRunPanel=Ci,window._gwOpenRun=r=>Lr(r),window._gwOpenReActRunner=()=>ji(),nt().then(()=>{if(window._pendingRunOpen){const r=window._pendingRunOpen;window._pendingRunOpen=null,Lr(r)}})}function B(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function li(e,t){const r=document.createElement("a");r.href="data:text/plain;charset=utf-8,"+encodeURIComponent(t),r.download=e,r.click()}function ur({title:e,fields:t=[],confirmLabel:r="OK",danger:o=!1}){return new Promise(n=>{const i=document.createElement("div");i.className="gw-modal-overlay";const a=document.createElement("div");a.className="gw-modal-box";let s=`<div class="gw-modal-title">${B(e)}</div>`;t.forEach(c=>{s+='<div class="gw-modal-field">',c.label&&(s+=`<label>${B(c.label)}</label>`),c.rows?s+=`<textarea id="_gm-${c.id}" rows="${c.rows}" placeholder="${B(c.placeholder||"")}">${B(c.value||"")}</textarea>`:s+=`<input id="_gm-${c.id}" type="${c.type||"text"}" value="${B(c.value||"")}" placeholder="${B(c.placeholder||"")}" />`,s+="</div>"}),s+=`<div class="gw-modal-footer">
      <button id="_gm-cancel" class="btn btn-ghost btn-sm">Cancel</button>
      <button id="_gm-ok" class="btn ${o?"btn-danger":"btn-primary"} btn-sm">${B(r)}</button>
    </div>`,a.innerHTML=s,i.appendChild(a),document.body.appendChild(i);const d=a.querySelector("input,textarea");d&&setTimeout(()=>{d.focus(),d.select?.()},0);const l=c=>{i.remove(),n(c)};a.querySelector("#_gm-cancel").onclick=()=>l(null),a.querySelector("#_gm-ok").onclick=()=>{const c={};t.forEach(g=>{c[g.id]=a.querySelector(`#_gm-${g.id}`)?.value??""}),l(c)},a.addEventListener("keydown",c=>{c.key==="Enter"&&c.target.tagName!=="TEXTAREA"&&(c.preventDefault(),a.querySelector("#_gm-ok").click()),c.key==="Escape"&&l(null)}),i.onclick=c=>{c.target===i&&l(null)}})}async function nt(){const e=document.getElementById("gw-wf-list");if(e){if(we&&we.project===ie){uo(we.workflows,we.roles,we.recentRuns),jt();return}e.innerHTML='<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div>',await jt()}}async function jt(){try{const[e,t,r]=await Promise.allSettled([m.graphWorkflows.list(ie||""),m.agentRoles.list(ie||"_global"),m.graphWorkflows.recentRuns(ie||"",15)]),o=e.status==="fulfilled"?e.value.workflows||[]:null,n=t.status==="fulfilled"?t.value.roles||[]:null,i=r.status==="fulfilled"?r.value.runs||[]:[];o!==null&&(we={project:ie,workflows:o,roles:n||Ye,recentRuns:i},uo(o,n,i))}catch{}}function uo(e,t,r){const o=document.getElementById("gw-wf-list");if(o){if(t&&(Ye=t,ci()),mi(r),!e||!e.length){o.innerHTML='<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No flows yet — use "From Template" to start</div>';return}o.innerHTML=e.map(n=>{const i=n.name==="_work_item_pipeline",a=i?"⚙ Work Item Pipeline":B(n.name),s=n.description?`<div style="font-size:0.65rem;color:var(--muted)">${B((i?"Auto-pipeline from Planner":n.description).slice(0,40))}</div>`:"";return`
      <div class="gw-wf-item ${L?.id===n.id?"active":""}"
           onclick="window._gwOpenWf('${n.id}')">
        <div style="font-size:0.8rem">${a}</div>
        ${s}
      </div>
    `}).join(""),window._gwOpenWf=pi}}function ci(){const e=document.getElementById("gw-role-library");if(!e)return;const t=Ye.filter(o=>o.role_type!=="internal");if(!t.length){e.innerHTML='<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No roles — create them in the Roles tab</div>';return}const r={agent:"#3ecf8e",system_designer:"#9b7ef8",reviewer:"#2dd4bf"};e.innerHTML=t.map(o=>{const n=r[o.role_type||"agent"]||"#6b7490",i=o.role_type==="system_designer"?"SYS":o.role_type==="reviewer"?"REV":"AGT";return`
      <div class="gw-role-card" onclick="window._gwAddFromRole(${o.id})" title="${B(o.description||o.name)}">
        <div class="gw-role-dot" style="background:${n}"></div>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${B(o.name)}</span>
        <span class="gw-role-badge">${i}</span>
      </div>
    `}).join(""),window._gwAddFromRole=vo}function mi(e){const t=document.getElementById("gw-recent-runs");if(!t)return;if(!e.length){t.innerHTML='<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No runs yet</div>';return}const r={done:"#3ecf8e",error:"#e85d75",running:"#f5a623",stopped:"#888",cancelled:"#888",waiting_approval:"#9b7ef8"};t.innerHTML=e.slice(0,12).map(o=>{const n=r[o.status]||"var(--muted)",i=o.started_at?xt(o.started_at,o.finished_at):"",a=o.total_cost_usd>0?` · $${Number(o.total_cost_usd).toFixed(3)}`:"",d=(o.workflow_name==="_work_item_pipeline"?"Work Item Pipeline":o.workflow_name||"Pipeline").slice(0,22),l=(o.user_input||"").slice(0,30);return`
      <div class="gw-run-row" onclick="window._gwOpenRun('${o.id}')" title="${B(o.user_input||"")}">
        <div class="gw-run-dot" style="background:${n}"></div>
        <div style="flex:1;min-width:0">
          <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500">${B(d)}</div>
          ${l?`<div style="font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${B(l)}</div>`:""}
        </div>
        <div style="font-size:0.65rem;color:var(--muted);white-space:nowrap;flex-shrink:0">${i}${a}</div>
      </div>`}).join("")}function xt(e,t){if(!e)return"";const r=new Date(e).getTime(),o=t?new Date(t).getTime():Date.now();return gr(o-r)}function gr(e){e<0&&(e=0);const t=Math.floor(e/1e3);if(t<60)return`${t}s`;const r=Math.floor(t/60);return r<60?`${r}m ${t%60}s`:`${Math.floor(r/60)}h ${r%60}m`}async function pi(e){try{const t=await m.graphWorkflows.get(e);L=t,_t(t),nt()}catch(t){p(`Failed to load flow: ${t.message}`,"error")}}function _t(e){const t=document.getElementById("gw-wf-name"),r=document.getElementById("gw-wf-name-wrap"),o=document.getElementById("gw-run-controls"),n=e.name==="_work_item_pipeline"?"Work Item Pipeline":e.name;t&&(t.value=n),r&&(r.style.display=""),o&&(o.style.display="flex"),$t(e)}async function ui(){if(!ie){p("Open a project first","error");return}const e=await ur({title:"New Pipeline",fields:[{id:"name",label:"Name",placeholder:"My Pipeline",value:"My Pipeline"},{id:"desc",label:"Description (optional)",placeholder:""}],confirmLabel:"Create"});if(!(!e||!e.name.trim()))try{const t=await m.graphWorkflows.create({name:e.name.trim(),description:e.desc.trim(),project:ie,max_iterations:5});L=t,_t(t),we=null,nt()}catch(t){p(`Could not create pipeline: ${t.message}`,"error")}}const gi=[{key:"pm_dev_reviewer",label:"PM → Dev → Reviewer",description:"Standard feature pipeline with approval gate",nodes:[{name:"Product Manager",stateless:!1,inputs:[{name:"prompt",type:"prompt"}],outputs:[{name:"spec.md",type:"md"}],role_prompt:"You are a senior product manager. Produce a detailed spec document."},{name:"Developer",stateless:!1,inputs:[{name:"spec.md",type:"md"}],outputs:[{name:"code",type:"code"}],role_prompt:"You are a senior software engineer. Implement the spec."},{name:"Reviewer",stateless:!0,inputs:[{name:"code",type:"code"},{name:"spec.md",type:"md"}],outputs:[{name:"feedback.md",type:"feedback"},{name:"approved",type:"score"}],role_prompt:"You are a code reviewer. Review with fresh eyes."}],edges:[{from:0,to:1},{from:1,to:2}]},{key:"pm_arch_dev_reviewer",label:"PM → Architect → Dev → Reviewer",description:"Full 4-agent work item pipeline (same as Planner ▶ Run)",nodes:[{name:"Product Manager",stateless:!1,inputs:[{name:"prompt",type:"prompt"}],outputs:[{name:"spec.md",type:"md"}],role_prompt:"You are a senior product manager. Produce a detailed spec document."},{name:"Architect",stateless:!1,inputs:[{name:"spec.md",type:"md"}],outputs:[{name:"arch.md",type:"md"}],role_prompt:"You are a Senior Architect. Write a technical implementation plan."},{name:"Developer",stateless:!1,inputs:[{name:"arch.md",type:"md"}],outputs:[{name:"code",type:"code"}],role_prompt:"You are a senior software engineer. Implement the architecture plan."},{name:"Reviewer",stateless:!0,inputs:[{name:"code",type:"code"}],outputs:[{name:"score",type:"score"}],role_prompt:"You are a code reviewer. Score the code 1-10."}],edges:[{from:0,to:1},{from:1,to:2},{from:2,to:3}]},{key:"dev_tester",label:"Dev → Tester",description:"Simple code generation + test scoring",nodes:[{name:"Developer",stateless:!1,inputs:[{name:"prompt",type:"prompt"}],outputs:[{name:"code",type:"code"}],role_prompt:"You are a senior software engineer. Write the code."},{name:"Tester",stateless:!1,inputs:[{name:"code",type:"code"}],outputs:[{name:"score",type:"score"}],role_prompt:"You are a QA engineer. Test the code and provide a score out of 100."}],edges:[{from:0,to:1}]}];function fi(e){const t=document.getElementById("_gw-tmpl-menu");if(t){t.remove();return}const o=(e?.currentTarget||e?.target)?.getBoundingClientRect?.()||{left:100,bottom:50},n=document.createElement("div");n.id="_gw-tmpl-menu",n.style.cssText=`position:fixed;z-index:2000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,0.18);padding:0.4rem 0;min-width:260px;
    left:${o.left}px;top:${(o.bottom||50)+4}px`,gi.forEach(i=>{const a=document.createElement("div");a.style.cssText="padding:0.5rem 0.85rem;cursor:pointer;",a.innerHTML=`
      <div style="font-size:0.82rem;font-weight:600">${B(i.label)}</div>
      <div style="font-size:0.7rem;color:var(--muted)">${B(i.description)}</div>
    `,a.onmouseenter=()=>a.style.background="var(--hover)",a.onmouseleave=()=>a.style.background="",a.onclick=()=>{n.remove(),vi(i)},n.appendChild(a)}),document.body.appendChild(n),setTimeout(()=>document.addEventListener("click",function i(){n.remove(),document.removeEventListener("click",i)}),0)}async function vi(e){if(!ie){p("Open a project first","error");return}try{const t=await m.graphWorkflows.create({name:e.label,description:e.description,project:ie,max_iterations:5}),r=[];for(let n=0;n<e.nodes.length;n++){const i=e.nodes[n],a=await m.graphWorkflows.createNode(t.id,{name:i.name,provider:"claude",role_prompt:i.role_prompt||"",stateless:i.stateless||!1,success_criteria:i.success_criteria||"",inputs:i.inputs||[],outputs:i.outputs||[],order_index:n,max_retry:3,position_x:100+n*220,position_y:150});r.push(a.id)}for(const n of e.edges)r[n.from]&&r[n.to]&&await m.graphWorkflows.createEdge(t.id,{source_node_id:r[n.from],target_node_id:r[n.to],condition:n.condition||null,label:n.label||""});const o=await m.graphWorkflows.get(t.id);L=o,_t(o),nt(),p(`Created "${e.label}"`,"success")}catch(t){p(`Template failed: ${t.message}`,"error")}}async function yi(e){if(!(!L||!e)&&L.name!=="_work_item_pipeline")try{await m.graphWorkflows.update(L.id,{name:e}),L.name=e,nt()}catch(t){p(`Save failed: ${t.message}`,"error")}}function $t(e){const t=document.getElementById("gw-empty-state"),r=document.getElementById("gw-pipeline");if(!r)return;t&&(t.style.display="none"),r.style.display="flex";const o=e.nodes||[],n=e.edges||[],i=new Map;for(const s of n)i.has(s.source_node_id)||i.set(s.source_node_id,[]),i.get(s.source_node_id).push(s);let a="";o.forEach((s,d)=>{if(a+=hi(s),d<o.length-1){const c=(i.get(s.id)||[])[0]?.label||"";a+=`
        <div class="gw-connector">
          <div class="gw-conn-line">
            ${c?`<div class="gw-conn-label">${B(c)}</div>`:""}
          </div>
        </div>
      `}}),a+=`
    <div style="display:flex;align-items:center;padding-left:${o.length?"0.5rem":"0"}">
      <button class="gw-add-btn" onclick="window._gwShowAddMenu(event)" title="Add node">+</button>
    </div>
  `,r.innerHTML=a,r.querySelectorAll(".gw-node-card").forEach(s=>{const d=s.dataset.nodeId;s.addEventListener("click",l=>{l.target.closest(".gw-node-del")||go(d)})}),window._gwShowAddMenu=s=>{s.stopPropagation(),xi(s)},window._gwDeleteNode=(s,d)=>{d&&d.stopPropagation(),$i(s)}}function hi(e){const t={agent:"#3ecf8e",system_designer:"#9b7ef8",reviewer:"#2dd4bf"},o=Ye.find(g=>g.id===e.role_id||g.name===e.name)?.role_type||"agent",n=t[o]||"#6b7490",i=o==="system_designer"?"SYS":o==="reviewer"?"REV":"AGT",a=e.id===He,s=e.model?`${e.provider} / ${e.model}`:e.provider||"claude",d=e.success_criteria||"",l=[];e.stateless&&l.push('<span class="gw-cfg-badge gw-cfg-stateless" title="Runs with fresh context each time">stateless</span>'),(e.max_retry??3)>1&&l.push(`<span class="gw-cfg-badge" title="Max retry attempts">retry:${e.max_retry??3}</span>`),e.continue_on_fail&&l.push('<span class="gw-cfg-badge gw-cfg-warn"     title="Pipeline continues even if this node fails">cont.fail</span>'),e.require_approval&&l.push('<span class="gw-cfg-badge gw-cfg-approval" title="Requires human approval before next node">approval</span>');const c=(e.role_prompt||"").trim().slice(0,72);return`
    <div class="gw-node-card ${a?"selected":""}" data-node-id="${e.id}">
      <div class="gw-node-header">
        <div class="gw-node-dot" style="background:${n}"></div>
        <div class="gw-node-name">${B(e.name)}</div>
        <div class="gw-node-badge">${B(i)}</div>
        <button class="gw-node-del" onclick="window._gwDeleteNode('${e.id}', event)" title="Delete node">✕</button>
      </div>
      <div class="gw-node-body">
        <div class="gw-node-row">
          <span class="gw-node-row-lbl">model</span>
          <span class="gw-node-row-val">${B(s)}</span>
        </div>
        ${c?`
        <div style="margin-top:0.3rem;font-size:0.68rem;color:var(--muted);line-height:1.35;
                    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden"
             title="${B(e.role_prompt||"")}">${B(c)}${(e.role_prompt||"").length>72?"…":""}</div>
        `:'<div style="font-size:0.68rem;color:var(--muted);font-style:italic">no prompt — click to configure</div>'}
        ${l.length?`<div class="gw-node-cfg-badges" style="margin-top:0.3rem">${l.join("")}</div>`:""}
      </div>
      <div class="gw-node-footer">
        <div class="gw-node-status" id="status-${e.id}"></div>
        ${d?`<span title="Success criteria">${B(d.slice(0,30))}${d.length>30?"…":""}</span>`:""}
      </div>
    </div>
  `}function go(e){He=e;const t=L?.nodes?.find(o=>o.id===e);if(!t)return;document.querySelectorAll(".gw-node-card").forEach(o=>{o.classList.toggle("selected",o.dataset.nodeId===e)}),bi(t);const r=document.getElementById("gw-detail");r&&r.classList.add("open")}function fo(){He=null,document.querySelectorAll(".gw-node-card").forEach(t=>t.classList.remove("selected"));const e=document.getElementById("gw-detail");e&&e.classList.remove("open")}function bi(e){const t=document.getElementById("gw-detail-title"),r=document.getElementById("gw-detail-body");if(!r)return;t&&(t.textContent=e.name);const o=["claude","openai","deepseek","gemini","grok"].map(d=>`<option value="${d}" ${e.provider===d?"selected":""}>${d}</option>`).join(""),n=["","reviewer_approved","tests_pass","score >= 80","score >= 85","approved == true"].map(d=>`<option value="${d}" ${e.success_criteria===d?"selected":""}>${d||"—"}</option>`).join(""),i=L?.nodes?.findIndex(d=>d.id===e.id)??-1,a=i>0?L.nodes.slice(0,i).map(d=>`"${d.name}"`).join(", "):null,s=a?`Previous nodes available in context: ${a}. Reference their output in your prompt.`:"This is the first node. It receives the user's task as input.";r.innerHTML=`
    <div class="gw-field">
      <label>Name</label>
      <input id="dn-name" value="${B(e.name)}" />
    </div>
    <div class="gw-field">
      <label>Provider</label>
      <select id="dn-provider">${o}</select>
    </div>
    <div class="gw-field">
      <label>Model (optional)</label>
      <input id="dn-model" value="${B(e.model||"")}" placeholder="leave blank for default" />
    </div>
    <div style="background:rgba(100,108,255,0.07);border:1px solid rgba(100,108,255,0.2);
                border-radius:6px;padding:0.5rem 0.65rem;margin-bottom:0.75rem;font-size:0.72rem;
                color:var(--muted);line-height:1.5">
      <b style="color:var(--fg)">Context flow:</b> ${B(s)}<br>
      Outputs from all previous nodes are automatically injected before your prompt.
      Each node's output is also saved to <code>documents/pipelines/…</code> after the run.
    </div>
    <div class="gw-field">
      <label>System Prompt</label>
      <textarea id="dn-prompt" rows="8" placeholder="You are a senior product manager. The user will describe a feature — write a complete technical specification for it.">${B(e.role_prompt||"")}</textarea>
    </div>
    <div class="gw-field">
      <label>Success Criteria</label>
      <select id="dn-criteria">${n}</select>
    </div>
    <div class="gw-field">
      <label>Max Retry</label>
      <input type="number" id="dn-max-retry" value="${e.max_retry??3}" min="1" max="10" />
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Stateless <span style="font-weight:400;color:var(--muted)">(ignore prior context)</span></label>
        <input type="checkbox" id="dn-stateless" ${e.stateless?"checked":""} />
      </div>
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Continue on Fail</label>
        <input type="checkbox" id="dn-continue-fail" ${e.continue_on_fail?"checked":""} />
      </div>
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Require Approval</label>
        <input type="checkbox" id="dn-approval" ${e.require_approval?"checked":""} />
      </div>
    </div>
  `}async function wi(){if(!He||!L)return;const e={name:document.getElementById("dn-name")?.value||"",provider:document.getElementById("dn-provider")?.value||"claude",model:document.getElementById("dn-model")?.value||"",role_prompt:document.getElementById("dn-prompt")?.value||"",success_criteria:document.getElementById("dn-criteria")?.value||"",stateless:document.getElementById("dn-stateless")?.checked||!1,continue_on_fail:document.getElementById("dn-continue-fail")?.checked||!1,require_approval:document.getElementById("dn-approval")?.checked||!1,max_retry:parseInt(document.getElementById("dn-max-retry")?.value||"3",10)};try{await m.graphWorkflows.updateNode(L.id,He,e);const t=await m.graphWorkflows.get(L.id);L=t,$t(t),go(He),p("Node saved","success")}catch(t){p(`Save failed: ${t.message}`,"error")}}function xi(e){const t=document.getElementById("_gw-add-menu");if(t){t.remove();return}const r=document.createElement("div");r.id="_gw-add-menu",r.style.cssText=`position:fixed;z-index:1000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);padding:0.25rem 0;min-width:180px;
    left:${e.clientX}px;top:${e.clientY}px`;const o={agent:"#3ecf8e",system_designer:"#9b7ef8",reviewer:"#2dd4bf"};(Ye.length?Ye:[{id:null,name:"Custom Node",role_type:"agent"}]).forEach(i=>{const a=o[i.role_type||"agent"]||"#6b7490",s=document.createElement("div");s.style.cssText="padding:0.35rem 0.75rem;cursor:pointer;font-size:0.8rem;display:flex;align-items:center;gap:0.4rem",s.innerHTML=`<span style="width:8px;height:8px;border-radius:50%;background:${a};display:inline-block;flex-shrink:0"></span>${B(i.name)}`,s.onmouseenter=()=>s.style.background="var(--hover)",s.onmouseleave=()=>s.style.background="",s.onclick=()=>{r.remove(),i.id?vo(i.id):yo()},r.appendChild(s)}),document.body.appendChild(r),setTimeout(()=>document.addEventListener("click",function i(){r.remove(),document.removeEventListener("click",i)}),0)}async function vo(e){if(!L){p("Open or create a flow first","error");return}const t=Ye.find(o=>o.id===e);if(!t)return;const r=(L.nodes||[]).length;try{const o=await m.graphWorkflows.createNode(L.id,{name:t.name,provider:t.provider||"claude",model:t.model||"",role_id:t.id,stateless:!1,inputs:t.inputs||[],outputs:t.outputs||[],order_index:r,position_x:100+r*200,position_y:150});await ho(o);const n=await m.graphWorkflows.get(L.id);L=n,$t(n)}catch(o){p(`Failed to add node: ${o.message}`,"error")}}async function yo(){if(!L){p("Open or create a flow first","error");return}const e=(L.nodes||[]).length;try{const t=await m.graphWorkflows.createNode(L.id,{name:"New Node",provider:"claude",order_index:e,position_x:100+e*200,position_y:150});await ho(t);const r=await m.graphWorkflows.get(L.id);L=r,$t(r)}catch(t){p(`Failed to add node: ${t.message}`,"error")}}async function _i(e){return yo()}async function ho(e){const t=L.nodes||[];if(t.length>0){const r=t[t.length-1];try{await m.graphWorkflows.createEdge(L.id,{source_node_id:r.id,target_node_id:e.id})}catch{}}}async function $i(e){if(!L)return;const t=L.nodes?.find(o=>o.id===e);if(await ur({title:`Delete "${t?.name||"node"}"?`,fields:[],confirmLabel:"Delete",danger:!0}))try{await m.graphWorkflows.deleteNode(L.id,e),He===e&&fo();const o=await m.graphWorkflows.get(L.id);L=o,we=null,$t(o)}catch(o){p(`Delete failed: ${o.message}`,"error")}}async function ki(){if(!L)return;const e=await ur({title:`Run: ${L.name}`,fields:[{id:"input",label:"Task / Prompt",placeholder:"Describe the task for this pipeline…",rows:4}],confirmLabel:"▶ Run"});if(!e||!e.input.trim())return;const t=e.input.trim();try{const{run_id:r}=await m.graphWorkflows.startRun(L.id,{user_input:t,project:ie});ge=r,et=new Date,bo(L.name,L.nodes||[]),fr(r)}catch(r){p(`Run failed: ${r.message}`,"error")}}function Ei(){const e=document.getElementById("gw-log"),t=document.getElementById("gw-log-toggle");if(!e)return;const r=e.querySelector(".gw-log-body"),o=r?.style.display!=="none";r&&(r.style.display=o?"none":""),t&&(t.textContent=o?"▶":"▼")}function bo(e,t){const r=document.getElementById("gw-run-panel");r&&r.classList.add("open");const o=document.getElementById("gw-rp-wf-name");o&&(o.textContent=e||"Pipeline"),Bt=[],dt={},_o(),xo(t.map(n=>({node_name:n.name,node_id:n.id,status:"pending"})),null),J&&clearInterval(J),J=setInterval(()=>{const n=document.getElementById("gw-rp-timer");n&&et&&(n.textContent=gr(Date.now()-et.getTime()))},1e3)}function Ci(){const e=document.getElementById("gw-run-panel");e&&e.classList.remove("open"),J&&(clearInterval(J),J=null)}function fr(e){re&&clearInterval(re),re=setInterval(async()=>{try{const t=await m.graphWorkflows.getRun(e);if(wo(t),["done","error","stopped","cancelled"].includes(t.status)&&(clearInterval(re),re=null,J&&(clearInterval(J),J=null),$o(t)),t.status==="waiting_approval"){const o=t.context?._waiting?.node_name;o&&o!==po&&(clearInterval(re),re=null,J&&(clearInterval(J),J=null),Si(t))}}catch{clearInterval(re),re=null}},1e3)}function wo(e){const t={done:"#3ecf8e",error:"#e85d75",running:"#f5a623",stopped:"#888",cancelled:"#888",waiting_approval:"#9b7ef8"},r=document.getElementById("gw-rp-dot"),o=document.getElementById("gw-rp-status"),n=document.getElementById("gw-rp-cost"),i=document.getElementById("gw-rp-nodes"),a=document.getElementById("gw-rp-stop");r&&(r.className=`gw-rp-status-dot ${e.status}`),o&&(o.textContent=e.status.replace("_"," "),o.style.color=t[e.status]||"var(--muted)"),n&&(n.textContent=`$${Number(e.total_cost_usd||0).toFixed(4)}`);const s=(e.node_results||[]).filter(f=>f.status==="done").length,d=L?.nodes?.length||(e.node_results||[]).length;i&&(i.textContent=`${s}/${d}`),a&&["done","error","stopped","cancelled"].includes(e.status)&&(a.style.display="none");const l=L?.nodes||[],c={};for(const f of e.node_results||[])c[f.node_name]=f;const g=l.length?l.map(f=>{const u=c[f.name];return u?{...u,node_id:f.id}:{node_name:f.name,node_id:f.id,status:f.name===e.current_node?"running":"pending"}}):e.node_results||[];xo(g,e.current_node);for(const f of e.node_results||[])if(dt[f.node_name]!==f.status)if(dt[f.node_name]=f.status,f.status==="running")Et(f.node_name,"Processing…");else if(f.status==="done"){const h=f.started_at?` (${xt(f.started_at,f.finished_at)})`:"",_=f.cost_usd>0?`, $${Number(f.cost_usd).toFixed(4)}`:"";Et(f.node_name,`✓ Done${h}${_}`)}else f.status==="error"&&Et(f.node_name,`✗ Error: ${f.output?.slice(0,100)||"unknown"}`);e.current_node&&e.current_node!==dt.__current__&&(dt.__current__=e.current_node,e.node_results?.find(f=>f.node_name===e.current_node&&f.status==="running")||Et(e.current_node,"Processing…"));for(const f of e.node_results||[]){const u=document.getElementById(`status-${f.node_id}`);u&&(u.className=`gw-node-status ${f.status}`)}if(e.current_node&&l.length){const f=l.find(u=>u.name===e.current_node);if(f){const u=document.getElementById(`status-${f.id}`);u&&(u.className="gw-node-status running")}}}function xo(e,t){const r=document.getElementById("gw-rp-timeline");r&&(r.innerHTML=e.map(o=>{let n=o.status||"pending";n==="pending"&&o.node_name===t&&(n="running");const i=o.started_at?xt(o.started_at,o.finished_at):"",a=o.cost_usd>0?`$${Number(o.cost_usd).toFixed(4)}`:"",s=[i,a].filter(Boolean).join(" · "),d=n==="done"?"✓":n==="error"?"✗":n==="running"?"⟳":n==="skipped"?"⤳":"○",l=o.output?`<div class="gw-rp-step-out">${xe(o.output.slice(0,500))}</div>`:"";return`
      <div class="gw-rp-step ${n}">
        <div class="gw-rp-step-hdr">
          <div class="gw-rp-step-dot"></div>
          <span class="gw-rp-step-name">${d} ${B(o.node_name)}</span>
        </div>
        ${s?`<div class="gw-rp-step-meta">${B(s)}</div>`:""}
        ${l}
      </div>`}).join(""))}function Et(e,t){const r=new Date().toLocaleTimeString("en",{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit"});Bt.push({node:e,msg:t,ts:r}),_o()}function _o(){const e=document.getElementById("gw-run-log");if(e){if(!Bt.length){e.innerHTML='<span style="color:var(--muted)">Waiting for pipeline to start…</span>';return}e.innerHTML=Bt.map(t=>`<div style="margin-bottom:0.1rem">
      <span style="color:${zi(t.node)};font-weight:600">${B(t.node)}:</span>
      <span style="color:var(--muted);font-size:0.65rem;margin:0 0.35rem">${t.ts}</span>
      <span>${B(t.msg)}</span>
    </div>`).join(""),e.scrollTop=e.scrollHeight}}function zi(e){const t=["#9b7ef8","#3ecf8e","#f5a623","#2dd4bf","#e85d75","#5b8ef0"];let r=0;for(const o of e||"")r=r*31+o.charCodeAt(0)&65535;return t[r%t.length]}async function $o(e){const t=document.getElementById("gw-rp-timer");if(t&&e.started_at&&(t.textContent=xt(e.started_at,e.finished_at||new Date().toISOString())),e.status==="error"&&e.error){const r=document.getElementById("gw-rp-timeline");r&&r.insertAdjacentHTML("beforeend",`
      <div style="margin:0.5rem 0.75rem;padding:0.5rem;background:rgba(232,93,117,0.1);
           border:1px solid rgba(232,93,117,0.3);border-radius:6px;font-size:0.72rem;color:#e85d75">
        ✗ ${B(e.error)}
      </div>`)}if(e.status==="done"&&ge)try{const{files:r,directory:o}=await m.graphWorkflows.deliverables(ge);Ii(r,o,e)}catch{}we=null,jt()}function Ii(e,t,r){const o=document.getElementById("gw-rp-deliverables");if(!o)return;o.style.display="";const i=L?.name==="_work_item_pipeline"?'<div style="font-size:0.72rem;color:#3ecf8e;margin-top:0.4rem">✓ Work item updated in Planner — open it to view AC &amp; implementation plan</div>':"",a=r?.context||{},s=(L?.nodes||[]).map(d=>{const l=a[d.name];if(!l||typeof l!="string")return"";const c=l.slice(0,600);return`
      <details style="margin:0.35rem 0" open>
        <summary style="cursor:pointer;font-size:0.72rem;font-weight:600;color:var(--fg);
                        padding:0.25rem 0;list-style:none;display:flex;align-items:center;gap:0.4rem">
          <span style="color:#3ecf8e">✓</span> ${B(d.name)}
        </summary>
        <div class="md-prose" style="font-size:0.71rem;line-height:1.5;
             margin:0.25rem 0 0.35rem 0.75rem;padding:0.4rem 0.5rem;
             background:var(--bg2);border-radius:4px;border-left:2px solid var(--accent)">
          ${xe(c)}${l.length>600?'<p style="color:var(--muted)">…</p>':""}
        </div>
      </details>`}).filter(Boolean).join("");o.innerHTML=`
    <div style="padding:0.5rem 0.75rem">
      <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                  color:var(--muted);margin-bottom:0.4rem">
        ✓ Pipeline Complete
      </div>
      ${s}
      ${e.length>0?`
        <div style="margin-top:0.5rem;padding-top:0.4rem;border-top:1px solid var(--border)">
          <div style="font-size:0.65rem;font-weight:600;color:var(--muted);margin-bottom:0.25rem">SAVED FILES</div>
          ${e.map(d=>`
            <div style="display:flex;align-items:center;gap:0.35rem;font-size:0.71rem;padding:0.15rem 0" title="${B(d.path)}">
              📄 <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${B(d.name)}</span>
              <span style="color:var(--muted)">${(d.size/1024).toFixed(1)}k</span>
            </div>`).join("")}
          <div style="font-size:0.63rem;color:var(--muted);margin-top:0.3rem">📁 ${B(t)}</div>
        </div>`:""}
      ${i}
    </div>
  `}async function Lr(e){if(!(!e||!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(e))))try{const t=await m.graphWorkflows.getRun(e);if(ge=e,et=t.started_at?new Date(t.started_at):new Date,t.workflow_id&&(!L||L.id!==t.workflow_id))try{L=await m.graphWorkflows.get(t.workflow_id),_t(L)}catch{}const r=t.workflow_name==="_work_item_pipeline"?"Work Item Pipeline":t.workflow_name||L?.name||"Pipeline";bo(r,L?.nodes||[]),J&&(clearInterval(J),J=null);const o=document.getElementById("gw-rp-timer");t.status==="running"?J=setInterval(()=>{const n=document.getElementById("gw-rp-timer");n&&et&&(n.textContent=gr(Date.now()-et.getTime()))},1e3):o&&t.started_at&&(o.textContent=xt(t.started_at,t.finished_at)),wo(t),t.status==="done"?$o(t):(t.status==="running"||t.status==="waiting_approval")&&fr(e)}catch(t){p(`Could not load run: ${t.message}`,"error")}}function Si(e){const t=document.getElementById("gw-approval-wrap");if(!t)return;Ee=[],Qe=e.context?._waiting?.output||"",zt=!1,po=e.context?._waiting?.node_name||null;const r=e.context?._waiting||{},o=r.next_node?` → ${B(r.next_node)}`:"";t.style.cssText="display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;padding:0.5rem 0.75rem;";const n=document.getElementById("gw-rp-timeline")?.parentElement;n&&(n.style.display="none"),t.innerHTML=`
    <!-- header row: title + action buttons -->
    <div style="display:flex;align-items:center;gap:0.6rem;flex-shrink:0;margin-bottom:0.3rem">
      <span style="font-size:0.82rem;font-weight:700;flex:1">
        ⏸ ${B(r.node_name||"Node")}${o}
      </span>
      <button class="btn btn-primary btn-sm" onclick="window._gwDecide(true,false)">✓ Approve</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwDecide(true,true)">↩ Retry</button>
      <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDecide(false,false)">✕ Stop</button>
    </div>
    <div style="font-size:0.71rem;color:var(--muted);flex-shrink:0;margin-bottom:0.4rem">
      ${B(r.approval_msg||"Review output and approve or reject.")}
    </div>
    <!-- 2-pane: current output (left) + chat (right) -->
    <div style="display:flex;flex:1;gap:0.75rem;min-height:0;overflow:hidden">
      <!-- Left: current output (updates after each chat reply) -->
      <div style="flex:1;display:flex;flex-direction:column;min-width:0">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                    color:var(--muted);margin-bottom:0.25rem;flex-shrink:0;display:flex;align-items:center;gap:0.5rem">
          Current Output
          <button id="gw-ap-edit-toggle" onclick="window._gwToggleEditMode()"
            style="font-size:0.6rem;padding:0.1rem 0.4rem;background:var(--surface2);border:1px solid var(--border);
                   border-radius:3px;cursor:pointer;color:var(--text2,var(--muted));font-family:var(--font)">
            ✏ Edit
          </button>
          <span id="gw-ap-processing" style="display:none;font-size:0.65rem;color:#f5a623">⟳ Processing…</span>
        </div>
        <div id="gw-ap-output" class="md-prose" data-raw-content="${B(r.output||"")}"
             style="flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;
             padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;
             border:1px solid var(--border)">${xe(r.output||"*(no output)*")}</div>
      </div>
      <!-- Right: chat pane -->
      <div style="width:320px;flex-shrink:0;display:flex;flex-direction:column;min-height:0">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                    color:var(--muted);margin-bottom:0.25rem;flex-shrink:0">Refine with Chat</div>
        <div id="gw-ap-msgs" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;
             gap:0.35rem;padding:0.4rem;background:var(--bg2);
             border:1px solid var(--border);border-bottom:none;border-radius:5px 5px 0 0;min-height:60px">
          <div id="gw-ap-hint" style="font-size:0.72rem;color:var(--muted);text-align:center;padding:0.5rem 0;margin:auto 0">
            Ask the agent to change anything. Once satisfied, click Approve.
          </div>
        </div>
        <div style="display:flex;gap:0.35rem;flex-shrink:0;border:1px solid var(--border);
                    border-radius:0 0 5px 5px;padding:0.35rem;background:var(--bg2)">
          <textarea id="gw-ap-input" placeholder="Request changes… (Ctrl+Enter to send)" rows="2"
            style="flex:1;resize:none;padding:0.35rem 0.45rem;border:1px solid var(--border);
                   border-radius:4px;background:var(--bg1);color:var(--fg);font-size:0.78rem;
                   font-family:inherit;line-height:1.4;min-height:48px;max-height:100px"></textarea>
          <button id="gw-ap-send" class="btn btn-primary btn-sm"
            style="align-self:flex-end;padding:0.3rem 0.65rem;font-size:0.75rem"
            onclick="window._gwApprovalSend()">Send</button>
        </div>
      </div>
    </div>
  `;const i=document.getElementById("gw-ap-input");i&&(i.addEventListener("keydown",a=>{a.key==="Enter"&&(a.ctrlKey||a.metaKey)&&(a.preventDefault(),window._gwApprovalSend())}),setTimeout(()=>i.focus(),80)),window._gwDecide=async(a,s)=>{try{await m.graphWorkflows.decide(ge,{approved:a,retry:s});const d=document.getElementById("gw-rp-timeline")?.parentElement;d&&(d.style.display=""),t.innerHTML="",t.style.cssText="display:none;padding:0.5rem 0.75rem 0;flex-shrink:0",Ee=[],fr(ge)}catch(d){p(`Decision failed: ${d.message}`,"error")}},window._gwApprovalSend=async()=>{const a=document.getElementById("gw-ap-input"),s=a?.value?.trim();if(!s||!ge)return;a.value="",a.disabled=!0;const d=document.getElementById("gw-ap-send");d&&(d.disabled=!0);const l=document.getElementById("gw-ap-processing");l&&(l.style.display="");const c=[...Ee];Ee.push({role:"user",content:s}),It();try{const{reply:g}=await m.graphWorkflows.approvalChat(ge,{message:s,history:c});Ee.push({role:"assistant",content:g}),It();const f=document.getElementById("gw-ap-output");f&&f.tagName!=="TEXTAREA"?(f.dataset.rawContent=g,f.innerHTML=er(Qe,g)):f?.tagName==="TEXTAREA"&&(f.value=g)}catch(g){p(`Chat failed: ${g.message}`,"error"),Ee.pop(),It()}finally{a&&(a.disabled=!1),d&&(d.disabled=!1),l&&(l.style.display="none"),a&&a.focus()}}}function er(e,t){if(!e||e===t)return xe(t);const r=e.split(`
`),o=t.split(`
`),n=new Set(r);let i="";for(const a of o)!n.has(a)&&a.trim()?i+=`<div style="background:rgba(62,207,142,0.15);display:block;border-left:3px solid #3ecf8e;padding-left:0.4rem;margin:1px 0">${xe(a)}</div>`:i+=xe(a+`
`);return i||xe(t)}window._gwToggleEditMode=()=>{const e=document.getElementById("gw-ap-output"),t=document.getElementById("gw-ap-edit-toggle");if(e)if(zt=!zt,zt){const r=e.dataset.rawContent||Qe,o=document.createElement("textarea");o.id="gw-ap-output",o.value=r,o.style.cssText='flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;resize:none;border:2px solid var(--accent);color:var(--fg);font-family:var(--font-mono,"Menlo",monospace);width:100%;box-sizing:border-box;min-height:200px',e.replaceWith(o),t&&(t.textContent="👁 Preview")}else{const r=document.getElementById("gw-ap-output"),o=r?.value||"",n=document.createElement("div");n.id="gw-ap-output",n.className="md-prose",n.dataset.rawContent=o,n.style.cssText="flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;border:1px solid var(--border)",n.innerHTML=er(Qe,o),r?.replaceWith(n),t&&(t.textContent="✏ Edit"),o!==Qe&&ge&&m.graphWorkflows.approvalChat(ge,{message:`Please use exactly this revised content as the new output (direct edit by user):

${o}`,history:[]}).then(i=>{Ee.push({role:"user",content:"(direct edit)"}),Ee.push({role:"assistant",content:i.reply}),It();const a=document.getElementById("gw-ap-output");a&&a.tagName!=="TEXTAREA"&&(a.dataset.rawContent=i.reply,a.innerHTML=er(Qe,i.reply))}).catch(()=>{})}};function It(){const e=document.getElementById("gw-ap-msgs");if(!e)return;const t=document.getElementById("gw-ap-hint");if(!Ee.length){t&&(t.style.display=""),e.querySelectorAll(".gw-ap-msg").forEach(r=>r.remove());return}t&&(t.style.display="none"),e.querySelectorAll(".gw-ap-msg").forEach(r=>r.remove());for(const r of Ee){const o=r.role==="user",n=r.content.length>400?r.content.slice(0,400)+"…":r.content,i=document.createElement("div");i.className="gw-ap-msg",i.style.cssText=`display:flex;flex-direction:column;align-items:${o?"flex-end":"flex-start"}`,i.innerHTML=`
      <div style="max-width:92%;padding:0.3rem 0.5rem;border-radius:7px;font-size:0.71rem;
           line-height:1.45;word-break:break-word;white-space:pre-wrap;
           background:${o?"rgba(100,108,255,0.18)":"var(--bg1)"};
           border:1px solid ${o?"rgba(100,108,255,0.35)":"var(--border)"}">
        ${B(n)}
      </div>
      <div style="font-size:0.6rem;color:var(--muted);margin-top:0.1rem;padding:0 0.2rem">
        ${o?"you":"agent"}
      </div>`,e.appendChild(i)}e.scrollTop=e.scrollHeight}async function Ti(){if(ge)try{await m.graphWorkflows.cancelRun(ge),re&&(clearInterval(re),re=null),J&&(clearInterval(J),J=null);const e=document.getElementById("gw-rp-dot"),t=document.getElementById("gw-rp-status"),r=document.getElementById("gw-rp-stop");e&&(e.className="gw-rp-status-dot cancelled"),t&&(t.textContent="cancelled",t.style.color="#888"),r&&(r.style.display="none"),we=null,jt()}catch(e){p(`Cancel failed: ${e.message}`,"error")}}async function Pi(){if(L)try{const e=await m.graphWorkflows.exportYAML(L.id),t=(L.name||"workflow").toLowerCase().replace(/[^a-z0-9_-]/g,"_");li(`${t}_graph.yaml`,e)}catch(e){p(`Export failed: ${e.message}`,"error")}}async function Li(e){const t=e.files?.[0];if(!t)return;const r=await t.text();try{const o=await m.graphWorkflows.importYAML(ie,r);L=o,_t(o),nt(),p("Workflow imported","success")}catch(o){p(`Import failed: ${o.message}`,"error")}e.value=""}function Bi(){re&&(clearInterval(re),re=null),J&&(clearInterval(J),J=null)}let lt=[];async function ji(e){let t=document.getElementById("react-runner-overlay");if(t)t.style.display="flex";else{t=document.createElement("div"),t.id="react-runner-overlay",t.style.cssText=`
      position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,0.65);
      display:flex;align-items:flex-start;justify-content:center;
      padding:3rem 1rem;overflow-y:auto;
    `,t.innerHTML=`
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;
                  width:100%;max-width:820px;display:flex;flex-direction:column;gap:0">
        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:1rem 1.25rem;border-bottom:1px solid var(--border)">
          <div style="font-weight:700;font-size:1rem;letter-spacing:0.01em">
            ▶ Run ReAct Pipeline
          </div>
          <button id="rr-close" style="background:none;border:none;cursor:pointer;
            color:var(--muted);font-size:1.2rem;padding:0.2rem 0.5rem">✕</button>
        </div>

        <!-- Pipeline selector + task input -->
        <div style="padding:1.25rem;display:flex;flex-direction:column;gap:1rem">
          <div style="display:flex;gap:0.75rem;align-items:flex-end">
            <div style="flex:0 0 200px">
              <label style="font-size:0.75rem;color:var(--muted);display:block;margin-bottom:0.35rem">Pipeline</label>
              <select id="rr-pipeline-select" style="width:100%;background:var(--bg-2);
                border:1px solid var(--border);border-radius:5px;padding:0.4rem 0.6rem;
                color:var(--fg);font-size:0.85rem">
                <option value="">Loading…</option>
              </select>
            </div>
            <div style="flex:1">
              <label style="font-size:0.75rem;color:var(--muted);display:block;margin-bottom:0.35rem">Task</label>
              <input id="rr-task-input" type="text" placeholder="Describe what the pipeline should do…"
                style="width:100%;box-sizing:border-box;background:var(--bg-2);
                  border:1px solid var(--border);border-radius:5px;padding:0.4rem 0.7rem;
                  color:var(--fg);font-size:0.85rem" />
            </div>
            <button id="rr-run-btn" style="padding:0.4rem 1.1rem;background:var(--accent);
              color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:0.85rem;
              white-space:nowrap">▶ Run</button>
          </div>
          <div id="rr-pipeline-desc" style="font-size:0.78rem;color:var(--muted);min-height:1em"></div>
        </div>

        <!-- Results area -->
        <div id="rr-results" style="border-top:1px solid var(--border);display:none;
          padding:0;max-height:60vh;overflow-y:auto"></div>
      </div>
    `,document.body.appendChild(t),document.getElementById("rr-close").onclick=()=>t.remove(),t.addEventListener("click",o=>{o.target===t&&t.remove()}),document.getElementById("rr-run-btn").onclick=Ri;try{lt=await m.agents.listPipelines()}catch{lt=[]}const r=document.getElementById("rr-pipeline-select");r.innerHTML=lt.length?lt.map(o=>`<option value="${o.name}">${o.name} — ${(o.stages||[]).map(n=>n.role).join(" → ")}</option>`).join(""):'<option value="">No pipelines found</option>',r.onchange=Br,Br()}}function Br(){const e=document.getElementById("rr-pipeline-select"),t=document.getElementById("rr-pipeline-desc"),r=lt.find(o=>o.name===e?.value);r?t.textContent=r.description||`${(r.stages||[]).length} stages · max ${r.max_rejection_retries??2} rejection retries`:t.textContent=""}async function Ri(){const e=document.getElementById("rr-pipeline-select")?.value,t=document.getElementById("rr-task-input")?.value?.trim(),r=document.getElementById("rr-run-btn"),o=document.getElementById("rr-results");if(!e||!t){alert("Select a pipeline and enter a task description.");return}r.disabled=!0,r.textContent="⏳ Running…",o.style.display="block",o.innerHTML=`
    <div style="padding:1.25rem;color:var(--muted);font-size:0.85rem;text-align:center">
      Running pipeline — this may take a few minutes…
    </div>`;try{const n=await m.agents.runPipeline({pipeline:e,task:t,project:ie||"aicli"});Ai(n)}catch(n){o.innerHTML=`
      <div style="padding:1.25rem;color:#e85d75;font-size:0.85rem">
        ✗ Pipeline failed: ${n.message}
      </div>`}finally{r.disabled=!1,r.textContent="▶ Run"}}function Ai(e){const t=document.getElementById("rr-results"),r=e.final_verdict||"unknown",o=r==="approved"?"#3ecf8e":r==="rejected"||r==="error"?"#e85d75":"#f5a623",n=Object.entries(e.stage_details||{}).map(([i,a])=>{const s=(a.steps||[]).map(c=>`
      <div style="margin-bottom:0.6rem">
        <div style="font-size:0.75rem;font-weight:600;color:var(--muted)">Step ${c.step}</div>
        ${c.thought?`<div style="font-size:0.8rem;color:var(--fg);opacity:0.9;margin-top:0.2rem">
          <span style="color:#9b7ef8;font-weight:600">Thought:</span> ${B(c.thought)}</div>`:""}
        ${c.action?`<div style="font-size:0.8rem;margin-top:0.15rem">
          <span style="color:#5b8ef0;font-weight:600">Action:</span>
          <code style="background:var(--bg-2);padding:0.1rem 0.3rem;border-radius:3px;font-size:0.78rem">${B(c.action)}</code>
          ${c.args?`<span style="color:var(--muted);font-size:0.75rem"> ${JSON.stringify(c.args)}</span>`:""}
          </div>`:""}
        ${c.observation?`<div style="font-size:0.78rem;color:var(--muted);margin-top:0.15rem;
          max-height:4em;overflow:hidden;text-overflow:ellipsis">
          <span style="color:#3ecf8e;font-weight:600">Obs:</span> ${B(c.observation.slice(0,300))}
          </div>`:""}
        ${c.guard_fired?'<div style="font-size:0.72rem;color:#f5a623">⚠ Hallucination guard fired</div>':""}
      </div>
    `).join(""),d=a.steps?.length>3,l=`rr-steps-${i}`;return`
      <div style="border-bottom:1px solid var(--border)">
        <div style="padding:0.75rem 1.25rem;display:flex;align-items:center;gap:0.75rem;
          cursor:pointer;user-select:none" onclick="
            const el=document.getElementById('${l}');
            el.style.display=el.style.display==='none'?'block':'none'">
          <span style="font-weight:600;font-size:0.85rem">${B(a.role)}</span>
          <span style="font-size:0.75rem;color:var(--muted)">${i}</span>
          ${a.attempt>1?`<span style="font-size:0.72rem;color:#f5a623">retry #${a.attempt}</span>`:""}
          <span style="font-size:0.75rem;color:${a.status==="done"?"#3ecf8e":"#e85d75"};margin-left:auto">
            ${a.status} · ${a.steps?.length??0} steps
          </span>
          <span style="font-size:0.75rem;color:var(--muted)">${d?"▼ expand":"▲"}</span>
        </div>
        <div id="${l}" style="display:${d?"none":"block"};
          padding:0 1.25rem 0.75rem;border-top:1px solid var(--border);background:var(--bg-2)">
          ${s||'<div style="color:var(--muted);font-size:0.8rem">No steps recorded.</div>'}
        </div>
      </div>
    `}).join("");t.innerHTML=`
    <!-- Summary bar -->
    <div style="padding:0.75rem 1.25rem;background:var(--bg-2);display:flex;
      align-items:center;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--border)">
      <span style="font-weight:700;color:${o};font-size:0.9rem">
        ${r.toUpperCase()}
      </span>
      <span style="color:var(--muted);font-size:0.8rem">${e.total_stages??0} stages</span>
      <span style="color:var(--muted);font-size:0.8rem">${e.total_steps??0} steps</span>
      <span style="color:var(--muted);font-size:0.8rem">$${(e.total_cost_usd??0).toFixed(4)}</span>
      <span style="color:var(--muted);font-size:0.8rem">${(e.duration_s??0).toFixed(1)}s</span>
    </div>
    <!-- Stage traces -->
    ${n}
    <!-- Structured output of last stage -->
    ${e.last_handoff?`
      <div style="padding:0.75rem 1.25rem;border-top:1px solid var(--border)">
        <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.4rem">Final structured output</div>
        <pre style="font-size:0.75rem;background:var(--bg-2);border-radius:5px;
          padding:0.6rem;overflow:auto;max-height:12rem;margin:0">${B(JSON.stringify(e.last_handoff,null,2))}</pre>
      </div>`:""}
  `}const vr=typeof window<"u"&&!!window.electronAPI;async function We(e,t={}){return vr?Mi(e,t):Oi(e,t)}async function Mi(e,t){const r=window.electronAPI;switch(e){case"settings_exist":return r.fileExists(t.path||Nt());case"load_settings":{const o=await r.readFile(Nt());if(o.error)return tr();try{return JSON.parse(o.content)}catch{return tr()}}case"save_settings":return!(await r.writeFile(Nt(),JSON.stringify(t.settings,null,2))).error;case"list_projects":return[];case"get_recent_projects":return[];default:return console.warn(`[electron] invoke not mapped: ${e}`,t),null}}function Nt(){return(window.__ENGINE_PATH__||"")+"/.aicli/ui_settings.json"}function tr(){return{api_keys:{},default_models:{},ui:{theme:"dark",font_size:13,sidebar_width:220},backend_url:or}}async function Di(){vr&&window.close()}async function Hi(){vr&&window.close()}async function Ni(){}async function Oi(e,t){console.log(`[mock] ${e}`,t);const r={settings_exist:()=>!1,load_settings:()=>tr(),save_settings:()=>null,list_projects:()=>[],get_recent_projects:()=>[],create_project:o=>({id:"mock-1",name:o.name,description:o.description,path:o.path,created_at:new Date().toISOString(),updated_at:new Date().toISOString(),llm_docs:{},code_files:[],workflows:[],tags:[]}),list_workflows:()=>[]};if(r[e])return r[e](t);throw new Error(`Mock not implemented: ${e}`)}const ko=[{id:"claude",label:"Claude",color:"var(--claude)",placeholder:"sk-ant-api03-...",models:["claude-opus-4-6","claude-sonnet-4-6","claude-haiku-4-5-20251001"]},{id:"openai",label:"OpenAI",color:"var(--openai)",placeholder:"sk-...",models:["gpt-4o","gpt-4o-mini","o3-mini","o3"]},{id:"deepseek",label:"DeepSeek",color:"var(--deepseek)",placeholder:"sk-...",models:["deepseek-chat","deepseek-reasoner"]},{id:"gemini",label:"Gemini",color:"var(--gemini)",placeholder:"AIza...",models:["gemini-1.5-pro","gemini-1.5-flash","gemini-2.0-flash"]},{id:"grok",label:"Grok",color:"var(--grok)",placeholder:"xai-...",models:["grok-3","grok-3-fast"]}];function Ui(e){e.className="view active settings-view",e.innerHTML=`
    <div style="max-width:900px">
      <div style="font-family:var(--font-ui);font-size:1.4rem;font-weight:800;letter-spacing:-1px;margin-bottom:0.3rem">Settings</div>
      <div style="font-size:0.68rem;color:var(--text2);margin-bottom:1.5rem">API keys are encrypted with AES-256-GCM using your master password.</div>

      <div class="settings-sections">
        <div class="settings-nav">
          ${x.currentProject?`
          <div class="settings-nav-item active" onclick="window._settingsSection('project')" id="snav-project">
            <span>◫</span> Project
          </div>`:""}
          <div class="settings-nav-item ${x.currentProject?"":"active"}" onclick="window._settingsSection('apikeys')" id="snav-apikeys">
            <span>🔑</span> API Keys
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('models')" id="snav-models">
            <span>◉</span> Models
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('backend')" id="snav-backend">
            <span>⚡</span> Backend
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('billing')" id="snav-billing">
            <span>💳</span> Billing
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('security')" id="snav-security">
            <span>🔐</span> Security
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('roles')" id="snav-roles">
            <span>◉</span> Agent Roles
          </div>
        </div>

        <div id="settings-content"></div>
      </div>
    </div>
  `;const t=x.currentProject?"project":"apikeys";jr(t),window._settingsSection=r=>{U({activeSettingsSection:r}),document.querySelectorAll(".settings-nav-item").forEach(o=>{o.classList.toggle("active",o.id===`snav-${r}`)}),jr(r)}}function jr(e){const t=document.getElementById("settings-content");if(!t)return;({project:Fi,apikeys:Rr,models:qi,workspace:Co,backend:Gi,billing:Eo,security:Vi,roles:ct}[e]||Rr)(t)}async function Fi(e){const t=x.currentProject;if(!t){e.innerHTML='<div class="empty-state"><p>No project open.</p></div>';return}e.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Loading project config…</div>';let r={};try{r=await m.getProjectConfig(t.name)}catch{r=t}e.innerHTML=`
    <div>
      <div class="settings-section-title">Project: ${t.name}</div>
      <div class="settings-section-desc">Per-project configuration stored in project.yaml.</div>

      <div class="field-group">
        <div class="field-label">Description</div>
        <input class="field-input" id="proj-description" value="${X(r.description||"")}" placeholder="Short project description" />
      </div>

      <div class="field-group">
        <div class="field-label">Default LLM Provider</div>
        <select class="field-select" id="proj-provider">
          ${["claude","openai","deepseek","gemini","grok"].map(i=>`<option value="${i}" ${r.default_provider===i?"selected":""}>${i}</option>`).join("")}
        </select>
      </div>

      <div class="field-group">
        <div class="field-label">Code Directory</div>
        <div style="display:flex;gap:8px">
          <input class="field-input" id="proj-codedir" value="${X(r.code_dir||"")}"
            placeholder="/path/to/your/code" style="flex:1" />
          <button class="btn btn-ghost" onclick="window._browseProjCodeDir()">Browse</button>
        </div>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">Used in Code view and for file injection into workflows.</div>
      </div>

      <div class="field-group">
        <label style="display:flex;align-items:center;gap:0.6rem;cursor:pointer;font-size:0.75rem">
          <input type="checkbox" id="proj-autocommit" ${r.auto_commit_push?"checked":""}
            style="width:15px;height:15px;accent-color:var(--accent);cursor:pointer" />
          <span>Auto commit &amp; push after every chat response</span>
        </label>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem;margin-left:1.5rem">
          When enabled, changed files in Code Directory are auto-committed (LLM generates the message) and pushed after each AI response.
        </div>
      </div>

      <div style="margin-top:1.25rem;display:flex;gap:0.75rem">
        <button class="btn btn-primary" onclick="window._saveProjSettings()">Save Project Config</button>
      </div>
      <div id="proj-save-status" style="font-size:0.68rem;margin-top:0.5rem;color:var(--muted)"></div>

      <!-- Git Setup section -->
      <div style="margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)">
        <div class="settings-section-title" style="font-size:0.85rem">Git Setup</div>
        <div class="settings-section-desc">
          Connect your project to GitHub. Credentials stored in <code>_system/.git_token</code> — never committed.
        </div>
        <div id="git-status-line" style="font-size:0.68rem;color:var(--muted);margin-bottom:1rem">
          Checking git status…
        </div>

        <!-- Repository URL -->
        <div class="field-group">
          <div class="field-label">GitHub Repository URL</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <input class="field-input" id="git-repo-url" value="${X(r.github_repo||"")}"
              placeholder="https://github.com/you/repo.git" style="flex:1;min-width:200px" />
            <button class="btn btn-ghost btn-sm" onclick="window._showCreateRepo()" id="git-create-btn">
              + Create on GitHub
            </button>
          </div>
          <!-- Inline create-repo form -->
          <div id="git-create-form" style="display:none;margin-top:0.6rem;padding:0.75rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border)">
            <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">
              Creates a new GitHub repository using your stored Browser Login token.
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <input class="field-input" id="new-repo-name" placeholder="repo-name" style="width:180px" />
              <label style="display:flex;align-items:center;gap:0.4rem;font-size:0.75rem;cursor:pointer">
                <input type="checkbox" id="new-repo-private" checked style="accent-color:var(--accent)" /> Private
              </label>
              <button class="btn btn-primary btn-sm" onclick="window._createRepoOnGitHub()">Create &amp; Connect</button>
              <button class="btn btn-ghost btn-sm" onclick="window._showCreateRepo(false)">Cancel</button>
            </div>
            <span id="git-create-status" style="font-size:0.68rem;color:var(--muted);display:block;margin-top:0.4rem"></span>
          </div>
          <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
            HTTPS format: <code>https://github.com/user/repo.git</code> · used for <code>/push</code> and auto-commit
          </div>
        </div>

        <!-- Default push branch -->
        <div class="field-group">
          <div class="field-label">Default Push Branch</div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <input class="field-input" id="git-branch" list="branch-suggestions"
              value="${X(r.git_branch||"")}" placeholder="main"
              style="width:160px" />
            <datalist id="branch-suggestions"></datalist>
            <button class="btn btn-ghost btn-sm" onclick="window._fetchBranches()" id="fetch-branches-btn">
              ↺ Fetch remote
            </button>
          </div>
          <div id="branches-hint" style="font-size:0.62rem;color:var(--muted);margin-top:0.2rem">
            Click ↺ Fetch remote to list branches from GitHub.
          </div>
        </div>

        <!-- Authentication -->
        <div style="margin-top:0.75rem">
          <div style="font-size:0.78rem;font-weight:600;color:var(--text);margin-bottom:0.5rem">Authentication</div>
          <div style="display:flex;gap:0;margin-bottom:0.75rem;border-bottom:1px solid var(--border)">
            <button id="git-tab-oauth" onclick="window._gitTab('oauth')"
              style="padding:0.4rem 0.85rem;border:none;border-bottom:2px solid var(--accent);
                     background:none;cursor:pointer;color:var(--text);font-size:0.75rem;font-weight:600">
              🌐 Browser Login
            </button>
            <button id="git-tab-pat" onclick="window._gitTab('pat')"
              style="padding:0.4rem 0.85rem;border:none;border-bottom:2px solid transparent;
                     background:none;cursor:pointer;color:var(--text2);font-size:0.75rem">
              🔑 PAT Token
            </button>
          </div>

          <!-- OAuth Device Flow panel -->
          <div id="git-panel-oauth">
            <div class="field-group">
              <div class="field-label">GitHub App Client ID</div>
              <input class="field-input" id="git-client-id" value="${X(r.github_client_id||"")}"
                placeholder="Ov23Li…" style="width:280px" />
              <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
                github.com → Settings → Developer settings → OAuth Apps → New OAuth App.
                Set any Homepage &amp; Callback URL to <code>http://localhost</code>. Enable <strong>Device Flow</strong> in the app settings. Copy the <strong>Client ID</strong>.
              </div>
            </div>
            <div id="git-device-box" style="display:none;margin:0.6rem 0;padding:0.85rem;
                 border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border)">
              <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.4rem">
                1. Open this URL (may open automatically):
              </div>
              <a id="git-verify-url" href="#" target="_blank"
                style="font-size:0.82rem;color:var(--accent);font-weight:600;display:block;margin-bottom:0.6rem">
                github.com/login/device
              </a>
              <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.3rem">2. Enter this code:</div>
              <div id="git-user-code"
                style="font-family:monospace;font-size:1.5rem;letter-spacing:0.25em;
                       color:var(--accent);font-weight:700;margin-bottom:0.6rem">—</div>
              <div id="git-device-status" style="font-size:0.72rem;color:var(--muted)">Waiting for authorization…</div>
            </div>
            <div style="display:flex;gap:0.75rem;margin-top:0.75rem;align-items:center">
              <button class="btn btn-primary btn-sm" id="git-oauth-btn" onclick="window._startDeviceFlow()">
                Login with GitHub
              </button>
              <span id="git-oauth-status" style="font-size:0.68rem;color:var(--muted)"></span>
            </div>
          </div>

          <!-- PAT Token panel -->
          <div id="git-panel-pat" style="display:none">
            <div class="field-group">
              <div class="field-label">Git Username</div>
              <input class="field-input" id="git-username" value="${X(r.git_username||"")}"
                placeholder="your-github-username" style="width:240px" />
            </div>
            <div class="field-group">
              <div class="field-label">Git Email</div>
              <input class="field-input" id="git-email" value="${X(r.git_email||"")}"
                placeholder="you@example.com" style="width:240px" />
            </div>
            <div class="field-group">
              <div class="field-label">Personal Access Token</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <input class="field-input" type="password" id="git-token"
                  placeholder="ghp_xxxxxxxxxxxx" style="flex:1;min-width:160px" />
                <button class="btn btn-ghost btn-sm" onclick="window._toggleGitToken()">👁</button>
                <a class="btn btn-ghost btn-sm"
                  href="https://github.com/settings/tokens/new?scopes=repo&description=aicli-desktop"
                  target="_blank">Open GitHub ↗</a>
              </div>
              <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
                GitHub → Settings → Developer settings → Personal access tokens → Generate new token → select <strong>repo</strong> scope
              </div>
            </div>
            <button class="btn btn-primary btn-sm" style="margin-top:0.5rem"
              onclick="window._saveGitCredentials()">Save &amp; Setup Git</button>
          </div>
        </div>

        <!-- Setup actions -->
        <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--border)">
          <div style="display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap">
            <button class="btn btn-ghost btn-sm" onclick="window._setupGit()">⚙ Setup Git</button>
            <button class="btn btn-ghost btn-sm" onclick="window._gitPull()" id="git-pull-btn">↓ Pull</button>
            <button class="btn btn-ghost btn-sm" onclick="window._gitPushAll()" id="git-push-btn">↑ Push</button>
            <button class="btn btn-ghost btn-sm" onclick="window._testGitConnection()" id="git-test-btn">⚡ Test Connection</button>
          </div>
          <!-- Error / status display — selectable text + copy button -->
          <div id="git-status-box" style="display:none;margin-top:0.5rem;padding:0.5rem 0.65rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border);
               font-size:0.72rem;line-height:1.5;position:relative">
            <span id="git-cred-status" style="user-select:text;cursor:text;white-space:pre-wrap;word-break:break-all"></span>
            <button onclick="window._copyGitStatus()" title="Copy to clipboard"
              style="position:absolute;top:0.3rem;right:0.3rem;background:none;border:none;
                     cursor:pointer;font-size:0.75rem;color:var(--text2);padding:2px 5px;
                     border-radius:3px;opacity:0.7" onmouseenter="this.style.opacity='1'"
              onmouseleave="this.style.opacity='0.7'">📋</button>
          </div>
          <div style="font-size:0.62rem;color:var(--muted);margin-top:0.4rem">
            Setup Git — init &amp; connect · Pull — sync from remote · Push — force-upload all files (replaces remote history) · Test — verify connection
          </div>
        </div>

        <!-- Setup Guide (collapsible) -->
        <div style="margin-top:1.25rem">
          <button class="btn btn-ghost btn-sm" onclick="window._toggleGitHelp()" id="git-help-btn"
            style="font-size:0.72rem;color:var(--text2)">
            ℹ How to set up git — step-by-step guide ▾
          </button>
          <div id="git-help-panel" style="display:none;margin-top:0.75rem;padding:1rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border);
               font-size:0.72rem;line-height:1.7;color:var(--text2)">
            <div style="font-weight:700;color:var(--text);margin-bottom:0.4rem">Step 1 — Install Git</div>
            <div>• <strong>Windows:</strong> Download <a href="https://gitforwindows.org" target="_blank" style="color:var(--accent)">Git for Windows</a> and run the installer with defaults. Tick "Git Bash" to get a terminal.</div>
            <div>• <strong>Mac:</strong> Run <code>xcode-select --install</code> in Terminal, or <code>brew install git</code> with <a href="https://brew.sh" target="_blank" style="color:var(--accent)">Homebrew</a>.</div>
            <div>• <strong>Linux:</strong> <code>sudo apt install git</code></div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Step 2 — GitHub account &amp; repo</div>
            <div>Sign up at <a href="https://github.com" target="_blank" style="color:var(--accent)">github.com</a>. Create a repo manually and paste its URL above, or use <strong>+ Create on GitHub</strong> (requires Browser Login first).</div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Option A — Browser Login (recommended)</div>
            <div>1. github.com → avatar → Settings → Developer settings → OAuth Apps → <strong>New OAuth App</strong></div>
            <div>2. Any name, Homepage URL: <code>http://localhost</code>, Callback URL: <code>http://localhost</code> → Register</div>
            <div>3. In the OAuth App page, scroll down → enable <strong>Device Flow</strong> → Update application</div>
            <div>4. Copy the <strong>Client ID</strong> (NOT the secret) → paste above → click <strong>Login with GitHub</strong></div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Option B — PAT Token</div>
            <div>1. github.com → avatar → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token</div>
            <div>2. Set a name, expiry, select <strong>repo</strong> scope → Generate. Copy the token (starts <code>ghp_</code>).</div>
            <div>3. Switch to PAT Token tab, fill username + email + token → Save &amp; Setup Git</div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Troubleshooting</div>
            <div>• <strong>400 on Login:</strong> Device Flow not enabled on your OAuth App — go to the app settings and check "Enable Device Flow".</div>
            <div>• <strong>Push 403:</strong> Token missing <code>repo</code> scope or expired — regenerate it.</div>
            <div>• <strong>Remote not found:</strong> Set GitHub Repo URL above and click ⚙ Setup Git.</div>
            <div>• <strong>No git repo error:</strong> Enter the repo URL, tick "Initial commit", click ⚙ Setup Git.</div>
          </div>
        </div>
      </div>
    </div>
  `,window._browseProjCodeDir=async()=>{if(window.electronAPI){const i=await window.electronAPI.openDirectory();i&&(document.getElementById("proj-codedir").value=i)}},window._fetchBranches=async()=>{const i=document.getElementById("fetch-branches-btn"),a=document.getElementById("branches-hint");i&&(i.disabled=!0,i.textContent="Fetching…");try{const s=await m.gitBranches(t.name),d=[...new Set([...s.remote_branches||[],...s.local_branches||[]])].filter(Boolean),l=document.getElementById("branch-suggestions");l&&(l.innerHTML=d.map(g=>`<option value="${g}">`).join("")),a&&(d.length?(a.innerHTML="Branches: "+d.map(g=>`<span onclick="document.getElementById('git-branch').value='${g}'"
              style="cursor:pointer;text-decoration:underline;margin-right:8px;color:var(--text2)">${g}</span>`).join(""),a.style.color="var(--text2)"):(a.textContent=s.is_git_repo?"No remote branches found — check Repo URL and credentials, then click ⚙ Setup Git.":"Not a git repo — enter the Repo URL and click ⚙ Setup Git first.",a.style.color="var(--muted)"));const c=document.getElementById("git-branch");c&&!c.value&&s.default_branch&&(c.value=s.default_branch)}catch(s){a&&(a.textContent=`Could not fetch branches: ${s.message}`,a.style.color="var(--red)")}finally{i&&(i.disabled=!1,i.textContent="↺ Fetch remote")}},window._saveProjSettings=async()=>{const i={description:document.getElementById("proj-description").value,default_provider:document.getElementById("proj-provider").value,code_dir:document.getElementById("proj-codedir").value,auto_commit_push:document.getElementById("proj-autocommit").checked},a=document.getElementById("proj-save-status");try{await m.updateProjectConfig(t.name,i),U({currentProject:{...x.currentProject,...i}}),a&&(a.textContent="✓ Project config saved",a.style.color="var(--green)"),p("Project config saved","success")}catch(s){a&&(a.textContent=`✕ ${s.message}`,a.style.color="var(--red)"),p(`Save failed: ${s.message}`,"error")}},m.gitStatus(t.name).then(i=>{const a=document.getElementById("git-status-line");if(a)if(!i.is_git_repo)a.textContent='⚠ Not a git repo — fill in credentials and click "Save & Setup Git"',a.style.color="var(--accent)";else{const s=i.has_credentials?"✓ credentials stored":"⚠ no credentials";if(a.innerHTML=`✓ Git repo on branch <strong>${i.branch||"main"}</strong> · ${i.changed_count} changed file(s) · ${s}`,a.style.color=i.has_credentials?"var(--green)":"var(--accent)",i.git_username){const d=document.getElementById("git-username");d&&!d.value&&(d.value=i.git_username)}}}).catch(()=>{});function o(i,a){const s=document.getElementById("git-status-box"),d=document.getElementById("git-cred-status");!d||!s||(d.textContent=i,d.style.color=a||"var(--text)",s.style.display=i?"":"none",s.style.borderColor=a==="var(--red)"?"rgba(255,80,80,0.3)":a==="var(--green)"?"rgba(80,200,120,0.3)":"var(--border)")}window._copyGitStatus=()=>{const i=document.getElementById("git-cred-status");i&&navigator.clipboard.writeText(i.textContent).then(()=>{const a=i.parentElement?.querySelector("button");a&&(a.textContent="✓",setTimeout(()=>{a.textContent="📋"},1500))}).catch(()=>{})},window._toggleGitToken=()=>{const i=document.getElementById("git-token");i&&(i.type=i.type==="password"?"text":"password")},window._gitTab=i=>{const a=i==="oauth",s=document.getElementById("git-tab-oauth"),d=document.getElementById("git-tab-pat"),l=document.getElementById("git-panel-oauth"),c=document.getElementById("git-panel-pat");s&&(s.style.borderBottomColor=a?"var(--accent)":"transparent",s.style.color=a?"var(--text)":"var(--text2)",s.style.fontWeight=a?"600":"normal"),d&&(d.style.borderBottomColor=a?"transparent":"var(--accent)",d.style.color=a?"var(--text2)":"var(--text)",d.style.fontWeight=a?"normal":"600"),l&&(l.style.display=a?"":"none"),c&&(c.style.display=a?"none":"")};let n=null;window._startDeviceFlow=async()=>{const i=document.getElementById("git-client-id")?.value.trim();if(!i){p("Enter your GitHub App Client ID first","error");return}m.updateProjectConfig(t.name,{github_client_id:i}).catch(()=>{});const a=document.getElementById("git-oauth-btn"),s=document.getElementById("git-oauth-status"),d=document.getElementById("git-device-box");a&&(a.disabled=!0,a.textContent="Starting…"),s&&(s.textContent=""),n&&(clearTimeout(n),n=null);const l=(c,g,f)=>{n=setTimeout(async()=>{const u=document.getElementById("git-device-status"),h=document.getElementById("git-oauth-status");if(Date.now()>f){u&&(u.textContent="Code expired — click Login again.",u.style.color="var(--accent)");return}try{const _=await m.gitOauthDevicePoll({client_id:i,device_code:c,project_name:t.name});if(_.status==="authorized"){u&&(u.textContent=`✓ Authorized as @${_.username}`,u.style.color="var(--green)"),h&&(h.textContent=`✓ Signed in as @${_.username}`,h.style.color="var(--green)"),p(`GitHub connected as @${_.username}`,"success"),window._setupGit?.();return}let C=g;if(_.status==="slow_down"&&(C=(_.interval||10)*1e3),_.status==="denied"){u&&(u.textContent="Access denied.",u.style.color="var(--red)");return}if(_.status==="expired"){u&&(u.textContent="Code expired — click Login again.",u.style.color="var(--accent)");return}l(c,C,f)}catch{l(c,g,f)}},g)};try{const c=await m.gitOauthDeviceStart({client_id:i});d&&(d.style.display="");const g=document.getElementById("git-verify-url"),f=document.getElementById("git-user-code"),u=document.getElementById("git-device-status");g&&(g.href=c.verification_uri,g.textContent=c.verification_uri),f&&(f.textContent=c.user_code||"—"),u&&(u.textContent="Waiting for you to authorize in browser…",u.style.color="var(--muted)"),c.verification_uri&&window.open(c.verification_uri,"_blank"),a&&(a.disabled=!1,a.textContent="Restart"),l(c.device_code,(c.interval||5)*1e3,Date.now()+(c.expires_in||900)*1e3)}catch(c){a&&(a.disabled=!1,a.textContent="Login with GitHub"),s&&(s.textContent=`Error: ${c.message}`,s.style.color="var(--red)"),p(`OAuth error: ${c.message}`,"error")}},window._toggleGitHelp=()=>{const i=document.getElementById("git-help-panel"),a=document.getElementById("git-help-btn");if(!i)return;const s=i.style.display!=="none";i.style.display=s?"none":"",a&&(a.textContent=a.textContent.replace(s?"▴":"▾",s?"▾":"▴"))},window._saveGitCredentials=async()=>{const i=document.getElementById("git-username").value.trim(),a=document.getElementById("git-email").value.trim(),s=document.getElementById("git-token").value.trim();if(!s){p("Enter a Personal Access Token","error");return}o("Setting up…","var(--muted)");try{const d=await m.gitSetup(t.name,{git_username:i,git_email:a,git_token:s,github_repo:document.getElementById("git-repo-url")?.value.trim()||"",git_branch:document.getElementById("git-branch")?.value.trim()||"",init_if_needed:!0,initial_commit:!0});o("✓ "+d.actions.join(`
`),"var(--green)"),p("Git configured","success");const l=await m.gitStatus(t.name),c=document.getElementById("git-status-line");c&&l.is_git_repo&&(c.innerHTML=`✓ Git repo on branch <strong>${l.branch||"main"}</strong> · credentials stored`,c.style.color="var(--green)"),window._fetchBranches?.()}catch(d){o(`✕ ${d.message}`,"var(--red)"),p(`Git setup failed: ${d.message}`,"error")}},window._setupGit=async()=>{const i=document.getElementById("git-repo-url")?.value.trim()||"",a=document.getElementById("git-branch")?.value.trim()||"",s=document.getElementById("git-client-id")?.value.trim()||"";o("Setting up…","var(--muted)");try{const d=await m.gitSetup(t.name,{github_repo:i,git_branch:a,github_client_id:s,init_if_needed:!0,initial_commit:!0});o("✓ "+d.actions.join(`
`),"var(--green)"),p("Git configured","success"),m.gitStatus(t.name).then(l=>{const c=document.getElementById("git-status-line");if(c&&l.is_git_repo){const g=l.has_credentials?"✓ credentials stored":"⚠ no credentials";c.innerHTML=`✓ Git repo · branch <strong>${l.branch||"main"}</strong> · ${l.changed_count} changed · ${g}`,c.style.color=l.has_credentials?"var(--green)":"var(--accent)"}}).catch(()=>{}),window._fetchBranches?.()}catch(d){o(`✕ ${d.message}`,"var(--red)"),p(`Setup failed: ${d.message}`,"error")}},window._testGitConnection=async()=>{const i=document.getElementById("git-test-btn");i&&(i.disabled=!0,i.textContent="Testing…"),o("","");try{const a=await m.gitTestConnection(t.name);if(a.ok){const s=a.branches?.length?a.branches.join(", "):"(no remote branches yet)";o(`✓ Connected
Branches: ${s}`,"var(--green)"),p("Git connection OK","success")}else o(`✕ ${a.error}`,"var(--red)"),p(`Connection failed: ${a.error}`,"error")}catch(a){o(`✕ ${a.message}`,"var(--red)"),p(`Test error: ${a.message}`,"error")}finally{i&&(i.disabled=!1,i.textContent="⚡ Test Connection")}},window._gitPull=async()=>{const i=document.getElementById("git-pull-btn");i&&(i.disabled=!0,i.textContent="Pulling…"),o("","");try{const a=await m.gitPull(t.name);a.ok?(o(`↓ ${a.message}`,"var(--green)"),p(a.message,"success")):(o(`✕ ${a.error}`,"var(--red)"),p(`Pull failed: ${a.error}`,"error"))}catch(a){o(`✕ ${a.message}`,"var(--red)"),p(`Pull error: ${a.message}`,"error")}finally{i&&(i.disabled=!1,i.textContent="↓ Pull")}},window._gitPushAll=async()=>{const i=document.getElementById("git-push-btn");i&&(i.disabled=!0,i.textContent="Pushing…"),o("Pushing — rewriting history to remove any secrets…","var(--muted)");try{const a=await m.gitPushAll(t.name);if(a.ok){const s=["↑ Pushed to remote (clean history)"];a.staged_count&&s.push(`${a.staged_count} file(s) committed`),o(s.join(`
`),"var(--green)"),p(s[0],"success")}else{const s=a.error||a.push_error||"Push failed";o(`✕ ${s}`,"var(--red)"),p(`Push failed: ${s}`,"error")}}catch(a){o(`✕ ${a.message}`,"var(--red)"),p(`Push error: ${a.message}`,"error")}finally{i&&(i.disabled=!1,i.textContent="↑ Push")}},window._showCreateRepo=(i=!0)=>{const a=document.getElementById("git-create-form");a&&(a.style.display=i?"":"none");const s=document.getElementById("git-create-btn");s&&(s.textContent=i?"− Cancel":"+ Create on GitHub")},window._createRepoOnGitHub=async()=>{const i=document.getElementById("new-repo-name")?.value.trim(),a=document.getElementById("new-repo-private")?.checked??!0,s=document.getElementById("git-create-status");if(!i){p("Enter a repository name","error");return}s&&(s.textContent="Creating…",s.style.color="var(--muted)");try{const d=await m.gitOauthCreateRepo({project_name:t.name,repo_name:i,private:a}),l=document.getElementById("git-repo-url");l&&(l.value=d.clone_url),s&&(s.textContent=`✓ Created: ${d.html_url}`,s.style.color="var(--green)"),p(`Repo created: ${d.html_url}`,"success"),window._showCreateRepo(!1),window._fetchBranches?.(),m.gitStatus(t.name).then(c=>{const g=document.getElementById("git-status-line");g&&c.is_git_repo&&(g.innerHTML="✓ Git repo · credentials stored",g.style.color="var(--green)")}).catch(()=>{})}catch(d){s&&(s.textContent=`✕ ${d.message}`,s.style.color="var(--red)"),p(`Create repo failed: ${d.message}`,"error")}}}function X(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Eo(e){const t=x.user?.is_admin||x.user?.role==="admin";e.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Loading billing info…</div>';try{const r=await m.billingBalance(),o=r.role||"free",n=r.balance_usd??0,i=r.free_tier_limit_usd,a=r.free_tier_used_usd??0;let s;if(o==="admin")s=`<div style="font-size:1.5rem;font-weight:700;color:var(--accent)">Admin</div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.25rem">Admin accounts have unlimited access</div>`;else if(o==="free"){const l=i?Math.min(100,a/i*100):0;s=`
        <div style="font-size:1.2rem;font-weight:700;color:var(--text)">Free Tier</div>
        <div style="font-size:0.72rem;color:var(--text2);margin-top:0.2rem">$${a.toFixed(4)} used of $${i?.toFixed(2)} limit</div>
        <div style="margin-top:0.5rem;background:var(--surface2);border-radius:4px;height:6px;overflow:hidden">
          <div style="width:${l}%;height:100%;background:${l>90?"var(--red)":l>70?"var(--accent)":"var(--green)"}"></div>
        </div>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
          Free models: ${(r.free_tier_models||[]).join(", ")||"none"}
        </div>`}else s=`
        <div style="font-size:1.5rem;font-weight:700;color:${n>=1?"var(--green)":n>=.1?"var(--accent)":"var(--red)"}">
          $${n.toFixed(4)}
        </div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.25rem">Available balance</div>`;e.innerHTML=`
      <div style="max-width:580px">
        <div class="settings-section-title">Billing &amp; Balance</div>

        <!-- Balance card -->
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                    padding:1rem 1.25rem;margin-bottom:1.5rem">
          <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.05em">Current Balance</div>
          ${s}
          ${t?"":`
          <div style="margin-top:1rem">
            <button onclick="window._billingAddPayment()"
              style="padding:0.45rem 1rem;background:var(--surface);border:1px solid var(--border);
                     border-radius:6px;color:var(--text2);font-size:0.75rem;cursor:pointer">
              + Add Payment (Coming Soon)
            </button>
          </div>`}
        </div>

        ${t?`
        <!-- Admin note -->
        <div style="background:rgba(255,107,53,0.07);border:1px solid rgba(255,107,53,0.2);
                    border-radius:var(--radius);padding:0.75rem 1rem;margin-bottom:1.5rem;font-size:0.72rem;color:var(--text2)">
          💡 Manage API keys, pricing, coupons, and user credits in the
          <a href="#" onclick="window._nav('admin');return false" style="color:var(--accent)">Admin Panel</a>.
        </div>
        `:`
        <!-- Apply coupon -->
        <div style="margin-bottom:1.5rem">
          <div style="font-size:0.78rem;font-weight:600;margin-bottom:0.6rem">Apply Coupon Code</div>
          <div style="display:flex;gap:0.5rem">
            <input id="billing-coupon" placeholder="Enter coupon code" style="flex:1;
              background:var(--bg);border:1px solid var(--border);border-radius:6px;
              color:var(--text);font-size:0.82rem;padding:0.45rem 0.65rem" />
            <button onclick="window._applyCoupon()"
              style="padding:0.45rem 1rem;background:var(--accent);border:none;border-radius:6px;
                     color:#fff;font-size:0.8rem;font-weight:600;cursor:pointer">Apply</button>
          </div>
          <div id="coupon-status" style="font-size:0.65rem;margin-top:0.35rem;color:var(--muted)"></div>
        </div>
        `}

        <!-- Transaction history -->
        <div>
          <div style="font-size:0.78rem;font-weight:600;margin-bottom:0.6rem">Transaction History</div>
          <div id="billing-history-body">
            <div style="color:var(--muted);font-size:0.72rem">Loading…</div>
          </div>
        </div>
      </div>
    `,window._billingAddPayment=async()=>{try{const l=await m.billingAddPayment();p(l.message,"info")}catch(l){p(l.message,"error")}},window._applyCoupon=async()=>{const l=document.getElementById("billing-coupon")?.value.trim(),c=document.getElementById("coupon-status");if(!l){c&&(c.textContent="Enter a coupon code",c.style.color="var(--red)");return}try{const g=await m.billingApplyCoupon(l);c&&(c.textContent=`✓ ${g.message}`,c.style.color="var(--green)"),p(g.message,"success"),document.getElementById("billing-coupon").value="",window._updateBalance?.().catch(()=>{}),await Eo(e)}catch(g){c&&(c.textContent=`✕ ${g.message}`,c.style.color="var(--red)"),p(g.message,"error")}};const d=document.getElementById("billing-history-body");try{const c=((await m.billingHistory()).transactions||[]).slice().reverse();c.length?d&&(d.innerHTML=`
          <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
            <thead>
              <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Date</th>
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Type</th>
                <th style="text-align:right;padding:0.3rem 0.4rem;font-weight:500">Amount</th>
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Description</th>
              </tr>
            </thead>
            <tbody>
              ${c.map(g=>{const f=g.type?.includes("credit"),u=g.amount_usd||0;return`
                  <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.35rem 0.4rem;color:var(--muted)">${g.ts?new Date(g.ts).toLocaleDateString():""}</td>
                    <td style="padding:0.35rem 0.4rem">${g.type||""}</td>
                    <td style="padding:0.35rem 0.4rem;text-align:right;color:${f?"var(--green)":"var(--text2)"}">
                      ${f?"+":"−"}$${u.toFixed(4)}
                    </td>
                    <td style="padding:0.35rem 0.4rem;color:var(--text2)">${g.description||""}</td>
                  </tr>`}).join("")}
            </tbody>
          </table>
        `):d&&(d.innerHTML='<div style="color:var(--muted);font-size:0.72rem">No transactions yet.</div>')}catch{d&&(d.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Could not load history.</div>')}}catch(r){e.innerHTML=`<div style="color:var(--red);font-size:0.75rem">Could not load billing: ${r.message}</div>`}}function Rr(e){if(x.user?.is_admin||x.user?.role==="admin"){e.innerHTML=`
      <div>
        <div class="settings-section-title">API Keys</div>
        <div class="settings-section-desc">As an admin, API keys are managed server-side in the Admin Panel.</div>
        <div style="background:rgba(255,107,53,0.07);border:1px solid rgba(255,107,53,0.2);
                    border-radius:var(--radius);padding:0.75rem 1rem;margin-top:0.75rem;font-size:0.75rem;color:var(--text2)">
          💡 Go to the <a href="#" onclick="window._nav('admin');return false" style="color:var(--accent)">Admin Panel → API Keys</a>
          to set server-side API keys for all users.
        </div>
      </div>
    `;return}e.innerHTML=`
    <div>
      <div class="settings-section-title">API Keys</div>
      <div class="settings-section-desc">Keys are encrypted at rest with AES-256-GCM. They are never sent anywhere except the respective LLM API.</div>

      <div class="lock-banner">
        <span class="lock-icon">🔐</span>
        <div>
          <div style="font-weight:700;font-size:0.72rem;margin-bottom:0.15rem">Encrypted Storage</div>
          <div>All API keys are stored in an encrypted file on your local machine. Enter your master password to save changes.</div>
        </div>
      </div>

      <div class="api-key-grid">
        ${ko.map(r=>`
          <div class="api-key-row">
            <div class="api-key-label">
              <div class="llm-color-dot" style="background:${r.color}"></div>
              <span>${r.label}</span>
            </div>
            <div class="key-input-wrap">
              <input
                class="key-input"
                type="password"
                id="key-${r.id}"
                placeholder="${r.placeholder}"
                value="${x.settings.api_keys?.[r.id]||""}"
                oninput="window._onKeyChange('${r.id}', this.value)"
              />
              <span class="key-toggle" onclick="window._toggleKeyVisible('${r.id}')">👁</span>
            </div>
            <div class="key-status ${x.settings.api_keys?.[r.id]?"set":""}" id="kstatus-${r.id}"></div>
          </div>
        `).join("")}
      </div>

      <div class="password-section">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.75rem">
          Enter your master password to save. If this is your first time, this becomes your password.
        </div>
        <div style="display:flex;gap:0.75rem;align-items:center">
          <div class="key-input-wrap" style="flex:1">
            <input class="key-input" type="password" id="save-pwd" placeholder="Master password..." />
            <span class="key-toggle" onclick="window._togglePwdVisible()">👁</span>
          </div>
          <button class="btn btn-primary" onclick="window._saveKeys()">Save Encrypted</button>
        </div>
        <div id="save-status" style="font-size:0.68rem;margin-top:0.5rem;color:var(--muted)"></div>
      </div>
    </div>
  `,window._keyDraft={...x.settings.api_keys||{}},window._onKeyChange=(r,o)=>{window._keyDraft[r]=o;const n=document.getElementById(`kstatus-${r}`);n&&(n.className=`key-status ${o?"set":""}`)},window._toggleKeyVisible=r=>{const o=document.getElementById(`key-${r}`);o&&(o.type=o.type==="password"?"text":"password")},window._togglePwdVisible=()=>{const r=document.getElementById("save-pwd");r&&(r.type=r.type==="password"?"text":"password")},window._saveKeys=async()=>{const r=document.getElementById("save-pwd").value;if(!r){p("Enter your master password","error");return}const o={...x.settings,api_keys:window._keyDraft},n=document.getElementById("save-status");try{await We("save_settings",{settings:o,password:r}),U({settings:o,masterPassword:r}),n&&(n.textContent="✓ Settings saved and encrypted"),n&&(n.style.color="var(--green)"),p("API keys saved (encrypted)","success"),await Wi(o.api_keys,o.backend_url)}catch(i){n&&(n.textContent=`✕ ${i}`),n&&(n.style.color="var(--red)"),p(`Save failed: ${i}`,"error")}}}async function Wi(e,t){const r=`# Generated by AgentDesk — do not edit manually
ANTHROPIC_API_KEY=${e.claude||""}
OPENAI_API_KEY=${e.openai||""}
DEEPSEEK_API_KEY=${e.deepseek||""}
GEMINI_API_KEY=${e.gemini||""}
GROK_API_KEY=${e.grok||""}
BACKEND_URL=${t||"http://localhost:8000"}
`;try{await We("write_linked_file",{path:"../backend/.env",content:r})}catch{}}async function Co(e){const t=(x.settings?.backend_url||"http://localhost:8000").replace(/\/$/,"");let r={},o={projects:[],active:""};try{const[n,i]=await Promise.all([fetch(`${t}/config/`),fetch(`${t}/projects/`)]);r=await n.json(),o=await i.json()}catch{}e.innerHTML=`
    <div>
      <div class="settings-section-title">Workspace Settings</div>
      <div class="settings-section-desc">Configure workspace directory and active project.</div>

      <div class="field-group" style="margin-top:1rem">
        <div class="field-label">Workspace Directory</div>
        <div style="display:flex;gap:8px">
          <input class="field-input" id="ws-dir" value="${r.workspace_dir||""}"
            placeholder="/path/to/workspace" style="flex:1" />
          <button class="btn btn-ghost" onclick="window._browseWorkspaceDir()">Browse</button>
        </div>
      </div>

      <div class="field-group">
        <div class="field-label">Active Project</div>
        <select class="field-select" id="ws-project" onchange="window._switchProject(this.value)">
          ${(o.projects||[]).map(n=>`<option value="${n.name}" ${n.name===o.active?"selected":""}>${n.name}${n.active?" ← active":""}</option>`).join("")}
        </select>
      </div>

      <div class="field-group">
        <div class="field-label">Code Directory</div>
        <input class="field-input" id="ws-codedir" value="${r.code_dir||""}"
          placeholder="/path/to/your/code" />
      </div>

      <div style="margin-top:1rem;display:flex;gap:8px">
        <button class="btn btn-primary" onclick="window._saveWorkspaceSettings()">Save</button>
        <button class="btn btn-ghost" onclick="window._newProject()">New Project...</button>
      </div>

      <div style="margin-top:2rem">
        <div class="field-label">Provider Availability</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
          ${Object.entries(r.providers_available||{}).map(([n,i])=>`<span style="padding:4px 10px;border-radius:12px;font-size:12px;background:${i?"var(--green)":"var(--surface)"};color:${i?"#000":"var(--muted)"}">${n} ${i?"✓":"✗"}</span>`).join("")}
        </div>
      </div>
    </div>
  `,window._browseWorkspaceDir=async()=>{if(window.electronAPI){const n=await window.electronAPI.openDirectory();n&&(document.getElementById("ws-dir").value=n)}},window._switchProject=async n=>{await fetch(`${t}/projects/switch/${n}`,{method:"POST"}),p(`Switched to project: ${n}`,"success")},window._saveWorkspaceSettings=()=>{p("Workspace settings saved (restart backend to apply directory changes)","info")},window._newProject=async()=>{const n=prompt("New project name:");if(!n)return;const i=prompt("Template (blank, python_api, quant_notebook, ui_app):","blank");try{const s=await(await fetch(`${t}/projects/`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,template:i||"blank"})})).json();s.created?(p(`Project created: ${n}`,"success"),Co(e)):p(s.detail||"Failed to create project","error")}catch(a){p(`Error: ${a.message}`,"error")}}}function qi(e){e.innerHTML=`
    <div>
      <div class="settings-section-title">Default Models</div>
      <div class="settings-section-desc">Select the default model for each LLM provider used in agent workflows.</div>

      <div style="display:flex;flex-direction:column;gap:0.75rem">
        ${ko.map(t=>`
          <div style="display:grid;grid-template-columns:120px 1fr;gap:0.75rem;align-items:center">
            <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.75rem">
              <div style="width:8px;height:8px;border-radius:50%;background:${t.color}"></div>
              ${t.label}
            </div>
            <select class="field-select" onchange="window._setModel('${t.id}',this.value)">
              ${t.models.map(r=>`
                <option value="${r}" ${x.settings.default_models?.[t.id]===r?"selected":""}>${r}</option>
              `).join("")}
            </select>
          </div>
        `).join("")}
      </div>

      <div style="margin-top:1.25rem">
        <button class="btn btn-primary" onclick="window._saveModels()">Save Model Settings</button>
      </div>
    </div>
  `,window._modelDraft={...x.settings.default_models||{}},window._setModel=(t,r)=>{window._modelDraft[t]=r},window._saveModels=async()=>{const t=x.masterPassword;if(!t){p("Unlock settings first (enter master password in API Keys tab)","error");return}const r={...x.settings,default_models:window._modelDraft};await We("save_settings",{settings:r,password:t}),U({settings:r}),p("Model settings saved","success")}}function Gi(e){e.innerHTML=`
    <div>
      <div class="settings-section-title">Backend Connection</div>
      <div class="settings-section-desc">Configure the Python FastAPI backend URL. The backend handles LLM calls, vector store, and chat history.</div>

      <div class="field-group">
        <div class="field-label">Backend URL</div>
        <input class="field-input" id="backend-url" value="${x.settings.backend_url||"http://localhost:8000"}" placeholder="http://localhost:8000" />
      </div>

      <div style="display:flex;gap:0.75rem;align-items:center;margin-top:1rem">
        <button class="btn btn-ghost" onclick="window._testBackend()">Test Connection</button>
        <button class="btn btn-primary" onclick="window._saveBackendUrl()">Save</button>
        <div id="backend-status" style="font-size:0.68rem;color:var(--muted)"></div>
      </div>

      <div style="margin-top:2rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.75rem">Backend quick-start:</div>
        <pre style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;font-size:0.7rem;color:var(--green);line-height:1.7">cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000</pre>
      </div>
    </div>
  `,window._testBackend=async()=>{const t=document.getElementById("backend-url").value,r=document.getElementById("backend-status");try{const n=await(await fetch(`${t}/health`)).json();r.textContent=`✓ Online — v${n.version}`,r.style.color="var(--green)",U({backendOnline:!0});const i=document.getElementById("status-dot");i&&(i.className="status-dot online")}catch{r.textContent="✕ Cannot connect",r.style.color="var(--red)",U({backendOnline:!1})}},window._saveBackendUrl=async()=>{const t=document.getElementById("backend-url").value,r=x.masterPassword,o={...x.settings,backend_url:t};r&&await We("save_settings",{settings:o,password:r}),U({settings:o}),p("Backend URL saved","success")}}function Vi(e){e.innerHTML=`
    <div>
      <div class="settings-section-title">Security</div>
      <div class="settings-section-desc">Manage your master password and encryption settings.</div>

      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin-bottom:1.5rem">
        <div style="font-size:0.72rem;font-weight:700;margin-bottom:0.5rem">Encryption Details</div>
        <div style="font-size:0.68rem;color:var(--text2);line-height:1.8">
          <div>Algorithm: <span style="color:var(--blue)">AES-256-GCM</span></div>
          <div>Key derivation: <span style="color:var(--blue)">SHA-256 with per-file salt</span></div>
          <div>Storage: <span style="color:var(--blue)">Local encrypted file</span></div>
          <div>Keys never leave: <span style="color:var(--green)">Your machine</span></div>
        </div>
      </div>

      <div style="margin-bottom:1.5rem">
        <div style="font-size:0.78rem;font-weight:700;margin-bottom:0.75rem">Change Master Password</div>
        <div class="field-group">
          <div class="field-label">Current password</div>
          <input class="field-input" type="password" id="sec-current" placeholder="Current master password" />
        </div>
        <div class="field-group">
          <div class="field-label">New password</div>
          <input class="field-input" type="password" id="sec-new" placeholder="New master password" />
        </div>
        <div class="field-group">
          <div class="field-label">Confirm new password</div>
          <input class="field-input" type="password" id="sec-confirm" placeholder="Confirm new password" />
        </div>
        <button class="btn btn-primary" onclick="window._changePassword()">Change Password</button>
      </div>

      <div style="padding-top:1.5rem;border-top:1px solid var(--border)">
        <div style="font-size:0.78rem;font-weight:700;color:var(--red);margin-bottom:0.5rem">Danger Zone</div>
        <div style="font-size:0.68rem;color:var(--text2);margin-bottom:0.75rem">This will permanently delete all encrypted settings and API keys.</div>
        <button class="btn btn-danger" onclick="window._clearSettings()">Clear All Settings</button>
      </div>
    </div>
  `,window._changePassword=async()=>{const t=document.getElementById("sec-current").value,r=document.getElementById("sec-new").value,o=document.getElementById("sec-confirm").value;if(!t||!r){p("Fill in all fields","error");return}if(r!==o){p("Passwords do not match","error");return}try{const n=await We("load_settings",{password:t});await We("save_settings",{settings:n,password:r}),U({masterPassword:r}),p("Password changed","success")}catch(n){p(`Error: ${n}`,"error")}},window._clearSettings=async()=>{if(confirm("This will delete all API keys and settings. Are you sure?"))try{await We("save_settings",{settings:{api_keys:{},default_models:{claude:"claude-sonnet-4-6",deepseek:"deepseek-chat",gemini:"gemini-1.5-flash",grok:"grok-3",openai:"gpt-4o"},ui:{theme:"dark",font_size:13,sidebar_width:220},backend_url:or},password:"default"}),p("Settings cleared","info")}catch(t){p(`Error: ${t}`,"error")}}}function Yi(){try{const e=localStorage.getItem("aicli_token");if(!e)return!1;const t=e.split(".")[1].replace(/-/g,"+").replace(/_/g,"/"),r=JSON.parse(atob(t));return r.is_admin===!0||r.role==="admin"}catch{return!1}}async function ct(e){const t=Yi();e.innerHTML='<div style="color:var(--muted);font-size:0.72rem">Loading roles…</div>';let r=[],o=!1;try{const n=await m.agentRoles.list();r=n.roles||[],o=n.is_admin||t}catch(n){e.innerHTML=`<div style="color:var(--red);font-size:0.72rem">Error: ${X(n.message)}</div>`;return}e.innerHTML=`
    <div>
      <div class="settings-section-title">Agent Roles</div>
      <div class="settings-section-desc">
        Reusable LLM personas used in workflow nodes.
        ${o?"As admin you can view and edit system prompts.":"Role names and descriptions are shown. System prompts are admin-only."}
      </div>

      ${o?`
      <div style="margin-bottom:1rem">
        <button class="btn btn-primary btn-sm" onclick="window._rolesShowCreate()">+ New Role</button>
      </div>
      <div id="roles-create-form" style="display:none;margin-bottom:1rem;padding:0.75rem;
           background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius)">
        <div style="font-size:0.72rem;font-weight:600;margin-bottom:0.5rem">New Role</div>
        <div class="field-group"><div class="field-label">Name</div>
          <input class="field-input" id="nr-name" placeholder="e.g. Data Engineer" /></div>
        <div class="field-group"><div class="field-label">Description (shown to all users)</div>
          <input class="field-input" id="nr-desc" placeholder="Short description of what this role does" /></div>
        <div class="field-group"><div class="field-label">Provider</div>
          <select class="field-input" id="nr-provider">
            ${["claude","openai","deepseek","gemini","grok"].map(n=>`<option value="${n}">${n}</option>`).join("")}
          </select></div>
        <div class="field-group"><div class="field-label">Model (blank = default)</div>
          <input class="field-input" id="nr-model" placeholder="" /></div>
        <div class="field-group"><div class="field-label">System Prompt</div>
          <textarea class="field-input" id="nr-prompt" rows="5"
            style="font-family:var(--font);font-size:0.72rem;resize:vertical"
            placeholder="You are a…"></textarea></div>
        <div style="display:flex;gap:0.5rem;margin-top:0.5rem">
          <button class="btn btn-primary btn-sm" onclick="window._rolesSaveCreate()">Create</button>
          <button class="btn btn-ghost btn-sm" onclick="window._rolesHideCreate()">Cancel</button>
        </div>
      </div>`:""}

      <div id="roles-list">
        ${r.length===0?'<div style="color:var(--muted);font-size:0.72rem;padding:1rem">No roles found.</div>':r.map(n=>Ki(n,o)).join("")}
      </div>
    </div>
  `,window._rolesShowCreate=()=>{document.getElementById("roles-create-form").style.display=""},window._rolesHideCreate=()=>{document.getElementById("roles-create-form").style.display="none"},window._rolesSaveCreate=async()=>{const n=document.getElementById("nr-name")?.value.trim(),i=document.getElementById("nr-desc")?.value.trim()||"",a=document.getElementById("nr-provider")?.value||"claude",s=document.getElementById("nr-model")?.value.trim()||"",d=document.getElementById("nr-prompt")?.value||"";if(!n){p("Name required","error");return}try{await m.agentRoles.create({name:n,description:i,provider:a,model:s,system_prompt:d}),p(`Role "${n}" created`,"success"),ct(e)}catch(l){p("Create failed: "+l.message,"error")}},window._rolesDelete=async(n,i)=>{if(confirm(`Delete role "${i}"?`))try{await m.agentRoles.delete(n),p("Role deleted","success"),ct(e)}catch(a){p("Delete failed: "+a.message,"error")}},window._rolesToggleEdit=n=>{const i=document.getElementById(`role-edit-${n}`);i&&(i.style.display=i.style.display==="none"?"":"none")},window._rolesSaveEdit=async n=>{const i=document.getElementById(`re-desc-${n}`)?.value.trim()||"",a=document.getElementById(`re-prov-${n}`)?.value||"claude",s=document.getElementById(`re-model-${n}`)?.value.trim()||"",d=document.getElementById(`re-prompt-${n}`)?.value||"",l=document.getElementById(`re-note-${n}`)?.value.trim()||"";try{await m.agentRoles.patch(n,{description:i,provider:a,model:s,system_prompt:d,note:l}),p("Role updated","success"),ct(e)}catch(c){p("Update failed: "+c.message,"error")}},window._rolesShowVersions=async(n,i)=>{const a=document.getElementById(`role-versions-${n}`);if(a){if(a.style.display!=="none"){a.style.display="none";return}a.innerHTML='<div style="color:var(--muted);font-size:0.65rem;padding:0.5rem">Loading…</div>',a.style.display="";try{const d=(await m.agentRoles.versions(n)).versions||[];if(!d.length){a.innerHTML='<div style="color:var(--muted);font-size:0.65rem;padding:0.5rem">No version history.</div>';return}a.innerHTML=d.map(l=>`
        <div style="border-bottom:1px solid var(--border);padding:0.4rem 0;font-size:0.65rem">
          <div style="display:flex;align-items:center;gap:0.5rem">
            <span style="color:var(--muted)">${(l.changed_at||"").slice(0,16)}</span>
            <span style="color:var(--text2)">${X(l.changed_by||"?")}</span>
            ${l.note?`<span style="color:var(--muted);font-style:italic">${X(l.note)}</span>`:""}
            <button onclick="window._rolesRestore(${n},${l.id},'${X(i)}')"
              style="margin-left:auto;font-size:0.6rem;padding:0.1rem 0.4rem;background:var(--surface2);
                     border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                     color:var(--text2);font-family:var(--font)">Restore</button>
          </div>
          <div style="color:var(--muted);font-size:0.62rem;margin-top:0.2rem;
                      white-space:pre-wrap;max-height:60px;overflow:hidden;font-family:monospace">${X((l.system_prompt||"").slice(0,200))}</div>
        </div>`).join("")}catch(s){a.innerHTML=`<div style="color:var(--red);font-size:0.65rem;padding:0.5rem">${X(s.message)}</div>`}}},window._rolesRestore=async(n,i,a)=>{if(confirm(`Restore role "${a}" to this version?`))try{await m.agentRoles.restore(n,i),p("Role restored","success"),ct(e)}catch(s){p("Restore failed: "+s.message,"error")}}}function Ki(e,t){const o={claude:"#e67e22",openai:"#27ae60",deepseek:"#2980b9",gemini:"#16a085",grok:"#8e44ad"}[e.provider]||"#888";return`
    <div style="border:1px solid var(--border);border-radius:var(--radius);margin-bottom:0.5rem;
                background:var(--surface)">
      <div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.75rem">
        <span style="font-size:0.75rem;font-weight:600;color:var(--text);flex:1">${X(e.name)}</span>
        <span style="font-size:0.6rem;color:#fff;background:${o};padding:0.1rem 0.45rem;
                     border-radius:8px;white-space:nowrap">${X(e.provider)}${e.model?" · "+X(e.model.split("-").slice(0,3).join("-")):""}</span>
        ${t?`
          <button onclick="window._rolesToggleEdit(${e.id})"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font)">Edit</button>
          <button onclick="window._rolesShowVersions(${e.id},'${X(e.name)}')"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font)">History</button>
          <button onclick="window._rolesDelete(${e.id},'${X(e.name)}')"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:none;
                   border:1px solid var(--red,#e74c3c);border-radius:var(--radius);cursor:pointer;
                   color:var(--red,#e74c3c);font-family:var(--font)">✕</button>`:""}
      </div>
      <div style="padding:0 0.75rem 0.5rem;font-size:0.67rem;color:var(--muted)">${X(e.description)}</div>

      ${t?`
      <!-- Edit form (hidden by default) -->
      <div id="role-edit-${e.id}" style="display:none;border-top:1px solid var(--border);
           padding:0.75rem;background:var(--surface2)">
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">Description</div>
          <input class="field-input" id="re-desc-${e.id}" value="${X(e.description)}" /></div>
        <div style="display:flex;gap:0.5rem">
          <div class="field-group" style="flex:1">
            <div class="field-label" style="font-size:0.6rem">Provider</div>
            <select class="field-input" id="re-prov-${e.id}">
              ${["claude","openai","deepseek","gemini","grok"].map(n=>`<option value="${n}" ${e.provider===n?"selected":""}>${n}</option>`).join("")}
            </select></div>
          <div class="field-group" style="flex:1">
            <div class="field-label" style="font-size:0.6rem">Model</div>
            <input class="field-input" id="re-model-${e.id}" value="${X(e.model||"")}" /></div>
        </div>
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">System Prompt</div>
          <textarea class="field-input" id="re-prompt-${e.id}" rows="6"
            style="font-family:monospace;font-size:0.68rem;resize:vertical">${X(e.system_prompt||"")}</textarea></div>
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">Change note (optional)</div>
          <input class="field-input" id="re-note-${e.id}" placeholder="What changed and why?" /></div>
        <div style="display:flex;gap:0.5rem;margin-top:0.25rem">
          <button class="btn btn-primary btn-sm" onclick="window._rolesSaveEdit(${e.id})">Save</button>
          <button class="btn btn-ghost btn-sm" onclick="window._rolesToggleEdit(${e.id})">Cancel</button>
        </div>
      </div>
      <!-- Version history panel -->
      <div id="role-versions-${e.id}" style="display:none;border-top:1px solid var(--border);
           padding:0.5rem 0.75rem;background:var(--bg);max-height:180px;overflow-y:auto"></div>
      `:""}
    </div>
  `}const Se=100;function at(e){const t=(x.settings?.backend_url||"http://localhost:8000").replace(/\/$/,""),r=x.currentProject?.name,o=e.includes("?")?"&":"?",n=r?`${o}project=${encodeURIComponent(r)}`:"";return`${t}${e}${n}`}class Xi{constructor(t){this.container=t,this.activeTab="chat",this._cachedProject=null,this._histData=null,this._commitData=null,this._tagCache=null,this._tagCacheMap={},this._entryTags={},this._chatGhBase="",this._ghBase="",this._histPage=1,this._commitPage=1,this._histFilter={source:"",phase:"",query:""},this._commitFilter={phase:""},this._render(),this._loadTab("chat")}_render(){const t=["chat","commits","runs","evals"];this.container.innerHTML=`
      <div class="history-layout" style="display:flex;flex-direction:column;height:100%">
        <div class="tab-bar" style="display:flex;gap:4px;padding:6px 10px;border-bottom:1px solid var(--border);align-items:center;flex-wrap:wrap">
          ${t.map(r=>`<button class="tab-btn" data-tab="${r}"
              style="padding:5px 12px;border-radius:6px;border:1px solid var(--border);cursor:pointer;background:${this.activeTab===r?"var(--accent)":"var(--surface)"};font-size:12px"
              onclick="window._historyView._loadTab('${r}')">
              ${r.charAt(0).toUpperCase()+r.slice(1)}
            </button>`).join("")}
          <div style="flex:1"></div>
          <!-- Pagination controls — updated by _renderPageBars() -->
          <div id="hist-nav-bar" style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)"></div>
          <input id="history-search" placeholder="Search…"
            style="padding:3px 7px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text);width:130px;font-size:12px;margin-left:6px" />
        </div>
        <div id="history-content" style="flex:1;overflow-y:auto;padding:12px;min-height:0"></div>
      </div>
    `,window._historyView=this,document.getElementById("history-search")?.addEventListener("input",r=>{this._filterContent(r.target.value)})}async _loadTab(t){this.activeTab=t,document.querySelectorAll(".tab-btn").forEach(n=>{n.style.background=n.dataset.tab===t?"var(--accent)":"var(--surface)"});const r=document.getElementById("history-content");if(!r)return;const o=x.currentProject?.name||"";if(o!==this._cachedProject&&(this._cachedProject=o,this._histData=null,this._commitData=null,this._tagCache=null,this._tagCacheMap={},this._entryTags={}),t==="chat"&&this._histData){this._renderChatContainer(r);return}if(t==="commits"&&this._commitData){this._renderCommitsContainer(r);return}if(t!=="chat"){const n=document.getElementById("hist-nav-bar");n&&(n.innerHTML="")}r.innerHTML=`<div style='padding:20px;color:var(--muted);display:flex;align-items:center;gap:8px'>
      <span id="hist-loading-spinner" style="display:inline-block;animation:spin 1s linear infinite">⟳</span>
      <span id="hist-loading-msg">Loading…</span>
    </div>`;try{t==="chat"?await this._renderChat(r):t==="commits"?await this._renderCommits(r):t==="runs"?await this._renderRuns(r):t==="evals"&&await this._renderEvals(r)}catch(n){r.innerHTML=`<div style="color:red;padding:20px">Error: ${n.message}</div>`}}_setLoadingMsg(t){const r=document.getElementById("hist-loading-msg");r&&(r.textContent=t)}async _renderChat(t){const r=x.currentProject?.name||"";this._setLoadingMsg("Fetching history entries…");const o=Date.now(),[n,i,a]=await Promise.all([fetch(at(`/history/chat?limit=500&_t=${o}`)).then(l=>l.json()),m.getProjectConfig(r).catch(()=>({})),m.entities.getSourceTags(r).catch(()=>({}))]),s=n.total||0;this._histData=n,this._histPage=1;for(const[l,c]of Object.entries(a||{}))this._entryTags[l]=c;let d=(i.github_repo||"").replace(/\.git$/,"").replace(/\/$/,"");d.startsWith("git@")&&(d=d.replace(/^git@([^:]+):/,"https://$1/")),this._chatGhBase=d,this._setLoadingMsg(`Building tag index (${s} entries)…`),await this._buildTagCache(r),this._renderChatContainer(t),this._commitData||m.historyCommits(r,500).then(l=>{this._commitData=l}).catch(()=>{this._commitData={commits:[]}})}_renderChatContainer(t){const r=this._histData?.entries||[],o=this._histData?.total||r.length,n=this._histData?.filtered||0,i=this._histData?.has_more||!1,a=r.filter(c=>!c.tags?.some(g=>g.startsWith("phase:"))).length;t.innerHTML=`
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding:5px 8px;
                  background:var(--surface);border-radius:6px;flex-wrap:wrap;font-size:11px">
        <select id="hist-filter-source" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
          <option value="">All sources</option>
          <option value="claude_cli">Claude CLI</option>
          <option value="ui">UI</option>
          <option value="workflow">Workflow</option>
        </select>
        <select id="hist-filter-phase" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
          <option value="">All phases</option>
          <option value="discovery">Discovery</option>
          <option value="development">Development</option>
          <option value="testing">Testing</option>
          <option value="review">Review</option>
          <option value="production">Production</option>
          <option value="maintenance">Maintenance</option>
          <option value="bugfix">Bug Fix</option>
        </select>
        ${n>0?`<span style="color:var(--muted)">${n} noise hidden</span>`:""}
        ${i?`<span style="color:var(--muted)">showing ${r.length} of ${o}</span>
          <button onclick="window._historyView._loadMore()"
            style="padding:2px 7px;border:1px solid var(--accent);border-radius:3px;cursor:pointer;
                   background:var(--surface);font-size:11px;color:var(--accent)">Load all</button>`:""}
        <div style="flex:1"></div>
        ${a>0?`<span style="color:#e74c3c;font-weight:600">${a} untagged</span>`:'<span style="color:green">All tagged ✓</span>'}
        <button onclick="window._historyView._refreshHistory()"
          style="padding:2px 7px;border:1px solid var(--border);border-radius:3px;cursor:pointer;background:var(--surface);font-size:11px;color:var(--muted)"
          title="Reload from server">↻</button>
      </div>
      <div id="hist-chat-groups"></div>`;const s=document.getElementById("hist-filter-source"),d=document.getElementById("hist-filter-phase");s&&this._histFilter.source&&(s.value=this._histFilter.source),d&&this._histFilter.phase&&(d.value=this._histFilter.phase);const l=document.getElementById("history-search");l&&this._histFilter.query&&(l.value=this._histFilter.query),this._applyFilter()}async _refreshHistory(){this._histData=null,this._commitData=null,this._entryTags={};const t=document.getElementById("history-content");t&&(t.innerHTML=`<div style='padding:20px;color:var(--muted);display:flex;align-items:center;gap:8px'>
        <span style="display:inline-block;animation:spin 1s linear infinite">⟳</span>
        <span id="hist-loading-msg">Reloading…</span>
      </div>`,await this._renderChat(t))}async _loadMore(){x.currentProject?.name,this._histData?.entries;const t=Date.now(),r=document.getElementById("history-content");if(r){const o=r.querySelector('button[onclick*="_loadMore"]');o&&(o.disabled=!0,o.textContent="…")}try{const o=await fetch(at(`/history/chat?limit=0&_t=${t}`)).then(n=>n.json());this._histData=o,this._histPage=1,this._renderChatContainer(r)}catch{if(r){const n=r.querySelector('button[onclick*="_loadMore"]');n&&(n.disabled=!1,n.textContent="Load all")}}}_applyFilter(){const t=document.getElementById("hist-filter-source")?.value||"",r=document.getElementById("hist-filter-phase")?.value||"",o=document.getElementById("history-search")?.value||"";this._histFilter={source:t,phase:r,query:o},this._histPage=1;const n=document.getElementById("hist-chat-groups");n&&this._renderChatGroups(n)}_renderChatGroups(t){if(!t)return;const{source:r,phase:o,query:n}=this._histFilter;let i=this._histData?.entries||[];if(r&&(i=i.filter(u=>(u.source||"ui")===r)),o&&(i=i.filter(u=>u.tags?.includes("phase:"+o))),n){const u=n.toLowerCase();i=i.filter(h=>(h.user_input||"").toLowerCase().includes(u)||(h.output||"").toLowerCase().includes(u))}const a=i.length;if(!a){t.innerHTML="<div style='padding:20px;color:var(--muted)'>No entries match the current filter.</div>",this._renderPageBars(0,0);return}const s=(this._histPage-1)*Se,d=i.slice(s,s+Se),l={},c={};for(const u of this._commitData?.commits||[])u.prompt_source_id?(l[u.prompt_source_id]||(l[u.prompt_source_id]=[]),l[u.prompt_source_id].push(u)):u.session_id&&(c[u.session_id]||(c[u.session_id]=[]),c[u.session_id].push(u));const g=[];for(const u of d){const h=g[g.length-1];h&&h.session_id===u.session_id?h.entries.push(u):g.push({session_id:u.session_id,entries:[u]})}const f=this._chatGhBase||"";t.innerHTML=g.map(u=>{const h=u.session_id||"",_=h?c[h]||[]:[],C=_.length?`
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;
                    padding:5px 8px;background:var(--surface2);border-radius:4px;margin-bottom:6px;font-size:11px">
          <span style="color:var(--muted);font-weight:600;white-space:nowrap">⑂ ${_.length} unlinked:</span>
          ${_.map(v=>{const b=(v.commit_hash||"").slice(0,8),z=(v.commit_msg||"").slice(0,60),y=(v.committed_at||"").slice(0,10);return f&&v.commit_hash?`<a href="${f}/commit/${this._escapeHtml(v.commit_hash)}" target="_blank"
                    style="font-family:monospace;color:var(--accent);text-decoration:none;white-space:nowrap"
                    title="${this._escapeHtml(z)} · ${y}">${b} ↗</a>`:`<span style="font-family:monospace;color:var(--accent);white-space:nowrap"
                       title="${this._escapeHtml(z)} · ${y}">${b}</span>`}).join("")}
        </div>`:"",S=u.entries.map((v,b)=>{const z=!v.tags?.some(W=>W.startsWith("phase:")),y=z?"#e74c3c":"var(--border)",$=`he-${(h||"ns").slice(0,6)}-${s+b}`,E=`ha-${$}`,R=v.ts||"",F=(this._entryTags[R]||[]).map(W=>{const ae=this._tagColor(W);return`<span data-tag="${this._escapeHtml(W)}"
                 style="font-size:10px;background:${ae}22;color:${ae};border:1px solid ${ae}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px">
             ${this._escapeHtml(W)}
             <button onclick="event.stopPropagation();window._historyView._removeTag('${this._escapeHtml(R)}','${this._escapeHtml(W)}','${E}')"
               style="border:none;background:none;cursor:pointer;color:${ae};font-size:9px;padding:0 1px;line-height:1;opacity:.7"
               title="Remove tag">✕</button>
           </span>`}).join(""),M=(W,ae)=>`<button onclick="navigator.clipboard.writeText(document.getElementById('${W}').innerText).then(()=>{this.textContent='✓ copied';setTimeout(()=>this.textContent='⎘ copy',1200)})"
             style="font-size:10px;padding:1px 5px;border:1px solid var(--border);border-radius:3px;
                    cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap;margin-left:4px">⎘ copy</button>`,Q=v.output?`<div style="margin-top:6px">
              <div style="display:flex;align-items:center;gap:4px;margin-bottom:2px">
                <span style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">Response</span>
                ${M(`${$}-resp`)}
                <span style="font-size:11px;color:var(--accent);cursor:pointer;user-select:none;margin-left:2px"
                    onclick="const el=document.getElementById('${$}-resp');
                             const collapsed=el.dataset.collapsed!=='false';
                             el.style.maxHeight=collapsed?'none':'200px';
                             el.dataset.collapsed=collapsed?'false':'true';
                             this.textContent=collapsed?'▲ collapse':'▼ expand'">▼ expand</span>
              </div>
              <div id="${$}-resp" data-collapsed="true"
                style="color:var(--muted);font-size:12px;border-left:2px solid var(--border);
                       padding-left:8px;white-space:pre-wrap;word-break:break-word;
                       max-height:200px;overflow-y:auto;transition:max-height 0.2s">
                ${this._escapeHtml(v.output)}
              </div>
            </div>`:"",te=l[R]||[],j=te.length?`
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;
                      margin-top:6px;padding:4px 8px;background:var(--surface2);
                      border-radius:4px;border-left:2px solid var(--accent);font-size:10px">
            <span style="color:var(--accent);font-weight:600;white-space:nowrap">⑂ linked commit${te.length>1?"s":""}:</span>
            ${te.map(W=>{const ae=(W.commit_hash||"").slice(0,8),Ie=(W.commit_msg||"").slice(0,70),Ke=(W.committed_at||"").slice(0,10),Dt=(W.tags||[]).map($r=>{const Ht=this._tagColor($r);return`<span style="font-size:9px;background:${Ht}22;color:${Ht};border:1px solid ${Ht}44;padding:0 3px;border-radius:2px">${this._escapeHtml($r)}</span>`}).join("");return`<span style="display:inline-flex;align-items:center;gap:3px">${f&&W.commit_hash?`<a href="${f}/commit/${this._escapeHtml(W.commit_hash)}" target="_blank"
                      style="font-family:monospace;color:var(--accent);text-decoration:none;white-space:nowrap"
                      title="${this._escapeHtml(Ie)} · ${Ke}">${ae} ↗</a>`:`<span style="font-family:monospace;color:var(--accent);white-space:nowrap"
                         title="${this._escapeHtml(Ie)} · ${Ke}">${ae}</span>`}${Dt}</span>`}).join('<span style="color:var(--muted)">·</span>')}
          </div>`:"";return`
        <div class="history-entry" data-ts="${this._escapeHtml(v.ts||"")}"
             style="border:1px solid ${y};border-left:3px solid ${y};
                    border-radius:6px;padding:8px 10px;margin-bottom:5px">
          <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:5px;font-size:11px">
            <span style="color:var(--muted)">${v.ts?.slice(0,16)||""}</span>
            <span style="color:var(--accent)">${v.provider||""}</span>
            <span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">${v.source||"ui"}</span>
            ${(v.tags||[]).filter(W=>W.startsWith("phase:")).map(W=>`<span style="background:rgba(74,144,226,.15);color:#4a90e2;padding:1px 5px;border-radius:3px">${this._escapeHtml(W.slice(6))}</span>`).join("")}
            ${z?'<span style="color:#e74c3c;font-size:10px">⚠ untagged</span>':""}
            <span id="${E}" style="margin-left:auto;display:inline-flex;align-items:center;gap:4px;flex-wrap:wrap;position:relative">
              ${F}
              <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(R)}','${E}')"
                style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                       cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
                + Tag
              </button>
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:4px;margin-bottom:2px">
            <span style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">Prompt</span>
            ${M(`${$}-prompt`)}
          </div>
          <div id="${$}-prompt" style="font-weight:500;margin-bottom:4px;white-space:pre-wrap;word-break:break-word;font-size:13px">${this._escapeHtml(v.user_input||"")}</div>
          ${Q}
          ${j}
        </div>`}).join("");return`
        <div style="border:1px solid var(--border);border-radius:8px;padding:8px;margin-bottom:8px">
          ${h?`<div style="font-size:10px;color:var(--muted);margin-bottom:4px;font-family:monospace">session: ${h.slice(0,20)}…</div>`:""}
          ${C}
          ${S}
        </div>`}).join(""),this._renderPageBars(a,s)}_renderPageBars(t,r){const o=document.getElementById("hist-nav-bar");if(!o)return;const n=this._histPage,i=Math.ceil(t/Se),a=Math.min(r+Se,t),s="padding:2px 8px;border:1px solid var(--border);border-radius:3px;background:var(--surface);font-size:11px",d=n<=1,l=n>=i;o.innerHTML=`
      <button onclick="window._historyView._changePage(-1)"
        style="${s};cursor:${d?"default":"pointer"};opacity:${d?".35":"1"}"
        ${d?"disabled":""}>◀</button>
      <span style="color:var(--text);white-space:nowrap;font-size:11px">${r+1}–${a} / ${t}</span>
      <button onclick="window._historyView._changePage(1)"
        style="${s};cursor:${l?"default":"pointer"};opacity:${l?".35":"1"}"
        ${l?"disabled":""}>▶</button>`}_changePage(t){this._histPage=Math.max(1,this._histPage+t);const r=document.getElementById("hist-chat-groups");r&&this._renderChatGroups(r),document.getElementById("history-content")?.scrollTo(0,0)}async _buildTagCache(t){this._tagCache=[],this._tagCacheMap={};try{const r=await m.tags.list(t),o=[],n=a=>{for(const s of a||[])o.push(s),s.children?.length&&n(s.children)};n(Array.isArray(r)?r:r.tags||[]);const i={};for(const a of o){const s=a.category_name||"other",d=a.color||"#4a90e2",l=`${s}:${a.name}`;i[s]||(i[s]={cat:{name:s,color:d,id:a.category_id},values:[]}),i[s].values.push({name:a.name,tagStr:l}),this._tagCacheMap[l]={color:d,label:l}}this._tagCache=Object.values(i)}catch{}}_openEntryTagPicker(t,r){document.querySelectorAll(".entry-tag-picker").forEach(l=>l.remove());const o=document.getElementById(r);if(!o)return;const n=this._tagCache||[],i=document.createElement("div");i.className="entry-tag-picker",i.style.cssText="position:absolute;right:0;top:100%;z-index:300;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:6px;min-width:180px;max-height:260px;overflow-y:auto;box-shadow:0 4px 16px rgba(0,0,0,.25)";const a=`etf-${Date.now()}`,s=this._escapeHtml(t),d=this._escapeHtml(r);i.innerHTML=`
      <input id="${a}" placeholder="Filter or type cat:name…"
        oninput="window._historyView._filterTagPicker('${a}','${s}','${d}')"
        onkeydown="if(event.key==='Enter'){event.preventDefault();window._historyView._pickerCreateFromInput('${a}','${s}','${d}')}"
        style="width:100%;box-sizing:border-box;margin-bottom:4px;padding:3px 6px;border:1px solid var(--border);
               border-radius:3px;background:var(--surface);color:var(--text);font-size:11px"/>
      <div id="etag-groups">
        ${n.length?n.map(({cat:l,values:c})=>`
          <div class="etag-group">
            <div style="font-size:10px;color:var(--muted);font-weight:600;padding:2px 4px;text-transform:uppercase;letter-spacing:.5px">
              ${this._escapeHtml(l.name)}
            </div>
            ${c.map(g=>`
              <div class="etag-item" data-catname="${this._escapeHtml(l.name)}" data-tagstr="${this._escapeHtml(g.tagStr)}"
                onclick="window._historyView._tagEntryWith('${s}','${this._escapeHtml(g.tagStr)}','${d}')"
                style="padding:3px 10px;cursor:pointer;border-radius:3px;font-size:12px;color:${this._escapeHtml(l.color||"var(--text)")}"
                onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">
                ${this._escapeHtml(g.name)}
              </div>`).join("")}
          </div>`).join(""):'<div style="font-size:11px;color:var(--muted);padding:4px 8px">No existing tags. Type <em>cat:name</em> and press Enter.</div>'}
      </div>
      <div id="etag-create-${a}" style="display:none;padding:4px 8px;cursor:pointer;border-radius:3px;font-size:11px;
           color:var(--accent);border-top:1px solid var(--border);margin-top:4px"
        onclick="window._historyView._pickerCreateFromInput('${a}','${s}','${d}')"
        onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">
      </div>`,o.appendChild(i),i.querySelector("input")?.focus(),setTimeout(()=>{document.addEventListener("click",function l(c){!i.contains(c.target)&&!o.contains(c.target)&&(i.remove(),document.removeEventListener("click",l))})},10)}_filterTagPicker(t,r,o){const n=document.getElementById(t)?.value?.trim()||"",i=n.toLowerCase();document.querySelectorAll(".etag-item").forEach(s=>{s.style.display=!i||s.textContent.toLowerCase().includes(i)||(s.dataset.catname||"").toLowerCase().includes(i)||(s.dataset.tagstr||"").toLowerCase().includes(i)?"":"none"}),document.querySelectorAll(".etag-group").forEach(s=>{s.style.display=[...s.querySelectorAll(".etag-item")].some(d=>d.style.display!=="none")?"":"none"});const a=document.getElementById(`etag-create-${t}`);a&&(n&&n.includes(":")&&!this._tagCacheMap[n]?(a.textContent=`✚ Create "${n}"`,a.style.display=""):a.style.display="none")}async _pickerCreateFromInput(t,r,o){const n=document.getElementById(t)?.value?.trim()||"";n&&(document.querySelectorAll(".entry-tag-picker").forEach(i=>i.remove()),n.includes(":")?await this._createAndTagWith(r,n,o):await this._tagEntryWith(r,n,o))}async _createAndTagWith(t,r,o){const n=x.currentProject?.name||"",i=r.indexOf(":"),a=r.slice(0,i),s=r.slice(i+1).trim();if(!s)return;const l=this._tagCache?.find(c=>c.cat.name===a)?.cat.id||null;try{await m.tags.create({project:n,name:s,category_id:l}),await this._buildTagCache(n)}catch(c){if(!c.message?.includes("already exists")){console.warn("Tag create failed:",c.message);return}}await this._tagEntryWith(t,r,o)}async _tagEntryWith(t,r,o){const n=x.currentProject?.name||"";document.querySelectorAll(".entry-tag-picker").forEach(s=>s.remove());const i=document.getElementById(o),a=this._tagColor(r);if(this._entryTags[t]||(this._entryTags[t]=[]),this._entryTags[t].includes(r)||this._entryTags[t].push(r),i){const s=document.createElement("span");s.dataset.tag=r,s.style.cssText=`font-size:10px;background:${a}22;color:${a};border:1px solid ${a}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px`,s.appendChild(document.createTextNode(r));const d=document.createElement("button");d.textContent="✕",d.title="Remove tag",d.style.cssText=`border:none;background:none;cursor:pointer;color:${a};font-size:9px;padding:0 1px;line-height:1;opacity:.7`,d.addEventListener("click",c=>{c.stopPropagation(),window._historyView._removeTag(t,r,o)}),s.appendChild(d);const l=i.querySelector('button:not([title="Remove tag"])');l?i.insertBefore(s,l):i.appendChild(s)}try{const s=await m.entities.tagBySourceId({source_id:t,tag:r,project:n});if(s?.propagated_to){const d=s.propagated_to;this._entryTags[d]||(this._entryTags[d]=[]),this._entryTags[d].includes(r)||this._entryTags[d].push(r);const l="ca-"+d.slice(0,8);this._addTagChipToAnchor(l,r,d)}}catch(s){if(console.warn("Tag entry failed:",s.message),i){const d=i.querySelector(`[data-tag="${CSS.escape(r)}"]`);d&&d.remove(),this._entryTags[t]&&(this._entryTags[t]=this._entryTags[t].filter(c=>c!==r));const l=document.createElement("span");l.style.cssText="font-size:10px;color:#e74c3c;white-space:nowrap",l.textContent="✕ "+s.message,i.appendChild(l),setTimeout(()=>l.remove(),4e3)}}}_addTagChipToAnchor(t,r,o){const n=document.getElementById(t);if(!n||n.querySelector(`[data-tag="${CSS.escape(r)}"]`))return;const i=this._tagColor(r),a=document.createElement("span");a.dataset.tag=r,a.style.cssText=`font-size:10px;background:${i}22;color:${i};border:1px solid ${i}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px`,a.appendChild(document.createTextNode(r));const s=document.createElement("button");s.textContent="✕",s.title="Remove tag",s.style.cssText=`border:none;background:none;cursor:pointer;color:${i};font-size:9px;padding:0 1px;line-height:1;opacity:.7`,s.addEventListener("click",l=>{l.stopPropagation(),window._historyView._removeTag(o,r,t)}),a.appendChild(s);const d=n.querySelector('button:not([title="Remove tag"])');d?n.insertBefore(a,d):n.appendChild(a)}async _renderCommits(t){const r=x.currentProject?.name||"",[o,n,i]=await Promise.all([m.historyCommits(r,500),m.getProjectConfig(r).catch(()=>({})),m.entities.getSourceTags(r).catch(()=>({}))]);this._tagCache||await this._buildTagCache(r);for(const[s,d]of Object.entries(i||{}))this._entryTags[s]||(this._entryTags[s]=d);this._commitData=o,this._commitPage=1;let a=(n.github_repo||"").replace(/\/$/,"").replace(/\.git$/,"");a.startsWith("git@")&&(a=a.replace(/^git@([^:]+):/,"https://$1/")),this._ghBase=a,this._renderCommitsContainer(t)}_renderCommitsContainer(t){const r=this._commitData?.commits||[],o=this._commitData?.source==="db",n=this._commitFilter.phase||"",i=n?r.filter(_=>_.tags?.includes("phase:"+n)):r,a=r.filter(_=>!_.tags?.some(C=>C.startsWith("phase:"))).length,d=`
      <select id="commit-filter-phase" onchange="window._historyView._applyCommitFilter()"
        style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
        ${[["","All phases"],["discovery","Discovery"],["development","Development"],["testing","Testing"],["review","Review"],["production","Production"],["maintenance","Maintenance"],["bugfix","Bug Fix"]].map(([_,C])=>`<option value="${_}" ${n===_?"selected":""}>${C}</option>`).join("")}
      </select>`,l=Math.ceil(i.length/Se)||1,c=(this._commitPage-1)*Se,g=Math.min(c+Se,i.length),f=i.slice(c,g),u=document.getElementById("hist-nav-bar");if(u){const _="padding:2px 8px;border:1px solid var(--border);border-radius:3px;background:var(--surface);font-size:11px",C=this._commitPage<=1,S=this._commitPage>=l;u.innerHTML=`
        <button onclick="window._historyView._changeCommitPage(-1)"
          style="${_};cursor:${C?"default":"pointer"};opacity:${C?".35":"1"}"
          ${C?"disabled":""}>◀</button>
        <span style="color:var(--text);white-space:nowrap;font-size:11px">${c+1}–${g} / ${i.length}</span>
        <button onclick="window._historyView._changeCommitPage(1)"
          style="${_};cursor:${S?"default":"pointer"};opacity:${S?".35":"1"}"
          ${S?"disabled":""}>▶</button>`}const h=`
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
        ${d}
        <span style="font-size:13px;color:var(--muted)">
          ${n?`${i.length} / ${r.length}`:r.length} commit${r.length!==1?"s":""}
          ${a>0?`· <span style="color:#e74c3c;font-weight:600">${a} untagged</span>`:""}
        </span>
        ${o?"":'<span style="font-size:11px;color:orange;background:rgba(230,126,34,.12);padding:2px 6px;border-radius:4px" title="PostgreSQL not connected — showing file-based data">file fallback</span>'}
        <div style="flex:1"></div>
        <button id="commits-sync-btn" onclick="window._historyView._syncCommits()"
          style="padding:4px 12px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:12px">
          ↻ Sync Commits
        </button>
      </div>`;if(!i.length){t.innerHTML=h+`
        <div style="padding:2rem;text-align:center;color:var(--muted);font-size:13px">
          <div style="font-size:2rem;margin-bottom:.5rem">⑂</div>
          ${n?`No commits with phase <strong>${n}</strong>.`:"No commits yet. Click <strong>↻ Sync Commits</strong> to import."}
        </div>`;return}t.innerHTML=h+`
      <div style="overflow-x:auto">
        <table id="commits-table" style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:var(--surface);font-size:10px;text-transform:uppercase;color:var(--muted)">
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Hash</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Date</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border)">Tags ⬡</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border)">Message</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Prompt ↗</th>
            </tr>
          </thead>
          <tbody>
            ${f.map((_,C)=>this._commitRow(_,c+C)).join("")}
          </tbody>
        </table>
      </div>`}_applyCommitFilter(){const t=document.getElementById("commit-filter-phase");this._commitFilter.phase=t?.value||"",this._commitPage=1;const r=document.getElementById("history-content");r&&this._renderCommitsContainer(r)}_changeCommitPage(t){const r=this._commitData?.commits||[],o=this._commitFilter.phase||"",n=o?r.filter(s=>s.tags?.includes("phase:"+o)):r,i=Math.ceil(n.length/Se);this._commitPage=Math.max(1,Math.min(i,this._commitPage+t));const a=document.getElementById("history-content");a&&this._renderCommitsContainer(a),a?.scrollTo(0,0)}_commitRow(t,r){const n=!t.tags?.some(C=>C.startsWith("phase:"))?"border-left:3px solid #e74c3c":"border-left:3px solid transparent",i=t.committed_at?t.committed_at.slice(0,10):"",a=this._ghBase||"",s=t.commit_hash||"",d=s.slice(0,8),l=`ca-${d}`,c=a&&s?`<a href="${a}/commit/${s}" target="_blank"
            style="font-family:monospace;color:var(--accent);text-decoration:none">${d} ↗</a>`:`<span style="font-family:monospace;color:var(--accent)">${d}</span>`,g=t.prompt_source_id&&this._histData?.entries?this._histData.entries.find(C=>C.ts===t.prompt_source_id):null,f=g?this._escapeHtml((g.user_input||"").slice(0,120)):this._escapeHtml(t.prompt_source_id||""),u=t.prompt_source_id?`<button onclick="window._historyView._jumpToPrompt('${this._escapeHtml(t.prompt_source_id)}')"
           title="${f}"
           style="font-family:monospace;font-size:11px;color:var(--accent);cursor:pointer;
                  background:none;border:none;padding:0;text-decoration:underline dotted;max-width:120px;
                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block">
           ⊙ ${(t.prompt_source_id||"").slice(11,16)||t.prompt_source_id.slice(0,8)}
         </button>`:'<span style="color:var(--muted);font-size:11px">—</span>',_=(this._entryTags[s]||[]).map(C=>{const S=this._tagColor(C);return`<span data-tag="${this._escapeHtml(C)}"
             style="font-size:10px;background:${S}22;color:${S};border:1px solid ${S}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px">
         ${this._escapeHtml(C)}
         <button onclick="event.stopPropagation();window._historyView._removeTag('${this._escapeHtml(s)}','${this._escapeHtml(C)}','${l}')"
           style="border:none;background:none;cursor:pointer;color:${S};font-size:9px;padding:0 1px;line-height:1;opacity:.7"
           title="Remove tag">✕</button>
       </span>`}).join("");return`
      <tr data-commit-id="${t.id||""}" data-hash="${this._escapeHtml(s)}"
          style="border-bottom:1px solid var(--border);${n};transition:background .15s"
          onmouseenter="this.style.background='var(--surface)'"
          onmouseleave="this.style.background=''">
        <td style="padding:4px 6px">${c}</td>
        <td style="padding:4px 6px;color:var(--muted);white-space:nowrap">${i}</td>
        <td style="padding:4px 6px">
          <span id="${l}" style="display:inline-flex;align-items:center;gap:4px;flex-wrap:wrap;position:relative">
            ${_}
            <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(s)}','${l}')"
              style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                     cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
              + Tag
            </button>
          </span>
        </td>
        <td style="padding:4px 6px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${this._escapeHtml(t.commit_msg||"")}">
          ${this._escapeHtml(t.commit_msg||"")}
        </td>
        <td style="padding:4px 6px;white-space:nowrap">${u}</td>
      </tr>
    `}async _saveField(t,r,o){if(t)try{await m.patchCommit(t,{[r]:o||null})}catch(n){console.warn("Commit patch failed:",n.message)}}async _jumpToPrompt(t){if(!t)return;const r=document.getElementById("history-content");if(!r)return;this._histData||(r.innerHTML="<div style='padding:20px;color:var(--muted)'>Loading…</div>",await this._renderChat(r));const o=this._histData?.entries||[],n=this._histFilter||{};let i=[...o];n.source&&(i=i.filter(s=>(s.source||"ui")===n.source)),n.phase&&(i=i.filter(s=>s.tags?.includes("phase:"+n.phase)));const a=i.findIndex(s=>s.ts===t);a>=0&&(this._histPage=Math.floor(a/Se)+1),this.activeTab="chat",document.querySelectorAll(".tab-btn").forEach(s=>{s.style.background=s.dataset.tab==="chat"?"var(--accent)":"var(--surface)"}),this._renderChatContainer(r),setTimeout(()=>{const s=r.querySelector(`.history-entry[data-ts="${CSS.escape(t)}"]`);s&&(s.scrollIntoView({behavior:"smooth",block:"center"}),s.style.outline="2px solid var(--accent)",setTimeout(()=>{s.style.outline=""},2500))},120)}async _removeTag(t,r,o){const n=x.currentProject?.name||"";this._entryTags[t]&&(this._entryTags[t]=this._entryTags[t].filter(a=>a!==r));const i=document.getElementById(o);if(i){const a=i.querySelector(`[data-tag="${CSS.escape(r)}"]`);a&&a.remove()}try{const a=await m.entities.untagBySourceId(t,r,n);if(a?.propagated_to){const s=a.propagated_to;this._entryTags[s]&&(this._entryTags[s]=this._entryTags[s].filter(c=>c!==r));const d="ca-"+s.slice(0,8),l=document.getElementById(d);if(l){const c=l.querySelector(`[data-tag="${CSS.escape(r)}"]`);c&&c.remove()}}}catch(a){console.warn("Remove tag failed:",a.message);try{const s=await m.entities.getSourceTags(n);for(const[d,l]of Object.entries(s||{}))this._entryTags[d]=l}catch{}}}_refreshUntaggedCount(){const t=document.querySelectorAll("#commits-table tbody tr");let r=0;t.forEach(n=>{n.style.borderLeft.includes("#e74c3c")&&r++});const o=document.querySelector('#history-content [style*="e74c3c"]');o&&o.tagName==="SPAN"&&(o.textContent=r>0?`${r} untagged`:"")}async _syncCommits(){const t=document.getElementById("commits-sync-btn");t&&(t.textContent="Syncing…",t.disabled=!0);const r=x.currentProject?.name||"";try{const o=await m.syncCommits(r);this._commitData=null,alert(`Synced ${o.imported} new commits.`),await this._loadTab("commits")}catch(o){alert("Sync failed: "+o.message)}finally{t&&(t.textContent="↻ Sync Commits",t.disabled=!1)}}async _renderRuns(t){t.innerHTML='<div style="padding:16px;color:var(--muted)">Loading runs…</div>';try{const n=(await(await fetch(at("/history/runs?limit=50"))).json()).runs||[];if(!n.length){t.innerHTML="<div style='padding:20px;color:var(--muted)'>No workflow runs yet.</div>";return}const i={done:"#3ecf8e",error:"#e85d75",running:"#f5a623",stopped:"#888",cancelled:"#888",waiting_approval:"#9b7ef8"},a=s=>String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");t.innerHTML=n.map(s=>{const d=i[s.status]||"var(--muted)",l=(s.started_at||"").slice(0,16).replace("T"," "),c=s.duration_secs?`${s.duration_secs}s`:"",g=s.total_cost_usd>0?`$${Number(s.total_cost_usd).toFixed(4)}`:"",f=(s.user_input||"").slice(0,80);return`
          <div class="run-entry" style="border:1px solid var(--border);border-radius:6px;
               padding:10px 14px;margin-bottom:8px;cursor:pointer;
               transition:background 0.12s" onmouseover="this.style.background='var(--bg2)'"
               onmouseout="this.style.background=''" ${s.id&&/^[0-9a-f-]{36}$/.test(s.id)?`onclick="window._historyView._openRunInPipelines('${a(s.id)}')"`:`onclick="window._historyView._showRunDetail('${a(s.file)}')"`}>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="width:8px;height:8px;border-radius:50%;background:${d};flex-shrink:0;display:inline-block"></span>
              <strong style="font-size:0.82rem">${a(s.workflow||s.file)}</strong>
              <span style="color:${d};font-size:0.72rem">${a(s.status||"")}</span>
              <span style="color:var(--muted);font-size:0.72rem;margin-left:auto">${a(l)}</span>
              ${s.steps?`<span style="color:var(--muted);font-size:0.72rem">${s.steps} steps</span>`:""}
              ${c?`<span style="color:var(--muted);font-size:0.72rem">${a(c)}</span>`:""}
              ${g?`<span style="color:#3ecf8e;font-size:0.72rem">${a(g)}</span>`:""}
            </div>
            ${f?`<div style="font-size:0.72rem;color:var(--muted);margin-top:4px;
                            overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${a(f)}</div>`:""}
            ${s.error?`<div style="font-size:0.72rem;color:#e85d75;margin-top:4px">${a(s.error.slice(0,100))}</div>`:""}
          </div>`}).join("")}catch(r){t.innerHTML=`<div style='padding:20px;color:var(--red)'>Could not load runs: ${r.message}</div>`}}_openRunInPipelines(t){window._pendingRunOpen=t,window.navigateTo&&window.navigateTo("workflow")}async _showRunDetail(t){try{const o=await(await fetch(at(`/history/runs/${t}`))).json(),n=document.createElement("div");n.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:1000",n.innerHTML=`
        <div style="background:var(--bg);border-radius:8px;padding:24px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
          <div style="display:flex;justify-content:space-between;margin-bottom:16px">
            <strong>Run: ${o.workflow}</strong>
            <button onclick="this.closest('div[style*=fixed]').remove()">✕</button>
          </div>
          <pre style="font-size:12px;background:var(--surface);padding:12px;border-radius:4px;overflow-x:auto">${JSON.stringify(o,null,2)}</pre>
        </div>`,document.body.appendChild(n)}catch(r){alert(`Could not load run detail: ${r.message}`)}}async _renderEvals(t){const n=(await(await fetch(at("/history/evals"))).json()).evals||[];if(!n.length){t.innerHTML="<div style='padding:20px;color:var(--muted)'>No prompt evaluations yet.</div>";return}t.innerHTML=n.map(i=>`
      <div style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px">
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <span style="color:var(--muted);font-size:12px">${i.ts?.slice(0,16)||""}</span>
          <span style="color:var(--accent)">${i.prompt_file||""}</span>
          <span style="color:green">Winner: ${i.winner||"(none)"}</span>
        </div>
        <div style="font-size:12px;color:var(--muted)">Providers: ${(i.providers||[]).join(", ")}</div>
        ${i.notes?`<div style="margin-top:4px;font-size:12px">${this._escapeHtml(i.notes)}</div>`:""}
      </div>`).join("")}_filterContent(t){if(this.activeTab==="chat"){this._histFilter.query=t,this._histPage=1;const r=document.getElementById("hist-chat-groups");r&&this._renderChatGroups(r)}else document.querySelectorAll(".history-entry, .run-entry").forEach(o=>{o.style.display=o.textContent.toLowerCase().includes(t.toLowerCase())?"":"none"})}_tagColor(t){const r=(t||"").split(":")[0];return{phase:"#3b82f6",feature:"#22c55e",bug:"#ef4444"}[r]||"#4a90e2"}_escapeHtml(t){return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}}let D={selectedCat:null,selectedCatName:"",selectedCatColor:"",selectedCatIcon:"",project:"",aiSubtypeFilter:null};function Ji(e){const t=x.currentProject?.name||"";if(D={selectedCat:null,selectedCatName:"",selectedCatColor:"",selectedCatIcon:"",project:t,aiSubtypeFilter:null},e.innerHTML=`
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Header -->
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:1rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Tag Management</span>
        ${t?`<span style="font-size:0.65rem;color:var(--accent)">${w(t)}</span>`:""}
        <button class="btn btn-ghost btn-sm" style="margin-left:auto"
          onclick="window._plannerSync()" title="Sync events + reload cache">↻ Sync</button>
        <button class="btn btn-ghost btn-sm"
          onclick="window._plannerMigrateAiTags()"
          title="Move AI-auto-created tags from bug/feature/task into AI Suggestions">⇢ Fix AI tags</button>
      </div>

      <!-- 2-pane body -->
      <div style="display:flex;flex:1;min-height:0;overflow:hidden">

        <!-- Left pane: category list -->
        <div id="planner-cats-pane"
             style="width:160px;flex-shrink:0;border-right:1px solid var(--border);
                    overflow:hidden;display:flex;flex-direction:column">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      padding:8px 10px 4px;letter-spacing:.05em;flex-shrink:0">Categories</div>
          <div id="planner-cat-list" style="flex:1;overflow-y:auto;padding:0 4px"></div>
          <div style="padding:6px 8px;border-top:1px solid var(--border);flex-shrink:0">
            <input id="planner-new-cat-inp" placeholder="+ New category…"
              style="width:100%;padding:3px 6px;border:1px dashed var(--border);border-radius:4px;
                     background:transparent;color:var(--text);font-size:0.62rem;
                     box-sizing:border-box;outline:none;font-family:var(--font)"
              onkeydown="if(event.key==='Enter')window._plannerNewCat(this.value)" />
          </div>
        </div>

        <!-- Right area: table + detail drawer -->
        <div style="flex:1;display:flex;min-height:0;overflow:hidden">

          <!-- Tag table -->
          <div id="planner-tags-pane" style="flex:1;overflow-y:auto;padding:0.75rem 1rem">
            <div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">
              ← Select a category
            </div>
          </div>

          <!-- Detail drawer (closed by default) -->
          <div id="planner-drawer"
               style="width:0;overflow:hidden;border-left:0 solid var(--border);
                      flex-shrink:0;transition:width 0.22s ease,border-width 0.22s;
                      background:var(--surface);display:flex">
            <div id="planner-drawer-inner"
                 style="width:290px;overflow-y:auto;flex-shrink:0;box-sizing:border-box"></div>
          </div>

        </div>

      </div>

      <!-- Bottom panel: Work Items (always visible) -->
    <div id="planner-wi-panel"
         style="height:210px;flex-shrink:0;display:flex;flex-direction:column;
                background:var(--surface)">
      <!-- Resize handle -->
      <div id="wi-panel-resizer"
           style="height:5px;background:var(--border);cursor:ns-resize;flex-shrink:0;
                  display:flex;align-items:center;justify-content:center;
                  border-top:1px solid var(--border);transition:background 0.1s"
           onmousedown="window._wiPanelResizeStart(event)"
           onmouseenter="this.style.background='var(--accent)44'"
           onmouseleave="this.style.background='var(--border)'">
        <div style="width:32px;height:2px;background:var(--muted);border-radius:2px;opacity:.5"></div>
      </div>
      <!-- Panel header -->
      <div style="display:flex;align-items:center;gap:0.5rem;padding:3px 10px;
                  border-bottom:1px solid var(--border);flex-shrink:0;
                  background:var(--surface2)">
        <span style="font-size:0.6rem;font-weight:700;color:var(--text);letter-spacing:.03em">⬡ WORK ITEMS</span>
        <span id="wi-panel-count" style="font-size:0.55rem;color:var(--muted)"></span>
        <span style="flex:1"></span>
        <button id="wi-panel-refresh-btn"
          title="Refresh list and trigger AI tag matching for new items"
          style="background:none;border:1px solid var(--border);color:var(--muted);font-size:0.62rem;
                 padding:0.1rem 0.4rem;border-radius:var(--radius);cursor:pointer;
                 font-family:var(--font);outline:none">↺</button>
      </div>
      <!-- Panel list (also a drop zone for unlinking) -->
      <div id="wi-panel-list" style="flex:1;overflow-y:auto;overflow-x:hidden"
           ondragover="window._wiPanelDragOver(event)"
           ondragleave="window._wiPanelDragLeave(event)"
           ondrop="window._wiPanelDrop(event)">
        <div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Loading…</div>
      </div>
    </div>

  </div>
  `,window._plannerSelectCat=ft,window._plannerMigrateAiTags=fa,window._plannerDeleteVal=ca,window._plannerSaveNewTag=ma,window._plannerCancelNewTag=So,window._plannerSync=To,window._plannerNewCat=ga,window._plannerAddChild=pa,window._plannerToggleExpand=ua,window._plannerOpenDrawer=ra,window._plannerCloseDrawer=tt,window._plannerDrawerSetStatus=na,window._plannerDrawerSaveRemarks=ia,window._plannerDrawerSaveDue=aa,window._plannerDrawerAddChild=sa,window._plannerDrawerAddLink=ya,window._plannerDrawerRemoveLink=ha,window._plannerGenerateSnapshot=da,window._plannerDrawerMerge=la,window._plannerWfPicker=(r,o,n,i)=>Zt(r,o,n,i),window._plannerRunPlan=async(r,o,n,i)=>{const a=document.getElementById("drawer-planner-btn"),s=document.getElementById("drawer-planner-doc");a&&(a.disabled=!0,a.textContent="…");try{const d=await m.tags.plan(r,i);p(`Planner done · ${d.work_items_updated} items synced`,"success"),s&&(s.innerHTML=`<a href="#" onclick="event.preventDefault();window._plannerOpenDoc('${w(d.doc_path)}','${w(i)}')"
           style="color:var(--accent);text-decoration:underline">&#128196; ${w(d.doc_path)}</a>`),setTimeout(()=>window._plannerOpenDrawer&&window._plannerOpenDrawer(se().find(l=>l.name===n)?.id,r),300)}catch(d){p("Planner error: "+d.message,"error")}finally{a&&(a.disabled=!1,a.textContent="&#9641; Run Planner")}},window._plannerOpenDoc=(r,o)=>{const n=document.querySelector('[data-view="documents"]');n&&n.click(),setTimeout(()=>window._documentsOpenFile?.(r,o),250)},window._plannerOpenWorkItemDrawer=(r,o,n)=>ea(r,o,n),window._extractWorkItemCode=async(r,o)=>{const n=document.getElementById(`wi-extract-btn-${r}`),i=document.getElementById(`wi-extract-status-${r}`);n&&(n.disabled=!0,n.textContent="…");try{const a=await m.workItems.extract(r,o),s=a.aggregated||{},d=`${s.commit_count||0} commits · ${(s.all_files||[]).length} files`;p(`Extracted · ${d}`,"success"),i&&(i.textContent=d);const l=document.getElementById(`wi-ai-tags-${r}`);if(aiTagsEl){const c=a.code_summary||{},g=a.test_coverage||{},f=[];c.key_classes?.length&&f.push(`Classes: ${c.key_classes.join(", ")}`),c.key_methods?.length&&f.push(`Methods: ${c.key_methods.join(", ")}`),g.missing?.length&&f.push(`<span style="color:#e67e22">Missing tests: ${g.missing.join(", ")}</span>`),f.length&&(aiTagsEl.innerHTML='<div style="font-size:0.52rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.2rem;color:var(--muted)">Code Intelligence</div>'+f.map(u=>`<div style="font-size:0.6rem;color:var(--muted)">${u}</div>`).join(""))}}catch(a){p("Extract error: "+a.message,"error")}finally{n&&(n.disabled=!1,n.textContent="&#11041; Extract Code")}},window._wiBotDragStart=(r,o,n,i)=>{ee={id:o,name_ai:n,category_ai:i},r.dataTransfer.effectAllowed="link",r.dataTransfer.setData("text/plain",o),r.currentTarget.style.opacity="0.5"},window._wiBotDragEnd=r=>{r&&r.currentTarget&&(r.currentTarget.style.opacity=""),ee=null,document.querySelectorAll("[data-tag-id]").forEach(n=>{n.style.background="",n.style.outline=""});const o=document.getElementById("planner-dnd-hint");o&&(o.style.display="none")},window._wiBotItemDragOver=(r,o)=>{const n=o.dataset.wiId;if(!ee||!n||n===ee.id)return;r.preventDefault(),r.stopPropagation(),o.style.outline="2px solid var(--accent)";const i=document.getElementById("planner-dnd-hint");i&&(i.style.display="block",i.textContent=`⊕ Merge with "${w(o.dataset.wiName||"")}"`,i.style.left=r.clientX+16+"px",i.style.top=r.clientY+12+"px")},window._wiBotItemDragLeave=(r,o)=>{o.style.outline=""},window._wiBotItemDrop=async(r,o,n)=>{r.preventDefault(),r.stopPropagation();const i=r.currentTarget;if(i.style.outline="",!ee||!o||o===ee.id)return;const a=ee.id,s=ee.name_ai;ee=null;try{await m.workItems.merge(a,o,n),p(`Merged "${s}" ⊕ merged`,"success"),fe(n)}catch(d){p("Merge failed: "+d.message,"error")}},window._wiDeleteLinked=async(r,o)=>{if(confirm("Delete this work item?")){_wiRowLoading(r,!0);try{await m.workItems.delete(r,o);const n=document.querySelector(`.wi-sub-row[data-wi-id="${CSS.escape(r)}"]`);n&&n.remove(),delete q[r],p("Work item deleted","success")}catch(n){p("Delete failed: "+n.message,"error"),_wiRowLoading(r,!1)}}},window._wiUnlink=async(r,o)=>{_wiRowLoading(r,!0);try{await m.workItems.patch(r,o,{tag_id_user:""}),p("Unlinked","success"),fe(o);const{selectedCatName:n}=D;n&&Ue(n)?Oe(o,n).catch(()=>{}):ye()}catch(n){p("Unlink failed: "+n.message,"error")}},window._wiPanelNewItem=()=>{const{project:r}=D,o=prompt("Category (bug/feature/task):");if(!o)return;const n=prompt("Work item name:");n&&m.workItems.create(r,{category_ai:o.toLowerCase(),name_ai:n}).then(()=>{p(`Created "${n}"`,"success"),fe(r)}).catch(i=>p(i.message,"error"))},document.getElementById("wi-panel-add-btn")?.addEventListener("click",window._wiPanelNewItem),window._wiPanelResizeStart=r=>{r.preventDefault();const o=document.getElementById("planner-wi-panel");if(!o)return;const n=r.clientY,i=o.offsetHeight,a=document.getElementById("wi-panel-resizer");a&&(a.style.background="var(--accent)66");const s=l=>{const c=n-l.clientY;o.style.height=Math.max(60,Math.min(520,i+c))+"px"},d=()=>{document.removeEventListener("mousemove",s),document.removeEventListener("mouseup",d),a&&(a.style.background="")};document.addEventListener("mousemove",s),document.addEventListener("mouseup",d)},window._wiSubRowDragStart=(r,o,n,i)=>{ee={id:o,name_ai:n,category_ai:i},r.dataTransfer.effectAllowed="move",r.dataTransfer.setData("text/plain",o)},window._wiPanelDragOver=r=>{if(ee){r.preventDefault(),r.dataTransfer.dropEffect="move";const o=document.getElementById("wi-panel-list");o&&(o.style.outline="2px dashed var(--accent)")}},window._wiPanelDragLeave=r=>{const o=document.getElementById("wi-panel-list");o&&!o.contains(r.relatedTarget)&&(o.style.outline="")},window._wiPanelDrop=async r=>{r.preventDefault();const o=document.getElementById("wi-panel-list");if(o&&(o.style.outline=""),!ee)return;const n={...ee};ee=null;const i=D.project;try{await m.workItems.patch(n.id,i,{tag_id_user:""}),p(`Unlinked "${n.name_ai}"`,"success"),fe(i),Oe(i).catch(()=>{})}catch(a){p("Unlink failed: "+a.message,"error")}},!t){document.getElementById("planner-tags-pane").innerHTML='<div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">No project open</div>';return}Qi(t)}async function Qi(e){const t=se(),r=t.some(i=>i.id===null),o=Cr()&&t.length>0&&t.every(i=>(i.value_count||0)>0&&Pe(i.id).length===0);(!Cr()||ln()!==e||r||o)&&(document.getElementById("planner-cat-list").innerHTML='<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">Loading…</div>',await Fe(e,!0)),ke();const n=se();if(!D.selectedCat&&n.length>0){const i=n.find(a=>Ue(a.name)&&a.id!=null)||n.find(a=>a.id!=null);i&&await ft(i.id,i.name)}fe(e)}function ke(){const e=document.getElementById("planner-cat-list");if(!e)return;const t=se();if(!t.length){e.innerHTML='<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">No categories yet</div>';return}const r=t.filter(s=>Ue(s.name)),o=t.filter(s=>!Ue(s.name)&&s.name!=="ai_suggestion"),n=s=>D.selectedCat===s,i=s=>`
    <div class="planner-cat-row" data-id="${s.id}" data-cat-name="${w(s.name)}"
         onclick="window._plannerSelectCat(${s.id},'${w(s.name)}')"
         ondragover="window._plannerCatDragOver(event,${s.id},'${w(s.name)}')"
         ondragleave="window._plannerCatDragLeave(event)"
         ondrop="window._plannerCatDrop(event,${s.id},'${w(s.name)}')"
         style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
                cursor:pointer;margin-bottom:2px;transition:background 0.1s;
                background:${n(s.id)?"var(--accent)22":"transparent"};
                border-left:2px solid ${n(s.id)?"var(--accent)":"transparent"}">
      <span style="color:${s.color};font-size:0.85rem">${s.icon}</span>
      <span style="font-size:0.65rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${w(s.name)}</span>
      <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${Pe(s.id).length}</span>
    </div>`,a=o.length?`
    <div style="font-size:0.5rem;text-transform:uppercase;letter-spacing:.1em;
                color:var(--muted);padding:8px 8px 3px;margin-top:4px;
                border-top:1px solid var(--border)">Tags</div>`:"";e.innerHTML=r.map(i).join("")+a+o.map(i).join("")}async function ft(e,t){if(D.aiSubtypeFilter=null,e==null){const o=document.getElementById("planner-tags-pane");o&&(o.innerHTML='<div style="color:var(--muted);font-size:0.7rem;padding:16px">Loading…</div>'),await Fe(D.project,!0);const n=se().find(i=>i.name===t&&i.id!=null);if(n)return ft(n.id,n.name);o&&(o.innerHTML='<div style="color:var(--muted);font-size:0.7rem;padding:16px">Database not ready yet — try again shortly</div>');return}D.selectedCat=e,D.selectedCatName=t;const r=se().find(o=>o.id===e)||{};D.selectedCatColor=r.color||"var(--accent)",D.selectedCatIcon=r.icon||"⬡",document.querySelectorAll(".planner-cat-row").forEach(o=>{const n=parseInt(o.dataset.id)===e;o.style.background=n?"var(--accent)22":"transparent",o.style.borderLeft=n?"2px solid var(--accent)":"2px solid transparent"}),ye()}let ee=null,q={};async function fe(e){const t=document.getElementById("wi-panel-list");if(!t)return;try{const n=(await m.workItems.unlinked(e)).items||[];q={},n.forEach(a=>{q[a.id]=a}),Re(n,e);const i=document.getElementById("wi-panel-count");i&&(i.textContent=n.length?`(${n.length} unlinked)`:"(all linked ✓)")}catch{t&&(t.innerHTML='<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Could not load work items</div>')}const r=document.getElementById("wi-panel-refresh-btn");r&&!r._wired&&(r._wired=!0,r.addEventListener("click",async()=>{r.textContent="…",r.disabled=!0;try{await m.workItems.rematchAll(e),await fe(e)}catch{}finally{r.textContent="↺",r.disabled=!1}}))}function Re(e,t){const r=document.getElementById("wi-panel-list");if(!r)return;if(!e.length){r.innerHTML='<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">All work items linked ✓ — or click ↺ to refresh</div>';return}const o={feature:"✨",bug:"🐛",task:"📋"},n={active:"#27ae60",in_progress:"#e67e22",done:"#4a90e2",paused:"#888"};window._wiPanelSort||(window._wiPanelSort={field:"updated_at",dir:"desc"});const{field:i,dir:a}=window._wiPanelSort,s=a==="asc"?1:-1,d=[...e].sort((v,b)=>i==="prompt_count"?s*((v.prompt_count||0)-(b.prompt_count||0)):i==="event_count"?s*((v.event_count||0)-(b.event_count||0)):i==="commit_count"?s*((v.commit_count||0)-(b.commit_count||0)):i==="seq_num"?s*((v.seq_num||0)-(b.seq_num||0)):s*(new Date(v.updated_at||v.created_at||0)-new Date(b.updated_at||b.created_at||0)));function l(v){if(!v)return"—";const b=new Date(v),z=String(b.getFullYear()).slice(2),y=String(b.getMonth()+1).padStart(2,"0"),$=String(b.getDate()).padStart(2,"0"),E=String(b.getHours()).padStart(2,"0"),R=String(b.getMinutes()).padStart(2,"0");return`${z}/${y}/${$}-${E}:${R}`}function c(v,b){const z=window._wiPanelSort.field===v,y=z?window._wiPanelSort.dir==="asc"?"↑":"↓":"↕";return`<th onclick="window._wiPanelResort('${v}')"
      style="text-align:right;padding:5px 10px;cursor:pointer;user-select:none;white-space:nowrap;
             font-size:0.68rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
             color:${z?"var(--accent)":"var(--muted)"};background:var(--surface2);
             border-bottom:2px solid ${z?"var(--accent)":"var(--border)"};border-left:1px solid var(--border);
             position:sticky;top:0;z-index:1">
      ${b}&nbsp;<span style="opacity:${z?1:.35};font-size:0.62rem">${y}</span>
    </th>`}window._wiPanelResort=v=>{window._wiPanelSort.field===v?window._wiPanelSort.dir=window._wiPanelSort.dir==="asc"?"desc":"asc":(window._wiPanelSort.field=v,window._wiPanelSort.dir="desc"),Re(Object.values(q),t)};function g(){if(document.getElementById("wi-loading-style"))return;const v=document.createElement("style");v.id="wi-loading-style",v.textContent="@keyframes wi-pulse{0%,100%{opacity:.55}50%{opacity:.25}}.wi-loading{animation:wi-pulse .7s ease-in-out infinite;pointer-events:none!important;}",document.head.appendChild(v)}function f(v,b){g();const z=document.querySelector(`#wi-panel-list tr[data-wi-id="${CSS.escape(v)}"]`)||document.querySelector(`.wi-sub-row[data-wi-id="${CSS.escape(v)}"]`);z&&(b?z.classList.add("wi-loading"):z.classList.remove("wi-loading"))}window._wiPanelDelete=async(v,b)=>{if(confirm("Remove this work item?")){f(v,!0);try{await m.workItems.delete(v,b),delete q[v];const z=Object.values(q);Re(z,b);const y=document.getElementById("wi-panel-count");y&&(y.textContent=z.length?`(${z.length} unlinked)`:"(all linked ✓)")}catch(z){p("Delete failed: "+z.message,"error"),f(v,!1)}}},window._wiPanelApproveTag=async(v,b)=>{const z=q[v];if(!(!z||!z.tag_id_ai)){f(v,!0);try{await m.workItems.patch(v,b,{tag_id_user:z.tag_id_ai}),delete q[v];const y=Object.values(q);Re(y,b);const $=document.getElementById("wi-panel-count");$&&($.textContent=y.length?`(${y.length} unlinked)`:"(all linked ✓)"),p(`Linked to "${z.ai_tag_name}"`,"success");const E=z.ai_tag_category;if(E){const F=se().find(M=>M.name===E&&M.id!=null);if(F&&F.id!==D.selectedCat){await ft(F.id,F.name);return}}const{selectedCatName:R}=D;R&&Oe(b,R).catch(()=>{})}catch(y){p("Approve failed: "+y.message,"error"),f(v,!1)}}},window._wiPanelRemoveTag=async(v,b)=>{f(v,!0);try{await m.workItems.patch(v,b,{tag_id_ai:"",tags_ai:{}}),q[v]&&(q[v].tag_id_ai=null,q[v].ai_tag_name=null,q[v].ai_tag_category=null,q[v].ai_tag_color=null,q[v].tags_ai={}),Re(Object.values(q),b)}catch(z){p("Remove failed: "+z.message,"error"),f(v,!1)}},window._wiSecApprove=async(v,b,z,y,$)=>{f(v,!0);try{const E=q[v]?.tags_ai||{},R=Array.isArray(E.confirmed)?E.confirmed:[],A={...E,secondary:null,confirmed:[...R,{tag_id:z,tag_name:y,category:$}]};await m.workItems.patch(v,b,{tags_ai:A}),q[v]&&(q[v].tags_ai=A),Re(Object.values(q),b),p(`Saved ${$?$+":":""}${y||""} as metadata`,"success")}catch(E){p("Failed: "+E.message,"error"),f(v,!1)}},window._wiSecDismiss=async(v,b)=>{f(v,!0);try{const y={...q[v]?.tags_ai||{},secondary:null};await m.workItems.patch(v,b,{tags_ai:y}),q[v]&&(q[v].tags_ai=y),Re(Object.values(q),b)}catch(z){p("Dismiss failed: "+z.message,"error"),f(v,!1)}},window._wiPanelCreateTag=async(v,b,z,y)=>{const $=z||"task";f(v,!0);try{const E=await m.tags.categories.list(y),R=E.find(j=>j.name===$)||E.find(j=>j.name==="task")||E[0],A=await m.tags.create({name:b,project:y,category_id:R?.id});await m.workItems.patch(v,y,{tag_id_user:A.id}),delete q[v];const F=Object.values(q);Re(F,y);const M=document.getElementById("wi-panel-count");M&&(M.textContent=F.length?`(${F.length} unlinked)`:"(all linked ✓)"),p(`Created ${$} tag "${b}" and linked`,"success"),await Fe(y,!0),ke();const te=se().find(j=>j.name===$&&j.id!=null);te?await ft(te.id,te.name):(D.selectedCat&&ye(),Oe(y,$).catch(()=>{}))}catch(E){p("Create failed: "+E.message,"error"),f(v,!1)}};const u="font-size:0.58rem;font-weight:600;flex-shrink:0;padding:1px 5px;border-radius:3px;letter-spacing:.02em;white-space:nowrap",h=u+";color:#27ae60;border:1px solid #27ae6066;background:#27ae6012",_=u+";color:#e74c3c;border:1px solid #e74c3c66;background:#e74c3c12",C=u+";color:#4a90e2;border:1px solid #4a90e266;background:#4a90e212",S=d.map(v=>{const b=o[v.category_ai]||"📋",z=n[v.status_user]||"#888",y=(v.desc_ai||"").replace(/\n/g," ").trim(),$=v.ai_tag_color||"#27ae60",E=v.ai_tag_name?v.ai_tag_category?v.ai_tag_category+":"+v.ai_tag_name:v.ai_tag_name:"",R=v.tags_ai&&v.tags_ai.suggested_new?v.tags_ai.suggested_new:"",A=v.tags_ai&&v.tags_ai.suggested_category?v.tags_ai.suggested_category:"task",F=R?A+":"+R:"",M=Array.isArray(v.user_tags)?v.user_tags:[];let Q;E?Q=`<div style="display:flex;align-items:center;gap:4px;margin-top:3px;flex-wrap:wrap">
        <span style="${h}">AI(EXISTS)</span>
        <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                     color:${$};border:1px solid ${$};background:${$}1a;
                     white-space:nowrap">${w(E)}</span>
        <button onclick="event.stopPropagation();window._wiPanelApproveTag('${w(v.id)}','${w(t)}')"
          title="Link to this tag" style="background:none;border:1px solid #27ae60;color:#27ae60;
                 cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
        <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${w(v.id)}','${w(t)}')"
          title="Dismiss" style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;
                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
      </div>`:R?Q=`<div style="display:flex;align-items:center;gap:4px;margin-top:3px;flex-wrap:wrap">
        <span style="${_}">AI(NEW)</span>
        <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                     color:#e74c3c;border:1px solid #e74c3c;background:#e74c3c1a;
                     white-space:nowrap" title="Does not exist yet — click ✓ to create">${w(F)}</span>
        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${w(v.id)}','${w(R)}','${w(A)}','${w(t)}')"
          title="Create this tag and link" style="background:none;border:1px solid #27ae60;color:#27ae60;cursor:pointer;
                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
        <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${w(v.id)}','${w(t)}')"
          title="Dismiss suggestion" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
      </div>`:Q=`<div style="display:flex;align-items:center;gap:4px;margin-top:3px">
        <span style="${h}">AI(EXISTS)</span>
        <span style="font-size:0.62rem;color:var(--muted);opacity:.5">—</span>
      </div>`;let te="";const j=v.tags_ai&&v.tags_ai.secondary;if(j){const ae=u+";color:#8e44ad;border:1px solid #8e44ad66;background:#8e44ad12",Ie=j.tag_id?(j.category||"phase")+":"+(j.tag_name||""):(j.suggested_category||"phase")+":"+(j.suggested_new||"");if(Ie&&Ie!==":"&&!Ie.endsWith(":")){const Ke=w(j.tag_id||""),Dt=w(j.tag_name||j.suggested_new||""),_r=w(j.category||j.suggested_category||"");te=`<div style="display:flex;align-items:center;gap:4px;margin-top:2px;flex-wrap:wrap">
          <span style="${ae}" title="Metadata tag — ✓ saves for search/filter, item stays in list">AI</span>
          <span style="font-size:0.60rem;color:var(--muted);white-space:nowrap">${w(Ie)}</span>
          <button onclick="event.stopPropagation();window._wiSecApprove('${w(v.id)}','${w(t)}','${Ke}','${Dt}','${_r}')"
            title="Save as metadata tag (item stays in list)" style="background:none;border:1px solid #8e44ad;color:#8e44ad;
                   cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
          <button onclick="event.stopPropagation();window._wiSecDismiss('${w(v.id)}','${w(t)}')"
            title="Dismiss" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
                   font-size:0.6rem;font-weight:700;padding:1px 5px;border-radius:4px;line-height:1.5">×</button>
        </div>`}}const W=M.length?`<div style="display:flex;align-items:center;flex-wrap:wrap;gap:3px;margin-top:2px">
           <span style="${C}">USER</span>
           ${M.map(ae=>`<span style="font-size:0.62rem;color:#4a90e2;border:1px solid #4a90e266;background:#4a90e212;
                           padding:1px 5px;border-radius:4px;white-space:nowrap">${w(ae)}</span>`).join("")}
         </div>`:`<div style="display:flex;align-items:center;gap:4px;margin-top:2px">
           <span style="${C}">USER</span>
           <span style="font-size:0.62rem;color:var(--muted);opacity:.5">—</span>
         </div>`;return`<tr draggable="true"
        data-wi-id="${w(v.id)}"
        data-wi-name="${w(v.name_ai)}"
        ondragstart="window._wiBotDragStart(event,'${w(v.id)}','${w(v.name_ai)}','${w(v.category_ai)}')"
        ondragend="window._wiBotDragEnd(event)"
        onclick="window._plannerOpenWorkItemDrawer('${w(v.id)}','${w(v.category_ai)}','${w(t)}')"
        style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background=''">
      <td style="padding:4px 8px 6px 12px;min-width:0;overflow:hidden">
        <div style="display:flex;align-items:center;gap:4px;min-width:0">
          <button title="Delete this item"
            onclick="event.stopPropagation();window._wiPanelDelete('${w(v.id)}','${w(t)}')"
            style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.6rem;
                   font-weight:700;padding:1px 5px;border-radius:4px;line-height:1.5;flex-shrink:0">×</button>
          <span style="flex-shrink:0;font-size:0.78rem">${b}</span>
          ${v.seq_num?`<span style="font-size:0.58rem;color:var(--muted);flex-shrink:0">#${v.seq_num}</span>`:""}
          <span style="font-size:0.72rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;
                       white-space:nowrap;flex:1;min-width:0" title="${w(v.name_ai)}">${w(v.name_ai)}</span>
          <span style="font-size:0.56rem;color:${z};background:${z}1a;
                       padding:0 0.3rem;border-radius:6px;flex-shrink:0;white-space:nowrap">${v.status_user||"active"}</span>
        </div>
        ${y?`<div style="font-size:0.63rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                              white-space:nowrap;margin-top:1px" title="${w(y)}">${w(y)}</div>`:""}
        ${Q}
        ${te}
        ${W}
      </td>
      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                 color:var(--text2);font-variant-numeric:tabular-nums;
                 border-left:1px solid var(--border)">${v.prompt_count||0}</td>
      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                 color:var(--text2);font-variant-numeric:tabular-nums;
                 border-left:1px solid var(--border)">${v.commit_count||0}</td>
      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                 color:var(--text2);font-variant-numeric:tabular-nums;
                 border-left:1px solid var(--border)">${v.event_count||0}</td>
      <td style="padding:4px 10px 4px 6px;text-align:right;white-space:nowrap;font-size:0.66rem;vertical-align:top;
                 color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;
                 border-left:1px solid var(--border)">${l(v.updated_at||v.created_at)}</td>
    </tr>`}).join("");r.innerHTML=`
    <table style="width:100%;border-collapse:collapse;table-layout:fixed">
      <colgroup><col><col style="width:46px"><col style="width:46px"><col style="width:46px"><col style="width:112px"></colgroup>
      <thead><tr>
        <th style="text-align:left;padding:5px 8px 5px 12px;font-size:0.68rem;font-weight:600;
                   letter-spacing:.03em;text-transform:uppercase;
                   color:var(--muted);background:var(--surface2);
                   border-bottom:2px solid var(--border);position:sticky;top:0;z-index:1">Name</th>
        ${c("prompt_count","Prompts")}
        ${c("commit_count","Commits")}
        ${c("event_count","Events")}
        ${c("updated_at","Updated")}
      </tr></thead>
      <tbody>${S}</tbody>
    </table>`}async function Oe(e,t){try{const o=((await m.workItems.list({project:e})).work_items||[]).filter(s=>s.tag_id_user&&!s.merged_into);if(document.querySelectorAll(".wi-sub-row").forEach(s=>s.remove()),!o.length)return;const n={feature:"✨",bug:"🐛",task:"📋"},i={active:"#27ae60",in_progress:"#e67e22",done:"#4a90e2",paused:"#888"},a={};o.forEach(s=>{(a[s.tag_id_user]=a[s.tag_id_user]||[]).push(s)}),Object.entries(a).forEach(([s,d])=>{const l=document.querySelector(`tr[data-tag-id="${CSS.escape(s)}"]`);l&&[...d].reverse().forEach(c=>{const g=i[c.status_user]||"#888",f=n[c.category_ai]||"📋",u=document.createElement("tr");u.className="wi-sub-row",u.dataset.wiId=c.id,u.dataset.parentTagId=s,u.draggable=!0,u.style.cssText="cursor:grab;user-select:none;transition:background 0.1s",u.innerHTML=`
          <td colspan="3" style="padding:2px 8px 2px 26px;border-bottom:1px solid var(--border);
                                  background:var(--accent)07">
            <div style="display:flex;align-items:center;gap:4px">
              <span style="font-size:0.7rem;flex-shrink:0">${f}</span>
              <span style="font-size:0.63rem;color:var(--text);flex:1;overflow:hidden;
                           text-overflow:ellipsis;white-space:nowrap"
                    title="${w(c.desc_ai||"")}">${w(c.name_ai)}</span>
              <span style="font-size:0.52rem;color:${g};background:${g}22;
                           padding:0.02rem 0.25rem;border-radius:8px;flex-shrink:0">${c.status_user||"active"}</span>
              <button title="Delete work item"
                onclick="event.stopPropagation();window._wiDeleteLinked('${w(c.id)}','${w(e)}')"
                style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.55rem;
                       font-weight:700;padding:0 3px;border-radius:3px;line-height:1.3;flex-shrink:0;opacity:.6"
                onmouseenter="this.style.opacity=1" onmouseleave="this.style.opacity=.6">×</button>
              <button title="Unlink — move back to Work Items"
                onclick="event.stopPropagation();window._wiUnlink('${w(c.id)}','${w(e)}')"
                style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:0.75rem;
                       padding:0 3px;line-height:1;flex-shrink:0;opacity:.6"
                onmouseenter="this.style.opacity=1" onmouseleave="this.style.opacity=.6">↓</button>
            </div>
          </td>`,u.addEventListener("mouseenter",()=>u.style.background="var(--accent)12"),u.addEventListener("mouseleave",()=>u.style.background=""),u.addEventListener("click",h=>{h.target.closest("button")||window._plannerOpenWorkItemDrawer(c.id,c.category_ai,e)}),u.addEventListener("dragstart",h=>{ee={id:c.id,name_ai:c.name_ai,category_ai:c.category_ai},h.dataTransfer.effectAllowed="move",h.dataTransfer.setData("text/plain",c.id),u.style.opacity="0.45"}),u.addEventListener("dragend",()=>{u.style.opacity="",ee=null}),l.parentNode.insertBefore(u,l.nextSibling)})})}catch{}}const Zi=new Set(["feature","bug","task"]);function Ue(e){return Zi.has((e||"").toLowerCase())}const qe=new Set;let le=null,Ae=null,pt=null,de=null;function ye(){const{selectedCat:e,selectedCatName:t,selectedCatColor:r,selectedCatIcon:o}=D,n=document.getElementById("planner-tags-pane");!n||!e||ta(n,e,t,r,o)}async function ea(e,t,r,o,n,i){const a=document.getElementById("planner-drawer"),s=document.getElementById("planner-drawer-inner");if(!(!a||!s)){a.style.width="300px",a.style.borderLeftWidth="1px",s.innerHTML='<div style="padding:1rem;color:var(--muted);font-size:0.72rem">Loading…</div>';try{const[d,l]=await Promise.all([m.workItems.get(e,r),m.workItems.list({project:r,limit:200})]);if(!d||d.error){s.innerHTML='<div style="padding:1rem;color:var(--muted)">Not found</div>';return}const c=(l.work_items||[]).filter(u=>u.id!==e&&u.status_user!=="done"&&(d.tag_id_user?u.tag_id_user===d.tag_id_user:!u.tag_id_user)),g=d.seq_num?`<span style="font-size:0.55rem;color:var(--muted);background:var(--surface2);
                       border:1px solid var(--border);padding:0.1rem 0.35rem;
                       border-radius:6px;white-space:nowrap;cursor:default"
              title="Reference #${d.seq_num}">#${d.seq_num}</span>`:"",f=d.tag_id_user?`<span style="font-size:0.58rem;color:var(--accent);background:var(--accent)18;
                      padding:0.1rem 0.35rem;border-radius:8px">linked ✓</span>`:d.tag_id_ai?`<span style="font-size:0.58rem;color:var(--muted);border:1px solid var(--border);
                          padding:0.1rem 0.35rem;border-radius:8px;opacity:.7">✦ suggested</span>`:"";s.innerHTML=`
      <div style="padding:0.9rem 1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.5rem">
        ${g}
        <strong style="font-size:0.75rem;flex:1;overflow:hidden;text-overflow:ellipsis">${w(d.name_ai)}</strong>
        ${f}
        <button onclick="window._plannerCloseDrawer()"
          style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem">✕</button>
      </div>

      <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.85rem">

        <!-- Status row: user dropdown + AI badge -->
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
          <div style="display:flex;flex-direction:column;gap:0.2rem">
            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                        letter-spacing:.06em">Your Status</div>
            <select
              style="background:var(--surface2);border:1px solid var(--border);
                     color:var(--text);font-size:0.65rem;padding:0.2rem 0.4rem;
                     border-radius:var(--radius);font-family:var(--font);cursor:pointer"
              onchange="api.workItems.patch('${e}','${r}',{status_user:this.value}).catch(e=>toast(e.message,'error'))">
              ${["active","in_progress","paused","done"].map(u=>`<option value="${u}"${d.status_user===u?" selected":""}>${u}</option>`).join("")}
            </select>
          </div>
          <div style="display:flex;flex-direction:column;gap:0.2rem">
            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                        letter-spacing:.06em">AI Status</div>
            <span style="font-size:0.62rem;padding:0.18rem 0.5rem;border-radius:10px;
                         color:${{active:"#27ae60",in_progress:"#e67e22",done:"#4a90e2",paused:"#888"}[d.status_ai]||"#888"};
                         background:${{active:"#27ae60",in_progress:"#e67e22",done:"#4a90e2",paused:"#888"}[d.status_ai]||"#888"}22;
                         border:1px solid currentColor;opacity:.8" title="AI-suggested status based on progress">
              ${w(d.status_ai||"active")}
            </span>
          </div>
        </div>

        <!-- Stats row -->
        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;font-size:0.6rem;color:var(--muted)">
          <span>&#128172; <span id="wi-stat-prompts-${e}">${d.prompt_count||0} prompts</span></span>
          <span>&#9741; ${d.event_count||0} events</span>
          <span id="wi-stat-words-${e}">~… words</span>
          <span>&#8859; ${d.commit_count||0} commits</span>
          <span id="wi-stat-files-${e}"></span>
        </div>

        <!-- Extract Code button -->
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
          <button id="wi-extract-btn-${e}"
            onclick="window._extractWorkItemCode('${e}','${r}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none">
            &#11041; Extract Code
          </button>
          <span id="wi-extract-status-${e}" style="font-size:0.57rem;color:var(--muted)"></span>
        </div>

        <!-- tags_ai display (populated after extract) -->
        ${d.tags_ai&&d.tags_ai.code_summary?`
        <div id="wi-ai-tags-${e}" style="font-size:0.6rem;color:var(--muted)">
          <div style="font-size:0.52rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.2rem">Code Intelligence</div>
          ${d.tags_ai.code_summary.key_classes?.length?`<div>Classes: ${w(d.tags_ai.code_summary.key_classes.join(", "))}</div>`:""}
          ${d.tags_ai.code_summary.key_methods?.length?`<div>Methods: ${w(d.tags_ai.code_summary.key_methods.join(", "))}</div>`:""}
          ${d.tags_ai.test_coverage?.missing?.length?`<div style="color:#e67e22">Missing tests: ${w(d.tags_ai.test_coverage.missing.join(", "))}</div>`:""}
        </div>`:`<div id="wi-ai-tags-${e}"></div>`}

        <!-- Start date -->
        <div>
          <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.2rem">Start Date</div>
          <input type="date"
            value="${d.start_date?d.start_date.slice(0,10):""}"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.65rem;padding:0.2rem 0.4rem;
                   border-radius:var(--radius);outline:none"
            onchange="api.workItems.patch('${e}','${r}',{start_date:this.value||''})
                        .catch(e=>toast(e.message,'error'))" />
        </div>

        <!-- Description -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Description</div>
          <textarea rows="3"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.68rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${e}','${r}',{desc_ai:this.value}).catch(e=>toast(e.message,'error'))"
          >${w(d.desc_ai||"")}</textarea>
        </div>

        <!-- Requirements -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Requirements</div>
          <textarea rows="3"
            placeholder="Describe requirements…"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${e}','${r}',{}.catch(e=>toast(e.message,'error'))"
          >${w("")}</textarea>
        </div>

        <!-- Acceptance Criteria -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Acceptance Criteria</div>
          <textarea rows="4"
            placeholder="- [ ] Criteria 1&#10;- [ ] Criteria 2"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${e}','${r}',{acceptance_criteria_ai:this.value}).catch(e=>toast(e.message,'error'))"
          >${w(d.acceptance_criteria_ai||"")}</textarea>
        </div>

        <!-- Action Items -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Action Items</div>
          <textarea rows="4"
            placeholder="1. Step one&#10;2. Step two"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${e}','${r}',{action_items_ai:this.value}).catch(e=>toast(e.message,'error'))"
          >${w(d.action_items_ai||"")}</textarea>
        </div>

        ${d.summary_ai?`
        <!-- AI Summary (read-only) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">AI Progress Summary</div>
          <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;
                      background:var(--surface2);padding:0.35rem 0.45rem;
                      border-radius:var(--radius)">${w(d.summary_ai)}</div>
        </div>`:""}

        ${d.code_summary?`
        <!-- Code Summary (read-only) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Code Summary</div>
          <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;font-family:monospace;
                      background:var(--surface2);padding:0.35rem 0.45rem;
                      border-radius:var(--radius);white-space:pre-wrap">${w(d.code_summary)}</div>
        </div>`:""}

        <!-- Linked Commits (loaded async) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Commits</div>
          <div id="wi-commits-${e}" style="font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- Merge into (only if siblings exist and this item is not itself a merged result) -->
        ${c.length&&!d.merge_count?`
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Merge Into…</div>
          <div style="display:flex;gap:5px">
            <select id="wi-merge-sel-${e}"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.65rem;padding:0.22rem 0.45rem;
                     border-radius:var(--radius);outline:none;min-width:0">
              <option value="">— select work item —</option>
              ${c.map(u=>`<option value="${w(u.id)}">${w(u.name_ai)}</option>`).join("")}
            </select>
            <button onclick="window._wiMergeInto('${e}','${r}')"
              style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);
                     font-size:0.6rem;padding:0.22rem 0.55rem;border-radius:var(--radius);
                     cursor:pointer;font-family:var(--font);outline:none;white-space:nowrap">⊕ Merge</button>
          </div>
          <div id="wi-merge-msg-${e}" style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem;min-height:0.8rem"></div>
        </div>`:""}

        <!-- Delete / Dismerge -->
        <div style="border-top:1px solid var(--border);padding-top:0.75rem;display:flex;gap:0.5rem;flex-wrap:wrap">
          ${d.merge_count>0?`
          <button onclick="window._wiDismerge('${e}','${r}')"
            title="Restore the ${d.merge_count} original item(s) and remove this merged result"
            style="background:none;border:1px solid var(--accent);color:var(--accent);
                   font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                   cursor:pointer;font-family:var(--font);outline:none">⊕ Dismerge (restore ${d.merge_count})</button>
          `:""}
          <button onclick="window._wiDelete('${e}','${r}')"
            style="background:none;border:1px solid var(--red,#e74c3c);color:var(--red,#e74c3c);
                   font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                   cursor:pointer;font-family:var(--font);outline:none">Delete ✕</button>
        </div>

      </div>
    `,window._wiDelete=async(u,h)=>{if(confirm("Delete this work item?"))try{await m.workItems.delete(u,h),tt(),fe(h)}catch(_){p("Delete failed: "+_.message,"error")}},window._wiDismerge=async(u,h)=>{if(confirm("Restore the original items and remove this merged result?"))try{const _=await m.workItems.dismerge(u,h);p(`Dismerged — ${_.restored.length} item(s) restored`,"success"),tt(),fe(h),Oe(h).catch(()=>{})}catch(_){p("Dismerge failed: "+_.message,"error")}},window._wiMergeInto=async(u,h)=>{const _=document.getElementById(`wi-merge-sel-${u}`),C=document.getElementById(`wi-merge-msg-${u}`),S=_?.value;if(!S){C&&(C.textContent="Select a work item first.");return}if(confirm("Merge these two work items into a new combined item?"))try{C&&(C.textContent="Merging…"),await m.workItems.merge(u,S,h),p("⊕ Merged — new combined item created","success"),tt(),fe(h),Oe(h).catch(()=>{})}catch(v){C&&(C.textContent="Error: "+v.message),p("Merge failed: "+v.message,"error")}},m.workItems.commits(e,r).then(u=>{const h=document.getElementById(`wi-commits-${e}`);if(!h)return;const _=u&&u.commits||[];if(!_.length){h.textContent="No linked commits";return}h.innerHTML=_.map(y=>`
        <div style="padding:0.25rem 0;border-bottom:1px solid var(--border)">
          <div style="color:var(--text);font-weight:500">${w((y.commit_msg||"").slice(0,60))}${(y.commit_msg||"").length>60?"…":""}</div>
          ${y.summary?`<div style="color:var(--muted);font-size:0.58rem;margin-top:0.15rem">${w(y.summary.slice(0,80))}</div>`:""}
          <div style="color:var(--muted);font-size:0.55rem;margin-top:0.1rem">${y.commit_hash?y.commit_hash.slice(0,8):""} · ${y.committed_at?y.committed_at.slice(0,10):""}</div>
        </div>`).join("");const C={};let S=0,v=0;_.forEach(y=>{if(!y.diff_summary)return;const $=(y.diff_summary.match(/(\d+) insertions?\(\+\)/)||[])[1],E=(y.diff_summary.match(/(\d+) deletions?\(-\)/)||[])[1];$&&(S+=parseInt($)),E&&(v+=parseInt(E)),y.diff_summary.split(`
`).forEach(R=>{const A=R.match(/^\s*(.+?)\s*\|\s*\d+/);A&&(C[A[1].trim()]=!0)})});const b=Object.keys(C).length,z=document.getElementById(`wi-stat-files-${e}`);if(z&&b>0&&(z.textContent=`&#128193; ${b} files · +${S}/-${v}`),b>0){const y=Object.keys(C).map($=>`<div style="font-size:0.57rem;color:var(--muted)">${w($)}</div>`).join("");h.insertAdjacentHTML("beforeend",`<details style="margin-top:4px"><summary style="font-size:0.58rem;
             color:var(--muted);cursor:pointer">Files (${b})</summary>${y}</details>`)}m.workItems.interactions(e,r,100).then(y=>{const $=(y?.interactions||[]).reduce((R,A)=>R+(A.prompt||"").length+(A.response||"").length,0),E=document.getElementById(`wi-stat-words-${e}`);E&&(E.textContent=`~${Math.round($/5).toLocaleString()} words`)}).catch(()=>{})}).catch(()=>{const u=document.getElementById(`wi-commits-${e}`);u&&(u.textContent="No linked commits")})}catch(d){s.innerHTML=`<div style="padding:1rem;color:#e74c3c;font-size:0.72rem">Error: ${w(d.message)}</div>`}}}function ta(e,t,r,o,n){const i={active:"#27ae60",done:"#4a90e2",archived:"#888"},a=r==="ai_suggestion";let s=cn(t);if(a&&D.aiSubtypeFilter){const l=`[suggested: ${D.aiSubtypeFilter}]`;s=s.filter(c=>(c.description||"").toLowerCase().startsWith(l))}function d(l,c){const g=i[l.status]||"#888",f=l.status==="archived",u=Kr(l.id),h=u.length>0,_=!qe.has(l.id),C=c*20,S=h?`<span onclick="window._plannerToggleExpand('${l.id}')"
               style="cursor:pointer;color:var(--muted);margin-right:3px;display:inline-block;
                      width:14px;text-align:center;font-size:0.72rem;user-select:none;flex-shrink:0"
               title="${_?"Collapse":"Expand"}">${_?"▾":"▸"}</span>`:'<span style="display:inline-block;width:14px;margin-right:3px;flex-shrink:0"></span>';let v=`
      <tr style="border-bottom:1px solid var(--border);opacity:${f?"0.45":"1"};
                 transition:background 0.1s;cursor:grab;user-select:none"
          data-val-id="${l.id}" data-tag-id="${l.id}" data-tag-name="${w(l.name)}"
          data-cat-id="${t}" data-cat-name="${w(r)}"
          draggable="true"
          onclick="window._plannerOpenDrawer(${t},'${l.id}')"
          onmouseenter="this.style.background='var(--surface2)'"
          onmouseleave="this.style.background=''">
        <td style="padding:0.5rem 0.5rem 0.5rem ${.5+C/16}rem;
                   color:var(--text);font-weight:${c===0?"500":"400"}">
          <div style="display:flex;align-items:center">
            ${S}
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${w(l.name)}</span>
          </div>
        </td>
        <td style="padding:0.5rem 0.5rem;white-space:nowrap" onclick="event.stopPropagation()">
          <span style="font-size:0.6rem;color:${g};background:${g}22;
                       padding:0.12rem 0.4rem;border-radius:10px;white-space:nowrap;user-select:none">
            ${w(l.status||"active")}
          </span>
        </td>
        <td style="padding:0.5rem 0.4rem;text-align:right;white-space:nowrap" onclick="event.stopPropagation()">
          <button onclick="window._plannerAddChild(${t},'${l.id}')"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;margin-right:3px"
            title="Add child tag">+▸</button>
          ${Ue(r)?`<button
            onclick="event.stopPropagation();window._plannerOpenDrawer(${t},'${l.id}');
                     setTimeout(()=>window._plannerDrawerRunPipeline('${w(r)}','${w(l.name)}','${w(D.project)}'),200)"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--accent)18;
                   border:1px solid var(--accent);border-radius:var(--radius);cursor:pointer;
                   color:var(--accent);font-family:var(--font);outline:none;margin-right:3px"
            title="Run AI Pipeline">▶</button>`:""}
          <button onclick="window._plannerOpenDrawer(${t},'${l.id}')"
            style="font-size:0.85rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);
                   cursor:pointer;color:var(--text2);font-family:var(--font);outline:none;
                   transition:background 0.12s,color 0.12s;line-height:1"
            onmouseenter="this.style.background='var(--accent)';this.style.color='#fff'"
            onmouseleave="this.style.background='var(--surface2)';this.style.color='var(--text2)'"
            title="Open details">⋯</button>
        </td>
      </tr>`;return h&&_&&(v+=u.map(b=>d(b,c+1)).join("")),v}if(e.innerHTML=`
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span style="font-size:0.8rem;color:${o}">${n}</span>
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">
        ${a&&D.aiSubtypeFilter?`AI → ${D.aiSubtypeFilter}`:w(r)}
      </span>
      ${a?"":`<button onclick="window._plannerShowNewTag(${t})"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New Tag</button>`}
    </div>

    <!-- New tag inline row (hidden) -->
    <div id="planner-new-tag-row"
         style="display:none;gap:0.4rem;align-items:center;margin-bottom:0.5rem;
                padding:0.4rem 0.5rem;background:var(--surface2);
                border:1px solid var(--border);border-radius:var(--radius)">
      <span id="planner-new-tag-label" style="font-size:0.6rem;color:var(--muted);white-space:nowrap;flex-shrink:0"></span>
      <input id="planner-new-tag-inp" placeholder="Tag name…" type="text"
        onkeydown="if(event.key==='Enter')window._plannerSaveNewTag();if(event.key==='Escape')window._plannerCancelNewTag()"
        style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
               font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
               border-radius:var(--radius);outline:none" />
      <button onclick="window._plannerSaveNewTag()"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">Save</button>
      <button onclick="window._plannerCancelNewTag()"
        style="background:none;border:1px solid var(--border);color:var(--muted);font-size:0.62rem;
               padding:0.22rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">✕</button>
    </div>

    ${s.length===0?`
      <div style="text-align:center;padding:3rem 1rem;color:var(--muted);font-size:0.72rem">
        <div style="font-size:2rem;margin-bottom:0.75rem">${n}</div>
        No tags in <strong>${w(r)}</strong> yet — click <strong>+ New Tag</strong>
      </div>`:`
    <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
      <thead>
        <tr style="border-bottom:2px solid var(--border)">
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500;width:75px">Status</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        ${s.map(l=>d(l,0)).join("")}
      </tbody>
    </table>`}
  `,_a(e),Ue(r)){const{project:l}=D;l&&Oe(l).catch(()=>{})}window._plannerShowNewTag=(l,c=null)=>{const g=document.getElementById("planner-new-tag-row"),f=document.getElementById("planner-new-tag-label");g&&(g.style.display="flex",g.dataset.catId=l,g.dataset.parentId=c??""),f&&(f.textContent=c?"Child tag:":"New root tag:"),setTimeout(()=>document.getElementById("planner-new-tag-inp")?.focus(),0)}}let Rt=null,yr=null;function ra(e,t){Rt=t,yr=e;const r=document.getElementById("planner-drawer");r&&(r.style.width="300px",r.style.borderLeftWidth="1px"),zo(),hr(t);const{selectedCatName:o,project:n}=D;if(Ue(o)){const i=Pe(e).find(a=>a.id===t);i&&Io(o,i.name,n)}oa(t,D.project)}function tt(){const e=document.getElementById("planner-drawer");e&&(e.style.width="0",e.style.borderLeftWidth="0"),Rt=null,yr=null}async function oa(e,t){const r=document.getElementById("drawer-wf-uc-section");if(r)try{const o=await m.tags.getSnapshot(e,t,"user").catch(()=>m.tags.getSnapshot(e,t,"ai").catch(()=>null));if(!o?.use_cases?.length){r.innerHTML="";return}r.innerHTML=`
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.4rem">Use Cases</div>
        ${o.use_cases.map(n=>`
          <div style="display:flex;align-items:center;justify-content:space-between;
                      gap:0.4rem;margin-bottom:0.35rem">
            <span style="font-size:0.67rem;color:var(--text2);overflow:hidden;
                         text-overflow:ellipsis;white-space:nowrap;flex:1"
                  title="${n.use_case_summary||""}">
              UC${n.use_case_num}: ${n.use_case_type||"feature"}
            </span>
            <button
              onclick="window._plannerWfPicker('${e}',${n.use_case_num},'${(n.use_case_summary||"").replace(/'/g,"\\")}','${t}')"
              style="font-size:0.6rem;padding:0.18rem 0.45rem;white-space:nowrap;
                     background:var(--surface2);border:1px solid var(--border);
                     border-radius:var(--radius);cursor:pointer;color:var(--accent);
                     font-family:var(--font);outline:none;flex-shrink:0">
              ▶ Workflow
            </button>
          </div>
        `).join("")}
      </div>
    `}catch{r.innerHTML=""}}function zo(){const e=document.getElementById("planner-drawer-inner");if(!e||!Rt)return;const t=yr,r=Pe(t),o=r.find(h=>h.id===Rt);if(!o){tt();return}const n={open:"#888",active:"#27ae60",done:"#4a90e2",archived:"#666"},i={open:"○ Open",active:"● Active",done:"✓ Done",archived:"⊘ Archived"},a=Object.fromEntries(r.map(h=>[String(h.id),h])),s=[];let d=o;for(;d;)s.unshift(d.name),d=d.parent_id?a[String(d.parent_id)]:null;const l=s.join(" / "),c=o.due_date||"",g=(o.created_at||"").slice(0,10),f=o.description||"",u=h=>{const _=o.status===h,C=n[h]||"#888";return`background:${_?C:"var(--surface2)"};color:${_?"#fff":"var(--text2)"};
            border:1px solid ${_?C:"var(--border)"};font-size:0.62rem;
            padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
            font-family:var(--font);outline:none;transition:all 0.12s;white-space:nowrap`};e.innerHTML=`
    <div style="padding:0.9rem 1rem;border-bottom:1px solid var(--border);
                display:flex;align-items:flex-start;gap:0.5rem">
      <div style="flex:1;min-width:0">
        <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.15rem;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
             title="${w(l)}">${w(l)}</div>
      </div>
      <button onclick="window._plannerCloseDrawer()"
        style="background:none;border:none;color:var(--muted);cursor:pointer;
               font-size:1rem;padding:0;line-height:1;flex-shrink:0">✕</button>
    </div>

    <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.9rem">

      <!-- Status -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Status</div>
        <div style="display:flex;gap:5px;flex-wrap:wrap">
          ${["open","active","done","archived"].map(h=>`
            <button style="${u(h)}"
              onclick="window._plannerDrawerSetStatus('${o.id}','${h}')">
              ${i[h]}
            </button>`).join("")}
        </div>
      </div>

      <!-- Short Description -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Description</div>
        <textarea id="tag-short-desc-ta" rows="2"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.68rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${o.id}', {description: this.value}).catch(e=>toast(e.message,'error'))"
        >${w(o.description||"")}</textarea>
      </div>

      <!-- Requirements -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Requirements</div>
        <textarea id="tag-req-ta" rows="3"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${o.id}', {requirements: this.value}).catch(e=>toast(e.message,'error'))"
        >${w(o.requirements||"")}</textarea>
      </div>

      <!-- Acceptance Criteria -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Acceptance Criteria</div>
        <textarea id="tag-ac-ta" rows="3"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${o.id}', {acceptance_criteria: this.value}).catch(e=>toast(e.message,'error'))"
        >${w(o.acceptance_criteria||"")}</textarea>
      </div>

      <!-- Priority + Due Date row -->
      <div style="display:flex;gap:0.6rem">
        <div style="flex:1">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Priority</div>
          <select
            onchange="api.tags.update('${o.id}', {priority: parseInt(this.value)}).catch(e=>toast(e.message,'error'))"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.22rem 0.4rem;border-radius:var(--radius);outline:none">
            ${[1,2,3,4,5].map(h=>`<option value="${h}" ${(o.priority||3)===h?"selected":""}>${h===1?"1 Critical":h===2?"2 High":h===3?"3 Normal":h===4?"4 Low":"5 Minimal"}</option>`).join("")}
          </select>
        </div>
        <div style="flex:1">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Due Date</div>
          <input type="date" value="${w(o.due_date?o.due_date.slice(0,10):"")}"
            onchange="api.tags.update('${o.id}', {due_date: this.value || null}).catch(e=>toast(e.message,'error'))"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.22rem 0.4rem;border-radius:var(--radius);outline:none;
                   box-sizing:border-box" />
        </div>
      </div>

      <!-- Remarks -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Remarks / Description</div>
        <textarea id="drawer-desc-ta" rows="3"
          onblur="window._plannerDrawerSaveRemarks('${o.id}',this.value)"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.68rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5">${w(f)}</textarea>
      </div>

      <!-- Due date -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Due Date</div>
        <input type="date" value="${w(c)}"
          onchange="window._plannerDrawerSaveDue('${o.id}',this.value)"
          style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                 font-family:var(--font);font-size:0.68rem;padding:0.25rem 0.4rem;
                 border-radius:var(--radius);outline:none;width:100%;box-sizing:border-box" />
      </div>

      <!-- Dependencies (Blocks) -->
      <div id="drawer-links-section">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Dependencies (Blocks)</div>
        <div id="drawer-links-chips" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:0.4rem">
          <span style="font-size:0.62rem;color:var(--muted)">Loading…</span>
        </div>
        <div style="display:flex;gap:5px;align-items:center">
          <input id="drawer-link-inp" type="text" placeholder="Value name to block…"
            list="drawer-link-datalist"
            style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.65rem;padding:0.2rem 0.4rem;
                   border-radius:var(--radius);outline:none" />
          <datalist id="drawer-link-datalist">
            ${Pe(t).map(h=>`<option value="${w(h.name)}"></option>`).join("")}
          </datalist>
          <button onclick="window._plannerDrawerAddLink('${o.id}',${t})"
            style="background:var(--accent);border:none;color:#fff;font-size:0.6rem;
                   padding:0.2rem 0.5rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;white-space:nowrap">+ Link</button>
        </div>
        <div id="drawer-link-msg" style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem;min-height:0.8rem"></div>
      </div>

      <!-- Meta -->
      <div style="display:flex;gap:1.5rem">
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.2rem">Created</div>
          <div style="font-size:0.68rem;color:var(--text2)">${g||"—"}</div>
        </div>
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.2rem">Events</div>
          <div style="font-size:0.68rem;color:var(--text2)">${o.event_count||0}</div>
        </div>
      </div>

      <!-- AI Pipeline (feature/bug/task only) -->
      ${Ue(D.selectedCatName)?`
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">AI Pipeline</div>
        <div id="drawer-pipeline-content">
          <span style="font-size:0.62rem;color:var(--muted)">Checking…</span>
        </div>
      </div>`:""}

      <!-- Planner -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Planner</div>
        <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap">
          <button id="drawer-planner-btn"
            onclick="window._plannerRunPlan('${o.id}','${w(o.name)}','${w(o.category_name||D.selectedCatName)}','${w(D.project)}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;white-space:nowrap">
            &#9641; Run Planner
          </button>
          <span id="drawer-planner-doc" style="font-size:0.57rem;color:var(--muted)"></span>
        </div>
      </div>

      <!-- Snapshot -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Memory Snapshot</div>
        <div style="display:flex;gap:5px;align-items:center">
          <button id="drawer-snapshot-btn"
            onclick="window._plannerGenerateSnapshot('${w(o.name)}','${w(D.project)}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--accent)18;
                   border:1px solid var(--accent);border-radius:var(--radius);cursor:pointer;
                   color:var(--accent);font-family:var(--font);outline:none;white-space:nowrap">
            ◈ Generate Snapshot
          </button>
          <span id="drawer-snapshot-msg" style="font-size:0.58rem;color:var(--muted)"></span>
        </div>
      </div>

      <!-- Use Cases / Workflow -->
      <div id="drawer-wf-uc-section"></div>

      <!-- Add sub-tag -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Add Sub-tag</div>
        <div style="display:flex;gap:5px">
          <input id="drawer-child-inp" type="text" placeholder="Sub-tag name…"
            onkeydown="if(event.key==='Enter')window._plannerDrawerAddChild(${t},'${o.id}')"
            style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
                   border-radius:var(--radius);outline:none" />
          <button onclick="window._plannerDrawerAddChild(${t},'${o.id}')"
            style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
                   padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;white-space:nowrap">+ Add</button>
        </div>
        <div id="drawer-child-msg" style="font-size:0.6rem;color:var(--muted);margin-top:0.25rem;min-height:0.9rem"></div>
      </div>

      <!-- Danger zone -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <button onclick="window._plannerDeleteVal('${o.id}')"
          style="background:none;border:1px solid var(--red,#e74c3c);color:var(--red,#e74c3c);
                 font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                 cursor:pointer;font-family:var(--font);outline:none;
                 transition:background 0.12s,color 0.12s"
          onmouseenter="this.style.background='var(--red,#e74c3c)';this.style.color='#fff'"
          onmouseleave="this.style.background='none';this.style.color='var(--red,#e74c3c)'">
          Delete tag ✕
        </button>
      </div>

    </div>
  `}function na(e,t){ar(e,{status:t}),ye(),ke(),zo(),m.entities.patchValue(e,{status:t}).catch(r=>p("Sync error: "+r.message,"error"))}function ia(e,t){const r=(t||"").trim();ar(e,{description:r}),m.entities.patchValue(e,{description:r}).catch(o=>p("Sync error: "+o.message,"error"))}function aa(e,t){ar(e,{due_date:t||null}),m.entities.patchValue(e,{due_date:t||""}).catch(r=>p("Sync error: "+r.message,"error"))}async function sa(e,t){const r=document.getElementById("drawer-child-inp"),o=document.getElementById("drawer-child-msg"),n=(r?.value||"").trim();if(!n){o&&(o.textContent="Enter a name");return}const{project:i}=D;o&&(o.textContent="Saving…");try{const a=await m.entities.createValue({category_id:e,name:n,project:i,parent_id:t});ir(e,{id:a.id,category_id:e,name:n,description:"",status:"active",event_count:0,due_date:null,parent_id:t,created_at:new Date().toISOString()}),qe.delete(t),r&&(r.value=""),o&&(o.textContent=`✓ "${n}" added`),ye(),ke()}catch(a){o&&(o.textContent=a.message)}}async function Io(e,t,r){const o=document.getElementById("drawer-pipeline-content");if(o)try{const i=((await m.workItems.list({project:r,category:e,name:t})).work_items||[]).find(c=>c.name===t),a=`<button id="drawer-run-pipeline-btn"
      onclick="window._plannerDrawerRunPipeline('${w(e)}','${w(t)}','${w(r)}')"
      style="font-size:0.62rem;padding:0.2rem 0.55rem;background:var(--accent);border:none;
             color:#fff;border-radius:var(--radius);cursor:pointer;font-family:var(--font);
             outline:none;white-space:nowrap">▶ Run Pipeline</button>`;if(!i){o.innerHTML=`<div style="display:flex;gap:6px;align-items:center">
        ${a}
        <span style="font-size:0.6rem;color:var(--muted)">No run yet</span>
      </div>`;return}const s=i.agent_status?`<span style="font-size:0.55rem;padding:0.1rem 0.4rem;border-radius:8px;color:#fff;
                      background:${i.agent_status==="done"?"#27ae60":i.agent_status==="failed"?"#e74c3c":"#e67e22"}">
           ${w(i.agent_status)}</span>`:"",d=i.acceptance_criteria?`<div style="margin-top:0.5rem">
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.25rem">Acceptance Criteria</div>
           <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;white-space:pre-wrap;
                       max-height:100px;overflow-y:auto;background:var(--surface2);
                       padding:0.35rem 0.5rem;border-radius:var(--radius)">${w(i.acceptance_criteria_ai)}</div>
         </div>`:"",l=i.implementation_plan?`<div style="margin-top:0.5rem">
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.25rem">Implementation Plan</div>
           <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;white-space:pre-wrap;
                       max-height:100px;overflow-y:auto;background:var(--surface2);
                       padding:0.35rem 0.5rem;border-radius:var(--radius)">${w(i.implementation_plan)}</div>
         </div>`:"";o.innerHTML=`<div style="display:flex;gap:6px;align-items:center;margin-bottom:0.35rem">
      ${a} ${s}
    </div>${d}${l}`}catch(n){o&&(o.innerHTML=`<span style="font-size:0.6rem;color:var(--red)">${w(n.message)}</span>`)}}window._plannerDrawerRunPipeline=async(e,t,r)=>{const o=document.getElementById("drawer-run-pipeline-btn");o&&(o.disabled=!0,o.textContent="…");try{let i=((await m.workItems.list({project:r,category:e,name:t})).work_items||[]).find(d=>d.name===t);i||(i=await m.workItems.create(r,{category_name:e,name:t}));const a=await m.workItems.runPipeline(i.id,r),s=a.run_id?String(a.run_id):null;if(s){window._pendingRunOpen=s,window._nav("workflow");let d=0;const l=setInterval(()=>{d+=200,window._gwOpenRun?(clearInterval(l),window._gwOpenRun(s),window._pendingRunOpen=null):d>=4e3&&clearInterval(l)},200)}else p("Pipeline started — check Pipelines tab for progress","success",5e3);setTimeout(()=>Io(e,t,r),5e3)}catch(n){p("Pipeline error: "+n.message,"error"),o&&(o.disabled=!1,o.textContent="▶ Run Pipeline")}};async function da(e,t){const r=document.getElementById("drawer-snapshot-btn"),o=document.getElementById("drawer-snapshot-msg");if(!(!r||!t)){r.disabled=!0,r.textContent="… Generating",o&&(o.textContent="");try{const n=await fetch((window._serverUrl||"http://localhost:8000")+`/projects/${encodeURIComponent(t)}/snapshot/${encodeURIComponent(e)}`,{method:"POST",headers:{"Content-Type":"application/json",...window._authHeaders?window._authHeaders():{}}});if(!n.ok){const i=await n.json().catch(()=>({}));throw new Error(i.detail||n.statusText)}o&&(o.textContent="✓ Snapshot ready",o.style.color="var(--green, #27ae60)"),p('Snapshot generated for "'+e+'"',"success")}catch(n){o&&(o.textContent="✗ "+n.message,o.style.color="var(--red, #e74c3c)"),p("Snapshot error: "+n.message,"error")}finally{r.disabled=!1,r.textContent="◈ Generate Snapshot"}}}async function la(e,t){const r=document.getElementById("drawer-merge-inp"),o=document.getElementById("drawer-merge-msg"),n=(r?.value||"").trim();if(!n){o&&(o.textContent="Enter target tag name");return}if(confirm(`Merge "${e}" into "${n}"? This moves all sources to the target and marks ${e} as merged.`)){o&&(o.textContent="…");try{await m.tags.merge({project:t,from_name:e,into_name:n}),p(`Merged "${e}" → "${n}"`,"success"),await To()}catch(i){o&&(o.textContent="✗ "+i.message),p("Merge error: "+i.message,"error")}}}async function ca(e){confirm("Delete this tag (and all its children + event links)?")&&(Tt(e).forEach(t=>zr(t.id)),zr(e),qe.delete(e),tt(),ye(),ke(),m.entities.deleteValue(e).catch(t=>p("Delete sync error: "+t.message,"error")))}async function ma(){const e=document.getElementById("planner-new-tag-inp"),t=document.getElementById("planner-new-tag-row"),r=(e?.value||"").trim();if(!r){p("Name required","error");return}const o=t?parseInt(t.dataset.catId,10):D.selectedCat,n=t?.dataset.parentId||null,{project:i}=D;try{const a=await m.entities.createValue({category_id:o,name:r,project:i,parent_id:n});ir(o,{id:a.id,category_id:o,name:r,description:"",status:"active",event_count:0,due_date:null,parent_id:n,created_at:new Date().toISOString()}),e&&(e.value=""),n&&qe.delete(n),So(),ye(),ke()}catch(a){p("Create failed: "+a.message,"error")}}function So(){const e=document.getElementById("planner-new-tag-row");e&&(e.style.display="none");const t=document.getElementById("planner-new-tag-inp");t&&(t.value="")}function pa(e,t){const r=document.getElementById("planner-new-tag-row"),o=document.getElementById("planner-new-tag-label"),n=document.getElementById("planner-new-tag-inp"),i=Pe(e).find(a=>a.id===t);r&&(r.style.display="flex",r.dataset.catId=e,r.dataset.parentId=t),o&&(o.textContent=`Child of "${i?.name??t}":`),n&&(n.value=""),setTimeout(()=>n?.focus(),0)}function ua(e){qe.has(e)?qe.delete(e):qe.add(e),ye()}async function ga(e){if(e=(e||"").trim(),!e)return;const{project:t}=D,r=document.getElementById("planner-new-cat-inp");try{const o=await m.entities.createCategory({name:e,project:t});mn({id:o.id,name:e,color:"#4a90e2",icon:"⬡"}),r&&(r.value=""),ke()}catch(o){p("Create failed: "+o.message,"error")}}async function To(){const{project:e,selectedCat:t,selectedCatName:r}=D;if(e)try{const o=await m.entities.syncEvents(e);p(`Synced — ${o.imported?.prompt||0} prompts, ${o.imported?.commit||0} commits`,"success"),await Fe(e,!0),ke(),t&&ye(),fe(e)}catch(o){p(o.message,"error")}}async function fa(){const{project:e}=D;if(e)try{const r=(await m.tags.migrateToAiSuggestions(e)).moved||0;r>0?(p(`Moved ${r} auto-created tag${r!==1?"s":""} to AI Suggestions`,"success"),await Fe(e,!0),ke(),ye()):p("No AI-auto-created tags found to migrate","info")}catch(t){p("Migration failed: "+t.message,"error")}}async function hr(e){const t=document.getElementById("drawer-links-chips");if(t)try{const r=await m.entities.getValueLinks(e);va(e,r.outgoing||[])}catch{t&&(t.innerHTML='<span style="font-size:0.62rem;color:var(--muted)">—</span>')}}function va(e,t){const r=document.getElementById("drawer-links-chips");if(r){if(!t.length){r.innerHTML='<span style="font-size:0.62rem;color:var(--muted)">None</span>';return}r.innerHTML=t.map(o=>`
    <span style="display:inline-flex;align-items:center;gap:3px;font-size:0.62rem;
                 background:${o.color||"var(--accent)"}22;color:${o.color||"var(--accent)"};
                 border:1px solid ${o.color||"var(--accent)"}44;
                 padding:0.1rem 0.35rem;border-radius:10px">
      ${w(o.name)}
      <span onclick="window._plannerDrawerRemoveLink('${e}','${o.to_value_id}')"
            style="cursor:pointer;color:var(--muted);font-size:0.75rem;margin-left:1px">×</span>
    </span>`).join("")}}async function ya(e,t){const r=document.getElementById("drawer-link-inp"),o=document.getElementById("drawer-link-msg"),n=(r?.value||"").trim();if(!n){o&&(o.textContent="Enter a value name");return}const a=Pe(t).find(s=>s.name===n&&s.id!==e);if(!a){o&&(o.textContent=`"${n}" not found in this category`);return}o&&(o.textContent="Linking…");try{await m.entities.createValueLink(e,{to_value_id:a.id,link_type:"blocks"}),r&&(r.value=""),o&&(o.textContent="✓ Linked"),await hr(e)}catch(s){o&&(o.textContent=s.message)}}async function ha(e,t){try{await m.entities.deleteValueLink(e,t),await hr(e)}catch(r){p("Remove link failed: "+r.message,"error")}}function ba(e,t){const r=t.getBoundingClientRect(),o=(e.clientY-r.top)/r.height;return o<.28?"top":o>.72?"bot":"mid"}function wa(e,t){Je(),Ae=e,pt=t,t==="top"?e.style.borderTop="2px solid var(--accent)":t==="bot"?e.style.borderBottom="2px solid var(--accent)":(e.style.background="rgba(255,165,0,0.08)",e.style.outline="1px dashed rgba(255,165,0,0.5)");const r=document.getElementById("planner-dnd-hint");r&&(r.textContent=t==="top"?"↑ Make parent":t==="mid"?"⊕ Merge":"↓ Make child",r.style.color=t==="mid"?"#e67e22":"var(--accent)")}function Je(){Ae&&(Ae.style.borderTop=Ae.style.borderBottom="",Ae.style.background=Ae.style.outline="",Ae=null),pt=null;const e=document.getElementById("planner-dnd-hint");e&&(e.style.display="none")}async function xa(e,t,r){const o=D.project;if(D.selectedCat,e!=="mid"){const n=Tt(t.id)||[],i=Tt(r.id)||[];if(e==="bot"&&n.some(a=>a.id===r.id)){p("Cannot make a descendant a parent","error");return}if(e==="top"&&i.some(a=>a.id===t.id)){p("Cannot create circular hierarchy","error");return}}if(e==="mid"){if(!confirm(`Merge "${t.name}" into "${r.name}"?

"${t.name}" will be archived and all its history remapped to "${r.name}". This cannot be undone.`))return;await m.tags.merge({project:o,from_name:t.name,into_name:r.name}),p(`Merged "${t.name}" → "${r.name}"`,"success")}else e==="bot"?(await m.tags.update(t.id,{parent_id:r.id}),p(`"${t.name}" is now a child of "${r.name}"`,"success")):(await m.tags.update(r.id,{parent_id:t.id}),p(`"${r.name}" is now a child of "${t.name}"`,"success"));await Fe(o,!0),ye(),ke()}function Ar(){if(document.getElementById("planner-dnd-hint"))return;const e=document.createElement("div");e.id="planner-dnd-hint",e.style.cssText="position:fixed;pointer-events:none;z-index:9999;display:none;font-size:0.62rem;background:var(--surface2);border:1px solid var(--border);padding:0.2rem 0.5rem;border-radius:var(--radius);white-space:nowrap;font-family:var(--font)",document.body.appendChild(e)}function _a(e,t){Ar(),e.querySelectorAll("tr[data-tag-id]").forEach(o=>{o.addEventListener("dragstart",function(n){const i=this.dataset;le={id:i.tagId,name:i.tagName,category_id:Number(i.catId),category_name:i.catName},n.dataTransfer.effectAllowed="move",n.dataTransfer.setData("text/plain",i.tagId),this.style.opacity="0.45"}),o.addEventListener("dragend",function(){this.style.opacity="",Je(),le=null})});const r=e.querySelector("tbody");r&&(r.addEventListener("dragover",function(o){const n=o.target.closest("tr[data-tag-id]");if(!n)return;if(ee){o.preventDefault(),o.dataTransfer.dropEffect="link",de&&de!==n&&(de.style.background="",de.style.outline=""),de=n,n.style.background="var(--accent)22",n.style.outline="2px solid var(--accent)",Ar();const s=document.getElementById("planner-dnd-hint");s&&(s.style.display="block",s.textContent=`→ Link to "${n.dataset.tagName||""}"`,s.style.color="var(--accent)",s.style.left=o.clientX+16+"px",s.style.top=o.clientY+12+"px");return}if(!le)return;if(le.category_name!==n.dataset.catName){o.dataTransfer.dropEffect="none";return}o.preventDefault(),o.dataTransfer.dropEffect="move";const i=ba(o,n);(n!==Ae||i!==pt)&&wa(n,i);const a=document.getElementById("planner-dnd-hint");a&&(a.style.display="block",a.style.left=o.clientX+16+"px",a.style.top=o.clientY+12+"px")}),r.addEventListener("dragleave",function(o){if(!this.contains(o.relatedTarget)){Je(),de&&(de.style.background="",de.style.outline="",de=null);const n=document.getElementById("planner-dnd-hint");n&&(n.style.display="none")}}),r.addEventListener("drop",function(o){o.preventDefault();const n=o.target.closest("tr[data-tag-id]");if(!n){Je();return}n.style.background="",n.style.outline="";const i=document.getElementById("planner-dnd-hint");if(i&&(i.style.display="none"),ee){const d=n.dataset.tagId,l=n.dataset.tagName,c=n.dataset.catName,g={...ee};ee=null,de&&(de.style.background="",de.style.outline="",de=null);const f=document.getElementById("planner-dnd-hint");f&&(f.style.display="none");const u=D.project,h=document.querySelector(`#wi-panel-list [data-wi-id="${CSS.escape(g.id)}"]`);if(h){h.remove();const _=document.getElementById("wi-panel-count"),C=document.querySelectorAll("#wi-panel-list [data-wi-id]").length;_&&(_.textContent=C?`(${C} unlinked)`:"(all linked ✓)")}m.workItems.patch(g.id,u,{tag_id_user:d}).then(()=>{p(`Linked "${g.name_ai}" → "${l}"`,"success"),fe(u),c&&Oe(u).catch(()=>{})}).catch(_=>{p(_.message,"error"),fe(u)});return}if(!le||!pt){Je();return}const a=pt,s={id:n.dataset.tagId,name:n.dataset.tagName,category_id:Number(n.dataset.catId),category_name:n.dataset.catName};Je(),s.id!==le.id&&xa(a,{...le},s).catch(d=>p(d.message,"error"))}))}window._plannerCatDragOver=function(e,t,r){if(!le||le.category_name!=="ai_suggestion"||r==="ai_suggestion")return;e.preventDefault(),e.dataTransfer.dropEffect="move";const o=e.target.closest(".planner-cat-row");o&&(o.style.background="var(--accent)22",o.style.outline="1px solid var(--accent)");const n=document.getElementById("planner-dnd-hint");n&&(n.style.display="block",n.textContent=`→ Move to ${r}`,n.style.color="var(--accent)",n.style.left=e.clientX+16+"px",n.style.top=e.clientY+12+"px")};window._plannerCatDragLeave=function(e){const t=e.target.closest(".planner-cat-row");if(t&&!t.contains(e.relatedTarget)){t.style.background=t.style.outline="";const r=document.getElementById("planner-dnd-hint");r&&(r.style.display="none")}};window._plannerCatDrop=async function(e,t,r){e.preventDefault();const o=e.target.closest(".planner-cat-row");o&&(o.style.background=o.style.outline="");const n=document.getElementById("planner-dnd-hint");if(n&&(n.style.display="none"),!le||le.category_name!=="ai_suggestion"||r==="ai_suggestion")return;const i={...le};le=null,await m.tags.update(i.id,{category_id:t}),p(`"${i.name}" moved to "${r}"`,"success"),await Fe(D.project,!0),ke(),ye()};window._wiShowLinkedTags=async(e,t)=>{try{const r=await m.tags.relations.listForWorkItem(t,e);if(!r||!r.length){p("No linked tags","info");return}const o=r.map(n=>`${n.tag_name||n.tag_id} (${n.relation||n.related_approved||"linked"})`).join(`
`);alert(`Linked tags:
${o}`)}catch(r){p("Error loading tags: "+r.message,"error")}};function w(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}let St=null,Mr=null;function Po(){St&&(clearInterval(St),St=null)}async function $a(e,t){Po(),Mr=t,e.innerHTML=`
    <div style="padding:1.5rem;max-width:900px;margin:0 auto;overflow-y:auto;height:100%">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem">
        <h2 style="margin:0;font-size:1.1rem">Pipeline Health</h2>
        <button id="pipeline-refresh-btn" class="btn btn-ghost btn-sm" onclick="window._pipelineRefresh()">↻ Refresh</button>
      </div>
      <div id="pipeline-cards" style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1.5rem">
        <div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Loading…</div>
      </div>
      <div id="pipeline-pending" style="margin-bottom:1.2rem"></div>
      <div id="pipeline-errors" style="margin-bottom:1.5rem"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
        <h3 style="margin:0;font-size:0.95rem">Recent Workflow Runs</h3>
        <button class="btn btn-ghost btn-sm" onclick="window._nav('workflow')">→ Pipelines</button>
      </div>
      <div id="pipeline-runs">
        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
      </div>
    </div>
  `,window._pipelineRefresh=()=>Ot(e,t),await Ot(e,t),St=setInterval(()=>{Mr===t&&Ot(e,t)},3e4)}const Dr={commit_embed:"commit_embed",commit_store:"commit_store",commit_code_extract:"commit_code",session_summary:"session_summary",tag_match:"tag_match",work_item_embed:"wi_embed"};function br(e){if(!e)return"—";const t=new Date(e),o=new Date-t;return o<6e4?`${Math.floor(o/1e3)}s ago`:o<36e5?`${Math.floor(o/6e4)}m ago`:o<864e5?`${Math.floor(o/36e5)}h ago`:t.toLocaleDateString()}async function Ot(e,t){if(!t){e.querySelector("#pipeline-cards").innerHTML='<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">No project selected</div>';return}try{const[r,o]=await Promise.all([m.pipeline.status(t).catch(()=>null),m.graphWorkflows.recentRuns(t,10).catch(()=>null)]);ka(e,r),Ea(e,r),Ca(e,r),za(e,o)}catch(r){console.warn("Pipeline load error:",r)}}function ka(e,t){const r=e.querySelector("#pipeline-cards");if(!r)return;if(!t){r.innerHTML='<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Pipeline data unavailable</div>';return}const o=t.last_24h||{},n=Object.keys(Dr);r.innerHTML=n.map(i=>{const a=o[i]||{ok:0,error:0,skipped:0,last_run:null},d=a.ok>0||a.error>0||a.skipped>0?a.error>0?"var(--red, #e74c3c)":"var(--green, #27ae60)":"var(--muted)",l=Dr[i]||i;return`
      <div style="background:var(--surface2);border-radius:var(--radius);padding:0.75rem;
                  border:1px solid var(--border)">
        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.5rem">
          <div style="width:7px;height:7px;border-radius:50%;background:${d};flex-shrink:0"></div>
          <span style="font-size:0.72rem;font-weight:600;color:var(--text);font-family:monospace">${l}</span>
        </div>
        <div style="font-size:0.72rem;color:var(--muted);display:flex;gap:0.6rem">
          <span style="color:var(--green,#27ae60)">&#10003;${a.ok}</span>
          <span style="color:${a.error>0?"var(--red,#e74c3c)":"var(--muted)"}">&#10007;${a.error}</span>
          <span>&#9197;${a.skipped}</span>
        </div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem">${br(a.last_run)}</div>
      </div>
    `}).join("")}function Ea(e,t){const r=e.querySelector("#pipeline-pending");if(!r)return;const o=t?.pending||{},n=[];o.commits_not_embedded>0&&n.push(`&#9888; Pending: ${o.commits_not_embedded} commit${o.commits_not_embedded!==1?"s":""} not embedded`),o.work_items_unmatched>0&&n.push(`&#9888; Pending: ${o.work_items_unmatched} work item${o.work_items_unmatched!==1?"s":""} unmatched`),r.innerHTML=n.map(i=>`<div style="font-size:0.78rem;color:var(--accent);margin-bottom:0.3rem">${i}</div>`).join("")}function Ca(e,t){const r=e.querySelector("#pipeline-errors");if(!r)return;const o=t?.recent_errors||[];if(!o.length){r.innerHTML="";return}r.innerHTML=`
    <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;color:var(--text)">Recent Errors</div>
    ${o.slice(0,5).map(n=>`
      <div style="font-size:0.72rem;color:var(--muted);margin-bottom:0.25rem;
                  display:flex;gap:0.5rem;align-items:baseline">
        <span style="color:var(--red,#e74c3c);font-family:monospace">${n.pipeline}</span>
        <span style="color:var(--muted);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${n.error_msg}">${n.error_msg||"(no message)"}</span>
        <span style="flex-shrink:0">${br(n.at)}</span>
      </div>
    `).join("")}
  `}function za(e,t){const r=e.querySelector("#pipeline-runs");if(!r)return;const o=t?.runs||t||[];if(!Array.isArray(o)||!o.length){r.innerHTML='<div style="color:var(--muted);font-size:0.8rem">No recent runs</div>';return}r.innerHTML=o.slice(0,8).map(n=>{const i=n.status==="done"?"var(--green,#27ae60)":n.status==="running"?"var(--accent)":n.status==="error"?"var(--red,#e74c3c)":"var(--muted)",a=n.status==="running"?`<span style="color:${i}">&#9679; running</span>`:`<span style="color:${i}">${n.status}</span>`;return`
      <div style="display:flex;gap:0.75rem;align-items:baseline;font-size:0.78rem;
                  padding:0.35rem 0;border-bottom:1px solid var(--border)">
        <span style="color:var(--muted);font-family:monospace;font-size:0.68rem">${n.workflow_name||n.workflow_id?.slice(0,8)||"?"}</span>
        <span style="flex:1;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${n.user_input||""}">${(n.user_input||"").slice(0,60)}</span>
        ${a}
        <span style="color:var(--muted);flex-shrink:0">${br(n.started_at)}</span>
      </div>
    `}).join("")}function Lo(e,t){const r=(x?.settings?.backend_url||"http://localhost:8000").replace(/\/$/,"");fetch(`${r}/logs/ui-error`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({level:"ERROR",message:String(e),stack:t||null,url:window.location.href})}).catch(()=>{})}window.addEventListener("error",e=>{Lo(e.message,e.error?.stack)});window.addEventListener("unhandledrejection",e=>{Lo(String(e.reason),e.reason?.stack)});let Xe=null,Hr=null;function Ia(e){const t=x.currentProject?.name||null;if(Xe&&Hr===t){e.innerHTML="",Xe.container=e,Xe._render(),Xe._loadTab(Xe.activeTab||"chat");return}Hr=t,Xe=new Xi(e)}const Sa=[{id:"summary",icon:"📄",label:"Summary"},{id:"chat",icon:"◉",label:"Chat"},{id:"planner",icon:"◎",label:"Planner"},{id:"prompts",icon:"≡",label:"Roles"},{id:"code",icon:"</>",label:"Code"},{id:"documents",icon:"📋",label:"Documents"},{id:"workflow",icon:"◈",label:"Pipelines"},{id:"pipeline",icon:"⊕",label:"Pipeline"},{id:"history",icon:"⏱",label:"History"},{id:"settings",icon:"⚙",label:"Settings"}];async function Ta(){Uo(),Nr(),localStorage.getItem("aicli_sidebar_open")==="0"&&document.body.classList.add("sidebar-collapsed");let e=!1;for(let t=0;t<8;t++)try{const r=await m.health();e=!0,U({backendOnline:!0,requireAuth:r.require_auth||!1,dbConnected:r.db_connected||!1}),yt();break}catch{if(t<7){const r=document.getElementById("status-text");r&&(r.textContent=`Connecting… (${t+1})`),await new Promise(o=>setTimeout(o,1500))}else U({backendOnline:!1}),yt()}if(!e){await Ct();return}if(x.requireAuth){const{valid:t,token:r,user:o}=await Vr(x.settings.backend_url);t?(U({user:o}),await Ct()):Gr(document.getElementById("app"),x.settings.backend_url,async(n,i)=>{U({user:i}),Nr(),localStorage.getItem("aicli_sidebar_open")==="0"&&document.body.classList.add("sidebar-collapsed"),await Ct(i)});return}await Ct()}async function Ct(e){yt(),rr(),xr("home");let t=[];try{if(t=(await m.listProjects()).projects||[],U({projects:t}),rr(),x.activeView==="home"){const o=document.getElementById("views-container"),n=o?.querySelector(".view.active")||o?.querySelector(".view");n&&Vt(n)}}catch(r){console.warn("Could not load projects:",r.message)}if(t.length){const r=nr(),o=t.map(i=>i.name),n=r.find(i=>o.includes(i));n&&(La(n),setTimeout(()=>jo(n).catch(()=>{}),200))}x.backendOnline&&x.user?.email&&wr().catch(()=>{}),Pa()}function Pa(){window._healthPollTimer||(window._healthPollTimer=setInterval(async()=>{try{const e=await m.health(),t=x.dbConnected;U({backendOnline:!0,dbConnected:e.db_connected||!1}),(t!==x.dbConnected||!t)&&yt()}catch{U({backendOnline:!1,dbConnected:!1}),yt()}},5e3))}function La(e){requestAnimationFrame(()=>{document.querySelectorAll("[data-project-name]").forEach(r=>{if(r.dataset.projectName===e){r.style.borderColor="var(--accent)";const o=document.createElement("span");o.id="restore-badge",o.style.cssText="font-size:0.6rem;color:var(--accent);margin-left:auto",o.textContent="↺ restoring…",r.querySelector("div")?.appendChild(o)}})})}function Nr(){document.getElementById("app").innerHTML=`
    <div class="app-shell" id="shell">

      <div id="titlebar">
        <button class="titlebar-toggle" onclick="window._toggleSidebar()" title="Toggle sidebar">☰</button>
        <div class="titlebar-logo">
          <span class="titlebar-icon">⬡</span>
          <span class="titlebar-name">aicli</span>
        </div>
        <span class="titlebar-sep">·</span>
        <div class="titlebar-project" id="titlebar-project" onclick="window._nav('home')" title="Switch project">
          <span style="font-size:0.68rem;color:var(--muted)">No project open</span>
        </div>
        <div class="titlebar-spacer"></div>
        <div class="titlebar-controls">
          <div style="display:none;align-items:center;gap:0.3rem" id="balance-chip-wrap">
            <div id="balance-chip" onclick="window._updateBalance()" title="Click to refresh balance"
              style="font-size:0.65rem;padding:0.2rem 0.5rem;border-radius:var(--radius);
                     background:var(--surface2);cursor:pointer;user-select:none"></div>
            <button id="balance-refresh-btn" onclick="window._updateBalance()" title="Refresh balance"
              style="background:none;border:none;color:var(--muted);cursor:pointer;
                     font-size:0.72rem;padding:2px 3px;line-height:1;transition:opacity 0.2s">↺</button>
          </div>
          <div id="db-status-chip" title="PostgreSQL status"
               style="display:none;font-size:0.6rem;padding:2px 7px;border-radius:10px;
                      font-weight:600;letter-spacing:0.02em"></div>
          <div class="status-pill">
            <div class="status-dot" id="status-dot"></div>
            <span id="status-text" style="font-size:0.62rem">Connecting…</span>
          </div>
        </div>
      </div>

      <div id="sidebar">
        <nav class="sidebar-nav" id="sidebar-nav"></nav>
        <div class="sidebar-footer" id="sidebar-footer"></div>
      </div>

      <div id="content">
        <div id="views-container" style="flex:1;overflow:hidden;display:flex;flex-direction:column"></div>
      </div>

    </div>
    <div class="toast-container"></div>
  `,window._winClose=Di,window._winMin=Hi,window._winMax=Ni,window._logout=()=>{Yr(),location.reload()},window._toggleSidebar=()=>{const e=document.body.classList.toggle("sidebar-collapsed");localStorage.setItem("aicli_sidebar_open",e?"0":"1")}}function rr(){Bo(),vt()}function Bo(){const e=document.getElementById("sidebar-nav");if(!e)return;const t=x.currentProject;t?e.innerHTML=`
      <div class="nav-project-label" title="${t.name}">${t.name}</div>
      <div class="nav-divider"></div>
      ${Sa.map(r=>`
        <div class="nav-item ${x.activeView===r.id?"active":""}"
             id="nav-${r.id}"
             data-label="${r.label}"
             onclick="window._nav('${r.id}')">
          <span class="nav-icon">${r.icon}</span>
          <span class="nav-label">${r.label}</span>
        </div>
      `).join("")}
      <div class="nav-divider"></div>
      <div class="nav-item ${x.activeView==="home"?"active":""}"
           id="nav-home"
           data-label="Projects"
           onclick="window._nav('home')">
        <span class="nav-icon">◫</span>
        <span class="nav-label">Projects</span>
      </div>
    `:e.innerHTML=`
      <div class="nav-item ${x.activeView==="home"?"active":""}"
           id="nav-home"
           data-label="Projects"
           onclick="window._nav('home')">
        <span class="nav-icon">◫</span>
        <span class="nav-label">Projects</span>
      </div>
      <div class="nav-item ${x.activeView==="workflow"?"active":""}"
           id="nav-workflow"
           data-label="Pipelines"
           onclick="window._nav('workflow')">
        <span class="nav-icon">◈</span>
        <span class="nav-label">Pipelines</span>
      </div>
    `}function vt(){const e=document.getElementById("sidebar-footer");if(!e)return;const t=x.user;if(t){const r=(t.email||"?").slice(0,2).toUpperCase(),o=t.role||(t.is_admin?"admin":"free"),n=o==="admin",a={admin:"var(--accent)",paid:"var(--green)",free:"var(--muted)"}[o]||"var(--muted)";e.innerHTML=`
      <div class="sidebar-user">
        <div class="sidebar-user-avatar" title="${t.email}">${r}</div>
        <div class="sidebar-user-info nav-label">
          <div class="sidebar-user-email" style="font-size:0.72rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${t.email}</div>
          <div style="font-size:0.58rem;color:${a};text-transform:uppercase;letter-spacing:0.04em;margin-top:1px">${o}</div>
        </div>
        <div class="sidebar-user-actions nav-label">
          ${n?`<button class="sidebar-user-btn" title="Admin panel" onclick="window._nav('admin')">👥</button>`:""}
          <button class="sidebar-user-btn" title="Settings" onclick="window._nav('settings')">⚙</button>
          <button class="sidebar-user-btn" title="Sign out"  onclick="window._logout()">↩</button>
        </div>
      </div>
    `}else e.innerHTML=`
      <div class="sidebar-user" style="flex-direction:column;align-items:stretch;gap:0.4rem;padding:0.6rem 0.75rem">
        <button class="btn btn-primary btn-sm" style="width:100%"
                onclick="window._showLoginModal('login')">Sign in</button>
        <button class="btn btn-ghost btn-sm" style="width:100%"
                onclick="window._showLoginModal('register')">Create account</button>
        <div style="display:flex;justify-content:flex-end;margin-top:0.2rem">
          <button class="sidebar-user-btn nav-label" title="Settings" onclick="window._nav('settings')">⚙ Settings</button>
        </div>
      </div>
    `}window._showLoginModal=(e="login")=>{document.getElementById("login-modal-overlay")?.remove();const t=document.createElement("div");t.id="login-modal-overlay",t.style.cssText="position:fixed;inset:0;z-index:9000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px)",document.body.appendChild(t);const r=()=>t.remove();Or(async()=>{const{renderLogin:o}=await Promise.resolve().then(()=>Qo);return{renderLogin:o}},void 0).then(({renderLogin:o})=>{o(t,x.settings.backend_url,(n,i)=>{t.remove(),localStorage.setItem("aicli_token",n),localStorage.setItem("aicli_user",JSON.stringify(i)),U({user:i}),vt(),p(`Signed in as ${i.email}`,"success"),wr().then(()=>vt()).catch(()=>{})},r),e==="register"&&setTimeout(()=>document.getElementById("tab-register")?.click(),50)}),t.addEventListener("click",o=>{o.target===t&&r()})};function yt(){const e=document.getElementById("status-dot"),t=document.getElementById("status-text"),r=document.getElementById("db-status-chip");e&&(e.className=`status-dot ${x.backendOnline?"online":""}`),t&&(t.textContent=x.backendOnline?"Online":"Offline"),r&&(x.backendOnline?x.dbConnected?(r.style.display="inline-block",r.style.background="rgba(39,174,96,.15)",r.style.color="#27ae60",r.style.border="1px solid rgba(39,174,96,.3)",r.textContent="DB"):(r.style.display="inline-block",r.style.background="rgba(231,76,60,.15)",r.style.color="#e74c3c",r.style.border="1px solid rgba(231,76,60,.3)",r.textContent="DB not connected"):r.style.display="none")}async function wr(){const e=document.getElementById("balance-chip"),t=document.getElementById("balance-chip-wrap"),r=document.getElementById("balance-refresh-btn");if(!e||!t)return;e.style.opacity="0.5",r&&(r.style.opacity="0.3",r.style.pointerEvents="none");const o=(n,i,a,s)=>{e.innerHTML=`${n} <span style="opacity:0.45;font-size:0.6em">↺</span>`,e.style.color=i,e.style.background=a||"var(--surface2)",e.style.opacity="1",e.title=s||"Click to refresh",t.style.display="flex"};try{const n=await m.billingBalance();U({balanceInfo:n});const i=n.role||"free";if(i==="admin")o("Admin","var(--accent)","rgba(255,107,53,0.12)","Click to refresh"),Promise.all([m.adminGetStats(),m.adminGetProviderBalances().catch(()=>({}))]).then(([a,s])=>{U({platformStats:a});const d=a.total_added_usd??0,l=a.total_charged_usd??0,c=a.by_provider||{};let g=null;Object.entries(s).forEach(([h,_])=>{if(_?.balance_usd!=null){const C=c[h]?.real_cost_usd||0;g===null&&(g=0),g+=Math.max(0,_.balance_usd-C)}});const f=g!==null?` | API: $${g.toFixed(2)}`:"",u=g===null?"var(--muted)":g>=5?"var(--green)":g>=1?"var(--accent)":"var(--red)";o(`Credits: $${d.toFixed(2)} · Used: $${l.toFixed(2)}<span style="color:${u}">${f}</span>`,"var(--accent)","rgba(255,107,53,0.12)","Platform credits (user wallets) + API provider remaining budget. Click to refresh."),vt()}).catch(()=>{o("Admin ↺","var(--accent)","rgba(255,107,53,0.12)","Click to refresh")});else if(i==="free"){const a=n.free_tier_used_usd??0,s=n.free_tier_limit_usd??5;o(`Free · $${a.toFixed(2)} / $${s.toFixed(2)}`,"var(--text2)","var(--surface2)","Free tier usage. Click to refresh.")}else{const a=n.balance_usd??0,s=a>=1?"var(--green)":a>=.1?"var(--accent)":"var(--red)";o(`$${a.toFixed(2)}`,s,"var(--surface2)","Your platform credit balance. Click to refresh.")}x.user?.email&&(U({user:{...x.user,role:i,balance_usd:n.balance_usd}}),vt())}catch{t&&(t.style.display="none")}finally{r&&(r.style.opacity="1",r.style.pointerEvents="")}}window._updateBalance=wr;window._nav=xr;function xr(e,t={}){U({activeView:e}),Bi(),Po();const r=document.getElementById("views-container");if(!r)return;r.innerHTML="";const o=document.createElement("div");o.className="view active",r.appendChild(o);const n=x.currentProject;switch(e){case"home":Vt(o),m.listProjects().then(i=>{const a=i.projects||[];U({projects:a}),rr(),Vt(o)}).catch(()=>{});break;case"summary":dn(o,n?.name);break;case"chat":pn(o);break;case"planner":Ji(o);break;case"prompts":Ln(o,n?.name);break;case"code":Xn(o,n?.name,n);break;case"documents":Zn(o,n?.name);break;case"workflow":di(o);break;case"pipeline":$a(o,n?.name);break;case"history":Ia(o);break;case"settings":Ui(o);break;case"admin":Go(o);break;default:o.innerHTML=`<div class="empty-state"><p>View not found: ${e}</p></div>`}Bo()}async function jo(e){const t=document.getElementById("titlebar-project");t&&(t.innerHTML=`<span style="font-size:0.75rem;color:var(--muted)">Opening ${e}…</span>`);try{const r=await m.getProject(e);await m.switchProject(e),r.system_prompt=r.context_md||r.claude_md||r.project_md||"",U({currentProject:r}),qo(e),Fe(e).catch(()=>{}),t&&(t.innerHTML=`<span style="font-size:0.75rem;color:var(--accent)">${e}</span><span class="caret">▾</span>`),xr("summary"),m.getMemoryStatus(e).then(a=>{a.needs_memory&&Ba(a,e)}).catch(()=>{});const o=30*60*1e3,n=`ctx_refresh_${e}`,i=parseInt(sessionStorage.getItem(n)||"0",10);Date.now()-i>o&&(sessionStorage.setItem(n,String(Date.now())),m.getProjectContext(e,!0).then(a=>{const s=a.context||a.claude_md||"";s&&x.currentProject?.name===e&&U({currentProject:{...x.currentProject,system_prompt:s}})}).catch(()=>{}))}catch(r){const o=document.getElementById("titlebar-project");o&&(o.innerHTML='<span style="font-size:0.75rem;color:var(--muted)">No project</span><span class="caret">▾</span>'),p(`Could not open project: ${r.message}`,"error")}}function Ba(e,t){const r=`memory-banner-dismissed-${t}`;if(sessionStorage.getItem(r))return;document.getElementById("memory-health-banner")?.remove();const o=e.prompts_since_last_memory||0,n=e.days_since_last_memory,i=n!=null?` (${n} day${n!==1?"s":""} ago)`:"",a=document.createElement("div");a.id="memory-health-banner",a.style.cssText=["display:flex;align-items:center;gap:0.75rem;padding:0.5rem 1rem","background:#fff3cd;border-bottom:1px solid #ffc107;font-size:0.72rem;","color:#856404;flex-shrink:0;z-index:10"].join(";"),a.innerHTML=`
    <span style="font-size:0.95rem">⚠</span>
    <span style="flex:1">
      <strong>${o} new prompts</strong> since last /memory${i}.
      Refresh AI context files to keep Claude, Cursor and Copilot in sync.
    </span>
    <button id="memory-banner-run"
      style="background:#ffc107;border:none;color:#000;font-size:0.65rem;
             padding:0.2rem 0.6rem;border-radius:4px;cursor:pointer;font-family:inherit;
             font-weight:600;white-space:nowrap">
      Run /memory
    </button>
    <button id="memory-banner-dismiss"
      style="background:none;border:none;color:#856404;font-size:0.9rem;
             cursor:pointer;padding:0;line-height:1;flex-shrink:0">✕</button>
  `;const s=document.getElementById("main-content");s&&s.prepend(a),document.getElementById("memory-banner-run")?.addEventListener("click",async()=>{const d=document.getElementById("memory-banner-run");d&&(d.disabled=!0,d.textContent="…");try{await m.generateMemory(t),a.remove(),sessionStorage.setItem(r,"1"),p("Memory files refreshed","success")}catch(l){p(`/memory failed: ${l.message}`,"error"),d&&(d.disabled=!1,d.textContent="Run /memory")}}),document.getElementById("memory-banner-dismiss")?.addEventListener("click",()=>{a.remove(),sessionStorage.setItem(r,"1")})}window._openProject=jo;Ta();Y.isTouch&&(ja(),Aa(),Ma(),Fa(),Wa());function ja(){new MutationObserver(t=>{for(const r of t)for(const o of r.addedNodes)o.classList?.contains("modal-overlay")&&Ra(o)}).observe(document.body,{childList:!0})}function Ra(e){const t=e.querySelector(".modal");if(!t)return;const r=t.querySelector(".modal-title")?.textContent||"",o=t.innerHTML;e.remove(),Ft({title:r,content:o})}function Aa(){window.addEventListener("viewchange",e=>{e.detail?.view==="workflow"&&Y.isMobile&&U({workflowMode:Do()})})}function Ma(){new MutationObserver(()=>{const t=document.getElementById("chat-messages");document.getElementById("chat-input"),t&&!t.dataset.mobilePatch&&(t.dataset.mobilePatch="1",Da(t))}).observe(document.getElementById("app")||document.body,{childList:!0,subtree:!0})}function Da(e,t){Oo(e,async()=>{Ge("light");try{const o=await(await fetch(`${state.settings.backend_url}/history/sessions`)).json();Ua(o.length)}catch{}}),e.addEventListener("touchstart",r=>{const o=r.target.closest(".msg-bubble")||r.target.closest('[class*="bubble"]');if(!o)return;const n=Ur(o,{onLeft:()=>{const i=o.textContent;navigator.clipboard?.writeText(i).then(()=>Ge("success")),Oa(),n()},threshold:80})}),Ha()}function Ha(){if(!document.querySelector("#chat-input")?.closest("div[style]")||document.getElementById("mobile-sessions-btn"))return;const t=document.createElement("button");t.id="mobile-sessions-btn",t.style.cssText=`
    position:absolute;top:0.75rem;right:0.75rem;
    background:var(--surface2);border:1px solid var(--border);
    color:var(--text2);font-size:0.7rem;
    padding:0.3rem 0.6rem;border-radius:var(--radius);
    cursor:pointer;z-index:10;
  `,t.textContent="≡ Sessions",t.onclick=()=>Na();const r=document.querySelector("#chat-messages")?.parentElement;r&&(r.style.position="relative",r.appendChild(t))}async function Na(){Ge("light");try{const t=await(await fetch(`${state.settings.backend_url}/history/sessions`)).json(),r=t.length===0?'<p style="color:var(--muted);font-size:0.78rem">No sessions yet</p>':t.slice(0,15).map(o=>`
          <div onclick="window._loadChatSession('${o.id}');document.getElementById('bottom-sheet-overlay')?.remove()"
            style="padding:0.75rem;border-bottom:1px solid var(--border);cursor:pointer;font-size:0.78rem">
            ${o.title||o.id.slice(0,12)}
            <span style="float:right;font-size:0.6rem;color:var(--muted)">${new Date(o.updated_at).toLocaleDateString()}</span>
          </div>
        `).join("");Ft({title:"Chat Sessions",content:r,actions:[{label:"+ New Chat",style:"btn-primary",onclick:"window._newChatSession();document.getElementById('bottom-sheet-overlay')?.remove()"}]})}catch{Ft({title:"Sessions",content:'<p style="color:var(--red)">Backend offline</p>'})}}function Oa(e){const t=document.createElement("div");t.textContent="Copied!",t.style.cssText=`
    position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
    background:var(--surface2);border:1px solid var(--border);
    border-radius:var(--radius);padding:0.5rem 1rem;
    font-size:0.75rem;color:var(--green);z-index:999;
    animation:fadeIn 0.15s ease-out;
  `,document.body.appendChild(t),setTimeout(()=>t.remove(),1200)}function Ua(e){const t=document.querySelector("#nav-chat .nav-badge");t&&(t.textContent=e)}function Fa(){new MutationObserver(()=>{const t=document.querySelector(".llm-list");t&&!t.dataset.mobilePatch&&Y.isMobile&&(t.dataset.mobilePatch="1",t.style.scrollSnapType="x mandatory",t.querySelectorAll(".llm-item").forEach(r=>{r.style.scrollSnapAlign="start"}))}).observe(document.getElementById("app")||document.body,{childList:!0,subtree:!0})}function Wa(){const e=["home","projects","workflow","chat","settings"];Ur(document.getElementById("app")||document.body,{onLeft:()=>{const r=window.__CURRENT_VIEW__||"home",o=e.indexOf(r);o<e.length-1&&(Ge("light"),window._nav(e[o+1]))},onRight:()=>{const r=window.__CURRENT_VIEW__||"home",o=e.indexOf(r);o>0&&(Ge("light"),window._nav(e[o-1]))},threshold:100});const t=window._nav;window._nav=(r,o)=>{window.__CURRENT_VIEW__=r,t(r,o)}}
