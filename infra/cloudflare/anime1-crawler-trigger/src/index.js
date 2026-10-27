const GITHUB_API = "https://api.github.com";

function githubHeaders(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "anime1-crawler-trigger",
  };
}

async function ensureWorkflowEnabled(env) {
  const url = `${GITHUB_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW}/enable`;
  const response = await fetch(url, {
    method: "PUT",
    headers: githubHeaders(env.GITHUB_TOKEN),
  });

  if (response.status !== 204) {
    throw new Error(`Failed to enable workflow: ${response.status}`);
  }
}

async function dispatchWorkflow(env) {
  const url = `${GITHUB_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW}/dispatches`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...githubHeaders(env.GITHUB_TOKEN),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ref: env.GITHUB_REF }),
  });

  if (response.status !== 204) {
    throw new Error(`Failed to dispatch workflow: ${response.status}`);
  }
}

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil((async () => {
      if (!env.GITHUB_TOKEN || !env.GITHUB_TOKEN.trim()) {
        throw new Error("Missing GITHUB_TOKEN Worker secret");
      }

      await ensureWorkflowEnabled(env);
      await dispatchWorkflow(env);
      console.log(JSON.stringify({ message: "Anime1 crawler workflow dispatched successfully" }));
    })());
  },
};
