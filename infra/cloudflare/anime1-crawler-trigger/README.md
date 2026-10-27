# Anime1 Crawler Cloudflare Trigger

Isolated migration candidate, following the TaiwanCalendar trigger reference.
Cloudflare Workers Cron invokes the genuine crawler workflow to refresh anime data.
There are no dummy commits, inactivity timestamps, or standalone Keepalive Actions.
The crawler still commits `docs/anime_data.json` only when its data changes.

- Schedule: `0 17 * * *` UTC, daily at 17:00 UTC (01:00 Asia/Taipei and 02:00 Asia/Tokyo the next day).
- GitHub target: `jacktdry/anime1_crawler` / `anime_crawler.yml` / `main`.
- Worker: `anime1-crawler-trigger`, with its own dedicated Cron Trigger.
- Public workers.dev and preview URLs: disabled; no routes or HTTP handler.
- Observability: enabled, including traces.
- Only runtime secret: `GITHUB_TOKEN`, stored as a Cloudflare Worker secret.

The scheduled handler defensively calls `PUT .../enable` on every invocation,
then awaits success before `POST .../dispatches` with `{"ref":"main"}`.
This also enables a workflow that has been disabled; an intentional pause must
therefore disable the Worker Cron, rather than just disable the GitHub workflow.
Missing secrets, non-204 API responses, and network errors reject the task passed
to `ctx.waitUntil`, surfacing failures in Cloudflare Cron events/logs. API errors
include the operation and status, without logging response bodies or credentials.
A success log means GitHub accepted the dispatch, not that the crawler completed.
There is no automatic dispatch retry: an ambiguous network failure may already
have created a run, so inspect GitHub before manually retrying.

## Local checks

From this directory, using Node.js 22 or newer (no dependency install needed):

```sh
node --check src/index.js
node --test
```

Tests mock all GitHub fetches and use an inert placeholder credential. They verify
enable-before-dispatch, the target/ref/authentication, and secret/API/network
failures. These checks do not deploy a Worker or prove live Cron delivery.

## Rollout order — required before merging

**Do not merge the GitHub schedule removal until the Worker secret is provisioned,
the Worker is deployed, and a real Cron-triggered crawler run is verified.**
Keep the current GitHub schedule on `main` throughout preparation. This candidate
is source-only; deployment, secret provisioning, and live verification are pending.

1. Create a fine-grained GitHub PAT with resource owner `jacktdry`, repository
   access restricted to **only `anime1_crawler`**, and repository **Actions: write**
   (the UI calls this “Read and write”). Leave other optional permissions unset;
   Metadata read is implicit. Do not use a classic PAT with broad `repo` scope,
   account-wide credentials, or grant Contents/Workflows write to this PAT.
   The crawler's existing workflow `GITHUB_TOKEN`/`contents: write` is separate
   and remains responsible for genuine data commits. Choose an expiry and rotate
   the PAT before expiry.
2. An authorized operator provisions the named Worker with no public routes and
   no Cron initially, then stores the PAT as its encrypted `GITHUB_TOKEN` secret.
   With an approved Wrangler installation and existing, appropriately scoped
   Cloudflare operator authentication, run from this directory:

   ```sh
   wrangler secret put GITHUB_TOKEN
   ```

   Enter the PAT only at the secret prompt. Never put it in source, config vars,
   command arguments, logs, chat, or committed files. No Cloudflare credentials
   belong in the Worker's runtime bindings. Do not extract existing credentials.
3. Deploy this candidate from the worktree **before merging**, using the same
   named Worker/account:

   ```sh
   wrangler deploy
   ```

   Confirm the secret binding, deployed code/config, disabled public/preview
   URLs, observability, and exactly one Cron `0 17 * * *`. Cron changes may take
   up to 15 minutes to propagate. The existing `main` workflow already supports
   `workflow_dispatch`, so pre-merge verification is possible.
4. Observe an actual scheduled invocation at 17:00 UTC in Cloudflare and correlate
   it with a `workflow_dispatch` run of `anime_crawler.yml` on `main` in GitHub.
   Confirm the crawler finishes successfully; unchanged data legitimately creates
   no commit. During this short overlap both schedulers can run: inspect both
   runs for failures or conflicting data pushes. Do not treat local tests or an
   accepted dispatch alone as deployment verification.
5. Only after that evidence is reviewed, merge the candidate removing GitHub's
   `schedule`. Keep `push`, `workflow_dispatch`, workflow permissions, and crawler
   steps unchanged. Monitor the next daily Cron and resulting crawler run.

## Rollback / pause

If preparation fails, do not merge: the original GitHub schedule stays in place.
Disable/remove the Worker's Cron while investigating. To remove it via Wrangler,
set `triggers.crons` to `[]` and deploy that config; allow propagation and verify
the trigger is gone. Disabling the GitHub workflow alone is insufficient because
the Worker enables it again.

After a merged cutover, restore the following trigger under `on` in
`.github/workflows/anime_crawler.yml` on `main` and verify GitHub scheduling is
active, then disable the Worker Cron and confirm it has stopped. Coordinate the
brief overlap and inspect active runs. If Cloudflare is unavailable, restore the
GitHub schedule first and use `workflow_dispatch` as needed until Cron removal
can be confirmed. Revoke the dedicated PAT once the Worker is retired.

```yaml
  schedule:
    - cron: '0 17 * * *'
```

References: [GitHub workflow enable/dispatch API and token permissions](https://docs.github.com/en/rest/actions/workflows),
[Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/),
and [scheduled handler error reporting](https://developers.cloudflare.com/workers/runtime-apis/handlers/scheduled/).
