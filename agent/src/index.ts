import { Agent, getAgentByName, routeAgentRequest } from "agents";
import type { DurableObjectNamespace, ExportedHandler } from "@cloudflare/workers-types";

export interface Env {
  AI: any; // Workers AI binding
  MyAgent: DurableObjectNamespace; // DO binding
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Optional: agents routing
    const routed = await routeAgentRequest(request as any, env as any);
    if (routed) return routed as Response;

    // Your API endpoint
    if (url.pathname === "/ask" && request.method === "POST") {
      const body = (await request.json().catch(() => ({}))) as any;
      const question = String(body?.question ?? "").trim();
      const leaseText = String(body?.leaseText ?? "").trim();

      if (!question) {
        return Response.json({ detail: "question is required" }, { status: 400 });
      }

      const stub = await getAgentByName<Env, MyAgent>(env.MyAgent, "default");
      const answer = await stub.chat(question, leaseText);

      return Response.json({ answer });
    }

    return Response.json({ msg: "Not found" }, { status: 404 });
  },
} as unknown as ExportedHandler<Env>;

export class MyAgent extends Agent<Env> {
  async chat(question: string, leaseText?: string): Promise<string> {
    const systemPrompt = `
You are ClauseBot, a friendly legal assistant.
Answer questions using ONLY the lease content the user provides.
If the lease does not clearly say it, reply exactly: "Not clearly specified in the lease."
No headings, no labels, no markdown.
`.trim();

    const userContent = leaseText
      ? `LEASE:\n${leaseText}\n\nQUESTION:\n${question}`
      : `QUESTION:\n${question}\n\n(If no lease text is provided, reply: "Not clearly specified in the lease.")`;

    const result = await (this as any).env.AI.run("@cf/meta/llama-3.3-70b-instruct", {
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userContent },
      ],
    });

    return (
      result?.response ??
      result?.result ??
      result?.output_text ??
      (typeof result === "string" ? result : "Not clearly specified in the lease.")
    );
  }
}
