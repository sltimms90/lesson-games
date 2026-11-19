/* Entry point (the logic and its notes are in plan.ts). */
import { handle } from "./plan.ts";
Deno.serve((req) => handle(req));
