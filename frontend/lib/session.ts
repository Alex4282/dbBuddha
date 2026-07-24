import { PersonaKey } from "./types";

const STORAGE_KEY = "nexusmind_session";

export interface Session {
  token: string;
  persona: PersonaKey;
}

/**
 * Thin localStorage wrapper standing in for a real session cookie.
 * Swapping this for NextAuth/Auth0 session state later is a change
 * confined to this file and the login page — nothing downstream cares
 * how the token was obtained.
 */
export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function setSession(session: Session): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}
