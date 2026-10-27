import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import worker from "../src/index.js";

const config = JSON.parse(await readFile(new URL("../wrangler.jsonc", import.meta.url), "utf8"));
const env = { ...config.vars, GITHUB_TOKEN: "test-only-placeholder" };
const workflowUrl = "https://api.github.com/repos/jacktdry/anime1_crawler/actions/workflows/anime_crawler.yml";

async function runScheduled(bindings = env) {
  const pending = [];
  await worker.scheduled({}, bindings, {
    waitUntil(promise) {
      pending.push(promise);
    },
  });
  assert.equal(pending.length, 1);
  await Promise.all(pending);
}

test("Cron enables the crawler before dispatching main with only the Worker secret", async (t) => {
  let finishEnable;
  const enabled = new Promise((resolve) => { finishEnable = resolve; });
  const fetchMock = t.mock.method(globalThis, "fetch", async () => {
    if (fetchMock.mock.callCount() === 1) {
      await enabled;
    }
    return new Response(null, { status: 204 });
  });
  const logMock = t.mock.method(console, "log", () => {});

  const run = runScheduled();
  try {
    assert.equal(fetchMock.mock.callCount(), 1, "dispatch must wait for enable to succeed");
    assert.equal(logMock.mock.callCount(), 0);
  } finally {
    finishEnable();
  }
  await run;

  const calls = fetchMock.mock.calls;
  assert.deepEqual(calls.map(({ arguments: [url, options] }) => [url, options.method]), [
    [`${workflowUrl}/enable`, "PUT"],
    [`${workflowUrl}/dispatches`, "POST"],
  ]);
  for (const { arguments: [, options] } of calls) {
    assert.equal(options.headers.Authorization, `Bearer ${env.GITHUB_TOKEN}`);
    assert.equal(options.headers.Accept, "application/vnd.github+json");
    assert.equal(options.headers["X-GitHub-Api-Version"], "2022-11-28");
    assert.equal(options.headers["User-Agent"], "anime1-crawler-trigger");
  }
  assert.equal(calls[0].arguments[1].body, undefined);
  assert.equal(calls[1].arguments[1].headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(calls[1].arguments[1].body), { ref: "main" });
  assert.equal(logMock.mock.callCount(), 1);
});

for (const token of [undefined, "", "   "]) {
  test(`missing/blank secret fails before any GitHub request (${JSON.stringify(token)})`, async (t) => {
    const fetchMock = t.mock.method(globalThis, "fetch", () => { throw new Error("Unexpected fetch"); });
    await assert.rejects(runScheduled({ ...env, GITHUB_TOKEN: token }), /Missing GITHUB_TOKEN Worker secret/);
    assert.equal(fetchMock.mock.callCount(), 0);
  });
}

for (const stage of ["enable", "dispatch"]) {
  for (const status of [401, 403, 404, 422, 429, 500]) {
    test(`${stage} HTTP ${status} rejects the Cron task without reporting success`, async (t) => {
      const fetchMock = t.mock.method(globalThis, "fetch", async (url) => {
        if (stage === "dispatch" && url.endsWith("/enable")) {
          return new Response(null, { status: 204 });
        }
        return new Response("Untrusted response body", { status });
      });
      const logMock = t.mock.method(console, "log", () => {});
      await assert.rejects(runScheduled(), {
        message: `Failed to ${stage} workflow: ${status}`,
      });
      assert.equal(fetchMock.mock.callCount(), stage === "enable" ? 1 : 2);
      assert.equal(logMock.mock.callCount(), 0);
    });
  }

  test(`${stage} network failure rejects the Cron task`, async (t) => {
    const failure = new Error("Network unavailable");
    const fetchMock = t.mock.method(globalThis, "fetch", async (url) => {
      if (stage === "dispatch" && url.endsWith("/enable")) {
        return new Response(null, { status: 204 });
      }
      throw failure;
    });
    const logMock = t.mock.method(console, "log", () => {});
    await assert.rejects(runScheduled(), (error) => error === failure);
    assert.equal(fetchMock.mock.callCount(), stage === "enable" ? 1 : 2);
    assert.equal(logMock.mock.callCount(), 0);
  });
}
