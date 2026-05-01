"use client";

import { useEffect, useMemo, useState } from "react";

import { CapabilityPanel } from "./capability-panel";
import { DiagnosticsPanel } from "./diagnostics-panel";
import { TelemetryPanel } from "./telemetry-panel";
import type { SessionSnapshot } from "../lib/contracts";

const POLL_INTERVAL_MS = 2_000;

export function SessionMonitor({ initialSession }: { initialSession: SessionSnapshot }) {
  const [session, setSession] = useState(initialSession);
  const [pollError, setPollError] = useState<string | null>(null);
  const shouldPoll = initialSession.session_id !== "unavailable";

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }

    let isMounted = true;

    async function fetchSession() {
      try {
        const response = await fetch(`/api/sessions/${encodeURIComponent(initialSession.session_id)}`, {
          headers: { Accept: "application/json" },
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Session refresh failed with HTTP ${response.status}`);
        }

        const nextSession = (await response.json()) as SessionSnapshot;
        if (isMounted) {
          setSession(nextSession);
          setPollError(null);
        }
      } catch (error) {
        if (isMounted) {
          setPollError(error instanceof Error ? error.message : "Session refresh failed");
        }
      }
    }

    void fetchSession();
    const interval = window.setInterval(fetchSession, POLL_INTERVAL_MS);

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [initialSession.session_id, shouldPoll]);

  const liveMessage = useMemo(() => {
    if (pollError) {
      return `Session refresh blocked: ${pollError}`;
    }
    if (session.state === "SCANNING") {
      if (session.telemetry.frame_count > 0) {
        return `Backend accepted scan start. Live telemetry received ${session.telemetry.frame_count} samples.`;
      }
      return "Backend accepted scan start. Waiting for Android telemetry.";
    }
    if (session.capability_report) {
      return `Session ${session.state}. Capability report received.`;
    }
    return "Waiting for Android capability report.";
  }, [pollError, session.capability_report, session.state, session.telemetry.frame_count]);

  return (
    <>
      <p className={pollError ? "network-note error" : "network-note"} role="status" aria-live="polite">
        {liveMessage}
      </p>
      <CapabilityPanel report={session.capability_report} lastError={session.last_error} state={session.state} />
      <TelemetryPanel state={session.state} telemetry={session.telemetry} />
      <DiagnosticsPanel session={session} />
    </>
  );
}
