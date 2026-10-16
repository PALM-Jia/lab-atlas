# Current checks

Run after the offline build from the repository root, with Node.js:

```powershell
Get-ChildItem scripts/checks -Filter '*.cjs' | Where-Object { $_.Name -notin @('frontend-fixture.cjs','check-browser.cjs','check-timeline-browser.cjs','check-timeline-selection-browser.cjs','check-migration.cjs') } | ForEach-Object { node $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Check failed: $($_.Name)" } }
```

- test-keyword-network: independent synthetic fixtures for contribution weights, accepted empty/excluded states, task profiles, quotes, IDF, top-five union and external scope.
- check-reviewed-keyword-integration: adopted data/atlas JSON parity with retrieval rows and independently recomputed keyword author profiles; executes browser relation modules.
- check_all_relations_top5: independently ranked synthetic candidates and ten live application view/relation combinations, including laboratory scope and per-end selection limits.
- check_first_author_filter: current three-state first-author selection, contribution weights and restoration.
- check_author_semantic_current: recomputes every displayed author semantic score and supporting pair count, then checks evidence navigation and authorship controls.
- check_search_match: hyphen/whitespace/case/fullwidth normalization and unrelated-word rejection.
- check_flow_structure: executes current workflow renderer and checks forward orthogonal routes and node collisions.
- check-timeline-history: independently tallies annual citations, preserves missing/empty/neighborhood scopes, rejects future publications before per-year top-five selection; its Python counterpart checks producer deduplication and unknown years.
- check-timeline-layout: orthographic projection, upward Z chronology, continuous Bezier tangents, ellipse/curve hit testing and viewport fitting.
- check-timeline-painter: records actual canvas drawing commands to verify chronological occlusion, within-year depth, same-year paper relations, cross-year paper continuity and upper-plane hit occlusion.
- check-timeline-selection: exact annual instance anchors, simultaneous activation across visible years, unique upward relations from the earliest visible instance, with matching endpoints, highlights and details for every relation, edge-click anchor preservation, solid/dashed thin lines and citation-based size contrast.

frontend-fixture executes every external script in index.html in page order, including paper-fields and keyword-relations. Real Cytoscape runs headlessly; DOM, layout installation and WebGL rendering use adapters. These checks validate application data, graph computation and event handlers; they do not certify browser layout, visual styling or WebGL rendering. No check performs network requests or writes reports into work.

check-migration.cjs is a historical v1.0 migration check. It compares 22 old fact files against the pre-two-source byte baseline and is expected to fail after adopting the current two-source snapshot; it is excluded from the current-check command above. The removed relations-full duplicate is excluded explicitly.

check-semantic-provenance.cjs recomputes every adopted title/abstract digest and model/input vector key, then validates actual vector files, pinned model revisions, dimensions, finite values, L2 normalization, generation coverage and retrieval provenance.

`python -B scripts/checks/test-semantic-refresh.py` uses an isolated fixture and stubbed inference to verify cached refresh without an existing report directory, changed input propagation, explained failure with cleared stale input, and preservation of unrelated retrieval/network evidence.

Browser runtime checks (no installation):

```powershell
$env:PLAYWRIGHT_MODULE = "C:/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright"
$env:PLAYWRIGHT_EXECUTABLE = "C:/Users/lee/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe"
node scripts/checks/check-browser.cjs --site work/rebuild-preview
node scripts/checks/check-browser.cjs --site work/rebuild-preview --file
node scripts/checks/check-timeline-browser.cjs
node scripts/checks/check-timeline-selection-browser.cjs
```

The browser check serves the selected directory on localhost, or opens it directly with file:// when --file is supplied. It blocks remote requests, exercises all three pages and reports JavaScript/console/HTTP errors. PLAYWRIGHT_EXECUTABLE is optional when the bundled Playwright browser is available. Browser process launch can be blocked by sandbox permissions (spawn EPERM); this is an execution limitation, not a passed browser check.
