#!/usr/bin/env node
// Visitor analytics for the docs site through @dougborg/site-analytics.
//
//   node scripts/site_analytics.mjs prepare      before `mkdocs build`
//   node scripts/site_analytics.mjs check site   after it, against the built site
//
// `prepare` reads scripts/site-analytics.json, fetches exactly the pinned package
// version, checks its tarball against the pinned registry integrity, and writes two
// gitignored files: the config element (made by the package's own configElement(),
// which validates it) plus the module tag, included by overrides/main.html, and the
// package's analytics.js under docs/assets. With an empty websiteId it removes both,
// so the site ships no tracker: that is the rollback. Local builds never run it.
//
// `check` fails if a built page lacks the privacy link, or, while tracking is on,
// the config element.
//
// This site is served from https://dougborg.org/<project>/, the blog's origin, so it
// uses the blog's Umami website ID and privacy page (one website ID per origin, see
// dougborg/site-analytics docs/consumers.md). Pin the same package version as the
// blog so the pages send exactly what that privacy notice discloses.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

const CONFIG = "scripts/site-analytics.json";
const PARTIAL = "overrides/partials/site-analytics.html";
const ASSET = "docs/assets/site-analytics/analytics.js";

const config = JSON.parse(readFileSync(CONFIG, "utf8"));

async function prepare() {
  rmSync(PARTIAL, { force: true });
  rmSync(ASSET, { force: true });
  if (!config.websiteId) {
    console.log("site-analytics: no websiteId, building without a tracker");
    return;
  }
  const work = mkdtempSync(join(tmpdir(), "site-analytics-"));
  const spec = `${config.package}@${config.version}`;
  const tarball = join(
    work,
    execFileSync("npm", ["pack", spec, "--silent", "--pack-destination", work], {
      encoding: "utf8",
    }).trim(),
  );
  const integrity = `sha512-${createHash("sha512").update(readFileSync(tarball)).digest("base64")}`;
  if (integrity !== config.integrity) {
    throw new Error(`${spec}: tarball integrity ${integrity} does not match ${CONFIG}`);
  }
  execFileSync("tar", ["-xzf", tarball, "-C", work]);
  const pkg = join(work, "package", "dist");
  const { configElement } = await import(pathToFileURL(join(pkg, "index.js")).href);
  const element = configElement({
    websiteId: config.websiteId,
    collector: config.collector,
    hostname: config.hostname,
    declaredEvents: config.declaredEvents,
  });
  mkdirSync(dirname(PARTIAL), { recursive: true });
  writeFileSync(
    PARTIAL,
    `${element}\n<script type="module" src="{{ base_url }}/assets/site-analytics/analytics.js"></script>\n`,
  );
  mkdirSync(dirname(ASSET), { recursive: true });
  copyFileSync(join(pkg, "analytics.js"), ASSET);
  rmSync(work, { recursive: true, force: true });
  console.log(`site-analytics: ${spec} prepared for ${config.hostname}`);
}

function htmlFiles(dir) {
  return readdirSync(dir, { withFileTypes: true, recursive: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".html"))
    .map((entry) => join(entry.parentPath, entry.name));
}

function check(siteDir) {
  const problems = [];
  let checked = 0;
  for (const file of htmlFiles(siteDir)) {
    const html = readFileSync(file, "utf8");
    // Only theme pages: redirect stubs and standalone files (such as an embedded
    // Swagger UI page, which runs framed, where the module never loads) are skipped.
    if (!html.includes("data-md-component")) continue;
    checked += 1;
    if (!html.includes(`href="${config.privacyUrl}"`)) {
      problems.push(`${file}: no link to ${config.privacyUrl}`);
    }
    if (config.websiteId && !html.includes('id="site-analytics"')) {
      problems.push(`${file}: no site-analytics config element`);
    }
  }
  if (checked === 0) problems.push(`${siteDir}: no theme pages found`);
  if (problems.length) {
    console.error(problems.join("\n"));
    process.exit(1);
  }
  console.log(`site-analytics: ${checked} theme pages checked`);
}

const [command, arg] = process.argv.slice(2);
if (command === "prepare") await prepare();
else if (command === "check" && arg) check(arg);
else {
  console.error("usage: site_analytics.mjs prepare | check <site-dir>");
  process.exit(2);
}
