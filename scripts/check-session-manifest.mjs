import fs from "node:fs";
import path from "node:path";

// OpenClaw session-manifest domain-logic check.
//
// pytest covers the Python package; check-pwa-static.mjs covers the PWA shell.
// This script covers the JSON contract layer the dashboard JS depends on at
// runtime: the session-manifest schema, the example manifests it validates,
// and the connector registry. It loads that data in a controlled way and
// asserts the core contracts hold, exiting 0 on success and throwing on
// failure.

const root = process.cwd();
let assertions = 0;

function assert(condition, message) {
  assertions += 1;
  if (!condition) {
    throw new Error(message);
  }
}

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

// ---------------------------------------------------------------------------
// 1. The session-manifest schema must be a self-consistent JSON Schema.
// ---------------------------------------------------------------------------
const schemaPath = "schemas/session-manifest.v1.schema.json";
const schema = readJson(schemaPath);

assert(
  typeof schema.$schema === "string" && schema.$schema.includes("json-schema.org"),
  "schema must declare a json-schema.org $schema dialect"
);
assert(
  typeof schema.$id === "string" && schema.$id.endsWith("session-manifest.v1.schema.json"),
  "schema $id must point at the v1 session-manifest"
);
assert(schema.type === "object", "session-manifest schema root must be an object type");
assert(Array.isArray(schema.required) && schema.required.length > 0, "schema must list required fields");
assert(schema.properties && typeof schema.properties === "object", "schema must define properties");

// Every required root field must have a matching property definition.
for (const field of schema.required) {
  assert(
    Object.prototype.hasOwnProperty.call(schema.properties, field),
    `schema requires "${field}" but defines no property for it`
  );
}

