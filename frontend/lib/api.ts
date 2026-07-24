import { PersonaKey, QueryResponse, SMEEntry } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * Exchanges the active persona for a bearer JWT.
 *
 * In production this is replaced by NextAuth/Auth0's session token — the
 * rest of this file (and the backend) doesn't change, since both only ever
 * deal in "a bearer token", never in raw role/group strings from the client.
 */
export async function getPersonaToken(persona: PersonaKey): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/auth/mock-token?persona=${persona}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to mint token for persona '${persona}'`);
  const data = await res.json();
  return data.access_token as string;
}

export async function queryKnowledgeBase(query: string, token: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Query failed with status ${res.status}`);
  return res.json();
}

export async function getSmeDirectory(): Promise<SMEEntry[]> {
  const res = await fetch(`${API_BASE}/api/v1/sme`);
  if (!res.ok) throw new Error("Failed to load SME directory");
  return res.json();
}
