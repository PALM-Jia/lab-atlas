"use strict";
const fs = require("node:fs"),
  path = require("node:path"),
  http = require("node:http"),
  assert = require("node:assert/strict");
const args = process.argv.slice(2),
  siteIndex = args.indexOf("--site");
const site = path.resolve(
  siteIndex < 0
    ? path.join(__dirname, "../../outputs/paper-atlas")
    : args[siteIndex + 1],
);
const modulePath =
  process.env.PLAYWRIGHT_MODULE ||
  "C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright";
const { chromium } = require(modulePath);
const server = http.createServer((req, res) => {
  const requested = decodeURIComponent(
    new URL(req.url, "http://127.0.0.1").pathname,
  );
  const file = path.resolve(site, "." + requested);
  if (!file.startsWith(site + path.sep)) {
    res.writeHead(403);
    return res.end();
  }
  fs.readFile(file, (err, body) => {
    const type =
      {
        ".html": "text/html",
        ".js": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
      }[path.extname(file)] || "application/octet-stream";
    res.writeHead(err ? 404 : 200, { "Content-Type": type });
    res.end(err ? "Missing" : body);
  });
});
(async () => {
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  let browser;
  const errors = [],
    pages = [];
  try {
    const options = { headless: true, args: ["--enable-unsafe-swiftshader"] };
    if (process.env.PLAYWRIGHT_EXECUTABLE)
      options.executablePath = process.env.PLAYWRIGHT_EXECUTABLE;
    browser = await chromium.launch(options);
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
    });
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => {
      if (m.type() === "error") errors.push(m.text());
    });
    page.on("response", (r) => {
      if (r.status() >= 400 && !r.url().endsWith("/favicon.ico"))
        errors.push(r.status() + " " + r.url());
    });
    const base = args.includes("--file")
      ? require("node:url")
          .pathToFileURL(site + path.sep)
          .href.replace(/\/$/, "")
      : "http://127.0.0.1:" + server.address().port;
    await page.route("**/*", (route) =>
      route.request().url().startsWith(base) ? route.continue() : route.abort(),
    );
    await page.goto(base + "/index.html");
    await page.waitForFunction(
      () => document.getElementById("visible-count")?.textContent,
    );
    const counts = await page.locator("#visible-count").innerText();
    await page.locator("#search").fill("unmatchable_migration_check_98a14");
    await page.waitForFunction(
      () => !document.getElementById("empty").classList.contains("hidden"),
    );
    await page.locator("#search").fill("");
    await page.locator("#relation").selectOption("semantic");
    await page.waitForFunction(
      () =>
        document.getElementById("relation").value === "semantic" &&
        document.getElementById("graph")._cyreg?.cy?.edges().length > 0,
    );
    await page.evaluate(() =>
      document.getElementById("graph")._cyreg.cy.edges().first().emit("tap"),
    );
    assert(
      (await page.locator("#detail-content").innerText()).length > 0,
      "Graph edge opens details",
    );
    await page.locator('[data-view="authors"]').click();
    await page.locator("#author-relation").selectOption("semantic");
    await page.locator("#first-author-only").click();
    await page.locator('[data-view="timeline"]').click();
    await page.locator('[data-view="papers"]').click();
    pages.push({
      page: "index.html",
      initial: counts,
      filter_details_views: true,
    });
    await page.goto(base + "/retrieval.html");
    await page.waitForFunction(() =>
      document.querySelector("#table-body [data-paper]"),
    );
    const before = await page.locator("#table-body tr").count();
    await page.locator("#search").fill("unmatchable_migration_check_98a14");
    await page.waitForFunction(
      () => document.getElementById("empty").hidden === false,
    );
    await page.locator("#search").fill("");
    await page.locator("#table-body [data-paper]").first().click();
    await page.waitForFunction(() => !document.getElementById("detail").hidden);
    assert((await page.locator("#detail-content").innerText()).length > 0);
    await page.locator("#close-detail").click();
    pages.push({ page: "retrieval.html", rows: before, filter_details: true });
    await page.goto(base + "/workflow.html");
    await page.waitForFunction(() =>
      document.querySelector("#lifecycle-board [data-flow-node]"),
    );
    const node = page.locator("[data-flow-node]").first();
    await node.click();
    assert.equal(await node.getAttribute("aria-pressed"), "true");
    assert((await page.locator("#selection-caption").innerText()).length > 0);
    await page.keyboard.press("Escape");
    assert(await page.locator("#clear").isHidden());
    const edge = page.locator("[data-flow-edge]").first();
    await edge.focus();
    await page.keyboard.press("Enter");
    assert.equal(await edge.getAttribute("aria-pressed"), "true");
    await page.locator("#clear").click();
    assert.equal(await edge.getAttribute("aria-pressed"), "false");
    pages.push({ page: "workflow.html", node_click_edge_keyboard_clear: true });
    assert.equal(errors.length, 0, errors.join("\n"));
    console.log(JSON.stringify({ site, pages, errors }));
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
})().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
