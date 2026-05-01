import type { CreateSessionResponse, SessionSnapshot } from "./contracts";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function apiBaseUrl(): string {
  return (process.env.ROOM_SCANNER_API_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export async function createSession(): Promise<CreateSessionResponse> {
  const response = await fetch(`${apiBaseUrl()}/sessions`, {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Session creation failed with HTTP ${response.status}`);
  }

  return response.json() as Promise<CreateSessionResponse>;
}

export async function getSession(sessionId: string): Promise<SessionSnapshot> {
  const response = await fetch(`${apiBaseUrl()}/sessions/${encodeURIComponent(sessionId)}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Session fetch failed with HTTP ${response.status}`);
  }

  return response.json() as Promise<SessionSnapshot>;
}

export async function startProcessing(sessionId: string): Promise<SessionSnapshot> {
  const response = await fetch(`${apiBaseUrl()}/sessions/${encodeURIComponent(sessionId)}/processing/start`, {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Processing start failed with HTTP ${response.status}`);
  }

  return response.json() as Promise<SessionSnapshot>;
}
