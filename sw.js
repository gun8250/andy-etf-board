/* 静态页面兜底 Service Worker（2026-11-04）
   托管网关实测约 20~30% 的请求会返回「HTTP 200 + 空响应体」，
   首页 HTML 一旦为空就是白屏，页面里任何自愈脚本都来不及执行。
   本 SW 只拦截「导航请求」：网络优先；空响应时用缓存顶上（回访用户生效）。
   站点启用访问密码后，缓存里只允许放「登录页」，避免网关空响应把看板外壳
   返回给未认证用户；读取时也只查当前版本缓存，并在激活时清掉旧版本缓存。
   data.js / app.js 由 index.html 里的 loader 自行 fetch + 重试，这里不拦截。 */
const CACHE = "etf-dash-shell-v2";
const IDX_KEY = "/__cached_index.html";

self.addEventListener("install", function (e) {
  e.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", function (e) {
  e.waitUntil((async function () {
    const keys = await caches.keys();
    await Promise.all(keys.filter(function (k) { return k !== CACHE; })
      .map(function (k) { return caches.delete(k); }));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", function (e) {
  const req = e.request;
  if (req.method !== "GET" || req.mode !== "navigate") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  e.respondWith((async function () {
    const headers = { "Content-Type": "text/html; charset=utf-8" };
    try {
      const r = await fetch(req, { cache: "no-store" });
      const body = await r.text();
      if (r.ok && body.length > 1000) {
        /* 只缓存「登录页」：站点已启用访问密码，若把认证后的看板 HTML 缓存下来，
           网关空响应时可能把看板外壳返回给未认证用户，等于绕过密码。
           缓存里永远只有登录页，兜底时也不会泄露看板。 */
        if (body.indexOf("请输入访问密码") >= 0) {
          const c = await caches.open(CACHE);
          await c.put(IDX_KEY, new Response(body, { status: 200, headers: headers }));
        }
        return new Response(body, { status: 200, headers: headers });
      }
      // 空响应：只回当前版本缓存里的「登录页」
      const hit = await caches.match(IDX_KEY, { cacheName: CACHE });
      if (hit) return hit;
      return new Response(body, { status: r.status || 200, headers: headers });
    } catch (err) {
      const hit = await caches.match(IDX_KEY, { cacheName: CACHE });
      if (hit) return hit;
      return new Response("", { status: 503 });
    }
  })());
});
