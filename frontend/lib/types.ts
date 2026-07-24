export type PersonaKey = "junior_dev" | "eng_manager";

export interface Persona {
  key: PersonaKey;
  displayName: string;
  title: string;
  roles: string[];
  groups: string[];
}

export const PERSONAS: Record<PersonaKey, Persona> = {
  junior_dev: {
    key: "junior_dev",
    displayName: "Alex Chen",
    title: "Junior Developer",
    roles: ["dev"],
    groups: ["eng-payments"],
  },
  eng_manager: {
    key: "eng_manager",
    displayName: "Sarah Patel",
    title: "Engineering Manager",
    roles: ["management", "dev"],
    groups: ["eng-payments", "management"],
  },
};

export interface SourceCitation {
  title: string;
  source_type: string;
  source_url: string;
  author: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceCitation[];
  confidence: number;
  access_denied: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  confidence?: number;
  accessDenied?: boolean;
}

export interface SMEEntry {
  author: string;
  domains: string[];
  document_count: number;
}
