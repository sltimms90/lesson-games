/* Entry point (the logic and its notes are in guest.ts). */
import { handle } from "./guest.ts";
Deno.serve((req) => handle(req));
