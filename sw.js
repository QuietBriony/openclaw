const CACHE_PREFIX = "openclaw-pwa";
const VERSION = `${CACHE_PREFIX}-v4`;

const PRECACHE_URLS = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "docs/manual.md",
  "docs/current-stack-alignment.md",
  "docs/packet-inspector-quickstart.md",
  "docs/music-orchestra-mission-board.md",
  "schemas/session-manifest.v1.schema.json",
  "connectors/registry.json",
  "sessions/examples/music-stack-session.example.json",
  "sessions/examples/music-orchestra-mission-board.example.json",
  "sessions/examples/chill-trio-live.example.json",
  "sessions/examples/chill-piano-bass-drum-trio.example.json",
  "sessions/examples/soft-piano-raw-drum-drive.example.json",
  "sessions/examples/raw-drum-candidate-export.example.json",
  "icons/icon-96.png",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-512-maskable.png",
  "icons/apple-touch-icon.png"
];

const METADATA_EXTENSIONS = new Set([".html", ".htm", ".json", ".md", ".webmanifest"]);

function scopedUrl(path) {
  return new URL(path, self.registration.scope).toString();
}

function isMetadataRequest(url) {
  const pathname = url.pathname.toLowerCase();
  return [...METADATA_EXTENSIONS].some((extension) => pathname.endsWith(extension));
}

async function cacheFirst(request) {
  const cache = await caches.open(VERSION);
  const cached = await cache.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  if (response.ok) {
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, fallbackPath = "index.html") {
  const cache = await caches.open(VERSION);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    return cached || cache.match(scopedUrl(fallbackPath));
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(VERSION)
      .then((cache) =>
        cache.addAll(
          PRECACHE_URLS.map((path) => new Request(scopedUrl(path), { cache: "reload" }))
        )
      )
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith(CACHE_PREFIX) && key !== VERSION)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET" || request.headers.has("range")) {
    return;
  }

  const requestUrl = new URL(request.url);
  const scopeUrl = new URL(self.registration.scope);
  if (requestUrl.origin !== scopeUrl.origin || !requestUrl.pathname.startsWith(scopeUrl.pathname)) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, "./"));
    return;
  }

  if (isMetadataRequest(requestUrl)) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});
