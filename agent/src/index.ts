import { Agent } from "@cloudflare/agents";

export interface Env {
  AI: any; // Workers AI binding
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Create ClauseBot agent
    const agent = new Agent("clausebot", {
      ai: env.AI,

      systemPrompt: `
You are ClauseBot, a friendly legal assistant.

Rules:
- Answer questions using ONLY the lease content provided by the user.
- If the lease does not clearly specify something, reply exactly:
  "Not clearly specified in the lease."
- Do not add headings, labels, markdown, or legal advice.
- Keep responses clear, concise, and user-friendly.
      `.trim(),
    });

    // Let the agent handle the request
    return agent.fetch(request);
  },
};