// No dangling local $ref anywhere in the schema tree.
function collectLocalRefs(node, refs) {
  if (Array.isArray(node)) {
    for (const item of node) collectLocalRefs(item, refs);
    return refs;
  }
  if (node && typeof node === "object") {
    for (const [key, value] of Object.entries(node)) {
      if (key === "$ref" && typeof value === "string" && value.startsWith("#")) {
        refs.push(value);
      }
      collectLocalRefs(value, refs);
    }
  }
  return refs;
}
function resolvePointer(doc, pointer) {
  if (pointer === "#" || pointer === "#/") return doc;
  const parts = pointer.replace(/^#\//, "").split("/").map((p) => p.replace(/~1/g, "/").replace(/~0/g, "~"));
  let cursor = doc;
  for (const part of parts) {
    if (cursor && typeof cursor === "object" && part in cursor) {
      cursor = cursor[part];
    } else {
      return undefined;
    }
  }
  return cursor;
}
for (const ref of collectLocalRefs(schema, [])) {
  assert(resolvePointer(schema, ref) !== undefined, `schema has a dangling local $ref: ${ref}`);
}

// bpm_range bounds in the schema must themselves be ordered (min <= max).
const bpmProps = schema.properties.bpm_range?.properties || {};
assert(
  bpmProps.min?.minimum === bpmProps.max?.minimum && bpmProps.min?.maximum === bpmProps.max?.maximum,
  "schema bpm_range min/max must share the same allowed numeric window"
);

// The schema's required-key sets are the contract the dashboard JS relies on.
const requiredConnectorKeys = schema.properties.connectors?.required || [];
const requiredRoleKeys = schema.properties.roles?.required || [];
assert(
  ["music", "drumFloor", "chill", "namima"].every((k) => requiredConnectorKeys.includes(k)),
  "schema must require the four core connectors (music, drumFloor, chill, namima)"
);
assert(
  ["musicProducer", "pocketDrummer", "softPiano", "giMood"].every((k) => requiredRoleKeys.includes(k)),
  "schema must require the four core session roles"
);

// guardrails, when present, are locked to false (no auto-arm / upload / record).
const guardrailProps = schema.properties.guardrails?.properties || {};
const lockedGuardrails = ["auto_arm", "upload_audio", "record_audio", "write_samples", "modify_workflows"];
for (const key of lockedGuardrails) {
  assert(
    guardrailProps[key]?.const === false,
    `schema must lock guardrail "${key}" to const:false`
  );
}

// ---------------------------------------------------------------------------
// 2. The connector registry must be well-formed with no duplicate ids.
// ---------------------------------------------------------------------------
const registryRaw = fs.readFileSync(path.join(root, "connectors/registry.json"), "utf8");
const registry = JSON.parse(registryRaw);

assert(Number.isInteger(registry.version) && registry.version >= 1, "registry must carry an integer version >= 1");
assert(registry.connectors && typeof registry.connectors === "object", "registry must define a connectors map");

const registryIds = Object.keys(registry.connectors);
assert(registryIds.length > 0, "registry must define at least one connector");
// Object keys are unique; a duplicate key in the source text would silently
// drop, so cross-check the key count against raw top-level id occurrences.
const idLineCount = registryIds.filter((id) => {
  const occurrences = registryRaw.match(new RegExp(`"${id}"\\s*:\\s*\\{`, "g")) || [];
  return occurrences.length === 1;
}).length;
assert(idLineCount === registryIds.length, "registry connector ids must each appear exactly once");

for (const [id, entry] of Object.entries(registry.connectors)) {
  assert(entry && typeof entry === "object", `registry connector "${id}" must be an object`);
  assert(typeof entry.repo === "string" && entry.repo.length > 0, `registry connector "${id}" needs a repo`);
  assert(typeof entry.role === "string" && entry.role.length > 0, `registry connector "${id}" needs a role`);
  assert(typeof entry.mode === "string" && entry.mode.length > 0, `registry connector "${id}" needs a mode`);
  assert(
    Array.isArray(entry.capabilities) && entry.capabilities.length > 0,
    `registry connector "${id}" needs a non-empty capabilities list`
  );
  assert(
    Array.isArray(entry.safety) && entry.safety.length > 0,
    `registry connector "${id}" needs a non-empty safety list`
  );
}

// The four core connectors required by the schema must exist in the registry.
for (const key of ["music", "drumFloor", "chill", "namima"]) {
  assert(registryIds.includes(key), `registry is missing the core connector "${key}"`);
}

// ---------------------------------------------------------------------------
// 3. Every session-manifest example must satisfy the schema contract plus the
//    semantic invariants the dashboard JS assumes when rendering.
// ---------------------------------------------------------------------------
const examplesDir = "sessions/examples";
const exampleFiles = fs
  .readdirSync(path.join(root, examplesDir))
  .filter((name) => name.endsWith(".example.json"))
  .sort();
assert(exampleFiles.length > 0, "expected at least one session-manifest example");

function validateAgainstSchema(manifest, file) {
  // Required root fields.
  for (const field of schema.required) {
    assert(
      manifest[field] !== undefined,
      `${file}: missing required field "${field}"`
    );
  }
  // Required nested keys for object fields that declare them.
  for (const [field, def] of Object.entries(schema.properties)) {
    if (def.type === "object" && Array.isArray(def.required) && manifest[field]) {
      for (const nested of def.required) {
        assert(
          manifest[field][nested] !== undefined,
          `${file}: ${field} is missing required key "${nested}"`
        );
      }
    }
  }
}

let generationManifestSeen = 0;
let energyArcCount = 0;

for (const file of exampleFiles) {
  const manifest = readJson(`${examplesDir}/${file}`);

  validateAgainstSchema(manifest, file);

  assert(typeof manifest.session_id === "string" && manifest.session_id.length > 0, `${file}: session_id must be a non-empty string`);
  assert(typeof manifest.title === "string" && manifest.title.length > 0, `${file}: title must be a non-empty string`);

  // duration_target.minutes must be a positive number (schema: exclusiveMinimum 0).
  assert(
    typeof manifest.duration_target.minutes === "number" && manifest.duration_target.minutes > 0,
    `${file}: duration_target.minutes must be a positive number`
  );

  // bpm_range must be internally ordered and inside the schema's window.
  const { min, max, target } = manifest.bpm_range;
  assert(Number.isInteger(min) && Number.isInteger(max), `${file}: bpm_range min/max must be integers`);
  assert(min >= 40 && max <= 240, `${file}: bpm_range must stay within 40-240`);
  assert(min <= max, `${file}: bpm_range.min (${min}) must not exceed max (${max})`);
  if (target !== undefined) {
    assert(
      Number.isInteger(target) && target >= min && target <= max,
      `${file}: bpm_range.target (${target}) must sit between min and max`
    );
  }

  // energy_arc: non-empty, each point in [0,1], and "at" non-decreasing so the
  // dashboard can render the arc as an ordered timeline.
  assert(Array.isArray(manifest.energy_arc) && manifest.energy_arc.length >= 1, `${file}: energy_arc must be a non-empty array`);
  let previousAt = -Infinity;
  for (const point of manifest.energy_arc) {
    assert(
      typeof point.at === "number" && point.at >= 0 && point.at <= 1,
      `${file}: energy_arc "at" must be within 0-1`
    );
    assert(
      typeof point.energy === "number" && point.energy >= 0 && point.energy <= 1,
      `${file}: energy_arc "energy" must be within 0-1`
    );
    assert(point.at >= previousAt, `${file}: energy_arc "at" values must be non-decreasing`);
    previousAt = point.at;
    energyArcCount += 1;
  }

  // Every role.connector reference must resolve to a connector defined either
  // in this manifest or in the shared registry.
  for (const [roleName, role] of Object.entries(manifest.roles)) {
    assert(role && typeof role === "object", `${file}: role "${roleName}" must be an object`);
    if (typeof role.connector === "string") {
      const resolvesLocally = Object.prototype.hasOwnProperty.call(manifest.connectors, role.connector);
      const resolvesInRegistry = registryIds.includes(role.connector);
      assert(
        resolvesLocally || resolvesInRegistry,
        `${file}: role "${roleName}" references unknown connector "${role.connector}"`
      );
    }
  }

  // The dashboard's generationConnector() picks the connector with
  // generate_enabled === true and an intent.style. Any such connector must
  // carry a complete, well-typed generation intent.
  for (const [connectorName, config] of Object.entries(manifest.connectors)) {
    if (config && config.generate_enabled === true) {
      generationManifestSeen += 1;
      assert(
        config.intent && typeof config.intent === "object",
        `${file}: connector "${connectorName}" is generate_enabled but has no intent`
      );
      assert(
        typeof config.intent.style === "string" && config.intent.style.length > 0,
        `${file}: generate_enabled connector "${connectorName}" needs intent.style`
      );
      assert(
        typeof config.intent.bpm === "number" && config.intent.bpm > 0,
        `${file}: generate_enabled connector "${connectorName}" needs a positive intent.bpm`
      );
      assert(
        Number.isInteger(config.intent.seed),
        `${file}: generate_enabled connector "${connectorName}" needs an integer intent.seed`
      );
    }
  }

  // guardrails, when present, must keep every unsafe action disabled.
  if (manifest.guardrails) {
    for (const key of lockedGuardrails) {
      if (manifest.guardrails[key] !== undefined) {
        assert(
          manifest.guardrails[key] === false,
          `${file}: guardrail "${key}" must be false (review-only, human-gated)`
        );
      }
    }
  }

  // human_gates must keep all three review gates marked as required.
  for (const gate of ["before_arm", "before_record", "before_merge"]) {
    const gateConfig = manifest.human_gates[gate];
    assert(gateConfig && typeof gateConfig === "object", `${file}: human_gates.${gate} must be an object`);
    assert(gateConfig.required === true, `${file}: human_gates.${gate} must stay required:true`);
  }
}

assert(generationManifestSeen >= 1, "at least one example must exercise a generate_enabled connector");

// ---------------------------------------------------------------------------
// 4. The dashboard's manifest switcher list must stay consistent with disk.
// ---------------------------------------------------------------------------
const indexHtml = fs.readFileSync(path.join(root, "index.html"), "utf8");
const manifestBlock = indexHtml.match(/const manifests = \[([\s\S]*?)\];/);
assert(manifestBlock, "index.html must define the manifests switcher list");

const listedUrls = [...manifestBlock[1].matchAll(/url:\s*"([^"]+)"/g)].map((m) => m[1]);
assert(listedUrls.length > 0, "index.html manifests list must reference manifest URLs");
for (const url of listedUrls) {
  assert(fs.existsSync(path.join(root, url)), `index.html references a missing manifest file: ${url}`);
  assert(
    exampleFiles.includes(path.basename(url)),
    `index.html manifest URL is not a known example: ${url}`
  );
}

// The dashboard fetches the registry from a fixed relative path; keep it real.
const registryUrlMatch = indexHtml.match(/const registryUrl = "([^"]+)";/);
assert(registryUrlMatch, "index.html must define registryUrl");
assert(
  fs.existsSync(path.join(root, registryUrlMatch[1])),
  `index.html registryUrl points at a missing file: ${registryUrlMatch[1]}`
);

console.log(
  `OpenClaw session-manifest logic check passed ` +
  `(${assertions} assertions, ${exampleFiles.length} manifests, ` +
  `${energyArcCount} energy-arc points, ${registryIds.length} connectors).`
);
