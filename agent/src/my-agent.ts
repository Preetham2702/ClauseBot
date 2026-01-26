import { Agent } from "@cloudflare/agents";
import { DurableObjectState } from "@cloudflare/workers-types";

export class MyAgent {
  state: DurableObjectState;
  env: any;
  agent: any;

  constructor(state: DurableObjectState, env: any) {
    this.state = state;
    this.env = env;

    this.agent = new Agent("clausebot", {
      ai: env.AI,
      systemPrompt: `
You are ClauseBot, a friendly legal assistant.
Answer questions using ONLY the lease content the user provides.
If the lease does not clearly say it, reply: "Not clearly specified in the lease."
No headings, no labels, no markdown.
      `.trim(),
    });
  }

  async fetch(request: Request) {
    return this.agent.fetch(request);
  }
}
