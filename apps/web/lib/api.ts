import type { CreateSessionResponse } from "./contracts";

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
