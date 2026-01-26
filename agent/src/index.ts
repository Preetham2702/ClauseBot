export { MyAgent } from "./my-agent.js";

export default {
  async fetch(request: Request, env: any) {
    const id = env.MyAgent.idFromName("clausebot"); // one global agent
    const stub = env.MyAgent.get(id);
    return stub.fetch(request);
  },
};
