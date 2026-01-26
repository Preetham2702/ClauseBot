import { Agent } from "@cloudflare/agents";

export default {
  async fetch(request: Request, env: any) {
    const agent = new Agent("clausebot", {
      ai: env.AI,
      systemPrompt: `
You are ClauseBot, a friendly legal assistant.
Answer questions using ONLY the lease content the user provides.
If the lease does not clearly say it, reply: "Not clearly specified in the lease."
No headings, no labels, no markdown.
      `
    });

    return agent.fetch(request);
  }
};
