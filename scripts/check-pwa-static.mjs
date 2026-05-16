import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function readText(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertExists(relativePath) {
  assert(fs.existsSync(path.join(root, relativePath)), `Missing ${relativePath}`);
}

const indexHtml = readText("index.html");
const manifest = JSON.parse(readText("manifest.webmanifest"));
const sw = readText("sw.js");

assert(indexHtml.includes('rel="manifest" href="./manifest.webmanifest"'), "index.html must link the manifest");
assert(indexHtml.includes("navigator.serviceWorker.register(\"./sw.js\")"), "index.html must register sw.js");
assert(indexHtml.includes("data-share-link"), "index.html must expose the URL share button");

assert(manifest.name === "Music Stack OpenClaw Desk", "manifest name changed unexpectedly");
assert(manifest.start_url === "./", "manifest start_url should remain relative");
assert(manifest.scope === "./", "manifest scope should remain relative");
assert(manifest.display === "standalone", "manifest display should be standalone");
assert(Array.isArray(manifest.icons) && manifest.icons.length >= 4, "manifest needs install icons");

for (const icon of manifest.icons) {
  const iconPath = icon.src.replace(/^\.\//, "");
  assertExists(iconPath);
}

assert(sw.includes('const CACHE_PREFIX = "openclaw-pwa";'), "sw.js cache prefix should be openclaw-pwa");
assert(sw.includes("const VERSION = `${CACHE_PREFIX}-v3`;"), "sw.js version should be v3");
assert(indexHtml.includes("Hazama conversation"), "index.html should render Hazama conversation metadata");
assert(sw.includes("self.addEventListener(\"install\""), "sw.js must install");
assert(sw.includes("self.addEventListener(\"fetch\""), "sw.js must handle fetch");

const precacheMatch = sw.match(/const PRECACHE_URLS = \[([\s\S]*?)\];/);
assert(precacheMatch, "sw.js must define PRECACHE_URLS");

const precacheUrls = [...precacheMatch[1].matchAll(/"([^"]+)"/g)].map((match) => match[1]);
assert(precacheUrls.includes("./"), "precache should include the app root");
assert(precacheUrls.includes("index.html"), "precache should include index.html");
assert(precacheUrls.includes("manifest.webmanifest"), "precache should include manifest.webmanifest");
assert(precacheUrls.includes("docs/current-stack-alignment.md"), "precache should include current stack alignment");
assert(precacheUrls.includes("connectors/registry.json"), "precache should include connector registry");

for (const url of precacheUrls) {
  if (url === "./") {
    continue;
  }
  assertExists(url);
}

console.log(`OpenClaw PWA static check passed (${precacheUrls.length} precache entries).`);
